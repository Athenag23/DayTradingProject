from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from app.config import APCA_API_KEY_ID, APCA_API_SECRET_KEY
from app.indicators import calculate_ema, calculate_rsi, classify_trend


client = StockHistoricalDataClient(APCA_API_KEY_ID, APCA_API_SECRET_KEY)


def get_market_snapshot(symbol: str):
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Minute,
        limit=100
    )

    bars = client.get_stock_bars(request)

    df = bars.df

    if df.empty:
        raise ValueError(f"No historical bars returned for {symbol}")

    if "symbol" in df.index.names:
        df = df.xs(symbol, level="symbol")

    df = df.sort_index()

    close = df["close"]
    volume = df["volume"]

    ema_9_series = calculate_ema(close, 9)
    ema_20_series = calculate_ema(close, 20)
    rsi_series = calculate_rsi(close, 14)

    latest_price = float(close.iloc[-1])
    latest_volume = float(volume.iloc[-1])
    latest_ema_9 = float(ema_9_series.iloc[-1])
    latest_ema_20 = float(ema_20_series.iloc[-1])
    latest_rsi = float(rsi_series.iloc[-1])

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
        "ema_9": round(latest_ema_9, 2),
        "ema_20": round(latest_ema_20, 2),
        "trend": trend,
        "news": "none"
    }