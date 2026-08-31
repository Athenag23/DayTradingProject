import math

import pandas as pd


def calculate_ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / period,
        min_periods=period,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        min_periods=period,
        adjust=False
    ).mean()

    flat_market = (avg_gain.fillna(0) == 0) & (avg_loss.fillna(0) == 0)
    rs = pd.Series(0.0, index=avg_gain.index, dtype=float)

    valid_loss = avg_loss != 0
    rs[valid_loss] = avg_gain[valid_loss] / avg_loss[valid_loss]

    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.mask(flat_market, 50.0)
    rsi = rsi.mask((avg_loss.fillna(0) == 0) & (avg_gain.fillna(0) > 0), 100.0)
    rsi = rsi.mask((avg_gain.fillna(0) == 0) & (avg_loss.fillna(0) > 0), 0.0)

    return rsi


def classify_rsi(rsi: float) -> str:
    if rsi < 30:
        return "OVERSOLD"

    if rsi > 70:
        return "OVERBOUGHT"

    return "NEUTRAL"


def classify_ema_alignment(ema_9: float, ema_20: float) -> str:
    if ema_9 > ema_20:
        return "BULLISH"

    if ema_9 < ema_20:
        return "BEARISH"

    return "NEUTRAL"


def calculate_ema_spread_percent(
    ema_9: float,
    ema_20: float
) -> float:
    if ema_20 == 0:
        return 0.0

    spread = ((ema_9 - ema_20) / ema_20) * 100

    return spread


def classify_ema_strength(
    ema_9: float,
    ema_20: float,
    weak_threshold_percent: float = 0.05
) -> str:
    spread_percent = abs(
        calculate_ema_spread_percent(
            ema_9=ema_9,
            ema_20=ema_20
        )
    )

    if spread_percent < weak_threshold_percent:
        return "WEAK"

    return "STRONG"


def classify_trend(
    ema_9: float,
    ema_20: float,
    price: float
) -> str:
    if price > ema_9 > ema_20:
        return "BULLISH"

    if price < ema_9 < ema_20:
        return "BEARISH"

    return "NEUTRAL"


def calculate_session_vwap(bars: pd.DataFrame) -> pd.Series:
    """Return the cumulative VWAP for the trading session represented in bars."""
    if bars.empty:
        return pd.Series(dtype=float, index=bars.index)

    session_bars = bars.sort_index().copy()
    if session_bars.index.empty:
        return pd.Series(dtype=float, index=session_bars.index)

    typical_price = (session_bars["high"] + session_bars["low"] + session_bars["close"]) / 3.0
    cumulative_volume = session_bars["volume"].cumsum()
    cumulative_tp_volume = (typical_price * session_bars["volume"]).cumsum()

    vwap = cumulative_tp_volume / cumulative_volume.replace(0, pd.NA)
    return vwap.fillna(0.0)


def classify_price_above_vwap(price: float, vwap: float) -> bool:
    """Return True when current price is above session VWAP, handling equality deterministically."""
    if math.isclose(price, vwap, rel_tol=1e-9, abs_tol=1e-8):
        return False

    return price > vwap