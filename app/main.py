import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agent import run_decision_engine
from app.data_fetcher import get_market_snapshot
from app.health_check import run_startup_checks
from app.logger import log_decision, log_risk_review
from app.risk_engine import validate_risk


def main():
    if not run_startup_checks():
        return

    print("\n🚀 Phase 4: Risk Engine Active\n")

    # Phase 3.5: Fetch real market data and compute real indicators
    data = get_market_snapshot("AAPL")
    market_data = json.dumps(data, separators=(",", ":"))

    print("Computed market snapshot:")
    print(data)

    # Get AI decision from Llama
    decision = run_decision_engine(market_data)

    if decision is not None:
        # Preserve timestamp used for this specific market decision
        decision["market_timestamp"] = data["market_timestamp"]

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