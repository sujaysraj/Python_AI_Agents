# common/logger.py
from pathlib import Path
from datetime import datetime
import json
import os

def log_conversation(message: dict, assistant_name: str):
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f"{assistant_name}_conversation.log"
    timestamp = message.get("timestamp", datetime.now().isoformat())
    sender = message.get("from", "unknown")
    content = message.get("message", "")
    conv_id = message.get("conversation_id", "unknown")

    log_line = f"{timestamp} {sender} [conversation: {conv_id}]: {content}\n"

    with open(log_file, "a") as f:
        f.write(log_line)

def get_conversation_history(assistant_name: str, conversation_id: str) -> list:
    log_file = f"logs/{assistant_name}_conversation_log.json"
    if not os.path.exists(log_file):
        return []
    with open(log_file, "r") as f:
        return [json.loads(line) for line in f if conversation_id in line]