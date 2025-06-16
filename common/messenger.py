# common/messenger.py

import json
import sys
import hmac
import hashlib
import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
from typing import Union, List, Optional
import time
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "fallbackkey").encode()

# Define inbox directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INBOX_DIR = PROJECT_ROOT / "inbox"
INBOX_DIR.mkdir(exist_ok=True)
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

def compute_hmac(message: str) -> str:
    """Compute HMAC-SHA256 for a given message using SECRET_KEY."""
    return hmac.new(SECRET_KEY, message.encode(), hashlib.sha256).hexdigest()

def process_startup_handshakes(self_id: str, peer_id: str):
    """
    Archive stale msgs, send handshake, then retry until peer replies.
    """
    archive_inbox(self_id)
    max_attempts = 10
    for attempt in range(1, max_attempts + 1):
        send_message(
            to=peer_id, 
            sender=self_id,
            message="Handshake Init", 
            msg_type="handshake",
            hmac_sig=compute_hmac("Handshake Init")
            )
        print(f"🤝 {self_id} sent handshake to {peer_id} (attempt {attempt})")
        if wait_for_peer_handshake(self_id, peer_id, timeout=1):
            return
    print(f"⚠️ {self_id} did not receive handshake from {peer_id} after {max_attempts} attempts")

def wait_for_peer_handshake(self_id: str, peer_id: str, timeout: int = 5):
    """
    Block up to `timeout` seconds waiting for a handshake from peer_id.
    """
    for _ in range(timeout):
        msgs = peek_messages(self_id)
        for m in msgs or []:
            if m.get("type") == "handshake" and m.get("from") == peer_id:
                print(f"🤝 {self_id} got handshake from {peer_id}")
                clear_inbox(self_id)
                return True
        time.sleep(1)
    return False

def archive_inbox(assistant_name: str):
    """Move all messages from inbox to a log file with a timestamp."""
    inbox_path = INBOX_DIR / f"{assistant_name}.json"
    if not inbox_path.exists():
        return

    with open(inbox_path, 'r') as f:
        try:
            messages = json.load(f)
        except json.JSONDecodeError:
            messages = []

    if not messages:
        return

    log_path = LOG_DIR / assistant_name
    log_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_path / f"{timestamp}.json"

    with open(log_file, 'w') as f:
        json.dump(messages, f, indent=2)

def init_conversation(assistant_name: str) -> str:
    """Ensure an inbox file exists for the assistant."""
    inbox_path = INBOX_DIR / f"{assistant_name}.json"
    if not inbox_path.exists():
        with open(inbox_path, "w") as f:
            json.dump([], f)
    return assistant_name

def send_message(
    to: str,
    sender: str,
    message: str,
    msg_type: str = "user",
    conversation_id: Optional[str] = None,
    user_initiated: bool = False,
    hmac_sig: Optional[str] = None
):
    """Append a message to the recipient's inbox."""
    inbox_path = INBOX_DIR / f"{to}.json"
    inbox_path.touch(exist_ok=True)

    try:
        with open(inbox_path, 'r') as f:
            messages = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        messages = []

    msg_data = {
        "from": sender,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "type": msg_type,
        "conversation_id": conversation_id,
        "user_initiated": user_initiated
    }

    if hmac_sig is not None:
        msg_data["hmac_sig"] = hmac_sig

    messages.append(msg_data)

    with open(inbox_path, 'w') as f:
        json.dump(messages, f, indent=2)


    with open(inbox_path, 'w') as f:
        json.dump(messages, f, indent=2)

def receive_messages(
    recipient: str,
    last_only: bool = False
) -> Optional[Union[dict, List[dict]]]:
    """Read and clear messages for the recipient."""
    inbox_path = INBOX_DIR / f"{recipient}.json"
    if not inbox_path.exists():
        return None

    try:
        with open(inbox_path, 'r') as f:
            messages = json.load(f)
    except json.JSONDecodeError:
        messages = []

    if not messages:
        return None

    result = messages[-1] if last_only else messages

    with open(inbox_path, 'w') as f:
        json.dump([], f)

    return result

def peek_messages(recipient: str) -> Optional[List[dict]]:
    """Read messages without clearing the inbox."""
    inbox_path = INBOX_DIR / f"{recipient}.json"
    if not inbox_path.exists():
        return None

    try:
        with open(inbox_path, 'r') as f:
            messages = json.load(f)
    except json.JSONDecodeError:
        messages = []

    return messages or None

def clear_inbox(recipient: str):
    """Clear the inbox for the recipient."""
    inbox_path = INBOX_DIR / f"{recipient}.json"
    with open(inbox_path, 'w') as f:
        json.dump([], f)
