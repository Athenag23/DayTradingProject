from datetime import datetime, timedelta, timezone

import pandas as pd
from alpaca.common.enums import Sort
from alpaca.data.enums import DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from app.config import APCA_API_KEY_ID, APCA_API_SECRET_KEY
from app.indicators import (
    calculate_ema,
    calculate_ema_spread_percent,
    calculate_rsi,
    calculate_session_vwap,
    classify_ema_alignment,
    classify_ema_strength,
    classify_price_above_vwap,
    classify_rsi,
    classify_trend,
)


client = StockHistoricalDataClient(
    APCA_API_KEY_ID,
    APCA_API_SECRET_KEY
)


def _latest_trading_session(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    if not isinstance(df.index, pd.DatetimeIndex):
        df = df.copy()
        df.index = pd.to_datetime(df.index)

    session_dates = pd.DatetimeIndex(df.index).normalize().unique()
    if len(session_dates) == 0:
        return df.copy()

    latest_session_date = session_dates[-1]
    latest_session = df.loc[df.index.normalize() == latest_session_date].copy()

    if latest_session.empty and not df.empty:
        return df.iloc[-1:].copy()

    return latest_session.sort_index()


def build_market_snapshot(df: pd.DataFrame, symbol: str) -> dict:
    if df.empty:
        raise ValueError(f"No historical bars provided for {symbol}")

    snapshot_df = df.copy()
    if "symbol" in snapshot_df.index.names:
        snapshot_df = snapshot_df.xs(symbol, level="symbol")

    if not isinstance(snapshot_df.index, pd.DatetimeIndex):
        snapshot_df.index = pd.to_datetime(snapshot_df.index)

    snapshot_df = snapshot_df.sort_index()
    latest_session_df = _latest_trading_session(snapshot_df)

    required_columns = {"open", "high", "low", "close", "volume"}
    missing = sorted(required_columns - set(snapshot_df.columns))
    if missing:
        raise ValueError(f"Missing required price columns for {symbol}: {missing}")

    close = snapshot_df["close"]
    volume = snapshot_df["volume"]

    ema_9_series = calculate_ema(close, 9)
    ema_20_series = calculate_ema(close, 20)
    rsi_series = calculate_rsi(close, 14)
    vwap_series = calculate_session_vwap(latest_session_df)

    latest_price = float(snapshot_df["close"].iloc[-1])
    latest_volume = float(snapshot_df["volume"].iloc[-1])
    latest_ema_9 = float(ema_9_series.iloc[-1])
    latest_ema_20 = float(ema_20_series.iloc[-1])
    latest_rsi = float(rsi_series.iloc[-1])
    latest_vwap = float(vwap_series.iloc[-1]) if not vwap_series.empty else latest_price
    price_above_vwap = classify_price_above_vwap(latest_price, latest_vwap)

    latest_timestamp = snapshot_df.index[-1]
    if hasattr(latest_timestamp, "isoformat"):
        market_timestamp = latest_timestamp.isoformat()
    else:
        market_timestamp = str(latest_timestamp)

    rsi_state = classify_rsi(latest_rsi)
    ema_alignment = classify_ema_alignment(
        ema_9=latest_ema_9,
        ema_20=latest_ema_20,
    )
    ema_strength = classify_ema_strength(
        ema_9=latest_ema_9,
        ema_20=latest_ema_20,
    )
    ema_spread_percent = calculate_ema_spread_percent(
        ema_9=latest_ema_9,
        ema_20=latest_ema_20,
    )
    trend = classify_trend(
        ema_9=latest_ema_9,
        ema_20=latest_ema_20,
        price=latest_price,
    )

    return {
        "symbol": symbol,
        "price": round(latest_price, 2),
        "volume": int(latest_volume),

        "rsi": round(latest_rsi, 2),
        "rsi_state": rsi_state,

        "ema_9": round(latest_ema_9, 2),
        "ema_20": round(latest_ema_20, 2),
        "ema_alignment": ema_alignment,
        "ema_strength": ema_strength,
        "ema_spread_percent": round(ema_spread_percent, 4),

        "trend": trend,
        "vwap": round(latest_vwap, 4),
        "price_above_vwap": bool(price_above_vwap),

        "news": "none",
        "market_timestamp": market_timestamp,
    }


def get_market_snapshot(symbol: str):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=7)

    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Minute,
        start=start,
        end=end,
        limit=100,
        feed=DataFeed.IEX,
        sort=Sort.DESC
    )

    bars = client.get_stock_bars(request)
    df = bars.df

    if df.empty:
        raise ValueError(
            f"No historical bars returned for {symbol} "
            f"between {start.isoformat()} and {end.isoformat()}"
        )

    return build_market_snapshot(df, symbol)