from datetime import datetime
import requests

def parse_command(message: str) -> str:
    """
    Fallback command parser if needed.
    """
    if "status" in message.lower():
        return "All systems operational."
    elif "time" in message.lower():
        return f"The current time is {datetime.now().strftime('%H:%M:%S')}."
    else:
        return f"You said: {message}"

def generate_response(message: str, assistant_name: str) -> str:
    """
    Simulated NLP-based response generation based on message content and assistant identity.
    """
    msg = message.lower()

    if "who are you" in msg:
        return f"I'm {assistant_name}, your personal assistant."
    elif "how are you" in msg:
        return "I'm doing well, thanks! How about you?"
    elif "time" in msg:
        return f"The time is {datetime.now().strftime('%H:%M:%S')}."
    elif "status" in msg:
        return "All systems are functioning normally."
    elif "bye" in msg:
        return "Goodbye! Talk to you later."
    else:
        return f"You said: {message}"

def query_llm(prompt: str, model: str = "phi3") -> str:
    url = "http://localhost:11434/api/generate"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.RequestException as e:
        return f"Error contacting LLM: {e}"