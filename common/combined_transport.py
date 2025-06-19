# common/combined_transport.py
"""
Combine two WebRTCTransport objects into one Transport interface.

• outbound – the connection where *this* peer created the DataChannel
• inbound  – the connection where the remote peer created the DataChannel

send_message()  → outbound
receive_messages() → inbound
"""
from typing import Any, Dict, Optional, List
from common.combined_transport import BaseTransport


class CombinedTransport(BaseTransport):
    def __init__(self, outbound: BaseTransport, inbound: BaseTransport) -> None:
        self.outbound = outbound
        self.inbound = inbound

    # ── BaseTransport API ────────────────────────────────────────────
    async def send_message(self, *args, **kw) -> None:        # type: ignore[override]
        return await self.outbound.send_message(*args, **kw)

    def receive_messages(self, self_id: str) -> Optional[Dict[str, Any]]:  # type: ignore[override]
        return self.inbound.receive_messages(self_id)

    # the following are no‑ops for WebRTC use‑case
    def peek_messages(self, recipient: str) -> Optional[List[dict]]: return None
    def clear_inbox(self, recipient: str) -> None: ...
    def archive_inbox(self, recipient: str) -> None: ...
