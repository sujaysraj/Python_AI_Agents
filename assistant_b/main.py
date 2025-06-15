# assistant_b/main.py

import time
import json
import sys
from pathlib import Path
import queue
import threading

# Ensure the project root is in the import path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from common.messenger import send_message, receive_messages, init_conversation
from common.agent import run_assistant

SELF_ID = "assistant_b"
PEER_ID = "assistant_a"

init_conversation(SELF_ID)
with open(f"inbox/{SELF_ID}.json", "w") as f:
    json.dump([], f)

# stdin listener
user_q: queue.Queue[str] = queue.Queue()
def _stdin_listener():
    for line in sys.stdin:
        line = line.strip()
        if line:
            user_q.put(line)
threading.Thread(target=_stdin_listener, daemon=True).start()

# B waits for A's handshake
handshake_done = False
print(f"🤖 {SELF_ID} active")

while True:
    # keyboard input → peer
    try:
        line = user_q.get_nowait()
    except queue.Empty:
        line = None
    if line:
        print(f"👤 You: {line}")
        send_message(to=PEER_ID, sender=SELF_ID, message=line,
                     msg_type="bot", user_initiated=True)

    # inbox processing
    msgs = receive_messages(SELF_ID) or []
    for m in msgs:
        typ   = m["type"]
        text  = m["message"]
        from_ = m["from"]

        if typ == "handshake":
            if not handshake_done:
                print(f"🤝 {SELF_ID} got handshake from {from_}")
                send_message(to=from_, sender=SELF_ID,
                             message="ack", msg_type="handshake")
                handshake_done = True
            continue

        if not m.get("user_initiated"):
            continue                    # ignore non‑human bot chatter

        print(f"📩 {from_} → {SELF_ID}: {text}")
        reply = run_assistant(text, assistant_name=SELF_ID)
        print(f"🧠 {SELF_ID}: {reply}")

        send_message(to=PEER_ID, sender=SELF_ID,
                     message=reply, msg_type="bot",
                     user_initiated=False)

    time.sleep(0.5)