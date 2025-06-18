# common/transport.py
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Union, Dict
import json
import os

# ───────────────────────────────── ABSTRACT BASE ──────────────────────────────
class BaseTransport(ABC):
    """Abstract base class for transport layers."""

    @abstractmethod
    def send_message(self, to: str, sender: str, message: str, msg_type: str = "user",
                     conversation_id: Optional[str] = None,
                     user_initiated: bool = False,
                     hmac_sig: Optional[str] = None):
        ...

    @abstractmethod
    def receive_messages(self, recipient: str) -> Optional[Dict[str, any]]:
        ...

    @abstractmethod
    def peek_messages(self, recipient: str) -> Optional[List[dict]]:
        ...

    @abstractmethod
    def clear_inbox(self, recipient: str):
        ...

    @abstractmethod
    def archive_inbox(self, recipient: str):
        ...

# ───────────────────────────────── FILE TRANSPORT ─────────────────────────────
class FileTransport(BaseTransport):
    """
    Disk‑backed transport: each recipient has <inbox_dir>/<name>.json
    All assistants **must** point to the same inbox_dir.
    """

    def __init__(self, inbox_dir: Optional[Union[str, Path]] = None):
        if inbox_dir is None:
            project_root = Path(__file__).resolve().parent.parent  # .../common/..
            inbox_dir = project_root / "inbox"
        self.inbox_dir: Path = Path(inbox_dir).expanduser().resolve()
        self.inbox_dir.mkdir(parents=True, exist_ok=True)

        self.log_dir: Path = self.inbox_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)

    # ── helpers ────────────────────────────────────────────────────────────────
    def _inbox_path(self, name: str) -> Path:
        return self.inbox_dir / f"{name}.json"

    # ── send ───────────────────────────────────────────────────────────────────
    def send_message(self, to: str, sender: str, message: str, msg_type: str = "user",
                     conversation_id: Optional[str] = None,
                     user_initiated: bool = False,
                     hmac_sig: Optional[str] = None):
        path = self._inbox_path(to)
        entry = {
            "from": sender,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "type": msg_type,
            "conversation_id": conversation_id,
            "user_initiated": user_initiated,
            "hmac_sig": hmac_sig,
        }

        try:
            messages = json.loads(path.read_text()) if path.exists() else []
        except json.JSONDecodeError:
            messages = []

        messages.append(entry)
        path.write_text(json.dumps(messages, indent=2))

    # ── receive (pop 1st message + log) ────────────────────────────────────────
    def receive_messages(self, recipient: str) -> Optional[Dict[str, any]]:
        inbox = self._inbox_path(recipient)
        if not inbox.exists():
            return None

        try:
            messages = json.loads(inbox.read_text())
        except json.JSONDecodeError:
            messages = []

        if not messages:
            inbox.unlink(missing_ok=True)
            return None

        message = messages.pop(0)

        if messages:
            inbox.write_text(json.dumps(messages, indent=2))
        else:
            inbox.unlink(missing_ok=True)

        # append to rolling log
        with (self.log_dir / f"{recipient}.jsonl").open("a") as lf:
            json.dump(message, lf)
            lf.write("\n")

        return message

    # ── util helpers ───────────────────────────────────────────────────────────
    def peek_messages(self, recipient: str) -> Optional[List[dict]]:
        path = self._inbox_path(recipient)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text()) or None
        except json.JSONDecodeError:
            return None

    def clear_inbox(self, recipient: str):
        self._inbox_path(recipient).write_text("[]")

    def archive_inbox(self, recipient: str):
        msgs = self.peek_messages(recipient)
        if not msgs:
            return
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        (self.log_dir / f"{recipient}_{ts}.json").write_text(json.dumps(msgs, indent=2))
        self.clear_inbox(recipient)
