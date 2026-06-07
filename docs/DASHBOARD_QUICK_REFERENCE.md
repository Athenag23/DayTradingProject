# Dashboard Quick Reference

## What's New

### Risk Engine Status Section

Three-column layout showing:

```
┌─────────────────────────────────────────────────────────┐
│  ⚖️  RISK ENGINE STATUS                                 │
├──────────────────────┬──────────────────────┬───────────┤
│  KILL SWITCH         │  LATEST DECISION     │  TRADES   │
│                      │                      │  TODAY    │
│  🟢 OFF / 🔴 ON      │  BUY/SELL/HOLD/...  │  3 / 10   │
│  ✓ Trading Enabled   │  ✅ APPROVED /      │           │
│  ⚠️  Trading Disabled │  ❌ REJECTED        │           │
└──────────────────────┴──────────────────────┴───────────┘

Rejection Reason (if applicable):
📉 BUY confidence 55% below threshold 65%

Decision Details:
Symbol: AAPL | Decision: BUY | Confidence: 75%
Reasoning: Strong bullish trend
```

### Recent Risk Reviews Table

```
Time                  Symbol  Decision  Status    Reason
2026-05-23 15:30:00  AAPL    BUY       ✅ APP    ✅ Passed all checks
2026-05-23 15:25:00  MSFT    BUY       ❌ REJ    📉 Low confidence
2026-05-23 15:20:00  SPY     HOLD      ❌ REJ    ⚪ Never executable
```

---

## Kill Switch Meanings

| Status | Visual | Meaning | Action |
|--------|--------|---------|--------|
| 🟢 OFF | Green border | Trading enabled | Normal operation |
| 🔴 ON | Red glow | Trading disabled | Check `risk_config.py` |

---

## Decision Statuses

| Status | Icon | Meaning |
|--------|------|---------|
| ✅ APPROVED | Green check | Passed all risk checks |
| ❌ REJECTED | Red X | Failed one or more rules |

---

## Common Rejection Reasons

| Reason | Cause | Fix |
|--------|-------|-----|
| ❌ KILL SWITCH ENABLED | `KILL_SWITCH = True` | Set to `False` |
| ⚪ HOLD never executable | Decision is HOLD | AI needs to decide BUY/SELL |
| 📛 Symbol not in watchlist | Symbol not approved | Add to `WATCHLIST` |
| 📉 BUY confidence below 65% | Confidence < threshold | AI needs higher confidence |
| 📊 Max trades/day reached | Hit daily limit | Wait for next day or increase `MAX_TRADES_PER_DAY` |
| Missing required field | Malformed decision | Check Llama output format |

---

## Navigation

```
Dashboard Home
│
├─ System Health (top)
│  ├─ Ollama status
│  ├─ Alpaca status
│  └─ Decision count
│
├─ Risk Engine Status (middle) ⭐ NEW
│  ├─ Kill switch indicator
│  ├─ Approval status
│  ├─ Trade count
│  ├─ Rejection reason (if applicable)
│  └─ Decision details
│
└─ Recent Risk Reviews (bottom) ⭐ ENHANCED
   └─ Table of last 20 decisions
```

---

## How to Read the Dashboard

### All Green, Happy Path

```
KILL SWITCH: 🟢 OFF
LATEST DECISION: BUY ✅ APPROVED
TRADES TODAY: 3 / 10

Symbol: AAPL
Decision: BUY
Confidence: 78%
Reasoning: Strong uptrend with breakout
```

**Interpretation:** System is working normally. Decision approved. Keep monitoring.

### Red Alert - Rejection

```
KILL SWITCH: 🟢 OFF
LATEST DECISION: SELL ❌ REJECTED
TRADES TODAY: 3 / 10

Rejection Reason:
📉 SELL confidence 45% below threshold 65%

Symbol: MSFT
Decision: SELL
```

**Interpretation:** AI suggested SELL but not confident enough. Blocked by risk engine. Good!

### Emergency - Kill Switch ON

```
KILL SWITCH: 🔴 ON
             ⚠️  TRADING DISABLED
```

**Interpretation:** All trading disabled immediately. Check config or system state.

---

## Files Used

| File | Location | Purpose |
|------|----------|---------|
| Risk reviews | `logs/risk_reviews.jsonl` | All risk validation records |
| Decisions | `logs/decisions.jsonl` | Approved trading decisions |
| Kill switch | `app/risk_config.py` | `KILL_SWITCH = False/True` |
| Max trades | `app/risk_config.py` | `MAX_TRADES_PER_DAY = 10` |

---

## Dashboard Utilities

New helper functions in `app/dashboard_utils.py`:

```python
load_risk_reviews()              # Get list of reviews from log
load_decisions()                 # Get list of decisions from log
get_latest_decision_and_review() # Get most recent pair
get_trade_count_today()          # Count approvals today
get_rejection_reason_display()   # Format rejection reason
get_kill_switch_status()         # Current switch state
format_risk_reviews_for_table()  # Pandas DataFrame for table
get_decision_status_metrics()    # All metrics in one call
```

All handle errors gracefully:
- Missing files → Empty list
- Malformed JSON → Skipped
- Bad timestamps → Fallback format

---

## Runbook

### View Dashboard
```bash
cd /Users/johnny5/AgentProjects/DayTradingApp
source venv/bin/activate
streamlit run app/dashboard.py
```
Open: http://localhost:8501

### Check Live Logs
```bash
tail -f logs/risk_reviews.jsonl
tail -f logs/decisions.jsonl
```

### Count Today's Trades
```bash
grep "$(date +%Y-%m-%d)" logs/decisions.jsonl | wc -l
```

### Enable Kill Switch (Emergency)
```bash
# Edit app/risk_config.py
KILL_SWITCH = True
```
Dashboard updates on next page load.

### Disable Kill Switch
```bash
# Edit app/risk_config.py
KILL_SWITCH = False
```

### See Last 10 Rejections
```bash
grep '"approved": false' logs/risk_reviews.jsonl | tail -10
```

---

## Common Scenarios

### "Why was my trade rejected?"
1. Check dashboard "Rejection Reason" section
2. Read the specific reason
3. Check `app/risk_config.py` for limits/settings
4. Verify symbol is in `WATCHLIST`

### "How many trades have I used today?"
Dashboard shows: `3 / 10` means 3 used, 7 remaining

### "Is the kill switch on?"
Look at top of Risk Engine Status section:
- 🟢 OFF = No
- 🔴 ON = Yes

### "What was the AI's last decision?"
Check "Latest Decision" and "Decision Details" sections

### "Show me my recent history"
Scroll to "Recent Risk Reviews" table - last 20 decisions

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Dashboard shows "No decisions yet" | Run `python app/main.py` to generate decisions |
| Kill switch is stuck ON | Check `risk_config.py`, ensure `KILL_SWITCH = False` |
| Table empty but logs exist | Check log file format (should be JSONL) |
| Dashboard won't load | Check Ollama/Alpaca health at top |
| Old data showing | Refresh page (F5) or restart streamlit |

---

## Credits

**Phase 4 Enhancement:**
- Modular `dashboard_utils.py` for logic
- Enhanced `dashboard.py` for UI
- Risk Engine Status section with kill switch, approval, trade count
- Recent Risk Reviews table
- Comprehensive error handling
