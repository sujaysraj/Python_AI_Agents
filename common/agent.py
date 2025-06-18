# common/agent.py
import requests
import time
import hmac
import hashlib
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parent.parent))

from common.transport import FileTransport
from common.messenger import Messenger

# Load environment variables
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "fallbackkey").encode()
OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "mistral"


def compute_hmac(message: str) -> str:
    return hmac.new(SECRET_KEY, message.encode(), hashlib.sha256).hexdigest()


def get_response_from_phi(prompt: str) -> str:
    if not prompt.strip():
        return ""

    SYSTEM_PROMPT = (
        "You are a concise, polite AI assistant. "
        "Reply in under 3 sentences. Avoid lists or greetings unless asked."
    )

    try:
        full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {prompt}\nAssistant:"
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.6,
                    "top_p": 0.9,
                    "num_predict": 80  # keeps it short
                }
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip()
    except Exception as e:
        print(f"[ERROR] get_response_from_phi: {e}")
        return f"⚠️ Error: {e}"


def send_text(sender: str, to: str, text: str, user_initiated: bool = True, messenger: Messenger = None) -> None:
    if not text.strip():
        print(f"⚠️  {sender} tried to send empty message — skipped.")
        return

    msg_type = "user" if user_initiated else "bot"

    messenger.send(
        to=to,
        message=text,
        msg_type=msg_type,
        user_initiated=user_initiated,
    )


def handle_handshake(self_id: str, peer_id: str, msg: dict, messenger: Messenger):
    sender = msg.get("from")
    message = msg.get("message")
    sig = msg.get("hmac_sig")
    if compute_hmac(message) != sig:
        print(f"🚨 {self_id} HMAC mismatch for handshake from {sender}")
        return
    print(f"🤝 {self_id} got handshake from {sender}")
    messenger.send(
        to=sender,
        sender=self_id,
        message="Handshake ACK",
        msg_type="handshake",
    )


def handle_bot_message(self_id: str, peer_id: str, msg: dict, messenger: Messenger):
    sender = msg.get("from")
    text = msg.get("message")
    sig = msg.get("hmac_sig")

    if sender == self_id or not msg.get("user_initiated", False):
        return

    if compute_hmac(text) != sig:
        print(f"🚨 {self_id} HMAC mismatch for message from {sender}")
        return

    print(f"📩 {sender} → {self_id}: {text}")
    response = get_response_from_phi(text)
    print(f"🧠 {self_id}: {response}")
    messenger.send(
        to=sender,  # reply to sender of original message
        message=response,
        msg_type="bot",
        user_initiated=False,
    )


def dispatch_message(self_id: str, peer_id: str, msg: dict, messenger: Messenger):
    mtype = msg.get("type")
    if not msg.get("message", "").strip():
        print(f"⚠️  {self_id} received empty message, ignoring.")
        return

    if mtype == "handshake":
        handle_handshake(self_id, peer_id, msg, messenger)
    elif mtype in ("bot", "user"):
        handle_bot_message(self_id, peer_id, msg, messenger)
    else:
        print(f"⚠️ {self_id}: Unknown message type {mtype}")


def run_loop(self_id: str, peer_id: str):
    global transport
    inbox_dir = Path(__file__).resolve().parent.parent / "inbox"
    transport = FileTransport(inbox_dir)
    messenger = Messenger(name=self_id, transport=transport, secret_key=SECRET_KEY)

    print(f"🟢 {self_id} ready. Talking to {peer_id}. Type /exit to quit.")
    try:
        while True:
            msg = input().strip()
            if msg.lower() in {"/exit", "exit", ":q"}:
                print(f"👋 {self_id} exiting.")
                break
            if msg:
                send_text(self_id, peer_id, msg, user_initiated=True, messenger=messenger)

            # Process incoming
            message = messenger.receive()
            if message:
                dispatch_message(self_id, peer_id, message, messenger)
                time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n👋 {self_id} interrupted. Exiting.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True, help="This assistant's name")
    parser.add_argument("--peer", required=True, help="Peer assistant's name")
    args = parser.parse_args()

    run_loop(args.id, args.peer)
