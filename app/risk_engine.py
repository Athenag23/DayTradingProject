import json
import os
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from app.risk_config import (
    WATCHLIST, 
    KILL_SWITCH, 
    MAX_TRADES_PER_DAY,
    CONFIDENCE_THRESHOLD_BUY,
    CONFIDENCE_THRESHOLD_SELL,
    TRADING_HOURS_START,
    TRADING_HOURS_END,
    STALE_DATA_THRESHOLD_SECONDS,
    COOLDOWN_SECONDS
)


def validate_risk(decision_data):
    """
    Validate a Llama decision against all risk rules.
    
    Phase 4.1: Approval/rejection only. No execution.
    Includes Cooldown Timer and Duplicate Trade Prevention.
    
    Args:
        decision_data: Dict from Llama with keys:
            - symbol: str
            - decision: str (BUY, SELL, HOLD, NO_TRADE)
            - confidence: float (0.0-1.0)
            - reason: str
            - risk_notes: str
            - market_timestamp: str (ISO format)
    
    Returns:
        Dict with:
            - approved: bool
            - reason: str (why approved or rejected)
            - symbol: str
            - decision: str
    """
    
    # Validate required fields exist
    required_fields = ["symbol", "decision", "confidence"]
    for field in required_fields:
        if field not in decision_data:
            return {
                "approved": False,
                "reason": f"Missing required field: {field}",
                "symbol": decision_data.get("symbol", "N/A"),
                "decision": decision_data.get("decision", "N/A")
            }
    
    symbol = decision_data.get("symbol")
    decision = decision_data.get("decision")
    confidence = decision_data.get("confidence")
    
    # Rule 1: Kill switch blocks all trading
    if KILL_SWITCH:
        return {
            "approved": False,
            "reason": "❌ KILL SWITCH ENABLED - All trading disabled",
            "symbol": symbol,
            "decision": decision
        }
    
    # Rule 2: HOLD/NO_TRADE 
    if decision in ["HOLD", "NO_TRADE"]:
        return {
            "approved": False,
            "reason": f"⚪ {decision} decisions are never executable",
            "symbol": symbol,
            "decision": decision
        }
    
    # Rule 3: Market data must not be stale
    is_stale, stale_reason = _is_data_stale(decision_data)
    if is_stale:
        return {
            "approved": False,
            "reason": f"🧊 STALE_DATA - {stale_reason}",
            "symbol": symbol,
            "decision": decision
        }
    
    # Rule 4: Market must be open
    if not _is_market_open():
        return {
            "approved": False,
            "reason": "🕒 MARKET_CLOSED",
            "symbol": symbol,
            "decision": decision
        }

    # Rule 5: watchlist
    if symbol not in WATCHLIST:
        return {
            "approved": False,
            "reason": f"📛 {symbol} not in approved watchlist {WATCHLIST}",
            "symbol": symbol,
            "decision": decision
        }
    
    # Rule 6: Buy Confidence 
    if decision == "BUY":
        threshold = CONFIDENCE_THRESHOLD_BUY
        if confidence < threshold:
            return {
                "approved": False,
                "reason": f"📉 BUY confidence {confidence:.0%} below threshold {threshold:.0%}",
                "symbol": symbol,
                "decision": decision
            }
    
    # Rule 7: Sell Confidence
    elif decision == "SELL":
        threshold = CONFIDENCE_THRESHOLD_SELL
        if confidence < threshold:
            return {
                "approved": False,
                "reason": f"📈 SELL confidence {confidence:.0%} below threshold {threshold:.0%}",
                "symbol": symbol,
                "decision": decision
            }
    
    # Rule 8: Max trades 
    trades_today = _count_trades_today()
    if trades_today >= MAX_TRADES_PER_DAY:
        return {
            "approved": False,
            "reason": f"📊 Max {MAX_TRADES_PER_DAY} trades/day reached ({trades_today} already done)",
            "symbol": symbol,
            "decision": decision
        }
    
    # Rule 9: Cooldown Timer (Phase 4.1) - NEW
    if _is_cooldown_active(symbol):
        return {
            "approved": False,
            "reason": f"⏳ COOLDOWN_ACTIVE - {symbol} still in cooldown",
            "symbol": symbol,
            "decision": decision
        }
    
    # Rule 10: Duplicate Trade Prevention (Phase 4.1) - NEW
    if _is_duplicate_trade(symbol, decision):
        return {
            "approved": False,
            "reason": f"🔁 DUPLICATE_TRADE - duplicate {decision} for {symbol}",
            "symbol": symbol,
            "decision": decision
        }
    
    # All risk checks passed
    return {
        "approved": True,
        "reason": "✅ Passed all risk checks",
        "symbol": symbol,
        "decision": decision
    }


def _count_trades_today():
    """
    Count trades executed today.
    
    Phase 4: Returns count from logs/decisions.jsonl
    Phase 5: Will query actual executed trades.
    """
    today = datetime.now().date()
    count = 0
    decisions_log = "logs/decisions.jsonl"
    
    if not os.path.exists(decisions_log):
        return count
    
    try:
        with open(decisions_log, "r") as f:
            for line in f:
                if line.strip():
                    try:
                        row = json.loads(line)
                        if row.get("approved"):
                            ts_str = row.get("timestamp", "")
                            try:
                                ts = datetime.fromisoformat(ts_str)
                                if ts.date() == today:
                                    count += 1
                            except (ValueError, TypeError):
                                pass
                    except json.JSONDecodeError:
                        pass
    except IOError:
        pass
    
    return count


def _is_market_open():
    """
    Check if current time is within configured trading hours.
    
    Uses US Eastern Time because market hours are defined in EST/EDT.
    """
    
    eastern = ZoneInfo("America/New_York")
    now = datetime.now(eastern)

    current_time = now.hour + (now.minute / 60)

    return (
        TRADING_HOURS_START <= current_time <= TRADING_HOURS_END
    )


def _is_data_stale(decision_data):
    """
    Check whether market data used for the decision is stale.

    Expected timestamp field:
        market_timestamp

    Timestamp should be ISO format, example:
        2026-06-06T19:30:00Z
    """

    market_timestamp = decision_data.get("market_timestamp")

    if not market_timestamp:
        return True, "Missing market_timestamp"

    try:
        market_time = datetime.fromisoformat(
            market_timestamp.replace("Z", "+00:00")
        )

        now = datetime.now(market_time.tzinfo)
        age_seconds = (now - market_time).total_seconds()

        if age_seconds > STALE_DATA_THRESHOLD_SECONDS:
            return True, f"Market data stale: {age_seconds:.0f}s old"

        return False, f"Market data fresh: {age_seconds:.0f}s old"

    except Exception as e:
        return True, f"Invalid market_timestamp: {e}"


# NEW PHASE 4.1 HELPER FUNCTIONS BELOW

def _get_last_approved_decision(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve the last approved decision for a symbol.
    Searches logs/risk_reviews.jsonl first, then logs/decisions.jsonl.
    Returns most recent entry or None.
    """
    risk_reviews_log = "logs/risk_reviews.jsonl"
    decisions_log = "logs/decisions.jsonl"
    
    # Try risk_reviews log first (preferred)
    if os.path.exists(risk_reviews_log):
        try:
            entries = []
            with open(risk_reviews_log, "r") as f:
                for line in f:
                    if line.strip():
                        try:
                            row = json.loads(line)
                            if row.get("symbol") == symbol and row.get("approved"):
                                entries.append(row)
                        except json.JSONDecodeError:
                            pass
            
            if entries:
                entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                return entries[0]
        except IOError:
            pass
    
    # Fallback to decisions log
    if os.path.exists(decisions_log):
        try:
            entries = []
            with open(decisions_log, "r") as f:
                for line in f:
                    if line.strip():
                        try:
                            row = json.loads(line)
                            if row.get("symbol") == symbol and row.get("approved"):
                                entries.append(row)
                        except json.JSONDecodeError:
                            pass
            
            if entries:
                entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                return entries[0]
        except IOError:
            pass
    
    return None


def _is_cooldown_active(symbol: str) -> bool:
    """
    Check if symbol is still in cooldown window.
    Returns True if last approved trade within COOLDOWN_SECONDS.
    Phase 4.1 Feature.
    """
    last_decision = _get_last_approved_decision(symbol)
    if not last_decision:
        return False
    
    try:
        last_timestamp_str = last_decision.get("timestamp", "")
        last_timestamp = datetime.fromisoformat(last_timestamp_str)
        cooldown_end = last_timestamp + timedelta(seconds=COOLDOWN_SECONDS)
        
        if datetime.now(last_timestamp.tzinfo or timezone.utc) < cooldown_end:
            return True
    except (ValueError, TypeError):
        pass
    
    return False


def _is_duplicate_trade(symbol: str, decision: str) -> bool:
    """
    Prevent duplicate consecutive executable decisions.
    Only checks BUY and SELL.
    Returns True if last approved decision for symbol has same action.
    Phase 4.1 Feature.
    """
    # Only apply to BUY and SELL
    if decision not in ["BUY", "SELL"]:
        return False
    
    last_decision = _get_last_approved_decision(symbol)
    if not last_decision:
        return False
    
    last_action = last_decision.get("decision", "")
    return last_action == decision