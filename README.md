# 🤖 Corveta.AI - Peer-to-Peer AI Assistant System

Corveta.AI is a privacy-first, local-first assistant framework where AI agents communicate peer-to-peer without relying on the cloud. It's built to scale from two simple assistants to a resilient mesh of intelligent agents over LAN, Bluetooth, or WebRTC.

---

## ✅ Current Features

### 🔄 Two-Way Handshake Protocol
- Each assistant initiates and confirms presence via a startup handshake.
- Prevents race conditions or infinite loops on startup.

### 🧠 Offline AI with Phi-3
- Each assistant uses [Phi-3](https://ollama.com/library/phi3) via Ollama to process and generate natural responses locally.
- No cloud dependency, ensuring privacy.

### 📬 Message-Based Communication
- Messages are exchanged via JSON inboxes (`inbox/assistant_a.json`, etc.).
- Fully decoupled communication pattern simulating a peer-to-peer bus.

### 👤 User Interaction
- Either assistant can initiate interaction via text.
- Assistants ignore self-generated or redundant bot messages.

---

## 🗂️ Project Structure
```
assistant_network/
├── assistant_a/
│ └── main.py # Launch assistant A
├── assistant_b/
│ └── main.py # Launch assistant B
├── common/
│ ├── agent.py # Core AI + message handling logic
│ ├── messenger.py # Messaging and inbox infrastructure
│ └── logger.py # Log archival utility
├── inbox/ # Message inbox for each assistant
├── logs/ # Archived message logs per assistant
└── utils/
└── (reserved) # Future: context memory, NLP tools, etc.
```

---

## 🚀 How to Run

1. Make sure you have [Ollama](https://ollama.com/) and the `phi3` model installed:
   ```ollama run phi3```
2. In two terminals:
   ```
   python assistant_a/main.py
   ```
   ```
   python assistant_b/main.py
   ```
4. Start chatting with either assistant!

🛠️ Future Enhancements
🧠 Context Awareness
Maintain conversation history

Feed last N messages to improve multi-turn replies

🔊 Voice Support
🗣 Input: Whisper or Vosk for speech-to-text

🔈 Output: Piper or OpenVoice for text-to-speech

🔗 True P2P Transport
Replace JSON files with WebRTC, Unix sockets, Bluetooth or multicast messaging

Enable multi-device AI collaboration without server dependence

## 📒 Logging
* Log all messages with:
* Timestamp
* Sender → Receiver
* Message text
* Log stored in logs/assistant_name/YYYYMMDD_HHMMSS.json

## 📌 Requirements
* Python 3.9+
* requests
* ollama running with phi3 model

## 🔐 Philosophy
Your assistant should work offline, on-device, and on your terms.

No cloud. No tracking. No middleman.


