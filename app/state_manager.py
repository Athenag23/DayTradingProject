from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


STATE_SCHEMA_DEFAULT: Dict[str, Any] = {
    "trade_count_today": 0,
    "last_reset_date": "",
    "cooldowns": {},
    "last_decisions": {},
    "positions": {}
}


def _state_file_path() -> Path:
    """Return the canonical path to data/state.json using pathlib."""
    # app/.. -> workspace root, then data/state.json
    return Path(__file__).parent.parent.joinpath("data", "state.json")


def _ensure_schema(obj: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure the loaded object contains all required keys with sensible defaults."""
    state = dict(STATE_SCHEMA_DEFAULT)
    if not isinstance(obj, dict):
        return state

    for k, v in STATE_SCHEMA_DEFAULT.items():
        if k in obj and obj[k] is not None:
            state[k] = obj[k]

    # Normalize types minimally
    try:
        state["trade_count_today"] = int(state.get("trade_count_today", 0) or 0)
    except Exception:
        state["trade_count_today"] = 0

    if not isinstance(state.get("last_reset_date"), str):
        state["last_reset_date"] = ""

    if not isinstance(state.get("cooldowns"), dict):
        state["cooldowns"] = {}

    if not isinstance(state.get("last_decisions"), dict):
        state["last_decisions"] = {}

    if not isinstance(state.get("positions"), dict):
        state["positions"] = {}

    return state


def load_state() -> Dict[str, Any]:
    """Load persistent state from `data/state.json`.

    - Creates `data/` directory if missing.
    - Creates `state.json` with defaults if missing or empty.
    - If JSON is corrupted, backs up the corrupted file and returns a fresh default state.
    - Always returns a valid state object conforming to the schema.
    """
    path = _state_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    # If file does not exist -> create with defaults and return
    if not path.exists():
        save_state(STATE_SCHEMA_DEFAULT)
        return dict(STATE_SCHEMA_DEFAULT)

    # Read file
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        # Could not read file; return defaults
        return dict(STATE_SCHEMA_DEFAULT)

    if not text.strip():
        # Empty file -> overwrite with defaults
        save_state(STATE_SCHEMA_DEFAULT)
        return dict(STATE_SCHEMA_DEFAULT)

    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        # Backup corrupted file and write fresh state
        try:
            stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            corrupt_path = path.with_name(path.name + f".corrupt.{stamp}")
            os.replace(path, corrupt_path)
        except Exception:
            # If backup fails, attempt to remove the file
            try:
                path.unlink()
            except Exception:
                pass

        save_state(STATE_SCHEMA_DEFAULT)
        return dict(STATE_SCHEMA_DEFAULT)

    # Normalize and ensure schema
    state = _ensure_schema(obj)

    # Persist normalized state back to file to maintain canonical form
    try:
        save_state(state)
    except Exception:
        # If save fails, still return the state object
        pass

    return state


def save_state(state: Dict[str, Any]) -> None:
    """Save state to `data/state.json` using UTF-8.

    Performs an atomic write via a temporary file replace where possible.
    """
    path = _state_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure schema before saving
    state_to_write = _ensure_schema(state)

    tmp_path = path.with_suffix(".tmp")
    try:
        tmp_path.write_text(json.dumps(state_to_write, ensure_ascii=False, indent=2), encoding="utf-8")
        # Move into place
        os.replace(tmp_path, path)
    except Exception:
        # Fallback: try direct write
        try:
            path.write_text(json.dumps(state_to_write, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            # If all writes fail, raise to inform caller
            raise


if __name__ == "__main__":
    # Quick manual smoke test when run directly
    s = load_state()
    print("Loaded state:", s)
    s["trade_count_today"] = s.get("trade_count_today", 0) + 1
    save_state(s)
    print("Updated state trade_count_today -> ", s["trade_count_today"])
