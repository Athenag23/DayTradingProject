import requests
from app.config import APCA_API_KEY_ID, APCA_API_SECRET_KEY, APCA_BASE_URL


def check_ollama() -> bool:
    try:
        response = requests.get("http://127.0.0.1:11434", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def check_alpaca_config() -> bool:
    return all([
        APCA_API_KEY_ID,
        APCA_API_SECRET_KEY,
        APCA_BASE_URL,
    ])


def run_startup_checks() -> bool:
    print("Running startup checks...\n")

    ollama_ok = check_ollama()
    alpaca_ok = check_alpaca_config()

    print("✅ Ollama connection successful" if ollama_ok else "❌ Ollama server not running")
    print("✅ Alpaca config loaded" if alpaca_ok else "❌ Alpaca config missing")

    if ollama_ok and alpaca_ok:
        print("\n🚀 Autonomous trading agent ready\n")
        return True

    print("\n🛑 Startup checks failed. Fix the issue before running the agent.\n")
    return False