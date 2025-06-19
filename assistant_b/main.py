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

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

NAME = Path(__file__).resolve().parent.name  # 'assistant_a' or 'assistant_b'
PEER = "assistant_b" if NAME == "assistant_a" else "assistant_a"

# Prepare asyncio loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# ── Boot WebRTC ──
print(f"[{NAME}] Using key {SECRET_KEY!r} – starting handshake…")
outbound, inbound = loop.run_until_complete(connect(NAME, PEER, SECRET_KEY))

# ── Start Messenger ──
from common.transport import BaseTransport  # type: ignore

class CombinedTransport(BaseTransport):
    def __init__(self, outbound, inbound):
        self.outbound = outbound
        self.inbound = inbound

    async def send_message(self, *args, **kwargs):
        return await self.outbound.send_message(*args, **kwargs)

    async def receive_messages(self, recipient):
        return await self.inbound.receive_messages(recipient)

    def archive_inbox(self, recipient):
        return

    def clear_inbox(self, recipient):
        return

    def peek_messages(self, recipient):
        return []

transport = CombinedTransport(outbound, inbound)
messenger = Messenger(self_name=NAME, shared_key=SECRET_KEY)

# ── Background thread to poll messages ──
def poll_for_incoming():
    while True:
        incoming = messenger.receive_messages()
        for msg in incoming:
            sender = msg["from"]
            content = msg["plaintext"]
            if msg.get("user_initiated", False):
                print(f"\033[94m[{NAME}] 💬 {sender} says: {content}\033")
                
                # 🔥 Call local AI to generate response
                response = get_response_from_phi(content)
                print(f"\033[94m[{NAME}] 🤖 Responding with: {response}\033")
                messenger.send_message(
                    to=sender,
                    message=response,
                    user_initiated=False  # since it's an auto-reply
                )
            else:
                print(f"\033[94m[{NAME}] 🤖 Got reply from {sender}: {content}\033")
        time.sleep(1)

threading.Thread(target=poll_for_incoming, daemon=True).start()

if __name__ == "__main__":
    threading.Thread(target=poll_for_incoming, daemon=True).start()
    print(f"\033[94m[{NAME}] You can start chatting with {PEER} (Ctrl+C to exit)\033")

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

