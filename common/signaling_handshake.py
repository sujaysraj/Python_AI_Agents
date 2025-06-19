# common/signaling_handshake.py
"""
File‑based WebRTC signalling so *either* assistant can start first.

It establishes **two** data‑channels:

• outbound  – we create the offer (always)
• inbound   – we answer the peer’s offer (if / when one exists)

connect(..)  ⇒  (outbound_transport, inbound_transport)
"""
from __future__ import annotations

import asyncio, json, time, uuid
from pathlib import Path
from typing import Dict, Tuple

from common.webrtc_transport import WebRTCTransport

SIGNAL_FILE   = Path("signaling.json")
STALE_SECONDS = 30        # ignore messages older than this
POLL_SECONDS  = 1         # how often we poll signalling file


# ───────────────────────── helpers ──────────────────────────
async def _read_state() -> Dict:
    try:
        return json.loads(SIGNAL_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


async def _write_state(state: Dict):
    SIGNAL_FILE.write_text(json.dumps(state, indent=2))

# ───────────────────────── main entry ───────────────────────
async def connect(my_id: str, peer_id: str, secret_key: str
                  ) -> Tuple[WebRTCTransport, WebRTCTransport]:
    """
    Returns (outbound, inbound) WebRTCTransport pair.
    • outbound – we are OFFERER
    • inbound  – we are RESPONDER
    """
    if not SIGNAL_FILE.exists():
        await _write_state({})

    inbound:  WebRTCTransport | None = None      # will fill later
    outbound: WebRTCTransport                    # created unconditionally

    # ── 1️⃣  check if peer already left an offer ────────────────────
    state       = await _read_state()
    peer_offer  = state.get(f"{peer_id}_offer")
    fresh_offer = peer_offer and time.time() - peer_offer.get("ts", 0) < STALE_SECONDS

    if fresh_offer:
        print(f"[{my_id}] 📥 found fresh offer from {peer_id}, acting as responder")
        inbound = await WebRTCTransport.create_responder(
            my_id, peer_offer["sdp"], secret_key
        )

        # write our answer back
        state = await _read_state()
        state[f"{my_id}_answer"] = {
            "for": peer_offer["id"],
            "ts" : time.time(),
            "sdp": inbound.local_description,
        }
        await _write_state(state)
        print(f"[{my_id}] 📤 wrote inbound answer – link ready")

    # ── 2️⃣  create our OWN outbound offer (always) ────────────────
    outbound = await WebRTCTransport.create_offerer(my_id, secret_key)
    sess_id  = str(uuid.uuid4())

    state = await _read_state()
    state[f"{my_id}_offer"] = {
        "id":  sess_id,
        "ts":  time.time(),
        "sdp": outbound.local_description,
    }
    await _write_state(state)
    print(f"[{my_id}] 📤 wrote outbound offer")

    # wait for answer to our offer
    waited = 0
    while waited < STALE_SECONDS:
        await asyncio.sleep(POLL_SECONDS)
        waited += POLL_SECONDS
        state = await _read_state()
        ans = state.get(f"{peer_id}_answer")
        if ans and ans.get("for") == sess_id:
            await outbound.apply_remote_answer(ans["sdp"])
            print(f"[{my_id}] ✅ outbound link ready")
            break
    else:
        raise TimeoutError(f"[{my_id}] ❌ timed‑out waiting for answer")

    # ── 3️⃣  if we didn’t already build inbound, wait & build now ──
    if inbound is None:
        print(f"[{my_id}] ⏳ waiting for inbound offer from {peer_id}…")
        waited = 0
        while waited < STALE_SECONDS:
            await asyncio.sleep(POLL_SECONDS)
            waited += POLL_SECONDS
            state = await _read_state()
            peer_offer = state.get(f"{peer_id}_offer")
            if peer_offer and time.time() - peer_offer["ts"] < STALE_SECONDS:
                inbound = await WebRTCTransport.create_responder(
                    my_id, peer_offer["sdp"], secret_key
                )
                # write our answer
                state = await _read_state()
                state[f"{my_id}_answer"] = {
                    "for": peer_offer["id"],
                    "ts" : time.time(),
                    "sdp": inbound.local_description,
                }
                await _write_state(state)
                print(f"[{my_id}] 📤 wrote inbound answer – link ready")
                break
        else:
            raise TimeoutError(f"[{my_id}] ❌ timed‑out waiting for inbound offer")

    return outbound, inbound
