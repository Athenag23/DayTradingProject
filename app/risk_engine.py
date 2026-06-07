import json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from app.risk_config import (
    WATCHLIST, 
    KILL_SWITCH, 
    MAX_TRADES_PER_DAY,
    CONFIDENCE_THRESHOLD_BUY,
    CONFIDENCE_THRESHOLD_SELL,
    TRADING_HOURS_START,
    TRADING_HOURS_END
)


def validate_risk(decision_data):
    """
    Validate a Llama decision against all risk rules.
    
    Phase 4: Approval/rejection only. No execution.
    
    Args:
        decision_data: Dict from Llama with keys:
            - symbol: str
            - decision: str (BUY, SELL, HOLD, NO_TRADE)
            - confidence: float (0.0-1.0)
            - reason: str
            - risk_notes: str
    
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
    
    # Rule 3: Market must be open
    if not _is_market_open():
        return {
            "approved": False,
            "reason": "🕒 MARKET_CLOSED",
            "symbol": symbol,
            "decision": decision
    }
    
    # Rule 4: watchlist
    if symbol not in WATCHLIST:
        return {
            "approved": False,
            "reason": f"📛 {symbol} not in approved watchlist {WATCHLIST}",
            "symbol": symbol,
            "decision": decision
        }
    
    # Rule 5: Buy Confidence 
    if decision == "BUY":
        threshold = CONFIDENCE_THRESHOLD_BUY
        if confidence < threshold:
            return {
                "approved": False,
                "reason": f"📉 BUY confidence {confidence:.0%} below threshold {threshold:.0%}",
                "symbol": symbol,
                "decision": decision
            }
    
    # Rule 6: Sell Confidence
    elif decision == "SELL":
        threshold = CONFIDENCE_THRESHOLD_SELL
        if confidence < threshold:
            return {
                "approved": False,
                "reason": f"📈 SELL confidence {confidence:.0%} below threshold {threshold:.0%}",
                "symbol": symbol,
                "decision": decision
            }
    
    # Rule 7: Max trades 
    trades_today = _count_trades_today()
    if trades_today >= MAX_TRADES_PER_DAY:
        return {
            "approved": False,
            "reason": f"📊 Max {MAX_TRADES_PER_DAY} trades/day reached ({trades_today} already done)",
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
    
    Phase 4: Returns 0 (no trades executed yet).
    Phase 5: Will query actual executed trades from logs.
    """
    # TODO: In Phase 5, count actual executed trades
    # For now, always return 0
    return 0

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
