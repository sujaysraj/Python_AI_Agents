# PeerAI - Distributed AI Communication System

*A comprehensive guide to setting up and running your secure, peer-to-peer AI assistant network*

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)
- [Security Features](#security-features)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Overview

Local Test is a sophisticated peer-to-peer communication system that enables AI assistants to communicate securely using **WebRTC**, **end-to-end encryption**, and **file-based signaling**. The system supports multiple transport protocols and provides a resilient, decentralized network for AI agent communication.

### Key Capabilities
- **Secure Peer-to-Peer Communication** - Direct AI assistant communication without central servers
- **End-to-End Encryption** - AES-GCM encryption with HMAC authentication
- **Multiple Transport Protocols** - HTTP and WebRTC support
- **Local AI Processing** - Privacy-preserving AI interactions
- **Resilient Architecture** - Continues operating even when parts of the network are compromised

---

## Features

### Security Features
- **AES-GCM Encryption** - Authenticated encryption for all messages
- **HMAC Authentication** - Message integrity and authenticity verification
- **Zero Trust Architecture** - No implicit trust, continuous verification
- **Secure Signaling** - Protected connection establishment

### Communication Features
- **WebRTC Transport** - Peer-to-peer communication with NAT traversal
- **HTTP Transport** - Fallback communication method
- **File-Based Signaling** - Secure connection establishment
- **Bidirectional Communication** - Both assistants can initiate connections

### AI Integration
- **Local AI Processing** - Runs AI models locally for privacy
- **Ollama Integration** - Supports local LLM models
- **Customizable Prompts** - Configurable AI behavior
- **Error Handling** - Graceful AI service failures

---

## Prerequisites

Before setting up the system, ensure you have:

### Required Software
- **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
- **Ollama** - For local AI processing ([Install Ollama](https://ollama.ai/))
- **Git** - For cloning the repository

### Required Models
- **Mistral Model** - Install via Ollama: `ollama pull mistral`

### Network Requirements
- **Port 8080** - Available for HTTP transport
- **NAT Traversal** - For WebRTC communication (usually automatic)

---

## Installation

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd Local_test
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Python Dependencies
```bash
cd common
pip install -r requirements.txt
```

If you don't have a requirements.txt file, install these packages:
```bash
pip install flask requests cryptography pycryptodome aiortc asyncio python-dotenv
```

### 4. Install Ollama and Models
```bash
# Install Ollama (follow instructions at https://ollama.ai/)
# Then pull the required model
ollama pull mistral
```

---

## Configuration

### 1. Environment Variables
Create a `.env` file in the project root:

```env
# Security Configuration
SECRET_KEY=your_very_secure_secret_key_here

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
MODEL_NAME=mistral

# Network Configuration
PEER_URL=https://your-peer-ngrok-url.ngrok-free.app
```

### 2. Directory Structure
Ensure your project structure looks like this:
```
Local_test/
├── .env
├── signaling.json
├── common/
│   ├── agent.py
│   ├── messenger.py
│   ├── transport_http.py
│   ├── webrtc_transport.py
│   ├── signaling_handshake.py
│   └── requirements.txt
├── assistant_a/
│   └── main.py
├── assistant_b/
│   └── main.py
├── inbox/
│   ├── assistant_a.json
│   ├── assistant_b.json
│   └── logs/
└── logs/
```

### 3. Ngrok Setup (for HTTP Transport)
If using HTTP transport, set up ngrok for peer communication:

```bash
# Install ngrok
# Then expose your local server
ngrok http 8080
```

Copy the ngrok URL to your `.env` file as `PEER_URL`.

---

## Usage

### Starting the System

#### Method 1: Using Main Scripts
```bash
# Terminal 1 - Start Assistant A
cd assistant_a
python main.py

# Terminal 2 - Start Assistant B
cd assistant_b
python main.py
```

#### Method 2: Using Agent Script
```bash
# Terminal 1 - Start Assistant A
cd common
python agent.py --id assistant_a --peer assistant_b

# Terminal 2 - Start Assistant B
cd common
python agent.py --id assistant_b --peer assistant_a
```

### Basic Interaction
1. **Start both assistants** in separate terminals
2. **Wait for connection** - You'll see handshake messages
3. **Type messages** in either terminal to communicate
4. **AI responses** will be generated automatically

### Example Session
```
[assistant_a] 🟢 assistant_a ready. Talking to assistant_b. Type /exit to quit.
[assistant_b] 🟢 assistant_b ready. Talking to assistant_a. Type /exit to quit.

> Hello, how are you today?
[assistant_a] 📩 assistant_a → assistant_b: Hello, how are you today?
[assistant_b] 📩 assistant_a → assistant_b: Hello, how are you today?
[assistant_b] 🧠 assistant_b: I'm doing well, thank you for asking! How about you?

> What's the weather like?
[assistant_a] 📩 assistant_a → assistant_b: What's the weather like?
[assistant_b] 🧠 assistant_b: I don't have access to real-time weather data, but I hope it's nice where you are!
```

---

## Architecture

### Communication Flow
```
┌─────────────────┐    WebRTC/HTTP    ┌─────────────────┐
│  Assistant A    │◄─────────────────►│  Assistant B    │
│                 │                   │                 │
│ • Local AI      │                   │ • Local AI      │
│ • WebRTC Client │                   │ • WebRTC Client │
│ • HTTP Server   │                   │ • HTTP Server   │
└─────────────────┘                   └─────────────────┘
         │                                      │
         └─────────── File System ──────────────┘
                    (signaling.json)
```

### Transport Layers
1. **WebRTC Transport** - Primary peer-to-peer communication
2. **HTTP Transport** - Fallback communication method
3. **File Signaling** - Connection establishment protocol

### Security Layers
1. **AES-GCM Encryption** - Message confidentiality and integrity
2. **HMAC Authentication** - Message authenticity verification
3. **Secure Signaling** - Protected connection establishment

---

## Security Features

### Encryption
- **AES-GCM** - Authenticated encryption for all messages
- **Random Nonces** - Unique encryption for each message
- **Integrity Tags** - Tamper detection and prevention

### Authentication
- **HMAC-SHA256** - Message signature verification
- **Shared Secrets** - Pre-shared keys for authentication
- **Handshake Validation** - Secure connection establishment

### Privacy
- **Local AI Processing** - No data leaves local systems
- **No Central Servers** - Decentralized communication
- **End-to-End Encryption** - Messages encrypted in transit

---

## Advanced Configuration

### Custom AI Models
Modify `common/agent.py` to use different models:

```python
MODEL_NAME = "llama2"  # Change to your preferred model
```

### Transport Configuration
Configure transport settings in `common/transport_http.py`:

```python
class HTTPTransport:
    def __init__(self, self_name, peer_url, shared_key: str, port=8080):
        # Change port if needed
        self.port = port
```

### WebRTC Settings
Adjust WebRTC configuration in `common/webrtc_transport.py`:

```python
class WebRTCTransport(BaseTransport):
    def __init__(self, name: str, secret_key: str) -> None:
        # Configure WebRTC settings
        self.pc = RTCPeerConnection()
```

---

## Troubleshooting

### Common Issues

#### Connection Problems
1. **Check ngrok URL** - Ensure PEER_URL is correct in .env
2. **Verify ports** - Ensure port 8080 is available
3. **Check firewall** - Allow connections on required ports

#### AI Not Responding
1. **Verify Ollama** - Ensure Ollama is running:
   ```bash
   ollama list
   ```
2. **Check model** - Ensure Mistral model is installed:
   ```bash
   ollama pull mistral
   ```
3. **Test Ollama** - Verify API is accessible:
   ```bash
   curl http://localhost:11434/api/generate -d '{"model":"mistral","prompt":"Hello"}'
   ```

#### WebRTC Issues
1. **Check signaling file** - Ensure signaling.json is writable
2. **Verify network** - Check NAT traversal capabilities
3. **Restart assistants** - Clear stale connection state

#### Encryption Errors
1. **Check SECRET_KEY** - Ensure it's set in .env file
2. **Verify key format** - Use a strong, random secret key
3. **Check permissions** - Ensure files are readable/writable

### Error Messages

#### "Failed to decrypt message"
- Check SECRET_KEY is identical on both assistants
- Verify no special characters in the key
- Restart both assistants

#### "HMAC mismatch"
- Ensure SECRET_KEY is the same on both systems
- Check for encoding issues
- Verify message integrity

#### "Connection timeout"
- Check network connectivity
- Verify ngrok URL is correct
- Ensure both assistants are running

---

## Data Storage

### Signaling File (`signaling.json`)
```json
{
  "assistant_a_offer": {
    "id": "uuid-here",
    "ts": 1234567890.123,
    "sdp": {
      "type": "offer",
      "sdp": "v=0\r\no=- ..."
    }
  },
  "assistant_b_answer": {
    "for": "uuid-here",
    "ts": 1234567890.456,
    "sdp": {
      "type": "answer",
      "sdp": "v=0\r\no=- ..."
    }
  }
}
```

### Inbox Files
- `inbox/assistant_a.json` - Messages for Assistant A
- `inbox/assistant_b.json` - Messages for Assistant B

### Log Files
- `logs/` - System and communication logs

---

## Security Best Practices

### Key Management
- **Use strong secrets** - Generate cryptographically secure keys
- **Rotate keys regularly** - Change SECRET_KEY periodically
- **Secure storage** - Protect .env files and keys

### Network Security
- **Use HTTPS** - When possible, use secure ngrok URLs
- **Firewall rules** - Restrict access to required ports only
- **VPN usage** - Consider VPN for additional security

### System Security
- **Keep updated** - Regularly update dependencies
- **Monitor logs** - Check for suspicious activity
- **Backup data** - Regularly backup configuration and data

---

## Contributing

### Adding New Features
1. **Create feature branch** - `git checkout -b feature/new-feature`
2. **Follow architecture** - Maintain modular design
3. **Add tests** - Include security and functionality tests
4. **Update documentation** - Modify this README as needed

### Reporting Issues
- **Check troubleshooting** - Review common issues first
- **Provide logs** - Include relevant error messages
- **Describe steps** - Include steps to reproduce the issue

### Security Issues
- **Responsible disclosure** - Report security issues privately
- **Detailed description** - Include vulnerability details
- **Proof of concept** - Provide reproduction steps

---

## Support

If you need help:
1. **Check this README** - Review installation and troubleshooting
2. **Check logs** - Examine log files for error details
3. **Test components** - Verify each component individually
4. **Create issue** - Report problems with detailed information

---

## License

This project is open source. Feel free to modify and distribute according to your needs.

---

## Future Enhancements

Planned features:
- **Blockchain Integration** - Immutable message logging
- **Federated Learning** - Collaborative AI training
- **Mesh Networks** - Multi-hop communication
- **Quantum Cryptography** - Future-proof encryption
- **Mobile Support** - iOS and Android applications

---

*Happy communicating with your secure AI network!*
