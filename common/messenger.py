# common/messenger.py

import json
from pathlib import Path
from datetime import datetime
from typing import Union, List, Optional

# Define inbox location
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INBOX_DIR = PROJECT_ROOT / "inbox"
INBOX_DIR.mkdir(exist_ok=True)

def init_conversation(assistant_name: str) -> str:
    """
    Ensure an inbox file exists for the assistant.
    """
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
    user_initiated: bool = False
):
    """
    Append a message to the recipient's inbox.
    """
    inbox_path = INBOX_DIR / f"{to}.json"
    inbox_path.touch(exist_ok=True)

    try:
        with open(inbox_path, 'r') as f:
            messages = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        messages = []

    messages.append({
        "from": sender,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "type": msg_type,
        "conversation_id": conversation_id,
        "user_initiated": user_initiated
    })

    with open(inbox_path, 'w') as f:
        json.dump(messages, f, indent=2)

def receive_messages(
    recipient: str,
    last_only: bool = False
) -> Optional[Union[dict, List[dict]]]:
    """
    Read and clear all messages for the recipient.
    """
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
