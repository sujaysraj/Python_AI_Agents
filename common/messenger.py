# common/messenger.py — clean, working version
"""
Messenger
~~~~~~~~~
• End‑to‑end encryption via Fernet
• Outbound queue → background thread so .send() is non‑blocking
• Duplicate‑suppression (exact + near‑duplicate)
• Helper .receive() returns **one** decrypted message dict or None

The only public methods you need are:
    messenger.send(...)
    messenger.receive()

Both assistants *must* share the same SECRET_KEY string (32‑byte url‑safe
base64) which you load from .env and pass into Messenger.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import os
import queue
import threading
import time
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet, InvalidToken

from common.transport import BaseTransport

# ───────────────────── constants ─────────────────────
DEFAULT_DEDUP_WINDOW = 50
SIMILARITY_THRESHOLD = 0.90
SENDER_THREAD_SLEEP = 0.05   # seconds between queue polls

# ───────────────────── Messenger ─────────────────────
class Messenger:
    def __init__(
        self,
        name: str,
        transport: BaseTransport,
        secret_key: str,                   # base64 string, *not* bytes!
        dedup_window: int = DEFAULT_DEDUP_WINDOW,
        similarity_threshold: float = SIMILARITY_THRESHOLD,
    ) -> None:
        self.name = name
        self.transport = transport
        self._cipher = Fernet(secret_key)

        # outbound queue
        self._outbox: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        threading.Thread(target=self._drain_outbox, daemon=True).start()

        # deduplication memory
        self._recent_plain: List[str] = []
        self._recent_hash:  List[str] = []
        self._dedup_window = dedup_window
        self._similarity_threshold = similarity_threshold
        self._lock = threading.Lock()

    # ── public api ────────────────────────────────────
    def send(
        self,
        to: str,
        message: str,
        msg_type: str = "user",
        conversation_id: Optional[str] = None,
        user_initiated: bool = False,
    ) -> None:
        if self._is_duplicate(message):
            print(f"[{self.name}] suppressing duplicate outbound → {to}: {message[:60]}")
            return
        payload = {
            "to": to,
            "sender": self.name,
            "plaintext": message,
            "msg_type": msg_type,
            "conversation_id": conversation_id,
            "user_initiated": user_initiated,
        }
        self._outbox.put(payload)
        self._remember(message)

    def receive(self) -> Optional[Dict[str, Any]]:
        """Return ONE decrypted message dict or None if inbox empty"""
        encrypted_messages = self.transport.receive_messages(self.name)
        if not encrypted_messages:
            return None

        # normalise to dict
        encrypted = encrypted_messages[0] if isinstance(encrypted_messages, list) else encrypted_messages
        if encrypted is None or "message" not in encrypted:
            return None  # malformed

        try:
            decrypted_text = self._cipher.decrypt(encrypted["message"].encode()).decode()
        except InvalidToken:
            print(f"[{self.name}] WARNING: could not decrypt message from {encrypted.get('from')}")
            return None

        # inbound dedup
        if self._is_duplicate(decrypted_text, inbound=True):
            return None
        self._remember(decrypted_text, inbound=True)

        return {
            "sender": encrypted["from"],
            "message": decrypted_text,
            "timestamp": encrypted.get("timestamp"),
            "type": encrypted.get("type", "user"),
            "conversation_id": encrypted.get("conversation_id"),
            "user_initiated": encrypted.get("user_initiated", False),
        }

    # ── internal helpers ──────────────────────────────
    def _drain_outbox(self) -> None:
        while True:
            try:
                item = self._outbox.get(timeout=SENDER_THREAD_SLEEP)
            except queue.Empty:
                continue

            ciphertext = self._cipher.encrypt(item["plaintext"].encode()).decode()
            self.transport.send_message(
                to=item["to"],
                sender=item["sender"],
                message=ciphertext,
                msg_type=item["msg_type"],
                conversation_id=item["conversation_id"],
                user_initiated=item["user_initiated"],
            )
            self._outbox.task_done()
            print(f"[{self.name}] ✉️ Sent encrypted message to {item['to']}")

    def _hash(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    def _is_duplicate(self, text: str, inbound: bool = False) -> bool:
        with self._lock:
            h = self._hash(text)
            if h in self._recent_hash:
                return True
            for prev in self._recent_plain:
                if difflib.SequenceMatcher(None, prev, text).ratio() >= self._similarity_threshold:
                    return True
            return False

    def _remember(self, text: str, inbound: bool = False) -> None:
        with self._lock:
            self._recent_hash.append(self._hash(text))
            self._recent_plain.append(text)
            if len(self._recent_plain) > self._dedup_window:
                self._recent_plain.pop(0)
                self._recent_hash.pop(0)
