# assistant_a or assistant_b/main.py

import os
import sys
import time
import threading
import asyncio
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parent.parent))

from common.messenger import Messenger
from common.signaling_handshake import connect
from common.agent import get_response_from_phi

NAME = Path(__file__).resolve().parent.name
PEER = "assistant_a" if NAME == "assistant_b" else "assistant_b"
PEER_URL = os.environ["PEER_URL"]
PORT = os.environ["PORT"]
print(f"[{NAME}] 🚀 Will send messages to {PEER_URL} on {PORT}")

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    print("❌ ERROR: SECRET_KEY not set in environment.")
    sys.exit(1)

messenger = Messenger(
    self_name=NAME,
    peer_name=PEER,
    peer_url=PEER_URL,
    shared_key=SECRET_KEY,
    port=PORT
)

def poll_for_incoming():
    while True:
        incoming = messenger.receive_messages()
        for msg in incoming:
            sender = msg["from"]
            content = msg["plaintext"]
            if msg.get("user_initiated", False):
                print(f"[{NAME}] 💬 {sender} says: {content}")
                response = get_response_from_phi(content)
                print(f"[{NAME}] 🤖 Responding with: {response}")
                messenger.send_message(to=sender, message=response, user_initiated=False)
            else:
                print(f"[{NAME}] 🤖 Got reply from {sender}: {content}")
        time.sleep(1)

threading.Thread(target=poll_for_incoming, daemon=True).start()

print(f"[{NAME}] You can start chatting with {PEER} (Ctrl+C to exit)")
try:
    while True:
        user_input = input("> ").strip()
        if user_input:
            messenger.send_message(
                to=PEER,
                message=user_input,
                user_initiated=True
            )
except KeyboardInterrupt:
    print("\n[Exit]")
