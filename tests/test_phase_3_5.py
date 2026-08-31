import math

import pandas as pd
import pytest

from app.agent import validate_decision
from app.data_fetcher import build_market_snapshot
from app.indicators import (
    calculate_ema,
    calculate_rsi,
    calculate_session_vwap,
    classify_ema_alignment,
    classify_ema_strength,
    classify_price_above_vwap,
    classify_rsi,
    classify_trend,
)


def build_session_bars(session_date: str, price_start: float = 100.0):
    index = pd.date_range(f"{session_date} 09:30", periods=4, freq="min")
    closes = [price_start + offset for offset in (0, 1, 2, 3)]
    opens = [close - 0.5 for close in closes]
    highs = [close + 1.0 for close in closes]
    lows = [close - 1.0 for close in closes]
    volumes = [100, 200, 300, 400]

    return pd.DataFrame(
        {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
        },
        index=index,
    )


def test_calculate_ema():
    series = pd.Series([100.0, 101.0, 102.0, 103.0], dtype=float)
    ema = calculate_ema(series, 3)

    assert ema.iloc[-1] > 101.0
    assert math.isfinite(float(ema.iloc[-1]))


def test_calculate_rsi():
    series = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0], dtype=float)
    rsi = calculate_rsi(series, 14)

    assert 0 <= float(rsi.iloc[-1]) <= 100
    assert math.isfinite(float(rsi.iloc[-1]))


def test_flat_price_rsi_is_neutral():
    series = pd.Series([100.0] * 10, dtype=float)
    rsi = calculate_rsi(series, 14)

    assert float(rsi.iloc[-1]) == 50.0


def test_rsi_classification():
    assert classify_rsi(20.0) == "OVERSOLD"
    assert classify_rsi(75.0) == "OVERBOUGHT"
    assert classify_rsi(50.0) == "NEUTRAL"


def test_ema_alignment():
    assert classify_ema_alignment(101.0, 100.0) == "BULLISH"
    assert classify_ema_alignment(99.0, 100.0) == "BEARISH"
    assert classify_ema_alignment(100.0, 100.0) == "NEUTRAL"


def test_ema_strength():
    assert classify_ema_strength(105.0, 100.0) == "STRONG"
    assert classify_ema_strength(100.03, 100.0) == "WEAK"


def test_trend_classification():
    assert classify_trend(110.0, 105.0, 111.0) == "BULLISH"
    assert classify_trend(95.0, 101.0, 90.0) == "BEARISH"
    assert classify_trend(100.0, 100.0, 100.0) == "NEUTRAL"


def test_session_vwap_calculation():
    bars = pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0],
            "high": [101.0, 102.0, 103.0],
            "low": [99.0, 100.0, 101.0],
            "close": [100.5, 101.5, 102.5],
            "volume": [100, 200, 300],
        },
        index=pd.date_range("2026-08-28 09:30", periods=3, freq="min"),
    )

    vwap = calculate_session_vwap(bars)
    assert math.isclose(float(vwap.iloc[-1]), 101.5, rel_tol=1e-9, abs_tol=1e-9)


def test_session_vwap_resets_per_session():
    day_one = build_session_bars("2026-08-27", price_start=100.0)
    day_two = build_session_bars("2026-08-28", price_start=110.0)
    combined = pd.concat([day_one, day_two])

    snapshot = build_market_snapshot(combined, "AAPL")
    day_two_vwap = calculate_session_vwap(day_two)

    assert snapshot["vwap"] == pytest.approx(float(day_two_vwap.iloc[-1]), rel=1e-9)
    assert snapshot["market_timestamp"] == day_two.index[-1].isoformat()


def test_price_above_vwap_classification():
    assert classify_price_above_vwap(102.0, 100.0) is True
    assert classify_price_above_vwap(100.0, 100.0) is False
    assert classify_price_above_vwap(99.0, 100.0) is False


def test_invalid_ai_decision_is_rejected():
    invalid = {
        "symbol": "AAPL",
        "decision": "HOLD",
        "confidence": 0.8,
        "reason": "mixed signal",
        "risk_notes": "do not trade",
    }
    assert validate_decision(invalid) is False


def test_valid_ai_decisions_pass_validation():
    for decision in ["BUY", "SELL", "NO_TRADE"]:
        payload = {
            "symbol": "AAPL",
            "decision": decision,
            "confidence": 0.72,
            "reason": "valid signal",
            "risk_notes": "risk managed",
        }
        assert validate_decision(payload) is True


def test_market_snapshot_contains_required_phase_3_5_fields():
    session = build_session_bars("2026-08-28", price_start=100.0)
    snapshot = build_market_snapshot(session, "AAPL")

    required_fields = {
        "symbol",
        "price",
        "volume",
        "rsi",
        "rsi_state",
        "ema_9",
        "ema_20",
        "ema_alignment",
        "ema_strength",
        "ema_spread_percent",
        "trend",
        "vwap",
        "price_above_vwap",
        "news",
        "market_timestamp",
    }

    assert required_fields.issubset(snapshot.keys())
    assert snapshot["price_above_vwap"] in {True, False}
    assert snapshot["symbol"] == "AAPL"


def test_ema_and_rsi_span_full_bar_window_while_vwap_resets_to_latest_session():
    day_one = build_session_bars("2026-08-27", price_start=100.0)
    day_two = build_session_bars("2026-08-28", price_start=110.0)
    combined = pd.concat([day_one, day_two])

    snapshot = build_market_snapshot(combined, "AAPL")
    expected_close = combined["close"]
    expected_ema_9 = calculate_ema(expected_close, 9).iloc[-1]
    expected_ema_20 = calculate_ema(expected_close, 20).iloc[-1]
    expected_rsi = calculate_rsi(expected_close, 14).iloc[-1]
    expected_vwap = calculate_session_vwap(day_two).iloc[-1]

    assert snapshot["ema_9"] == pytest.approx(round(float(expected_ema_9), 2), rel=1e-9)
    assert snapshot["ema_20"] == pytest.approx(round(float(expected_ema_20), 2), rel=1e-9)
    assert snapshot["rsi"] == pytest.approx(round(float(expected_rsi), 2), rel=1e-9)
    assert snapshot["vwap"] == pytest.approx(float(expected_vwap), rel=1e-9)
    assert snapshot["market_timestamp"] == combined.index[-1].isoformat()
