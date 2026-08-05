"""
alerts.py

Alert manager for Fawad Trade AI Agent (TEST MODE safe defaults).

Features:
- Telegram price alerts (periodic)
- Balance update alerts (periodic)
- Market signal alerts using TradeEngine.recommend
- Configurable alert interval and thresholds via environment variables

Safety:
- Respects USE_TESTNET and LIVE_ENABLE settings; does not place orders.
- Sends Telegram alerts only to configured ALERT_CHAT_ID or BOT_OWNER_TELEGRAM_ID.
- Runs as a background thread or can be started/stopped programmatically.

Usage:
from alerts import start_alerts, stop_alerts
am = start_alerts()
# ... later
stop_alerts(am)
"""

import os
import time
import threading
from typing import Dict, List, Optional

from utils.logger import logger

# Local imports that may rely on project modules
try:
    from trade_engine import TradeEngine
except Exception:
    TradeEngine = None  # will handle gracefully

try:
    from telegram import Bot
except Exception:
    Bot = None


def _get_env(name: str, default=None):
    v = os.getenv(name)
    return v if v is not None else default


class AlertManager:
    def __init__(self,
                 symbols: Optional[List[str]] = None,
                 interval: int = None,
                 price_change_pct: float = None,
                 balance_change_pct: float = None,
                 signal_confidence_threshold: float = None,
                 alert_chat_id: Optional[int] = None):
        # Configuration from env
        self.interval = int(interval or _get_env("ALERT_INTERVAL", 60))
        self.symbols = symbols or (_get_env("ALERT_SYMBOLS", "BTC/USDT,ETH/USDT").split(",") if _get_env("ALERT_SYMBOLS") else ["BTC/USDT"]) 
        self.price_change_pct = float(price_change_pct or _get_env("ALERT_PRICE_CHANGE_PCT", 0.5))  # percent
        self.balance_change_pct = float(balance_change_pct or _get_env("ALERT_BALANCE_CHANGE_PCT", 5.0))  # percent
        self.signal_confidence_threshold = float(signal_confidence_threshold or _get_env("ALERT_SIGNAL_CONFIDENCE", 0.75))

        # Telegram settings
        self.telegram_token = _get_env("TELEGRAM_TOKEN", "")
        owner = _get_env("BOT_OWNER_TELEGRAM_ID", "0")
        self.alert_chat_id = int(alert_chat_id or _get_env("ALERT_CHAT_ID", owner or 0))

        # Test mode flags
        self.use_testnet = str(_get_env("USE_TESTNET", "true")).lower() in ("1","true","yes")
        self.live_enable = str(_get_env("LIVE_ENABLE", "false")).lower() in ("1","true","yes")

        # Internal state
        self._last_prices: Dict[str, float] = {}
        self._last_balance_total: Optional[float] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Initialize connectors if available
        if TradeEngine:
            try:
                self.engine = TradeEngine(exchange_id=_get_env("EXCHANGE_ID", None))
            except Exception as e:
                logger.warning("AlertManager: failed to initialize TradeEngine: %s", e)
                self.engine = None
        else:
            logger.warning("AlertManager: TradeEngine not available in import path.")
            self.engine = None

        # Telegram bot instance (optional)
        if Bot and self.telegram_token:
            try:
                self.bot = Bot(token=self.telegram_token)
            except Exception as e:
                logger.warning("AlertManager: failed to initialize Telegram Bot: %s", e)
                self.bot = None
        else:
            self.bot = None

    def start(self):
        if self._running:
            logger.info("AlertManager already running")
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("AlertManager started with interval=%s seconds", self.interval)

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("AlertManager stopped")

    def _run_loop(self):
        # Initialize baseline values
        try:
            self._update_baselines()
        except Exception as e:
            logger.debug("AlertManager: baseline update failed: %s", e)

        while self._running:
            try:
                self._check_price_alerts()
                self._check_balance_alert()
                self._check_market_signals()
            except Exception as e:
                logger.exception("AlertManager run loop error: %s", e)
            time.sleep(self.interval)

    def _update_baselines(self):
        # populate last prices and balance
        for sym in self.symbols:
            price = self._get_last_price(sym)
            if price is not None:
                self._last_prices[sym] = price
        bal = self._get_total_balance()
        if bal is not None:
            self._last_balance_total = bal

    def _get_last_price(self, symbol: str) -> Optional[float]:
        # Try multiple methods to get a price (prefer connector's ticker, fallback to ohlcv)
        if not self.engine:
            logger.debug("AlertManager: no engine to fetch price for %s", symbol)
            return None
        connector = getattr(self.engine, "connector", None)
        if not connector:
            logger.debug("AlertManager: engine has no connector for %s", symbol)
            return None
        # try fetch_ticker
        try:
            if hasattr(connector, 'fetch_ticker'):
                t = connector.fetch_ticker(symbol)
                if isinstance(t, dict) and t.get('last') is not None:
                    return float(t['last'])
        except Exception:
            logger.debug("AlertManager: fetch_ticker failed for %s", symbol)
        # fallback: fetch_ohlcv
        try:
            ohlcv = connector.fetch_ohlcv(symbol, timeframe='1h', limit=1)
            if ohlcv and len(ohlcv) > 0:
                last = float(ohlcv[-1][4])
                return last
        except Exception:
            logger.debug("AlertManager: fetch_ohlcv failed for %s", symbol)
        return None

    def _get_total_balance(self) -> Optional[float]:
        if not self.engine:
            logger.debug("AlertManager: no engine to fetch balance")
            return None
        try:
            bal = self.engine.connector.fetch_balance()
            total = 0.0
            # prefer USDT
            if isinstance(bal, dict):
                totals = bal.get('total', {})
                if isinstance(totals, dict) and 'USDT' in totals:
                    return float(totals['USDT'])
                # sum numeric values
                for v in totals.values():
                    try:
                        total += float(v)
                    except Exception:
                        pass
                return total if total > 0 else None
        except Exception as e:
            logger.debug("AlertManager: fetch_balance failed: %s", e)
        return None

    def _check_price_alerts(self):
        for sym in self.symbols:
            try:
                last = self._get_last_price(sym)
                if last is None:
                    continue
                prev = self._last_prices.get(sym)
                if prev is None:
                    self._last_prices[sym] = last
                    continue
                change_pct = abs((last - prev) / prev) * 100.0 if prev else 0.0
                if change_pct >= self.price_change_pct:
                    txt = f"Price alert for {sym}: {prev:.6f} -> {last:.6f} ({change_pct:.2f}%)"
                    logger.info(txt)
                    self._send_alert(txt)
                    # update baseline
                    self._last_prices[sym] = last
            except Exception as e:
                logger.debug("AlertManager: price check failed for %s: %s", sym, e)

    def _check_balance_alert(self):
        try:
            bal = self._get_total_balance()
            if bal is None:
                return
            prev = self._last_balance_total
            if prev is None:
                self._last_balance_total = bal
                return
            change_pct = abs((bal - prev) / prev) * 100.0 if prev else 0.0
            if change_pct >= self.balance_change_pct:
                txt = f"Balance alert: total changed {prev:.2f} -> {bal:.2f} ({change_pct:.2f}%)"
                logger.info(txt)
                self._send_alert(txt)
                self._last_balance_total = bal
        except Exception as e:
            logger.debug("AlertManager: balance check failed: %s", e)

    def _check_market_signals(self):
        # Use engine.recommend() to produce market signals
        if not self.engine:
            return
        for sym in self.symbols:
            try:
                rec = None
                # recommend should be safe to call; wrap in try
                try:
                    rec = self.engine.recommend(sym)
                except Exception as e:
                    logger.debug("AlertManager: recommend() failed for %s: %s", sym, e)
                if rec and isinstance(rec, dict):
                    conf = float(rec.get('confidence', 0.0))
                    side = rec.get('side', 'wait')
                    if conf >= self.signal_confidence_threshold and side in ('buy', 'sell'):
                        txt = f"Market signal for {sym}: {side.upper()} (confidence {conf:.2f})"
                        logger.info(txt)
                        self._send_alert(txt)
            except Exception as e:
                logger.debug("AlertManager: market signal check failed for %s: %s", sym, e)

    def _send_alert(self, text: str):
        # Only send if Bot available and chat id non-zero
        if not self.bot:
            logger.info("Alert (no-telegram): %s", text)
            return
        try:
            if not self.alert_chat_id or self.alert_chat_id == 0:
                logger.info("Alert (no chat id): %s", text)
                return
            self.bot.send_message(chat_id=self.alert_chat_id, text=text)
            logger.debug("Alert sent to chat_id=%s: %s", self.alert_chat_id, text)
        except Exception as e:
            logger.warning("Failed to send alert via Telegram: %s", e)


# Convenience functions
_active_manager: Optional[AlertManager] = None


def start_alerts(**kwargs) -> AlertManager:
    global _active_manager
    if _active_manager and _active_manager._running:
        logger.info("An AlertManager is already running")
        return _active_manager
    mgr = AlertManager(**kwargs)
    mgr.start()
    _active_manager = mgr
    return mgr


def stop_alerts(manager: Optional[AlertManager] = None):
    global _active_manager
    m = manager or _active_manager
    if not m:
        logger.info("No AlertManager to stop")
        return
    m.stop()
    if manager is None:
        _active_manager = None


if __name__ == '__main__':
    # Simple CLI runner for manual testing (safe mode; will not place orders)
    logger.info("Starting AlertManager from __main__ (test mode)")
    mgr = start_alerts()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_alerts(mgr)
