# common/webrtc_transport.py

import asyncio
import json
from typing import Any, Dict, Optional

from aiortc import RTCPeerConnection
from aiortc.contrib.signaling import object_from_string, object_to_string
from cryptography.fernet import Fernet
from common.transport import BaseTransport


class WebRTCTransport(BaseTransport):
    def __init__(self, name: str, secret_key: str) -> None:
        self.name = name
        self._cipher = Fernet(secret_key)
        self.pc = RTCPeerConnection()
        self._recv_queue: asyncio.Queue[str] = asyncio.Queue()
        self.channel_ready = asyncio.Event()

    def create_datachannel(self):
        """Only the offerer calls this before create_offer()"""
        ch = self.pc.createDataChannel("chat")
        self._setup_channel(ch)

    def _setup_channel(self, channel):
        @channel.on("open")
        def on_open():
            print(f"[{self.name}] 🔓 DataChannel is OPEN")
            self.channel_ready.set()

        @channel.on("message")
        def on_message(message):
            try:
                plaintext = self._cipher.decrypt(message.encode()).decode()
                asyncio.create_task(self._recv_queue.put(plaintext))
            except Exception:
                print(f"[{self.name}] ⚠️ Could not decrypt incoming message.")

        self.channel = channel

    @classmethod
    async def create_offerer(cls, name: str, secret_key: str) -> "WebRTCTransport":
        self = cls(name, secret_key)
        self._setup_channel(self.pc.createDataChannel("chat"))

        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)
        self.local_description = json.loads(object_to_string(self.pc.localDescription))
        return self

    @classmethod
    async def create_responder(cls, name: str, peer_offer: Dict[str, str], secret_key: str) -> "WebRTCTransport":
        self = cls(name, secret_key)
        self.pc.on("datachannel", self._setup_channel)

        if not peer_offer:
            raise ValueError(f"[{name}] ❌ Peer offer is missing or empty!")

        if isinstance(peer_offer, dict):
            sdp_string = json.dumps(peer_offer)
        elif isinstance(peer_offer, str):
            sdp_string = peer_offer
        else:
            raise TypeError(f"[{name}] ❌ Unexpected peer_offer type: {type(peer_offer)}")

        offer_obj = object_from_string(sdp_string)
        await self.pc.setRemoteDescription(offer_obj)
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)
        self.local_description = json.loads(object_to_string(self.pc.localDescription))
        return self

    async def set_remote_description(self, peer_answer: Dict[str, str]) -> None:
        answer_obj = object_from_string(json.dumps(peer_answer))
        await self.pc.setRemoteDescription(answer_obj)

    async def send_message(
        self,
        to: str,
        sender: str,
        message: str,
        msg_type: str = "user",
        conversation_id: Optional[str] = None,
        user_initiated: bool = False,
    ) -> None:
        if not self.channel_ready.is_set():
            print(f"[{self.name}] ⏳ Waiting for channel to open...")
            await self.channel_ready.wait()
        payload = self._cipher.encrypt(message.encode()).decode()
        self.channel.send(payload)

    async def receive_messages(self, self_id: str) -> Optional[Dict[str, Any]]:
        try:
            plaintext = self._recv_queue.get_nowait()
            return {
                "from": "peer",
                "message": plaintext,
                "type": "user",
                "user_initiated": True,
            }
        except asyncio.QueueEmpty:
            return None
# ------------------------------------------------------------
    async def apply_remote_answer(self, sdp_dict: dict | str):
        """
        Offerer calls this after the peer writes an answer.
        Accepts either a dict {"type": "answer", "sdp": "..."} or
        the raw JSON string dumped by object_to_string().
        """
        if isinstance(sdp_dict, dict):
            sdp_json = json.dumps(sdp_dict)
        else:
            sdp_json = sdp_dict
        answer_obj = object_from_string(sdp_json)
        await self.pc.setRemoteDescription(answer_obj)

    async def apply_remote_offer(self, sdp_dict: dict | str):
        """
        Responder convenience: apply a remote *offer* outside the factory
        (used only if you want to re‑negotiate later).
        """
        if isinstance(sdp_dict, dict):
            sdp_json = json.dumps(sdp_dict)
        else:
            sdp_json = sdp_dict
        offer_obj = object_from_string(sdp_json)
        await self.pc.setRemoteDescription(offer_obj)
    # ------------------------------------------------------------
    @classmethod
    async def create_offerer(cls, name: str, secret_key: str):
        self = cls(name, secret_key)
        self.create_datachannel()                   # must happen before offer
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)
        self.local_description = json.loads(object_to_string(self.pc.localDescription))
        return self
    # No-op compatibility methods
    def archive_inbox(self, self_id: str) -> None:
        pass

    def clear_inbox(self, self_id: str) -> None:
        pass

    def peek_messages(self, self_id: str) -> list:
        return []

    async def receive_messages_async(self, self_id: str) -> Optional[Dict[str, Any]]:
        plaintext = await self._recv_queue.get()
        return {
            "from": "peer",
            "message": plaintext,
            "type": "user",
            "user_initiated": True,
        }