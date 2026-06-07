# Enhanced Risk Engine Dashboard - Implementation Guide

## Overview

The dashboard has been redesigned with a new **Risk Engine Status** section providing complete visibility into:
- ⚖️ Kill switch status (ON/OFF)
- ✅/❌ Decision approval/rejection status
- 📊 Daily trade count vs. limits
- 🎯 Latest decision details with AI reasoning
- 📋 Recent risk review history table

**Philosophy:** This dashboard is for **observability, governance, and safety** - helping you monitor what the AI wants to do and what the risk engine allowed.

---

## Architecture

### File Structure

```
app/
├── dashboard.py              # Main Streamlit UI (enhanced)
├── dashboard_utils.py        # NEW: Helper functions (modular, testable)
├── risk_engine.py            # Risk validation rules
├── risk_config.py            # Risk configuration
├── health_check.py           # System health checks
├── logger.py                 # Decision/risk logging
└── ...
```

### Key Principle: Separation of Concerns

**OLD (Monolithic):**
```
dashboard.py
├── Load logs
├── Parse JSON
├── Count trades
├── Format tables
├── Render sections
└── All in one file = hard to test & maintain
```

**NEW (Modular):**
```
dashboard_utils.py (testable, reusable)
├── load_risk_reviews()
├── load_decisions()
├── get_latest_decision_and_review()
├── get_trade_count_today()
├── get_rejection_reason_display()
├── get_kill_switch_status()
├── format_risk_reviews_for_table()
└── get_decision_status_metrics()

dashboard.py (UI only)
├── render_system_health()
├── render_risk_engine_status()
├── render_risk_review_table()
└── main()
```

---

## File: `app/dashboard_utils.py`

**Purpose:** Logic for data loading, parsing, counting, and formatting

**Key Functions:**

### `load_risk_reviews(limit: int = 50) -> List[Dict]`
- Reads `logs/risk_reviews.jsonl`
- Handles missing/empty files gracefully
- Skips malformed JSON lines silently
- Returns newest first
- Thread-safe

### `load_decisions(limit: int = 50) -> List[Dict]`
- Reads `logs/decisions.jsonl`
- Same error handling as `load_risk_reviews()`

### `get_latest_decision_and_review() -> Tuple[Dict, Dict]`
- Gets the most recent AI decision AND its risk review
- Matches them by symbol and decision type
- Returns `(None, None)` if not found

### `get_trade_count_today() -> int`
- Counts approved trades logged TODAY
- Parses ISO timestamps safely
- Returns integer

### `get_rejection_reason_display(risk_review: Dict) -> str`
- Extracts rejection reason from risk review
- Returns empty string if approved
- Examples:
  - "❌ KILL SWITCH ENABLED - All trading disabled"
  - "📉 BUY confidence 55% below threshold 65%"
  - "📛 TSLA not in approved watchlist"

### `get_kill_switch_status() -> bool`
- Reads from `app.risk_config.KILL_SWITCH`
- Returns `True` if ON (trading disabled)

### `format_risk_reviews_for_table(limit: int = 20) -> pd.DataFrame`
- Formats risk reviews for Streamlit table display
- Columns: Time, Symbol, Decision, Status, Reason
- Handles timestamp parsing gracefully
- Ready for `st.dataframe()`

### `get_decision_status_metrics() -> Dict`
- **Aggregates all metrics** for Risk Engine Status section
- Returns single dict with:
  ```python
  {
    "latest_decision": Dict,
    "latest_review": Dict,
    "approved": bool,
    "rejection_reason": str,
    "kill_switch": bool,
    "trades_today": int,
    "max_trades": int,
  }
  ```

---

## File: `app/dashboard.py`

**Purpose:** UI rendering only (logic moved to utils)

**Key Changes:**

### Imports
```python
from app.dashboard_utils import (
    get_decision_status_metrics,
    format_risk_reviews_for_table,
    load_decisions,
    load_risk_reviews
)
```

### New Rendering Functions

#### `render_system_health()`
- Shows: Ollama, Alpaca, decision count
- Same as before, visually unchanged

#### `render_risk_engine_status()` (NEW)
Three-column layout:
1. **Kill Switch Indicator**
   - 🟢 OFF / 🔴 ON
   - Visual indicator (green border vs red glow)
   - Trading status message

2. **Latest Decision Approval**
   - ✅ APPROVED / ❌ REJECTED
   - Decision type (BUY, SELL, HOLD, NO_TRADE)
   - Color-coded status

3. **Trade Count**
   - `3 / 10` trades used today
   - Percentage of daily limit

**Additional subsections:**
- Rejection reason (if rejected)
- Decision details (Symbol, Decision, Confidence, Reasoning)

#### `render_risk_review_table()` (NEW)
- Displays last 20 risk reviews
- Table columns: Time, Symbol, Decision, Status, Reason
- Shows total recorded reviews
- Graceful handling of empty logs

---

## CSS Styling

### Kill Switch Visual States

**OFF (Trading Enabled):**
```css
.kill-switch-off {
    background-color: var(--bg-card);
    border: 1px solid rgba(0, 255, 65, 0.3);  /* Green */
    box-shadow: 0 8px 32px rgba(0, 255, 65, 0.1);
}
```

**ON (Trading Disabled):**
```css
.kill-switch-on {
    background: linear-gradient(135deg, rgba(255, 0, 110, 0.3), ...);
    border: 2px solid #FF006E;  /* Bright red */
    box-shadow: 0 0 30px rgba(255, 0, 110, 0.3);  /* Red glow */
}
```

---

## Error Handling

All functions handle errors gracefully:

### Missing Log Files
```python
if not risk_log_file.exists():
    return []  # Empty list, not exception
```

### Malformed JSON Lines
```python
try:
    entry = json.loads(line)
except json.JSONDecodeError:
    continue  # Skip, don't crash
```

### Date Parsing Errors
```python
try:
    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
except ValueError:
    time_display = timestamp[:19]  # Fallback
```

---

## Data Flow Examples

### Example 1: Approved BUY Trade

**Logs:**
```json
# logs/risk_reviews.jsonl
{"timestamp": "2026-05-23T15:30:00Z", "risk_review": {"approved": true, "reason": "✅ Passed all risk checks", "symbol": "AAPL", "decision": "BUY"}}

# logs/decisions.jsonl
{"timestamp": "2026-05-23T15:30:00Z", "decision": {"symbol": "AAPL", "decision": "BUY", "confidence": 0.75, "reason": "Strong bullish trend", "risk_notes": "Standard risk"}}
```

**Dashboard Display:**
```
KILL SWITCH: 🟢 OFF (Trading Enabled)
LATEST DECISION: BUY ✅ APPROVED
TRADES TODAY: 1 / 10

Symbol: AAPL
Decision: BUY
Confidence: 75%
Reasoning: Strong bullish trend
```

### Example 2: Rejected LOW CONFIDENCE BUY

**Logs:**
```json
# logs/risk_reviews.jsonl
{"timestamp": "2026-05-23T15:35:00Z", "risk_review": {"approved": false, "reason": "📉 BUY confidence 55% below threshold 65%", "symbol": "MSFT", "decision": "BUY"}}
```

**Dashboard Display:**
```
KILL SWITCH: 🟢 OFF
LATEST DECISION: BUY ❌ REJECTED
TRADES TODAY: 1 / 10

Rejection Reason:
📉 BUY confidence 55% below threshold 65%

Symbol: N/A
(No decision details shown if rejected)
```

### Example 3: Kill Switch ON

**Config:**
```python
# app/risk_config.py
KILL_SWITCH = True
```

**Dashboard Display:**
```
KILL SWITCH: 🔴 ON (Bright red, glowing border)
             ⚠️  TRADING DISABLED
```

---

## Testing the Dashboard

### 1. View with Current Data

```bash
# Run dashboard with existing logs
streamlit run app/dashboard.py
```

Open: http://localhost:8501

### 2. Generate Test Data

```bash
# Run test to populate risk_reviews.jsonl
python app/test_risk_engine.py

# Now refresh dashboard - should show test data
```

### 3. Manual Testing

Edit `app/risk_config.py`:
```python
KILL_SWITCH = True  # Toggle to red alert
MAX_TRADES_PER_DAY = 2  # Test trade limit
```

Dashboard updates automatically on page refresh.

---

## Usage Guide

### For Monitoring

1. **Kill Switch Status**
   - Always visible at top of Risk Engine Status section
   - Red glow = trading disabled = ⚠️ check config

2. **Latest Decision**
   - Quick at-a-glance: Approved or Rejected?
   - Why rejected? See "Rejection Reason" section

3. **Trade Count**
   - `3 / 10` means 3 trades today out of max 10
   - Resets daily (based on trade timestamp)

4. **History Table**
   - Scroll to see recent decisions
   - Newest first by default
   - Rejection reasons explain each NO

### For Debugging

1. Check logs directly:
   ```bash
   tail -f logs/risk_reviews.jsonl
   tail -f logs/decisions.jsonl
   ```

2. Understand a rejection? Read the "Reason" column

3. Count today's trades:
   ```bash
   grep "$(date +%Y-%m-%d)" logs/decisions.jsonl | wc -l
   ```

---

## Integration with Risk Engine

**Data Flow:**

```
Llama Decision
    ↓
risk_engine.py validates
    ↓
logger.log_risk_review(result)
    ↓
logger.log_decision(decision)  # if approved
    ↓
dashboard_utils.load_risk_reviews()
    ↓
render_risk_engine_status()
```

Dashboard reads completed logs - no coupling to live engine.

---

## Resilience Checklist

✅ Missing `logs/risk_reviews.jsonl` → Shows "No risk reviews yet"
✅ Empty `logs/risk_reviews.jsonl` → Shows empty table
✅ Corrupted JSON line → Skipped silently
✅ Future timestamp → Parsed safely
✅ No latest decision → "No decisions yet"
✅ Kill switch toggle → Immediate visual change
✅ Network error → Streamlit handles gracefully

---

## Code Quality

### Testability

All logic in `dashboard_utils.py` - can be tested independently:
```python
# Example unit test
def test_get_trade_count_today():
    count = get_trade_count_today()
    assert isinstance(count, int)
    assert 0 <= count <= 100  # Reasonable bounds
```

### Readability

- Clear function names: `get_trade_count_today()` not `gtc()`
- Docstrings for all functions
- Type hints for parameters and returns

### Maintainability

- Small, focused functions (single responsibility)
- No hardcoded values (uses `risk_config`)
- Error handling at data loading layer
- UI logic separate from data logic

---

## Future Enhancements

### Phase 5: Add Live Trade Execution Metrics
```python
# In dashboard_utils.py
def get_executed_trades_today() -> int:
    """Count trades actually executed via Alpaca."""
    # Will query Alpaca API or logs/executions.jsonl
    pass
```

### Show Trade P&L
```python
st.markdown("### 💰 TODAY'S PERFORMANCE")
# Profit/loss if trades were executed
```

### Alert on Unusual Patterns
```python
if rejection_count > 10:
    st.error("⚠️  High rejection rate - check risk config")
```

### Export Decision History (CSV)
```python
df = format_risk_reviews_for_table(limit=1000)
csv = df.to_csv(index=False)
st.download_button("Download", csv, "decisions.csv")
```

---

## Summary

**What Changed:**
- ✅ Created modular `dashboard_utils.py`
- ✅ Enhanced dashboard with Risk Engine Status section
- ✅ Added kill switch visual indicator
- ✅ Added approval/rejection display
- ✅ Added trade count tracking
- ✅ Added rejection reason display
- ✅ Added recent risk reviews table
- ✅ Improved error handling throughout

**Benefits:**
- Easier to test (logic separated)
- Easier to maintain (focused functions)
- More resilient (graceful error handling)
- Better observability (Risk Engine Status section)
- Professional UI (consistent styling, color coding)

**Files:**
- `app/dashboard_utils.py` - NEW
- `app/dashboard.py` - UPDATED
- No changes to other files needed

Run it:
```bash
streamlit run app/dashboard.py
```
