print("LLAMA CLIENT LOADED")

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1:8b"

def query_llama(prompt: str) -> str:
    print("QUERYING OLLAMA...")

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0
            }
        },
        timeout=60
    )

    print("STATUS:", response.status_code)

    if response.status_code != 200:
        raise Exception(f"Error: {response.text}")

    data = response.json()
    print("RAW RESPONSE RECEIVED")
    return data["response"]
