import streamlit as st
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.health_check import check_ollama, check_alpaca_config


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
    
    /* Status indicators */
    .status-online {
        color: var(--success);
        text-shadow: 0 0 10px var(--success);
        font-weight: bold;
    }
    
    .status-offline {
        color: var(--danger);
        text-shadow: 0 0 10px var(--danger);
        font-weight: bold;
    }
    
    .decision-online {
        color: var(--success);
        text-shadow: 0 0 15px var(--success);
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
    
    /* Decision status colors */
    .decision-buy {
        color: var(--success);
        font-weight: bold;
    }
    
    .decision-sell {
        color: var(--danger);
        font-weight: bold;
    }
    
    .decision-hold {
        color: var(--warning);
        font-weight: bold;
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


def load_decisions():
    """Load all decisions from JSONL file."""
    decisions_file = Path(__file__).parent.parent / "logs" / "decisions.jsonl"
    
    if not decisions_file.exists():
        return []
    
    decisions = []
    try:
        with open(decisions_file, "r") as f:
            for line in f:
                if line.strip():
                    decisions.append(json.loads(line))
    except Exception as e:
        st.error(f"Error reading decisions log: {e}")
        return []
    
    return decisions


def get_latest_decision(decisions):
    """Get the most recent decision."""
    if not decisions:
        return None
    return decisions[-1]


def format_decision_data(decisions):
    """Format decisions for table display."""
    if not decisions:
        return pd.DataFrame()
    
    data = []
    for entry in decisions[-20:]:  # Show last 20 decisions
        decision = entry.get("decision", {})
        data.append({
            "Timestamp": entry.get("timestamp", "N/A"),
            "Symbol": decision.get("symbol", "N/A"),
            "Decision": decision.get("decision", "N/A"),
            "Confidence": f"{decision.get('confidence', 0):.0%}",
            "Reason": decision.get("reason", "N/A"),
        })
    
    return pd.DataFrame(data)


def render_metric_card(label, value, delta, icon):
    """Render a custom metric card."""
    st.metric(label, value, delta=delta)


def main():
    # Header Section
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("# ⚡ HELIX TRADING COMMAND CENTER")
        st.markdown(
            "<small style='color: #A0AABF;'>Real-time AI-powered market decision engine</small>",
            unsafe_allow_html=True
        )
    
    st.markdown("---")
    
    # System Health Status
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
    
    # Load decisions
    decisions = load_decisions()
    
    if not decisions:
        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; padding: 40px; color: #A0AABF;'>"
            "<h3>⏳ AWAITING FIRST DECISION</h3>"
            "<p>The autonomous agent will record its first trading decision here.</p>"
            "</div>",
            unsafe_allow_html=True
        )
        return
    
    st.markdown("---")
    
    # Latest Decision Panel
    latest = get_latest_decision(decisions)
    if latest:
        decision_data = latest.get("decision", {})
        symbol = decision_data.get("symbol", "N/A")
        decision = decision_data.get("decision", "N/A")
        confidence = decision_data.get("confidence", 0)
        reason = decision_data.get("reason", "N/A")
        risk_notes = decision_data.get("risk_notes", "N/A")
        timestamp = latest.get("timestamp", "N/A")
        
        # Determine decision color and emoji
        decision_colors = {
            "BUY": ("🟢 BUY", "#00FF41"),
            "SELL": ("🔴 SELL", "#FF006E"),
            "HOLD": ("🟡 HOLD", "#FFB700"),
            "NO_TRADE": ("⚪ NO_TRADE", "#A0AABF"),
        }
        decision_display, decision_color = decision_colors.get(decision, ("❓ UNKNOWN", "#A0AABF"))
        
        st.markdown("### 🎯 LATEST AI DECISION")
        
        # Decision metrics row
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        with metric_col1:
            st.markdown(
                f"<div class='command-card' style='text-align: center;'>"
                f"<div style='font-size: 0.85em; color: #A0AABF;'>SYMBOL</div>"
                f"<div style='font-size: 2em; color: #00D9FF; margin: 8px 0;'>{symbol}</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        
        with metric_col2:
            st.markdown(
                f"<div class='command-card' style='text-align: center;'>"
                f"<div style='font-size: 0.85em; color: #A0AABF;'>DECISION</div>"
                f"<div style='font-size: 1.8em; color: {decision_color}; margin: 8px 0; font-weight: bold;'>{decision_display}</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        
        with metric_col3:
            confidence_pct = f"{confidence:.0%}"
            confidence_color = "#00FF41" if confidence >= 0.6 else "#FFB700" if confidence >= 0.4 else "#FF006E"
            st.markdown(
                f"<div class='command-card' style='text-align: center;'>"
                f"<div style='font-size: 0.85em; color: #A0AABF;'>CONFIDENCE</div>"
                f"<div style='font-size: 2em; color: {confidence_color}; margin: 8px 0;'>{confidence_pct}</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        
        with metric_col4:
            time_display = timestamp.split("T")[0] if "T" in timestamp else timestamp
            st.markdown(
                f"<div class='command-card' style='text-align: center;'>"
                f"<div style='font-size: 0.85em; color: #A0AABF;'>TIMESTAMP</div>"
                f"<div style='font-size: 1.3em; color: #00D9FF; margin: 8px 0; word-break: break-all;'>{time_display}</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        
        # Decision details
        st.markdown("**📋 Analysis Details:**")
        st.markdown(
            f"<div class='command-card'>"
            f"<div style='margin: 12px 0;'><strong>Reasoning:</strong></div>"
            f"<div style='color: #A0AABF; font-size: 0.95em;'>{reason}</div>"
            f"</div>",
            unsafe_allow_html=True
        )
        
        st.markdown(
            f"<div class='command-card'>"
            f"<div style='margin: 12px 0;'><strong>⚠️ Risk Assessment:</strong></div>"
            f"<div style='color: #FFB700; font-size: 0.95em;'>{risk_notes}</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    st.markdown("---")
    
    # Decision History Table
    st.markdown("### 📊 DECISION HISTORY")
    df = format_decision_data(decisions)
    
    if not df.empty:
        df_display = df.iloc[::-1].reset_index(drop=True)
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Timestamp": st.column_config.TextColumn(width="medium"),
                "Symbol": st.column_config.TextColumn(width="small"),
                "Decision": st.column_config.TextColumn(width="small"),
                "Confidence": st.column_config.TextColumn(width="small"),
                "Reason": st.column_config.TextColumn(width="large"),
            }
        )
        
        st.markdown(
            f"<div style='text-align: center; color: #A0AABF; font-size: 0.9em; margin-top: 16px;'>"
            f"Displaying {len(df_display)} recent decisions • Total recorded: {len(decisions)}"
            f"</div>",
            unsafe_allow_html=True
        )


if __name__ == "__main__":
    main()
