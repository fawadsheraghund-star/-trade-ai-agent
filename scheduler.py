"""
scheduler.py

Lightweight scheduler for Fawad Trade AI Agent (TEST MODE).

Features:
- Runs periodic market checks via the AlertManager
- Sends Telegram alerts at set intervals
- Monitors default symbols: BTC/USDT, ETH/USDT, BNB/USDT
- Designed for TEST MODE (respects USE_TESTNET and LIVE_ENABLE)

Usage:
from scheduler import start_scheduler, stop_scheduler
sched = start_scheduler()
# ... later
stop_scheduler(sched)

Run directly:
python scheduler.py

This module intentionally keeps dependencies light and uses the AlertManager
from alerts.py to perform checks and send alerts. The scheduler simply
configures and starts the AlertManager with appropriate defaults.
"""

import os
import threading
import time
from typing import Optional, List

from utils.logger import logger

try:
    from alerts import AlertManager
except Exception:
    AlertManager = None


def _get_env(name: str, default=None):
    v = os.getenv(name)
    return v if v is not None else default


class Scheduler:
    def __init__(self,
                 symbols: Optional[List[str]] = None,
                 interval: Optional[int] = None,
                 alert_price_change_pct: Optional[float] = None):
        # Default symbols to monitor in TEST MODE
        self.symbols = symbols or _get_env("SCHED_SYMBOLS", "BTC/USDT,ETH/USDT,BNB/USDT").split(",")
        self.interval = int(interval or _get_env("ALERT_INTERVAL", 60))
        self.price_change_pct = float(alert_price_change_pct or _get_env("ALERT_PRICE_CHANGE_PCT", 0.5))

        # Respect test-mode flags
        self.use_testnet = str(_get_env("USE_TESTNET", "true")).lower() in ("1","true","yes")
        self.live_enable = str(_get_env("LIVE_ENABLE", "false")).lower() in ("1","true","yes")

        self._manager: Optional[AlertManager] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self):
        if not AlertManager:
            logger.warning("Scheduler: alerts.AlertManager not available; cannot start scheduler")
            return None
        if self._running:
            logger.info("Scheduler already running")
            return self

        logger.info("Scheduler starting (test mode=%s, live_enable=%s)", self.use_testnet, self.live_enable)
        # Create an AlertManager configured for our symbols
        self._manager = AlertManager(symbols=self.symbols, interval=self.interval, price_change_pct=self.price_change_pct)
        self._manager.start()
        self._running = True

        # Background thread to monitor manager health and log heartbeats
        self._thread = threading.Thread(target=self._run_monitor, daemon=True)
        self._thread.start()
        return self

    def _run_monitor(self):
        while self._running:
            try:
                logger.debug("Scheduler heartbeat: manager_running=%s", (self._manager._running if self._manager else False))
            except Exception:
                pass
            time.sleep(max(10, min(60, int(self.interval))))

    def stop(self):
        logger.info("Scheduler stopping")
        self._running = False
        try:
            if self._manager:
                self._manager.stop()
        except Exception as e:
            logger.debug("Scheduler: error stopping manager: %s", e)
        try:
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=2.0)
        except Exception:
            pass


_active_scheduler: Optional[Scheduler] = None


def start_scheduler(**kwargs) -> Optional[Scheduler]:
    global _active_scheduler
    if _active_scheduler and _active_scheduler._running:
        logger.info("A scheduler is already active")
        return _active_scheduler
    sched = Scheduler(**kwargs)
    sched.start()
    _active_scheduler = sched
    return sched


def stop_scheduler(sched: Optional[Scheduler] = None):
    global _active_scheduler
    s = sched or _active_scheduler
    if not s:
        logger.info("No active scheduler to stop")
        return
    s.stop()
    if sched is None:
        _active_scheduler = None


if __name__ == '__main__':
    # Simple CLI runner
    logger.info("Starting scheduler (TEST MODE). Use CTRL-C to stop.")
    sched = start_scheduler()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, stopping scheduler")
        stop_scheduler(sched)
