# common/agent.py

import requests

OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "phi3"

def run_assistant(prompt: str, assistant_name: str = "assistant") -> str:
    """Send prompt to local Phi-3 model via Ollama and return response."""
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()
    except requests.RequestException as e:
        return f"⚠️ Error communicating with {MODEL_NAME}: {str(e)}"
