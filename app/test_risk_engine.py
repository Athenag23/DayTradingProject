"""
Phase 4 Risk Engine Test Suite
Demonstrates all 6 risk validation rules
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.risk_engine import validate_risk
from app.logger import log_risk_review
from app.risk_config import WATCHLIST, KILL_SWITCH, CONFIDENCE_THRESHOLD_BUY, CONFIDENCE_THRESHOLD_SELL

def test_scenario(name, decision_data):
    """Test a single risk scenario."""
    print(f"\n{'='*70}")
    print(f"TEST: {name}")
    print(f"{'='*70}")
    print(f"Input: {decision_data}")
    result = validate_risk(decision_data)
    log_risk_review(result)
    print(f"Result: {result}")
    return result

def main():
    print("\n🔐 PHASE 4 RISK ENGINE TEST SUITE")
    print(f"Watchlist: {WATCHLIST}")
    print(f"BUY Threshold: {CONFIDENCE_THRESHOLD_BUY:.0%}")
    print(f"SELL Threshold: {CONFIDENCE_THRESHOLD_SELL:.0%}")
    print(f"Kill Switch: {KILL_SWITCH}")
    
    # Test 1: Valid BUY decision (should PASS)
    test_scenario(
        "Valid BUY Decision (Watchlist, High Confidence)",
        {
            "symbol": "AAPL",
            "decision": "BUY",
            "confidence": 0.75,
            "reason": "Strong bullish trend",
            "risk_notes": "Standard risk"
        }
    )
    
    # Test 2: Low confidence BUY (should FAIL)
    test_scenario(
        "Low Confidence BUY (Below 65% threshold)",
        {
            "symbol": "MSFT",
            "decision": "BUY",
            "confidence": 0.55,
            "reason": "Weak signal",
            "risk_notes": "Uncertain"
        }
    )
    
    # Test 3: SELL with high confidence (should PASS)
    test_scenario(
        "Valid SELL Decision (Watchlist, High Confidence)",
        {
            "symbol": "SPY",
            "decision": "SELL",
            "confidence": 0.72,
            "reason": "Strong bearish signal",
            "risk_notes": "Volatility expected"
        }
    )
    
    # Test 4: HOLD decision (should always FAIL)
    test_scenario(
        "HOLD Decision (Never Executable)",
        {
            "symbol": "GOOGL",
            "decision": "HOLD",
            "confidence": 0.95,
            "reason": "Mixed signals",
            "risk_notes": "Wait and see"
        }
    )
    
    # Test 5: Symbol not on watchlist (should FAIL)
    test_scenario(
        "Unlisted Symbol (Not in Watchlist)",
        {
            "symbol": "TSLA",
            "decision": "BUY",
            "confidence": 0.80,
            "reason": "Strong momentum",
            "risk_notes": "High volatility"
        }
    )
    
    # Test 6: Missing required field (should FAIL)
    test_scenario(
        "Missing Required Field (No confidence)",
        {
            "symbol": "QQQ",
            "decision": "BUY",
            "reason": "Trend following",
            "risk_notes": "Standard risk"
        }
    )
    
    print("\n" + "="*70)
    print("✅ ALL TESTS COMPLETED")
    print("="*70)
    print("\nLog file: logs/risk_reviews.jsonl")
    print("Review results in Dashboard: streamlit run app/dashboard.py")

if __name__ == "__main__":
    main()
