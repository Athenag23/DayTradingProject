# ⚡ HELIX - Autonomous Day Trading Agent

A local AI-powered autonomous trading system using Llama, Ollama, and Alpaca API. Built in phases with strict risk controls and decision oversight before paper trading and live execution.

**Current Status:** Phase 4 (Risk Engine - Approval/Rejection) ✅

---

## 📋 Overview

HELIX is an autonomous day trading system that:
- Analyzes real market data from Alpaca
- Calculates trading indicators (RSI, EMA-9, EMA-20, Trend)
- Uses local Llama AI (via Ollama) to generate trading decisions
- Validates all decisions through a risk engine with 6 approval rules
- Logs all decisions and risk reviews for audit trail
- Provides a modern Streamlit dashboard for monitoring
- Currently requires human approval before execution while autonomous safeguards and risk controls are being validated

### Key Features
- **Local Risk Engine**: 6 validation rules before trade approval
- **Approved Watchlist**: Only trade whitelisted symbols
- **Confidence Thresholds**: Require 65%+ confidence for BUY/SELL
- **Kill Switch**: Emergency stop for all trading
- **Audit Trail**: Complete decision history in JSONL logs
- **Real Market Data**: Live integration with Alpaca
- **Modern Dashboard**: Dark-themed command center interface
- **Modular Architecture**: Clean separation of concerns
- **Deterministic Controls**: Hard rules override AI decisions

---

## 🏗️ Architecture

```
Alpaca API
    ↓
[data_fetcher.py]
    ↓
Real Market Data (OHLCV)
    ↓
[indicators.py] → RSI, EMA-9, EMA-20, Trend Classification
    ↓
[prompt_builder.py] → Market analysis prompt
    ↓
[llama_client.py] → Local Llama via Ollama
    ↓
JSON Decision: {symbol, decision, confidence, reason, risk_notes}
    ↓
[risk_engine.py] → Validation against deterministic rules
    ↓
├─ APPROVED → [logger.py] → decisions.jsonl
└─ REJECTED → [logger.py] → risk_reviews.jsonl
    ↓
[dashboard.py] → Streamlit monitoring
```

---

## 📊 Current Phases

### ✅ Phase 1: Local Llama Decision Engine
- Local Llama model via Ollama
- JSON parsing from LLM responses
- Decision validation

### ✅ Phase 1.5: JSON Parsing & Validation
- Robust JSON extraction from Llama output
- Field validation and error handling
- Deterministic temperature configuration (temperature=0)

### ✅ Phase 1.6: Decision Logging
- JSONL-based decision logs
- Timestamped entries with full metadata

### ✅ Phase 2: Controlled Loop
- Main trading loop with error handling
- Health checks for dependencies
- Safe Ctrl+C shutdown behavior

### ✅ Phase 3: Alpaca Real Market Data
- Integration with Alpaca API
- Real-time market data fetching
- Volume, price, and indicator calculations

### ✅ Phase 3.5: Real Indicators
- RSI (Relative Strength Index)
- EMA-9 (9-period Exponential Moving Average)
- EMA-20 (20-period Exponential Moving Average)
- Trend classification (BULLISH, BEARISH, NEUTRAL)

### ✅ Phase 3.6: Dashboard
- Streamlit monitoring dashboard
- Startup health checks
- System monitoring interface

### ✅ Phase 3.7: Documentation
- Trading rules (docs/trading_rules.md)
- Watchlist (docs/watchlist.md)
- Architecture (docs/architecture.md)
- Roadmap (docs/roadmap.md)

### ✅ Phase 4: Risk Engine ⭐
**6 Validation Rules:**
1. **Kill Switch**: Emergency stop disables all trading
2. **Executable Decisions**: HOLD and NO_TRADE are never executed
3. **Watchlist Enforcement**: Only trade approved symbols
4. **Confidence Thresholds**: BUY/SELL require 65%+ confidence
5. **Risk Limits**: Max 10 trades per day
6. **Field Validation**: Required fields must exist

**Output:**
```
{
  "approved": true,
  "reason": "✅ Passed all risk checks",
  "symbol": "AAPL",
  "decision": "BUY"
}
```

---

## 🚀 Quick Start

### Requirements
- Python 3.10+
- Ollama with Llama model running locally
- Alpaca API credentials
- macOS/Linux/WSL

### 1. Clone & Setup

```bash
git clone https://github.com/YOUR_USERNAME/DayTradingApp.git
cd DayTradingApp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Credentials

Create `.env` file:
```env
APCA_API_KEY_ID=your_alpaca_api_key
APCA_API_SECRET_KEY=your_alpaca_secret
APCA_BASE_URL=https://paper-api.alpaca.markets
```

### 3. Start Ollama

```bash
# In separate terminal
ollama serve
ollama pull llama3.1:8b  # if not already installed
ollama list
```

### 4. Run the System

```bash
# Single decision cycle
python app/main.py

# Test risk engine with 6 scenarios
python app/test_risk_engine.py

# View dashboard
streamlit run app/dashboard.py
```

---

## 📁 Project Structure

```
DayTradingApp/
├── app/
│   ├── main.py                 # Entry point - orchestrates workflow
│   ├── agent.py                # AI decision engine
│   ├── llama_client.py         # Ollama client
│   ├── data_fetcher.py         # Alpaca data integration
│   ├── indicators.py           # RSI, EMA calculations
│   ├── prompt_builder.py       # Market analysis prompt
│   ├── health_check.py         # Dependency verification
│   ├── config.py               # Environment variables
│   ├── logger.py               # Decision & risk logging
│   ├── dashboard.py            # Streamlit UI
│   ├── risk_config.py          # Risk rules configuration ⭐
│   ├── risk_engine.py          # Risk validation logic ⭐
│   └── test_risk_engine.py     # Risk engine test suite ⭐
├── docs/
│   ├── trading_rules.md        # Market analysis strategy
│   ├── watchlist.md            # Approved symbols
│   ├── architecture.md         # Technical design
│   └── roadmap.md              # Future phases
├── logs/
│   ├── decisions.jsonl         # Approved trading decisions
│   └── risk_reviews.jsonl      # Risk validation audit trail
├── data/
│   └── sample_market_data.json # Test data
├── .env                        # Credentials (git ignored)
├── .gitignore
└── README.md
```

---

## ⚙️ Configuration

### Risk Engine Settings (`app/risk_config.py`)

```python
# Approved trading symbols
WATCHLIST = ["AAPL", "MSFT", "SPY", "QQQ", "GOOGL"]

# Emergency disable
KILL_SWITCH = False

# Max trades per day
MAX_TRADES_PER_DAY = 10

# Confidence thresholds
CONFIDENCE_THRESHOLD_BUY = 0.65   # 65%
CONFIDENCE_THRESHOLD_SELL = 0.65  # 65%
```

### Health Checks

Both Ollama and Alpaca must pass startup checks:
```
✅ Ollama connection successful
✅ Alpaca config loaded
🚀 Autonomous trading agent ready
```

---

## 📊 Dashboard

Current Dashboard Modules:
- **System Health**: Ollama, Alpaca, decision count
- **Latest Decision**: Symbol, decision, confidence, timestamp
- **Analysis Details**: Reasoning and risk assessment
- **Decision History**: Last 20 decisions in table format
- **Dark Theme**: Cyan neon styling, professional command center design

Planned Dashboard Modules:
- **Risk Engine Status**: 
- **Trade Cooldowns**: 
- **Market Session Status**: 
- **Stale Data Alerts**: 
- **Execution Queue Monitoring**: 

Run it:
```bash
streamlit run app/dashboard.py
```

Accessible at: `http://localhost:8501`

---

## 📋 Logging

### `logs/decisions.jsonl`
Approved decisions ready for future execution pipeline:
```json
{
  "timestamp": "2026-05-23T04:37:24.750431Z",
  "decision": {
    "symbol": "AAPL",
    "decision": "BUY",
    "confidence": 0.75,
    "reason": "Strong bullish trend",
    "risk_notes": "Standard risk"
  }
}
```

### `logs/risk_reviews.jsonl`
Complete audit trail of all risk validations:
```json
{
  "timestamp": "2026-05-23T04:37:24.750431Z",
  "risk_review": {
    "approved": true,
    "reason": "✅ Passed all risk checks",
    "symbol": "AAPL",
    "decision": "BUY"
  }
}
```

---

## 🧪 Testing

Run the risk engine test suite:
```bash
python app/test_risk_engine.py
```

Tests all 6 risk validation rules:
- ✅ Valid BUY decision passes
- ❌ Low confidence BUY rejected
- ✅ Valid SELL decision passes
- ❌ HOLD decision rejected
- ❌ Unlisted symbol rejected
- ❌ Missing required field rejected

---

## 🛣️ Roadmap

### Phase 4.1 : Risk Hardening
- Market-hours validation
- Stale-data detection
- Cooldown timers
- Duplicate trade prevention
- Expanded dashboard risk visibility


### Phase 4.5: Persistent State Layer
- state_manager.py
- Trade cooldown persistence
- Position tracking
- Session state tracking
- Daily trade counters

### Phase 5: Autonomous Paper Trading
- Alpaca paper execution layer
- Submit approved paper-trading orders
- Track fills and execution lifecycle
- Position and P&L tracking
- Transaction logging

### Phase 6: Advanced Risk Management
- Position sizing 
- Stop-loss automation
- Profit-taking levels
- Portfolio exposure limits

### Phase 7: Autonomous Live Trading
- Controlled live execution
- Real-money safeguards
- Daily loss limits
- Position limits per symbol
- Advanced execution governance

### Phase 8: Advanced Features
- Multi-symbol concurrent trading
- Backtesting engine
- Strategy optimization
- external monitoring API

---

## 🔐 Security & Controls

- ✅ **Kill Switch**: Emergency stop for all trading
- ✅ **Whitelist Only**: Trade only approved symbols
- ✅ **Confidence Thresholds**: Require high confidence
- ✅ **Daily Limits**: Max trades per day
- ✅ **Audit Trail**: Complete decision history
- ✅ **No Auto-Execution**: Phase 4 is approval only
- ✅ **Environment Variables**: Secrets in .env (git ignored)
- ✅ **Paper Trading First**: Practice before live money

---

## 🐛 Troubleshooting

### Ollama connection fails
```bash
# Make sure Ollama is running
ollama serve

# In another terminal, check
curl http://127.0.0.1:11434
```

### Alpaca config missing
```bash
# Check your .env file
cat .env

# Verify credentials are set
echo $APCA_API_KEY_ID
```

### Market data not available
- Use sample data (current main.py uses sample for testing)
- Check trading hours (market may be closed)
- Verify Alpaca API connection

### Dashboard not loading
```bash
# Make sure Streamlit is installed
pip install streamlit

# Clear cache if needed
rm -rf ~/.streamlit/
```

---

## 📚 Documentation

- [Trading Rules](docs/trading_rules.md) - Strategy and indicators
- [Watchlist](docs/watchlist.md) - Approved symbols
- [Architecture](docs/architecture.md) - System design details
- [Roadmap](docs/roadmap.md) - Future development phases

---

## 📝 Git Workflow

```bash
# Check status
git status

# Add changes
git add app/ docs/ logs/

# Commit with phase info
git commit -m "Phase X: Description"

# Push to GitHub
git push origin main
```

---

## 🤝 Contributing

This is a personal trading project. Modifications should be tested thoroughly before deployment.

**Recommended workflow:**
1. Create feature branch: `git checkout -b feature/phase-5`
2. Implement changes
3. Test thoroughly: `python app/test_*.py`
4. Review logs: `tail -f logs/risk_reviews.jsonl`
5. Commit with clear messages
6. Push and verify

---

## 📞 Support

For issues:
1. Check logs: `logs/decisions.jsonl` and `logs/risk_reviews.jsonl`
2. Run health checks: Verify Ollama and Alpaca
3. Test risk engine: `python app/test_risk_engine.py`
4. Review dashboard: `streamlit run app/dashboard.py`

---

## 🎯 Key Metrics

**Phase 4 Status:**
- ✅ 6 deterministic validation rules
- ✅ Full audit trail
- ✅ Real market data integration
- ✅ Local AI decision engine
- ✅ Streamlit dashboard
- ⏳ Autonomous paper execution pending

**Next Milestone:**
Phase 5 — Controlled autonomous paper trading through Alpaca execution layer.

---

**Built with:** Python • Llama2 • Ollama • Alpaca API • Streamlit

**Created:** May 2026
