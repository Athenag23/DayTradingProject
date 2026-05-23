# Trading Rules

## Purpose

These rules define how the autonomous trading agent is allowed to behave.

The AI may suggest trades, but hard-coded rules and risk controls decide whether a trade is allowed.

## Core Rules

1. Prefer NO_TRADE over weak or unclear setups.
2. Do not trade if confidence is below 0.75.
3. Do not trade if required market data is missing.
4. Do not trade if indicators conflict strongly.
5. Do not exceed 3 trades per day.
6. Do not risk more than 1% of account value per trade.
7. Do not trade without a stop-loss plan.
8. Do not trade if the market is closed.
9. Do not trade during system errors.
10. Kill switch overrides everything.

## AI Role

The AI agent may:
- evaluate setups
- explain reasoning
- classify opportunity quality
- recommend BUY, SELL, HOLD, or NO_TRADE

The AI agent may not:
- bypass risk rules
- trade without approval
- ignore missing data
- override kill switch

## Enforcement

These rules must eventually be enforced in:

```text
app/risk_engine.py