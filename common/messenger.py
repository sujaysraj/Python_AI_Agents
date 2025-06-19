import os
import json
import base64
import hashlib
from typing import List, Optional
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from common.transport_http import HTTPTransport
from datetime import datetime

class Messenger:
    def __init__(self, self_name: str, peer_name: str, peer_url: str, shared_key: str):
        self.self_name = self_name
        self.peer_name = peer_name
        self.transport = HTTPTransport(self_name, peer_url, shared_key)

    def send_message(self, to: str, message: str, msg_type: str = "user",
                     conversation_id=None, user_initiated=False):
        self.transport.send_message(
            to=to,
            sender=self.self_name,
            message=message,
            msg_type=msg_type,
            conversation_id=conversation_id,
            user_initiated=user_initiated
        )

    def receive_messages(self):
        return self.transport.receive_messages()