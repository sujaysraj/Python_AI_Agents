# assistant_a/main.py

import time
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
# assistant_a/main.py or assistant_b/main.py

from common.agent import run_loop
from common.messenger import init_conversation, process_startup_handshakes

if __name__ == "__main__":
    self_id = "assistant_a" if "assistant_a" in sys.argv[0] else "assistant_b"
    peer_id = "assistant_b" if self_id == "assistant_a" else "assistant_a"

    init_conversation(self_id)
    process_startup_handshakes(self_id, peer_id)
    print(f"🤖 {self_id} active")
    print("💬 Type your message (or /exit to quit):")
    run_loop(self_id, peer_id)
