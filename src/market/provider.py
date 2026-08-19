import os
from typing import List, Dict, Any
import requests

class MarketDataError(Exception):
    pass

class MarketDataProvider:
    def ping(self) -> bool:
        raise NotImplementedError

    def get_current_price(self, symbol: str) -> float:
        raise NotImplementedError

    def get_24h_stats(self, symbol: str) -> Dict[str, Any]:
        raise NotImplementedError

    def get_candles(self, symbol: str, interval: str = '1h', limit: int = 50) -> List[Dict[str, Any]]:
        raise NotImplementedError

class BinanceProvider(MarketDataProvider):
    BASE = "https://api.binance.com"

    def __init__(self, api_key: str = None):
        # Public endpoints do not require an API key for market data
        self.api_key = api_key or os.environ.get('MARKET_DATA_API_KEY')

    def ping(self) -> bool:
        try:
            r = requests.get(self.BASE + "/api/v3/ping", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def get_current_price(self, symbol: str) -> float:
        url = f"{self.BASE}/api/v3/ticker/price"
        params = {"symbol": symbol}
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            raise MarketDataError(f"Failed to fetch current price: {r.status_code}")
        data = r.json()
        if "price" not in data:
            raise MarketDataError("Malformed price response")
        try:
            return float(data["price"])
        except Exception as e:
            raise MarketDataError("Malformed price value") from e

    def get_24h_stats(self, symbol: str) -> Dict[str, Any]:
        url = f"{self.BASE}/api/v3/ticker/24hr"
        params = {"symbol": symbol}
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            raise MarketDataError(f"Failed to fetch 24h stats: {r.status_code}")
        data = r.json()
        # expected keys: lastPrice, priceChangePercent, volume
        try:
            return {
                "lastPrice": float(data.get("lastPrice", 0)),
                "priceChangePercent": float(data.get("priceChangePercent", 0)),
                "volume": float(data.get("volume", 0)),
            }
        except Exception as e:
            raise MarketDataError("Malformed 24h stats") from e

    def get_candles(self, symbol: str, interval: str = '1h', limit: int = 50) -> List[Dict[str, Any]]:
        url = f"{self.BASE}/api/v3/klines"
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            raise MarketDataError(f"Failed to fetch klines: {r.status_code}")
        data = r.json()
        # each kline: [openTime, open, high, low, close, volume, closeTime, ...]
        candles = []
        try:
            for k in data:
                candles.append({
                    "open_time": int(k[0]),
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5]),
                    "close_time": int(k[6])
                })
        except Exception as e:
            raise MarketDataError("Malformed candle data") from e
        return candles


def build_market_summary(symbol: str, provider: MarketDataProvider, timeframe: str = '1h') -> str:
    """Fetch market data and return a short text summary."""
    supported = {"BTCUSDT", "ETHUSDT"}
    sym = symbol.upper()
    if sym not in supported:
        raise MarketDataError(f"Symbol not supported: {symbol}")

    # gather data
    price = provider.get_current_price(sym)
    stats = provider.get_24h_stats(sym)
    candles = provider.get_candles(sym, interval=timeframe, limit=10)

    lines = [f"{sym} MARKET SUMMARY"]
    lines.append("")
    lines.append(f"Price: {price}")
    lines.append(f"24h change (%): {stats.get('priceChangePercent')}")
    lines.append(f"24h volume: {stats.get('volume')}")
    lines.append("")
    lines.append("Recent candles (last 5):")
    for c in candles[-5:]:
        lines.append(f"{c['open_time']}: O={c['open']} H={c['high']} L={c['low']} C={c['close']} V={c['volume']}")

    return "\n".join(lines)
