import pandas as pd
import pandas_ta as ta


def ohlcv_to_df(ohlcv, cols=["timestamp","open","high","low","close","volume"]):
    df = pd.DataFrame(ohlcv, columns=cols) if len(ohlcv) and len(ohlcv[0])>=6 else pd.DataFrame(ohlcv)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
    return df


def compute_indicators(df, ema_periods=(8,21,50), rsi_period=14, macd_fast=12, macd_slow=26, macd_signal=9):
    res = {}
    for p in ema_periods:
        df[f"EMA_{p}"] = ta.ema(df['close'], length=p)
        res[f"EMA_{p}"] = df[f"EMA_{p}"].iloc[-1]
    df["RSI"] = ta.rsi(df['close'], length=rsi_period)
    res["RSI"] = df["RSI"].iloc[-1]
    macd = ta.macd(df['close'], fast=macd_fast, slow=macd_slow, signal=macd_signal)
    # pandas_ta returns columns like MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
    res["MACD"] = macd.get("MACD_12_26_9").iloc[-1] if "MACD_12_26_9" in macd else None
    res["MACD_signal"] = macd.get("MACDs_12_26_9").iloc[-1] if "MACDs_12_26_9" in macd else None
    res["volume"] = df['volume'].iloc[-1] if 'volume' in df.columns else None
    return res, df
