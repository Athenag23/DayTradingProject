import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.health_check import run_startup_checks
from app.agent import run_decision_engine
from app.logger import log_decision, log_risk_review
from app.risk_engine import validate_risk

def get_sample_market_data(symbol: str):
    """
    Use sample data for testing when market data is unavailable.
    Phase 5 will always use real Alpaca data.
    """
    return {
        "symbol": symbol,
        "price": 150.25,
        "volume": 2500000,
        "rsi": 72.5,
        "ema_9": 149.80,
        "ema_20": 148.50,
        "trend": "BULLISH",
        "news": "none"
    }

def main():
    if not run_startup_checks():
        return

    print("\n🚀 Phase 4: Risk Engine Active\n")

    # Use sample data for testing
    data = get_sample_market_data("AAPL")

    market_data = f"""
    {{
      "symbol": "{data['symbol']}",
      "price": {data['price']},
      "volume": {data['volume']},
      "rsi": {data['rsi']},
      "ema_9": {data['ema_9']},
      "ema_20": {data['ema_20']},
      "trend": "{data['trend']}",
      "news": "{data['news']}"
    }}
    """

    print("Computed market snapshot:")
    print(data)

    # Get AI decision from Llama
    decision = run_decision_engine(market_data)

    print("\n🤖 Llama decision:")
    print(decision)

    if decision is not None:
        # Phase 4: Validate decision through risk engine
        risk_review = validate_risk(decision)
        log_risk_review(risk_review)
        
        print("\nRisk Review:")
        print(risk_review)
        
        if risk_review["approved"]:
            print(f"\n✅ {risk_review['reason']}")
            log_decision(decision)
            print("✅ Decision logged")
        else:
            print(f"\n⛔ {risk_review['reason']}")
            print("⛔ Decision rejected by risk engine") 
    else:
        print("\n❌ No decision received from Llama")


if __name__ == "__main__":
    main()