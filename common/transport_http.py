# common/transport_http.py

import requests
from flask import Flask, request, jsonify
import threading, base64
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import hashlib

class HTTPTransport:
    def __init__(self, self_name, peer_url, shared_key: str, port: int):
        self.self_name = self_name
        self.peer_url = peer_url.rstrip("/")
        self.shared_key = hashlib.sha256(shared_key.encode()).digest()
        self.inbox = []
        self.port = port
        self.app = Flask(self_name)
        
        @self.app.route("/inbox", methods=["POST"])
        def receive():
            msg = request.json
            decrypted = self._decrypt(msg.get("encrypted"))
            if decrypted:
                msg["plaintext"] = decrypted
                self.inbox.append(msg)
            return jsonify({"status": "ok"}), 200

        self.server_thread = threading.Thread(
            target=lambda: self.app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False),
            daemon=True
        )
        self.server_thread.start()

    def _encrypt(self, plaintext: str) -> str:
        nonce = get_random_bytes(12)
        cipher = AES.new(self.shared_key, AES.MODE_GCM, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode())
        return base64.b64encode(nonce + tag + ciphertext).decode()

    def _decrypt(self, payload: str) -> str:
        try:
            raw = base64.b64decode(payload.encode())
            nonce, tag, ciphertext = raw[:12], raw[12:28], raw[28:]
            cipher = AES.new(self.shared_key, AES.MODE_GCM, nonce=nonce)
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)
            return plaintext.decode()
        except Exception as e:
            print(f"[{self.self_name}] ❌ Failed to decrypt message: {e}")
            return None

    def send_message(self, to, sender, message, msg_type="user", conversation_id=None, user_initiated=False):
        data = {
            "from": sender,
            "to": to,
            "type": msg_type,
            "encrypted": self._encrypt(message),
            "conversation_id": conversation_id,
            "user_initiated": user_initiated
        }
        try:
            r = requests.post(f"{self.peer_url}/inbox", json=data, timeout=3)
            if r.status_code != 200:
                print(f"[{sender}] ❌ Failed to deliver message to {to}: {r.text}")
        except Exception as e:
            print(f"[{sender}] ❌ Error sending message to {to}: {e}")

    def receive_messages(self):
        msgs = self.inbox[:]
        self.inbox.clear()
        return msgs
