import json
from app.llama_client import query_llama
from app.prompt_builder import build_prompt


ALLOWED_DECISIONS = {"BUY", "SELL", "HOLD", "NO_TRADE"}


def validate_decision(data: dict) -> bool:
    required_fields = {"symbol", "decision", "confidence", "reason", "risk_notes"}

    if not isinstance(data, dict):
        print("Validation failed: response is not a dictionary")
        return False

    missing = required_fields - data.keys()
    if missing:
        print(f"Validation failed: missing fields {missing}")
        return False

    if data["decision"] not in ALLOWED_DECISIONS:
        print(f"Validation failed: invalid decision {data['decision']}")
        return False

    if not isinstance(data["confidence"], (int, float)):
        print("Validation failed: confidence must be a number")
        return False

    if not 0 <= data["confidence"] <= 1:
        print("Validation failed: confidence must be between 0 and 1")
        return False

    if not isinstance(data["symbol"], str) or not data["symbol"].strip():
        print("Validation failed: symbol must be a non-empty string")
        return False

    if not isinstance(data["reason"], str) or not data["reason"].strip():
        print("Validation failed: reason must be a non-empty string")
        return False

    if not isinstance(data["risk_notes"], str) or not data["risk_notes"].strip():
        print("Validation failed: risk_notes must be a non-empty string")
        return False

    return True


def run_decision_engine(market_data: str):
    prompt = build_prompt(market_data)
    raw_response = query_llama(prompt)

    print("\nRaw Llama response:")
    print(raw_response)

    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError as e:
        print(f"\nJSON parse failed: {e}")
        return None

    if not validate_decision(parsed):
        return None

    return parsed