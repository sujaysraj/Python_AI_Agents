import os
import json
import base64
import hashlib
from typing import List, Optional
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from datetime import datetime

INBOX_DIR = "inbox"


def _ensure_inbox():
    os.makedirs(INBOX_DIR, exist_ok=True)


def _get_inbox_path(assistant_name: str) -> str:
    return os.path.join(INBOX_DIR, f"{assistant_name}.json")


class Messenger:
    def __init__(self, self_name: str, shared_key: str):
        _ensure_inbox()
        self.self_name = self_name
        self.shared_key = hashlib.sha256(shared_key.encode()).digest()

    def _encrypt(self, plaintext: str) -> str:
        nonce = get_random_bytes(12)
        cipher = AES.new(self.shared_key, AES.MODE_GCM, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode())
        payload = base64.b64encode(nonce + tag + ciphertext).decode()
        return payload

    def _decrypt(self, payload: str) -> Optional[str]:
        try:
            raw = base64.b64decode(payload.encode())
            nonce, tag, ciphertext = raw[:12], raw[12:28], raw[28:]
            cipher = AES.new(self.shared_key, AES.MODE_GCM, nonce=nonce)
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)
            return plaintext.decode()
        except Exception as e:
            print(f"[{self.self_name}] 🔐 Failed to decrypt message: {e}")
            return None

    def send_message(self, to: str, message: str, msg_type: str = "user",
                     conversation_id: Optional[str] = None, user_initiated: bool = False):
        inbox_path = _get_inbox_path(to)
        entry = {
            "from": self.self_name,
            "to": to,
            "type": msg_type,
            "encrypted": self._encrypt(message),
            "timestamp": datetime.utcnow().isoformat(),
            "conversation_id": conversation_id,
            "user_initiated": user_initiated
        }

        try:
            if os.path.exists(inbox_path):
                with open(inbox_path, "r") as f:
                    messages = json.load(f)
            else:
                messages = []

            messages.append(entry)

            with open(inbox_path, "w") as f:
                json.dump(messages, f, indent=2)
        except Exception as e:
            print(f"[{self.self_name}] ❌ Failed to write to inbox: {e}")

    def receive_messages(self) -> List[dict]:
        inbox_path = _get_inbox_path(self.self_name)
        messages = []

        if not os.path.exists(inbox_path):
            return []

        try:
            with open(inbox_path, "r") as f:
                content = f.read()
                if not content.strip():  # ⛑ protect against empty file
                    return []
                all_messages = json.loads(content)
        except Exception as e:
            print(f"[{self.self_name}] ❌ Failed to read inbox: {e}")
            return []

        processed = []
        remaining = []

        for msg in all_messages:
            if msg["to"] != self.self_name:
                remaining.append(msg)
                continue
            if msg["from"] == self.self_name:
                continue  # Skip messages sent by self (paranoia check)
            decrypted = self._decrypt(msg["encrypted"])
            if decrypted is not None:
                msg["plaintext"] = decrypted
                messages.append(msg)

        # write back only remaining unprocessed messages
        with open(inbox_path, "w") as f:
            json.dump(remaining, f, indent=2)

        # Remove processed messages
        try:
            with open(inbox_path, "w") as f:
                json.dump(remaining, f, indent=2)
        except Exception as e:
            print(f"[{self.self_name}] ❌ Failed to update inbox: {e}")

        return messages
