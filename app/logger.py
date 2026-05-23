import json
from datetime import datetime
from pathlib import Path


LOG_FILE = Path("logs/decisions.jsonl")


def log_decision(decision: dict) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "decision": decision
    }

    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")