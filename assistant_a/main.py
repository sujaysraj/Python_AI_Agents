import os, sys, time, threading
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from common.messenger import Messenger
from common.transport import FileTransport
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")


transport = FileTransport("inbox")
messenger = Messenger(name="assistant_a", transport=transport, secret_key=SECRET_KEY)
print(f"[{messenger.name}] Using SECRET_KEY = {repr(SECRET_KEY)}")

# ── Background thread to poll for messages ──
def poll_for_incoming():
    from common.agent import get_response_from_phi
    while True:
        incoming = messenger.receive()
        if incoming:
            print(f"[assistant_a] Got message from {incoming['sender']}: {incoming['message']}")
            if not incoming.get("user_initiated", False):
                print(f"[assistant_a] Skipping response — not user-initiated.")
                continue
            reply = get_response_from_phi(incoming["message"])
            if reply:
                messenger.send(to=incoming["sender"], message=reply, msg_type="bot", user_initiated=False)
        time.sleep(1)

threading.Thread(target=poll_for_incoming, daemon=True).start()

# ── CLI for manual input ──
while True:
    msg = input("[assistant_a] Type a message to send (or 'exit'): ").strip()
    if msg.lower() == "exit":
        break
    messenger.send(to="assistant_b", message=msg, user_initiated=True, msg_type="user")
