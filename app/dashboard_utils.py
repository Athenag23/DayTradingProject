"""
Dashboard utility functions for risk engine monitoring.

This module provides clean, testable functions for:
- Loading and parsing risk review logs
- Extracting decision data
- Counting trades
- Formatting data for display
- Handling errors gracefully
"""

import json
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pandas as pd
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.risk_config import KILL_SWITCH, MAX_TRADES_PER_DAY


def load_risk_reviews(limit: int = 50) -> List[Dict]:
    """
    Load risk review entries from JSONL file.
    
    Args:
        limit: Maximum number of entries to load (newest first)
    
    Returns:
        List of risk review entries, or empty list if file missing/empty
    """
    risk_log_file = Path(__file__).parent.parent / "logs" / "risk_reviews.jsonl"
    
    if not risk_log_file.exists():
        return []
    
    reviews = []
    try:
        with open(risk_log_file, "r") as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        reviews.append(entry)
                    except json.JSONDecodeError:
                        # Skip malformed lines silently
                        continue
        
        # Return newest first
        return list(reversed(reviews))[:limit]
    
    except Exception as e:
        print(f"Error loading risk reviews: {e}")
        return []


def load_decisions(limit: int = 50) -> List[Dict]:
    """
    Load decision entries from JSONL file.
    
    Args:
        limit: Maximum number of entries to load (newest first)
    
    Returns:
        List of decision entries, or empty list if file missing/empty
    """
    decisions_file = Path(__file__).parent.parent / "logs" / "decisions.jsonl"
    
    if not decisions_file.exists():
        return []
    
    decisions = []
    try:
        with open(decisions_file, "r") as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        decisions.append(entry)
                    except json.JSONDecodeError:
                        continue
        
        # Return newest first
        return list(reversed(decisions))[:limit]
    
    except Exception as e:
        print(f"Error loading decisions: {e}")
        return []


def get_latest_decision_and_review() -> Tuple[Optional[Dict], Optional[Dict]]:
    """
    Get the latest AI decision and its corresponding risk review.
    
    Returns:
        Tuple of (decision_dict, risk_review_dict) or (None, None) if not found
    """
    reviews = load_risk_reviews(limit=1)
    
    if not reviews:
        return None, None
    
    latest_review = reviews[0]
    risk_review = latest_review.get("risk_review", {})
    
    # Get the latest decision with matching symbol and decision type
    decisions = load_decisions()
    
    if not decisions:
        return None, latest_review
    
    # Find decision matching the risk review
    target_symbol = risk_review.get("symbol")
    target_decision = risk_review.get("decision")
    
    for dec_entry in decisions:
        dec = dec_entry.get("decision", {})
        if (dec.get("symbol") == target_symbol and 
            dec.get("decision") == target_decision):
            return dec_entry, latest_review
    
    # If no match found, return latest of each
    return decisions[0] if decisions else None, latest_review


def get_trade_count_today() -> int:
    """
    Count approved trades executed today.
    
    Returns:
        Number of approved trades today
    """
    today = date.today()
    decisions = load_decisions(limit=1000)  # Check last 1000
    
    count = 0
    for dec_entry in decisions:
        timestamp_str = dec_entry.get("timestamp", "")
        
        try:
            # Parse timestamp like "2026-05-23T04:37:24.750431Z"
            entry_date = datetime.fromisoformat(
                timestamp_str.replace("Z", "+00:00")
            ).date()
            
            if entry_date == today:
                count += 1
        except ValueError:
            continue
    
    return count


def get_rejection_reason_display(risk_review: Dict) -> str:
    """
    Extract and format rejection reason from risk review.
    
    Args:
        risk_review: Risk review dictionary
    
    Returns:
        Human-readable rejection reason or empty string if approved
    """
    if not risk_review:
        return ""
    
    if risk_review.get("approved"):
        return ""
    
    reason = risk_review.get("reason", "Unknown reason")
    return reason


def get_kill_switch_status() -> bool:
    """
    Get current kill switch status from configuration.
    
    Returns:
        True if kill switch is ON (trading disabled), False if OFF
    """
    return KILL_SWITCH


def format_risk_reviews_for_table(limit: int = 20) -> pd.DataFrame:
    """
    Format risk reviews for table display.
    
    Args:
        limit: Maximum number of rows to show
    
    Returns:
        Pandas DataFrame formatted for display
    """
    reviews = load_risk_reviews(limit=limit)
    
    if not reviews:
        return pd.DataFrame()
    
    data = []
    for entry in reviews:
        timestamp = entry.get("timestamp", "N/A")
        risk_review = entry.get("risk_review", {})
        
        # Parse timestamp for display
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            time_display = dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            time_display = timestamp[:19]  # First 19 chars
        
        approved = risk_review.get("approved", False)
        reason = risk_review.get("reason", "N/A")
        
        data.append({
            "Time": time_display,
            "Symbol": risk_review.get("symbol", "N/A"),
            "Decision": risk_review.get("decision", "N/A"),
            "Status": "✅ APPROVED" if approved else "❌ REJECTED",
            "Reason": reason,
        })
    
    return pd.DataFrame(data)


def get_decision_status_metrics() -> Dict:
    """
    Gather all metrics for the Risk Engine Status section.
    
    Returns:
        Dictionary with:
        - latest_decision: Latest AI decision
        - latest_review: Latest risk review
        - approved: Is latest approved?
        - rejection_reason: Why rejected (if applicable)
        - kill_switch: Is kill switch ON?
        - trades_today: Number of trades today
        - max_trades: Max trades allowed per day
    """
    decision, review = get_latest_decision_and_review()
    
    return {
        "latest_decision": decision,
        "latest_review": review,
        "approved": review.get("risk_review", {}).get("approved", False) if review else False,
        "rejection_reason": get_rejection_reason_display(review.get("risk_review", {}) if review else {}),
        "kill_switch": get_kill_switch_status(),
        "trades_today": get_trade_count_today(),
        "max_trades": MAX_TRADES_PER_DAY,
    }
