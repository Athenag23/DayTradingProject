import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.health_check import check_ollama, check_alpaca_config
from app.dashboard_utils import (
    get_decision_status_metrics,
    format_risk_reviews_for_table,
    load_decisions,
    load_risk_reviews
)


# Custom CSS for modern dark theme
CUSTOM_CSS = """
<style>
    :root {
        --primary: #00D9FF;
        --success: #00FF41;
        --danger: #FF006E;
        --warning: #FFB700;
        --bg-dark: #0A0E27;
        --bg-card: #1B2038;
        --text-primary: #FFFFFF;
        --text-secondary: #A0AABF;
    }
    
    body {
        background-color: var(--bg-dark);
        color: var(--text-primary);
    }
    
    .stApp {
        background: linear-gradient(135deg, #0A0E27 0%, #1B1E3F 100%);
    }
    
    /* Custom metric card styling */
    [data-testid="metric-container"] {
        background-color: var(--bg-card);
        border: 1px solid rgba(0, 217, 255, 0.2);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 0 20px rgba(0, 217, 255, 0.1);
        transition: all 0.3s ease;
    }
    
    [data-testid="metric-container"]:hover {
        border-color: rgba(0, 217, 255, 0.4);
        box-shadow: 0 0 30px rgba(0, 217, 255, 0.2);
    }
    
    /* Card styling */
    .command-card {
        background-color: var(--bg-card);
        border: 1px solid rgba(0, 217, 255, 0.3);
        border-radius: 16px;
        padding: 24px;
        margin: 12px 0;
        box-shadow: 0 8px 32px rgba(0, 217, 255, 0.1);
    }
    
    .kill-switch-on {
        background: linear-gradient(135deg, rgba(255, 0, 110, 0.3), rgba(255, 0, 110, 0.1));
        border: 2px solid #FF006E !important;
        box-shadow: 0 0 30px rgba(255, 0, 110, 0.3) !important;
    }
    
    .kill-switch-off {
        background-color: var(--bg-card);
        border: 1px solid rgba(0, 255, 65, 0.3);
        box-shadow: 0 8px 32px rgba(0, 255, 65, 0.1);
    }
    
    /* Header styling */
    h1, h2, h3 {
        color: var(--text-primary);
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    
    h1 {
        background: linear-gradient(90deg, var(--primary), #00FFFF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5em !important;
        margin-bottom: 8px;
    }
    
    /* Divider */
    hr {
        border: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0, 217, 255, 0.3), transparent);
    }
    
    /* Dataframe styling */
    [data-testid="stDataFrame"] {
        background-color: var(--bg-card) !important;
    }
</style>
"""

st.set_page_config(
    page_title="Autonomous Trading Command Center",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_system_health():
    """Render system health status section."""
    st.markdown("### 🔧 SYSTEM STATUS")
    health_col1, health_col2, health_col3 = st.columns(3)
    
    ollama_ok = check_ollama()
    alpaca_ok = check_alpaca_config()
    
    with health_col1:
        status = "🟢 ONLINE" if ollama_ok else "🔴 OFFLINE"
        st.markdown(
            f"<div class='command-card'>"
            f"<div style='font-size: 0.85em; color: #A0AABF; margin-bottom: 8px;'>AI ENGINE</div>"
            f"<div style='font-size: 1.4em; {'color: #00FF41;' if ollama_ok else 'color: #FF006E;'}'>"
            f"{'✓ OLLAMA' if ollama_ok else '✗ OLLAMA'}</div>"
            f"<div style='font-size: 0.8em; color: #A0AABF; margin-top: 8px;'>{status}</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    with health_col2:
        status = "🟢 CONNECTED" if alpaca_ok else "🔴 MISSING"
        st.markdown(
            f"<div class='command-card'>"
            f"<div style='font-size: 0.85em; color: #A0AABF; margin-bottom: 8px;'>BROKER</div>"
            f"<div style='font-size: 1.4em; {'color: #00FF41;' if alpaca_ok else 'color: #FF006E;'}'>"
            f"{'✓ ALPACA' if alpaca_ok else '✗ ALPACA'}</div>"
            f"<div style='font-size: 0.8em; color: #A0AABF; margin-top: 8px;'>{status}</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    with health_col3:
        decision_count = len(load_decisions())
        st.markdown(
            f"<div class='command-card'>"
            f"<div style='font-size: 0.85em; color: #A0AABF; margin-bottom: 8px;'>DECISIONS</div>"
            f"<div style='font-size: 1.4em; color: #00D9FF;'>{decision_count}</div>"
            f"<div style='font-size: 0.8em; color: #A0AABF; margin-top: 8px;'>📊 Total logged</div>"
            f"</div>",
            unsafe_allow_html=True
        )


def render_risk_engine_status():
    """Render risk engine status section with kill switch, approval status, and trade count."""
    st.markdown("### ⚖️  RISK ENGINE STATUS")
    
    # Get all metrics
    metrics = get_decision_status_metrics()
    latest_decision = metrics["latest_decision"]
    latest_review = metrics["latest_review"]
    is_approved = metrics["approved"]
    rejection_reason = metrics["rejection_reason"]
    kill_switch_on = metrics["kill_switch"]
    trades_today = metrics["trades_today"]
    max_trades = metrics["max_trades"]
    
    # Kill Switch Indicator
    kill_switch_col, approval_col, trades_col = st.columns(3)
    
    with kill_switch_col:
        kill_status = "🔴 ON" if kill_switch_on else "🟢 OFF"
        kill_color = "#FF006E" if kill_switch_on else "#00FF41"
        kill_class = "kill-switch-on" if kill_switch_on else "kill-switch-off"
        st.markdown(
            f"<div class='command-card {kill_class}'>"
            f"<div style='font-size: 0.85em; color: #A0AABF; margin-bottom: 8px;'>KILL SWITCH</div>"
            f"<div style='font-size: 2em; color: {kill_color}; margin: 12px 0; font-weight: bold;'>{kill_status}</div>"
            f"<div style='font-size: 0.75em; color: #A0AABF;'>"
            f"{'⚠️  TRADING DISABLED' if kill_switch_on else '✓ TRADING ENABLED'}"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    # Latest Decision Approval Status
    with approval_col:
        if latest_review:
            status_badge = "✅ APPROVED" if is_approved else "❌ REJECTED"
            status_color = "#00FF41" if is_approved else "#FF006E"
            decision = latest_review.get("risk_review", {}).get("decision", "N/A")
            
            st.markdown(
                f"<div class='command-card'>"
                f"<div style='font-size: 0.85em; color: #A0AABF; margin-bottom: 8px;'>LATEST DECISION</div>"
                f"<div style='font-size: 1.5em; color: #00D9FF; margin: 8px 0;'>{decision}</div>"
                f"<div style='font-size: 1.2em; color: {status_color}; font-weight: bold;'>{status_badge}</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div class='command-card'>"
                f"<div style='font-size: 0.85em; color: #A0AABF; margin-bottom: 8px;'>LATEST DECISION</div>"
                f"<div style='font-size: 0.95em; color: #A0AABF;'>No decisions yet</div>"
                f"</div>",
                unsafe_allow_html=True
            )
    
    # Trade Count
    with trades_col:
        st.markdown(
            f"<div class='command-card'>"
            f"<div style='font-size: 0.85em; color: #A0AABF; margin-bottom: 8px;'>TRADES TODAY</div>"
            f"<div style='font-size: 2em; color: #00D9FF; margin: 8px 0;'>{trades_today} / {max_trades}</div>"
            f"<div style='font-size: 0.75em; color: #A0AABF;'>Approved trades</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    # Rejection Reason (if applicable)
    if not is_approved and rejection_reason:
        st.markdown("### ❌ Rejection Reason")
        st.markdown(
            f"<div class='command-card'>"
            f"<div style='font-size: 1.1em; color: #FF006E;'>{rejection_reason}</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    # Latest Decision Details
    if latest_decision:
        decision_data = latest_decision.get("decision", {})
        symbol = decision_data.get("symbol", "N/A")
        decision = decision_data.get("decision", "N/A")
        confidence = decision_data.get("confidence", 0)
        reason = decision_data.get("reason", "N/A")
        risk_notes = decision_data.get("risk_notes", "N/A")
        
        st.markdown("### 🎯 Decision Details")
        
        detail_col1, detail_col2 = st.columns(2)
        
        with detail_col1:
            st.markdown(
                f"<div class='command-card'>"
                f"<div style='margin: 12px 0;'><strong>Symbol:</strong> <span style='color: #00D9FF;'>{symbol}</span></div>"
                f"<div style='margin: 12px 0;'><strong>Decision:</strong> <span style='color: #FFB700;'>{decision}</span></div>"
                f"<div style='margin: 12px 0;'><strong>Confidence:</strong> <span style='color: #00FF41;'>{confidence:.0%}</span></div>"
                f"</div>",
                unsafe_allow_html=True
            )
        
        with detail_col2:
            st.markdown(
                f"<div class='command-card'>"
                f"<div style='margin: 12px 0;'><strong>📋 Reasoning:</strong></div>"
                f"<div style='color: #A0AABF; font-size: 0.95em;'>{reason}</div>"
                f"</div>",
                unsafe_allow_html=True
            )


def render_risk_review_table():
    """Render the recent risk reviews table."""
    st.markdown("### 📊 RECENT RISK REVIEWS")
    
    df = format_risk_reviews_for_table(limit=20)
    
    if df.empty:
        st.info("📋 No risk reviews yet. Decisions will appear here once they're evaluated.")
    else:
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Time": st.column_config.TextColumn(width="medium"),
                "Symbol": st.column_config.TextColumn(width="small"),
                "Decision": st.column_config.TextColumn(width="small"),
                "Status": st.column_config.TextColumn(width="small"),
                "Reason": st.column_config.TextColumn(width="large"),
            }
        )
        
        total_reviews = len(load_risk_reviews(limit=10000))
        st.caption(f"Showing latest 20 reviews • Total recorded: {total_reviews}")


def main():
    # Header Section
    st.markdown("# ⚡ HELIX TRADING COMMAND CENTER")
    st.markdown(
        "<small style='color: #A0AABF;'>Real-time AI-powered market decision engine • Phase 4: Risk Engine Active</small>",
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    
    # System Health
    render_system_health()
    st.markdown("---")
    
    # Risk Engine Status
    render_risk_engine_status()
    st.markdown("---")
    
    # Risk Review Table
    render_risk_review_table()
    
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #A0AABF; font-size: 0.85em; margin-top: 20px;'>"
        "🤖 HELIX v1.0 • Autonomous Trading System • Phase 4: Risk Engine Approval/Rejection"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
