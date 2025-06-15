# utils/llm.py
import openai

openai.api_key = "your-api-key"  # Or read from env

def generate_response(message, assistant_name="assistant"):
    system_prompt = f"You are {assistant_name}. Respond intelligently to the other assistant."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-4o",  # or "gpt-3.5-turbo" or switch to local
        messages=messages,
        temperature=0.7
    )
    return response['choices'][0]['message']['content'].strip()
