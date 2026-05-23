import json
from datetime import datetime
from pathlib import Path


LOG_FILE = Path("logs/decisions.jsonl")
RISK_LOG_FILE = Path("logs/risk_reviews.jsonl")


def log_decision(decision: dict) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "decision": decision
    }

    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")


def log_risk_review(risk_result: dict) -> None:
    """
    Log risk engine decision to risk_reviews.jsonl
    
    Args:
        risk_result: Dict from risk_engine.validate_risk()
            {
                "approved": bool,
                "reason": str,
                "symbol": str,
                "decision": str
            }
    """
    RISK_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    review_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "risk_review": risk_result
    }
    
    try:
        with RISK_LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(review_entry) + "\n")
    except Exception as e:
        print(f"❌ Error logging risk review: {e}")