# common/agent.py

import requests
import time
import sys
import select
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
# common/agent.py
from common.messenger import (
    send_message,
    receive_messages,
    archive_inbox,
)

OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "phi3"

def get_response_from_phi(prompt: str, assistant_name: str = "assistant") -> str:
    """Send prompt to local Phi-3 model via Ollama and return response."""
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
        return f"⚠️ Error communicating with {MODEL_NAME}: {str(e)}"

def handle_handshake(self_id: str, peer_id: str, received_from: str, msg_text: str):
    """Reply only to the first Handshake Init; ignore ACKs."""
    if received_from != peer_id:
        return                               # not our peer

    if msg_text == "Handshake Init":
        print(f"🤝 {self_id} got handshake from {peer_id}")
        send_message(
            to=peer_id,
            sender=self_id,
            message="Handshake ACK",
            msg_type="handshake"
        )

def handle_user_input(self_id: str, peer_id: str, user_input: str):
    print(f"👤 You: {user_input}")
    send_message(
        to=peer_id,
        sender=self_id,
        message=user_input,
        msg_type="bot",
        user_initiated=True
    )
    wait_for_peer_response(self_id)

def handle_incoming_message(self_id: str, peer_id: str, msg: dict):
    msg_type = msg.get("type")
    msg_sender = msg.get("from")
    msg_text = msg.get("message")

    if not (msg_type and msg_sender and msg_text):
        print(f"⚠️ Malformed message ignored: {msg}")
        return

    if msg_type == "handshake":
        handle_handshake(self_id, peer_id, msg_sender, msg_text)
        return


    elif msg_type == "bot":
        if msg_sender == self_id or not msg.get("user_initiated", False):
            return  # Ignore own bot messages
        print(f"📩 {msg_sender} → {self_id}: {msg_text}")
        response = get_response_from_phi(msg_text, assistant_name=self_id)
        print(f"🧠 {self_id}: {response}")
        send_message(
            to=peer_id,
            sender=self_id,
            message=response,
            msg_type="bot",
            user_initiated=False
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
