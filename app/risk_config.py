# Risk Engine Configuration - Phase 4
# Controls approval/rejection of all AI trading decisions

# Approved symbols (from watchlist)
WATCHLIST = ["AAPL", "MSFT", "SPY", "QQQ", "GOOGL"]

# Kill switch - set True to disable ALL trading immediately
KILL_SWITCH = False

# Maximum trades allowed per day
MAX_TRADES_PER_DAY = 10

# Confidence thresholds for BUY/SELL execution
CONFIDENCE_THRESHOLD_BUY = 0.65   # Require 65% confidence for BUY
CONFIDENCE_THRESHOLD_SELL = 0.65  # Require 65% confidence for SELL

# Trading window (24-hour format, decimal hours)
TRADING_HOURS_START = 9.5   # 9:30 AM EST
TRADING_HOURS_END = 16.0    # 4:00 PM EST
