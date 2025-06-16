# common/agent.py

import requests
import time
import hmac
import hashlib
import sys
import select
from dotenv import load_dotenv
import os
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from common.messenger import (
    send_message,
    receive_messages,
    archive_inbox,
)
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "fallbackkey").encode()

OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "phi3"

def get_response_from_phi(prompt: str, assistant_name: str = "assistant", retries: int = 3, backoff: float = 1.0) -> str:
    """Send prompt to local Phi-3 model via Ollama with retry logic and return response."""
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": MODEL_NAME,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except requests.RequestException as e:
            if attempt < retries:
                    print(f"⚠️ Attempt {attempt} failed: {e}. Retrying in {backoff} seconds...")
                    time.sleep(backoff)
                    backoff *= 2  # Exponential backoff
            else:
                return f"❌ Failed to get response from {MODEL_NAME} after {retries} attempts: {e}"

def compute_hmac(message: str) -> str:
    """Compute HMAC-SHA256 for a given message using SECRET_KEY."""
    return hmac.new(SECRET_KEY, message.encode(), hashlib.sha256).hexdigest()



def handle_handshake(self_id: str, peer_id: str, received_from: str, message: str, provided_sig: str):
    expected_sig = compute_hmac(message)
    print(f"🔐 {self_id} expected HMAC: {expected_sig} for message: {message}")

    if provided_sig != expected_sig:
        print(f"🚨 {self_id} HMAC mismatch!\nExpected: {expected_sig}\nReceived: {provided_sig}\nMessage ignored.")
        return

    print(f"✅ {self_id} HMAC verified for handshake from {received_from}")
    print(f"🤝 {self_id} got handshake from {received_from}")

    # ✅ Only respond if it's an initial handshake, not an ACK
    if received_from == peer_id and message.strip() == "Handshake Init":
        send_message(
            to=peer_id,
            sender=self_id,
            message="Handshake ACK",
            msg_type="handshake",
            hmac_sig=compute_hmac("Handshake ACK")
        )


def handle_user_input(self_id: str, peer_id: str, user_input: str):
    print(f"👤 You: {user_input}")
    send_message(
        to=peer_id,
        sender=self_id,
        message=user_input,
        msg_type="bot",
        user_initiated=True,
        hmac_sig=compute_hmac(user_input)
    )
    wait_for_peer_response(self_id)

def handle_incoming_message(self_id: str, peer_id: str, msg: dict):
    msg_type = msg.get("type")
    msg_sender = msg.get("from")
    msg_text = msg.get("message")
    provided_sig = msg.get("hmac_sig")

    if not (msg_type and msg_sender and msg_text):
        print(f"⚠️ Malformed message ignored: {msg}")
        return

    if msg_type == "handshake":
        handle_handshake(
            self_id=self_id,
            peer_id=peer_id,
            received_from=msg_sender,
            message=msg_text,
            provided_sig=provided_sig
        )
        archive_inbox(self_id)
        return

    elif msg_type == "bot":
        expected_sig = compute_hmac(msg_text)
        print(f"🔐 {self_id} expected HMAC: {expected_sig} for message: {msg_text}")

        if msg_sender == self_id or not msg.get("user_initiated", False):
            return  # avoid echo or loop

        if provided_sig != expected_sig:
            print(f"🚨 {self_id} HMAC mismatch!\nExpected: {expected_sig}\nReceived: {provided_sig}\nMessage ignored.")
            return

        print(f"✅ {self_id} HMAC verified for message from {msg_sender}")
        print(f"📩 {msg_sender} → {self_id}: {msg_text}")
        response = get_response_from_phi(msg_text, assistant_name=self_id)
        print(f"🧠 {self_id}: {response}")
        send_message(
            to=peer_id,
            sender=self_id,
            message=response,
            msg_type="bot",
            user_initiated=False,
            hmac_sig=compute_hmac(response)
        )

    else:
        print(f"⚠️ Unknown message type: {msg_type}")


def wait_for_peer_response(self_id: str):
    for _ in range(5):
        time.sleep(1)
        messages = receive_messages(self_id) or []
        for msg in messages:
            if msg.get("type") == "bot" and msg.get("from") != self_id:
                print(f"📩 {msg['from']} → {self_id}: {msg['message']}")
                return
    archive_inbox(self_id)

def run_loop(self_id: str, peer_id: str):
    """
    Continuous loop:
      • Checks stdin non‑blocking for user input.
      • Always polls inbox for new messages every 0.5 s.
      • /exit quits cleanly.
    """
    print("💬 Type your message (or /exit to quit):")
    try:
        while True:
            # ── 1) Non‑blocking user input
            if select.select([sys.stdin], [], [], 0)[0]:
                user_input = sys.stdin.readline().strip()
                if user_input.lower() in {"/exit", "exit", "quit", ":q"}:
                    print(f"👋 {self_id} exiting.")
                    break
                if user_input:
                    handle_user_input(self_id, peer_id, user_input)

            # ── 2) Always poll for new messages
            messages = receive_messages(self_id) or []
            for msg in messages:
                handle_incoming_message(self_id, peer_id, msg)

            time.sleep(0.5)

    except KeyboardInterrupt:
        print(f"\n👋 {self_id} interrupted. Exiting.")
