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

SELF_ID = "assistant_b"   # change to assistant_a in the other file
PEER_ID = "assistant_a"   # change to assistant_b in the other file
init_conversation(SELF_ID)

# ── 1. start stdin listener ─────────────────────────────────────────
q: queue.Queue[str] = queue.Queue()
def _stdin_listener():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        q.put(line.strip())
threading.Thread(target=_stdin_listener, daemon=True).start()

# ── 2. initial handshake (only A starts) ────────────────────────────
if SELF_ID == "assistant_b":
    send_message(to=PEER_ID, sender=SELF_ID, message="hello", msg_type="handshake")

handshake_done = SELF_ID == "assistant_a"  # B waits, A already sent

print(f"🤖 {SELF_ID} up.")

# ── 3. main event loop ───────────────────────────────────────────────
while True:
    # 3‑a. forward any user keystrokes
    try:
        line = q.get_nowait()
    except queue.Empty:
        line = None
    if line:
        print(f"👤 You: {line}")
        send_message(
            to=PEER_ID,
            sender=SELF_ID,
            message=line,
            msg_type="bot",          # a bot message
            user_initiated=True      # marks it as human‑triggered
        )

    # 3‑b. read inbox
    msgs = receive_messages(SELF_ID) or []
    for m in msgs:
        mtype = m["type"]
        sender = m["from"]
        text   = m["message"]

        # handshake handling
        if mtype == "handshake" and not handshake_done:
            print(f"🤝 {SELF_ID} got handshake from {sender}")
            send_message(to=sender, sender=SELF_ID, message="ack", msg_type="handshake")
            handshake_done = True
            continue
        if mtype == "handshake":
            continue  # ignore duplicates after ack

        # ignore automatic bot chatter
        if not m.get("user_initiated"):
            continue

        # generate reply with Phi‑3
        print(f"📩 {sender} → {SELF_ID}: {text}")
        reply = run_assistant(text, assistant_name=SELF_ID)
        print(f"🧠 {SELF_ID}: {reply}")

        send_message(
            to=PEER_ID,
            sender=SELF_ID,
            message=reply,
            msg_type="bot",
            user_initiated=False
        )

    time.sleep(0.5)