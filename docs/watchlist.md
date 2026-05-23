
---

## 4. Paste into `docs/watchlist.md`

```md
# Watchlist

## Purpose

The agent may only scan and trade approved symbols from this list.

This prevents the agent from randomly selecting trades outside the defined strategy universe.

## Initial Watchlist

| Symbol | Reason |
|---|---|
| AAPL | Large-cap, high liquidity, strong data availability |
| MSFT | Large-cap, high liquidity |
| NVDA | High-volume AI/semiconductor name |
| AMD | High-volume semiconductor name |
| TSLA | High-volume momentum stock |

## Rules

1. Only symbols in this watchlist are allowed.
2. New symbols must be manually approved.
3. The agent may not discover and trade random symbols on its own.
4. Low-liquidity stocks are not allowed yet.
5. Penny stocks are not allowed.
6. Options are not allowed.
7. Crypto is not allowed.

## Future Additions

Possible future groups:
- ETF watchlist
- mega-cap tech watchlist
- high-volume momentum watchlist
- market index ETFs