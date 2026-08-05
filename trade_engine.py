import os
from ccxt_connector import CCXTConnector
from analysis.technical import ohlcv_to_df, compute_indicators
from analysis.sentiment import fetch_news, analyze_texts
from analysis.ai_analysis import ai_summary
from utils.logger import logger
import math

class TradeEngine:
    def __init__(self, exchange_id=None):
        self.connector = CCXTConnector(exchange_id=exchange_id)
        self.max_order_pct = float(os.getenv("MAX_ORDER_PCT", 10.0))
        self.position_method = os.getenv("POSITION_SIZING_METHOD", "fixed")
        self.position_pct = float(os.getenv("POSITION_SIZE_PERCENT", 1.0))
        self.risk_pct = float(os.getenv("RISK_PERCENT", 1.0))
        self.dry_run = str(os.getenv("USE_TESTNET", "true")).lower() in ("1","true","yes")
    
    def recommend(self, symbol, timeframe="1h"):
        ohlcv = self.connector.fetch_ohlcv(symbol, timeframe=timeframe, limit=200)
        df = ohlcv_to_df(ohlcv)
        indic, df = compute_indicators(df)
        # sentiment
        import asyncio
        news = asyncio.run(fetch_news(symbol, pages=1))
        sent = analyze_texts(news)
        # basic rule-based recommendation
        confidence = 0.5
        side = "wait"
        # example rule: EMA crossover + RSI
        ema8 = indic.get("EMA_8")
        ema21 = indic.get("EMA_21")
        rsi = indic.get("RSI", 50)
        if ema8 and ema21:
            if ema8 > ema21 and rsi < 70:
                side = "buy"
                confidence += 0.2
            elif ema8 < ema21 and rsi > 30:
                side = "sell"
                confidence += 0.2
        # incorporate sentiment
        if sent.get("label") == "POSITIVE":
            confidence += 0.1
        elif sent.get("label") == "NEGATIVE":
            confidence -= 0.1
        confidence = max(0.0, min(1.0, confidence))
        # compute suggested SL/TP heuristics
        last_price = float(df['close'].iloc[-1])
        sl = last_price * 0.98 if side=="buy" else last_price * 1.02
        tp = last_price * 1.03 if side=="buy" else last_price * 0.97
        # position sizing
        balance = self._get_equity_value()
        if self.position_method == "fixed":
            qty_pct = self.position_pct / 100.0
            size_value = balance * qty_pct
        else:
            # risk-based: simplistic estimate
            risk_amount = balance * (self.risk_pct/100.0)
            # distance between price and sl
            distance = abs(last_price - sl)
            size_value = risk_amount / distance if distance>0 else risk_amount
        # limit by max
        if (size_value / balance) * 100 > self.max_order_pct:
            size_value = balance * (self.max_order_pct / 100.0)
        return {
            "symbol": symbol, "side": side, "confidence": confidence,
            "ema": indic, "rsi": indic.get("RSI"), "last_price": last_price,
            "suggested_sl": sl, "suggested_tp": tp, "suggested_size_value": size_value,
            "dry_run": self.dry_run
        }

    def _get_equity_value(self):
        try:
            bal = self.connector.fetch_balance()
            # try usable wallet: total USD/USDT balance fallback
            if "USDT" in bal.get("total", {}):
                return float(bal["total"]["USDT"])
            # fallback to sum of quote currencies
            total = 0.0
            for k, v in bal.get("total", {}).items():
                try:
                    total += float(v)
                except:
                    pass
            return max(total, 1000.0)  # fallback to a default not zero
        except Exception:
            return 1000.0

    def place_order(self, symbol, side, amount, order_type="market", price=None, owner_id=None, confirm_token=None):
        # confirm_token/owner_id checked at Telegram layer
        return self.connector.create_order(symbol, side, order_type, amount, price=price, dry_run=self.dry_run)
