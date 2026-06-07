import streamlit as st
import sys
import json
import os
from datetime import datetime
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.health_check import check_ollama, check_alpaca_config
from app.dashboard_utils import (
    get_decision_status_metrics,
    format_risk_reviews_for_table,
    load_decisions,
    load_risk_reviews
)
from app.risk_config import COOLDOWN_SECONDS, MAX_TRADES_PER_DAY, KILL_SWITCH

try:
    import plotly.graph_objects as go
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


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
    
    h2 {
        margin-top: 32px;
        margin-bottom: 16px;
        font-size: 1.6em;
        border-bottom: 1px solid rgba(0, 217, 255, 0.2);
        padding-bottom: 12px;
    }
    
    hr {
        border: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0, 217, 255, 0.3), transparent);
        margin: 24px 0;
    }
    
    [data-testid="stDataFrame"] {
        background-color: var(--bg-card) !important;
    }
    
    .cooldown-card {
        background: linear-gradient(135deg, rgba(255, 183, 0, 0.2), rgba(255, 183, 0, 0.1));
        border: 1px solid rgba(255, 183, 0, 0.4);
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
    }
    
    .section-card {
        background-color: var(--bg-card);
        border: 1px solid rgba(0, 217, 255, 0.2);
        border-radius: 12px;
        padding: 20px;
        margin: 16px 0;
    }
    
    .info-box {
        background: linear-gradient(135deg, rgba(0, 217, 255, 0.1), rgba(0, 217, 255, 0.05));
        border-left: 4px solid rgba(0, 217, 255, 0.5);
        border-radius: 8px;
        padding: 16px;
        margin: 12px 0;
    }
</style>
"""

st.set_page_config(
    page_title="HELIX Command Center",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def load_jsonl(path: str) -> list:
    """Load JSONL file safely, skipping malformed rows."""
    rows = []
    if not os.path.exists(path):
        return rows
    
    try:
        with open(path, "r") as f:
            for line in f:
                if line.strip():
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except IOError:
        pass
    
    return rows


def get_log_file_health() -> dict:
    """Get health status of all log files."""
    log_files = {
        "decisions.jsonl": "logs/decisions.jsonl",
        "risk_reviews.jsonl": "logs/risk_reviews.jsonl",
        "orders.jsonl": "logs/orders.jsonl",
        "transactions.jsonl": "logs/transactions.jsonl",
        "errors.jsonl": "logs/errors.jsonl",
    }
    
    health = {}
    for name, path in log_files.items():
        exists = os.path.exists(path)
        row_count = len(load_jsonl(path)) if exists else 0
        last_modified = None
        
        if exists:
            try:
                last_modified = datetime.fromtimestamp(os.path.getmtime(path)).isoformat()
            except:
                pass
        
        health[name] = {
            "exists": exists,
            "row_count": row_count,
            "last_modified": last_modified
        }
    
    return health


def normalize_risk_reviews(rows: list) -> list:
    """Normalize risk review rows to flat structure."""
    normalized = []
    for row in rows:
        if "risk_review" in row:
            normalized.append({
                "timestamp": row.get("timestamp"),
                **row.get("risk_review", {})
            })
        else:
            normalized.append(row)
    return normalized


def normalize_decisions(rows: list) -> list:
    """Normalize decision rows to flat structure."""
    normalized = []
    for row in rows:
        if "decision" in row:
            normalized.append({
                "timestamp": row.get("timestamp"),
                **row.get("decision", {})
            })
        else:
            normalized.append(row)
    return normalized


def render_kpi_cards():
    """Render top-level KPI metrics."""
    st.markdown("### 📊 KEY PERFORMANCE INDICATORS")
    
    decisions = normalize_decisions(load_jsonl("logs/decisions.jsonl"))
    risk_reviews = normalize_risk_reviews(load_jsonl("logs/risk_reviews.jsonl"))
    
    total_decisions = len(decisions)
    approved_count = len([r for r in risk_reviews if r.get("approved")])
    rejected_count = len([r for r in risk_reviews if not r.get("approved")])
    approval_rate = (approved_count / (approved_count + rejected_count) * 100) if (approved_count + rejected_count) > 0 else 0
    
    today = datetime.now().date()
    trades_today = len([d for d in decisions if d.get("timestamp") and datetime.fromisoformat(d.get("timestamp")).date() == today])
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Total Decisions", total_decisions, delta=None)
    
    with col2:
        st.metric("Approved ✅", approved_count, delta=None)
    
    with col3:
        st.metric("Rejected ❌", rejected_count, delta=None)
    
    with col4:
        st.metric("Approval Rate", f"{approval_rate:.1f}%", delta=None)
    
    with col5:
        st.metric("Trades Today", f"{trades_today} / {MAX_TRADES_PER_DAY}", delta=None)
    
    with col6:
        kill_status = "🔴 ON" if KILL_SWITCH else "🟢 OFF"
        st.metric("Kill Switch", kill_status, delta=None)


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
        decision_count = len(normalize_decisions(load_jsonl("logs/decisions.jsonl")))
        st.markdown(
            f"<div class='command-card'>"
            f"<div style='font-size: 0.85em; color: #A0AABF; margin-bottom: 8px;'>DECISIONS</div>"
            f"<div style='font-size: 1.4em; color: #00D9FF;'>{decision_count}</div>"
            f"<div style='font-size: 0.8em; color: #A0AABF; margin-top: 8px;'>📊 Total logged</div>"
            f"</div>",
            unsafe_allow_html=True
        )


def render_risk_engine_status():
    """Render risk engine status section with Phase 4.1 features."""
    st.markdown("### ⚖️  RISK ENGINE STATUS")
    
    metrics = get_decision_status_metrics()
    latest_decision = metrics["latest_decision"]
    latest_review = metrics["latest_review"]
    is_approved = metrics["approved"]
    rejection_reason = metrics["rejection_reason"]
    kill_switch_on = metrics["kill_switch"]
    trades_today = metrics["trades_today"]
    max_trades = metrics["max_trades"]
    
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
    
    with trades_col:
        st.markdown(
            f"<div class='command-card'>"
            f"<div style='font-size: 0.85em; color: #A0AABF; margin-bottom: 8px;'>TRADES TODAY</div>"
            f"<div style='font-size: 2em; color: #00D9FF; margin: 8px 0;'>{trades_today} / {max_trades}</div>"
            f"<div style='font-size: 0.75em; color: #A0AABF;'>Approved trades</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    st.markdown("### ⏳ PHASE 4.1 FEATURES")
    cooldown_col1, cooldown_col2 = st.columns(2)
    
    with cooldown_col1:
        st.markdown(
            f"<div class='cooldown-card'>"
            f"<div style='font-size: 0.85em; color: #FFB700; margin-bottom: 8px;'>⏳ Cooldown Timer</div>"
            f"<div style='font-size: 1.2em; color: #FFFFFF;'>{COOLDOWN_SECONDS}s between same-symbol trades</div>"
            f"<div style='font-size: 0.75em; color: #A0AABF; margin-top: 8px;'>Prevents rapid re-trading</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    with cooldown_col2:
        st.markdown(
            f"<div class='cooldown-card'>"
            f"<div style='font-size: 0.85em; color: #FFB700; margin-bottom: 8px;'>🔁 Duplicate Prevention</div>"
            f"<div style='font-size: 1.2em; color: #FFFFFF;'>Active</div>"
            f"<div style='font-size: 0.75em; color: #A0AABF; margin-top: 8px;'>Blocks consecutive same-action trades</div>"
            f"</div>",
            unsafe_allow_html=True
        )


def render_charts():
    """Render analytics charts."""
    st.markdown("### 📈 ANALYTICS")
    
    decisions = normalize_decisions(load_jsonl("logs/decisions.jsonl"))
    risk_reviews = normalize_risk_reviews(load_jsonl("logs/risk_reviews.jsonl"))
    
    if not risk_reviews or not decisions:
        st.info("📋 Not enough data to display charts yet.")
        return
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        approved_count = len([r for r in risk_reviews if r.get("approved")])
        rejected_count = len([r for r in risk_reviews if not r.get("approved")])
        
        if HAS_PLOTLY:
            fig = go.Figure(data=[
                go.Bar(x=["Approved", "Rejected"], y=[approved_count, rejected_count],
                       marker=dict(color=["#00FF41", "#FF006E"]))
            ])
            fig.update_layout(
                title="Approval vs Rejection",
                xaxis_title="Status",
                yaxis_title="Count",
                template="plotly_dark",
                showlegend=False,
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart({"Approved": [approved_count], "Rejected": [rejected_count]})
    
    with chart_col2:
        symbols = [d.get("symbol") for d in decisions if d.get("symbol")]
        symbol_counts = Counter(symbols)
        
        if symbol_counts and HAS_PLOTLY:
            fig = go.Figure(data=[
                go.Bar(x=list(symbol_counts.keys()), y=list(symbol_counts.values()),
                       marker=dict(color="#00D9FF"))
            ])
            fig.update_layout(
                title="Decisions by Symbol",
                xaxis_title="Symbol",
                yaxis_title="Count",
                template="plotly_dark",
                showlegend=False,
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            if symbol_counts:
                st.bar_chart(dict(symbol_counts))
            else:
                st.info("No symbol data available.")
    
    chart_col3, chart_col4 = st.columns(2)
    
    with chart_col3:
        rejection_reasons = [r.get("reason", "Unknown") for r in risk_reviews if not r.get("approved")]
        reason_counts = Counter(rejection_reasons)
        
        if reason_counts and HAS_PLOTLY:
            fig = go.Figure(data=[
                go.Bar(x=list(reason_counts.values()), y=list(reason_counts.keys()), orientation='h',
                       marker=dict(color="#FFB700"))
            ])
            fig.update_layout(
                title="Top Rejection Reasons",
                xaxis_title="Count",
                template="plotly_dark",
                showlegend=False,
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No rejection data available.")
    
    with chart_col4:
        decision_types = [d.get("decision") for d in decisions if d.get("decision")]
        decision_counts = Counter(decision_types)
        
        if decision_counts and HAS_PLOTLY:
            fig = go.Figure(data=[
                go.Pie(labels=list(decision_counts.keys()), values=list(decision_counts.values()),
                       marker=dict(colors=["#00FF41", "#FF006E", "#FFB700", "#00D9FF"]))
            ])
            fig.update_layout(
                title="Decision Type Breakdown",
                template="plotly_dark",
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No decision type data available.")


def render_risk_review_table():
    """Render recent risk reviews table."""
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
        
        total_reviews = len(load_jsonl("logs/risk_reviews.jsonl"))
        st.caption(f"Showing latest 20 reviews • Total recorded: {total_reviews}")


def render_decisions_table():
    """Render recent AI decisions table."""
    st.markdown("### 🤖 RECENT AI DECISIONS")
    
    decisions = normalize_decisions(load_jsonl("logs/decisions.jsonl"))
    decisions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    decisions = decisions[:20]
    
    if not decisions:
        st.info("📋 No AI decisions yet.")
    else:
        if HAS_PANDAS:
            df = pd.DataFrame(decisions)
            cols_to_show = ["timestamp", "symbol", "decision", "confidence", "reason", "risk_notes"]
            cols_available = [c for c in cols_to_show if c in df.columns]
            df = df[cols_available]
            
            if "confidence" in df.columns:
                df["confidence"] = df["confidence"].apply(lambda x: f"{x:.0%}" if x else "N/A")
            
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "timestamp": st.column_config.TextColumn("Time", width="medium"),
                    "symbol": st.column_config.TextColumn("Symbol", width="small"),
                    "decision": st.column_config.TextColumn("Decision", width="small"),
                    "confidence": st.column_config.TextColumn("Confidence", width="small"),
                    "reason": st.column_config.TextColumn("Reason", width="large"),
                    "risk_notes": st.column_config.TextColumn("Risk Notes", width="large"),
                }
            )
        else:
            st.write(decisions[:10])
        
        st.caption(f"Showing latest 20 decisions • Total recorded: {len(load_jsonl('logs/decisions.jsonl'))}")


def render_sidebar():
    """Render sidebar with controls and health status."""
    st.sidebar.markdown("## 🛠️ CONTROLS")
    
    if st.sidebar.button("🔄 Refresh Dashboard"):
        st.rerun()
    
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("## 📁 LOG FILE HEALTH")
    health = get_log_file_health()
    
    for name, status in health.items():
        if status["exists"]:
            emoji = "✅"
            status_text = f"{status['row_count']} rows"
            if status['last_modified']:
                status_text += f" • Updated {status['last_modified'][:10]}"
        else:
            emoji = "⚠️"
            status_text = "File missing"
        
        st.sidebar.markdown(f"{emoji} **{name}**")
        st.sidebar.caption(status_text)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ INFO")
    st.sidebar.caption(f"🔄 Phase: **4.1** — Risk Hardening")
    st.sidebar.caption(f"⏳ Cooldown: **{COOLDOWN_SECONDS}s**")
    st.sidebar.caption(f"📊 Max Trades: **{MAX_TRADES_PER_DAY}** per day")
    st.sidebar.caption(f"🔴 Kill Switch: **{'ON' if KILL_SWITCH else 'OFF'}**")


def main():
    st.markdown("# ⚡ HELIX TRADING COMMAND CENTER")
    st.markdown(
        "<small style='color: #A0AABF;'>"
        "Autonomous Trading System — Risk-Controlled Development Mode<br>"
        f"Phase 4.1 Risk Hardening • {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        "</small>",
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    
    render_kpi_cards()
    st.markdown("---")
    
    render_system_health()
    st.markdown("---")
    
    render_risk_engine_status()
    st.markdown("---")
    
    render_charts()
    st.markdown("---")
    
    render_risk_review_table()
    st.markdown("---")
    
    render_decisions_table()
    st.markdown("---")
    
    st.markdown(
        "<div style='text-align: center; color: #A0AABF; font-size: 0.85em; margin-top: 20px;'>"
        "🤖 HELIX v1.0 • Autonomous Trading System • Phase 4.1: Risk Engine + Cooldown + Duplicate Prevention"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    render_sidebar()
    main()