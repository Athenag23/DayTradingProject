from app.health_check import run_startup_checks
from app.agent import run_decision_engine
from app.logger import log_decision
from app.data_fetcher import get_market_snapshot

def main():
    if not run_startup_checks():
        return

    print("Phase 3.5: Real Indicators")

    data = get_market_snapshot("AAPL")

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

    print("\nComputed market snapshot:")
    print(data)

    result = run_decision_engine(market_data)

    print("\nFinal decision object:")
    print(result)

    if result is not None:
        log_decision(result)
        print("\nDecision logged")


if __name__ == "__main__":
    main()