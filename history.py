"""
history.py

Trading history logging helpers for Fawad Trade AI Agent.

Features:
- Append and store executed orders and trade events to a local SQLite database (data/history.db)
- Query recent history and filter by user_id or symbol
- Export history to CSV
- Thread-safe access

Notes:
- This module only records history; it does not place orders.
- LIVE_ENABLE must remain false in environment unless you explicitly enable live trading elsewhere.
"""

import os
import sqlite3
import threading
import json
import time
import csv
from typing import Any, Dict, List, Optional

DB_DIR = os.getenv("HISTORY_DB_DIR", "data")
DB_FILE = os.getenv("HISTORY_DB_FILENAME", "history.db")
DB_PATH = os.path.join(DB_DIR, DB_FILE)

# Ensure data directory exists
os.makedirs(DB_DIR, exist_ok=True)


class TradeHistory:
    """Simple SQLite-backed trade history logger."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_table()

    def _ensure_table(self):
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS trade_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts INTEGER NOT NULL,
                    user_id TEXT,
                    order_id TEXT,
                    symbol TEXT,
                    side TEXT,
                    price REAL,
                    amount REAL,
                    order_type TEXT,
                    status TEXT,
                    details TEXT
                )
                """
            )
            self._conn.commit()

    def log_trade(self, *, user_id: Optional[str], order_id: Optional[str], symbol: str, side: str, price: Optional[float], amount: float, order_type: str = "market", status: str = "unknown", details: Optional[Dict[str, Any]] = None) -> int:
        """Append a trade event. Returns the database id for the inserted row."""
        ts = int(time.time())
        details_json = json.dumps(details) if details is not None else None
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "INSERT INTO trade_history (ts, user_id, order_id, symbol, side, price, amount, order_type, status, details) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (ts, user_id, order_id, symbol, side, price, amount, order_type, status, details_json),
            )
            self._conn.commit()
            return cur.lastrowid

    def get_history(self, limit: int = 100, user_id: Optional[str] = None, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve recent history. Filter by user_id and/or symbol if provided."""
        with self._lock:
            cur = self._conn.cursor()
            query = "SELECT * FROM trade_history"
            params: List[Any] = []
            filters: List[str] = []
            if user_id is not None:
                filters.append("user_id = ?")
                params.append(user_id)
            if symbol is not None:
                filters.append("symbol = ?")
                params.append(symbol)
            if filters:
                query += " WHERE " + " AND ".join(filters)
            query += " ORDER BY ts DESC LIMIT ?"
            params.append(limit)
            cur.execute(query, params)
            rows = cur.fetchall()
            out: List[Dict[str, Any]] = []
            for r in rows:
                try:
                    details = json.loads(r["details"]) if r["details"] else None
                except Exception:
                    details = r["details"]
                out.append({
                    "id": r["id"],
                    "ts": r["ts"],
                    "user_id": r["user_id"],
                    "order_id": r["order_id"],
                    "symbol": r["symbol"],
                    "side": r["side"],
                    "price": r["price"],
                    "amount": r["amount"],
                    "order_type": r["order_type"],
                    "status": r["status"],
                    "details": details,
                })
            return out

    def export_csv(self, path: str, limit: int = 1000) -> None:
        """Export recent history to CSV file at path."""
        rows = self.get_history(limit=limit)
        fieldnames = ["id", "ts", "user_id", "order_id", "symbol", "side", "price", "amount", "order_type", "status", "details"]
        with open(path, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in reversed(rows):  # oldest first
                row = r.copy()
                row["details"] = json.dumps(row.get("details")) if row.get("details") is not None else ""
                writer.writerow(row)

    def clear_history(self) -> None:
        """Clear all history (use with caution)."""
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("DELETE FROM trade_history")
            self._conn.commit()

    def close(self):
        try:
            with self._lock:
                self._conn.commit()
                self._conn.close()
        except Exception:
            pass


# Module-level default instance
_default_history: Optional[TradeHistory] = None


def get_history_store() -> TradeHistory:
    global _default_history
    if _default_history is None:
        _default_history = TradeHistory()
    return _default_history


if __name__ == '__main__':
    store = get_history_store()
    # quick manual test
    store.log_trade(user_id='user_test', order_id='ord_1', symbol='BTC/USDT', side='buy', price=50000.0, amount=0.001, order_type='market', status='filled', details={'note': 'test'})
    print('Recent:', store.get_history(limit=10))
