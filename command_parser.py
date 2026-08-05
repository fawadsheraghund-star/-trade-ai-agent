# Minimal command parser for text/voice commands.
# parse_command returns a dictionary with at least the `action` key.

import re
from typing import Dict, Any

SYMBOL_RE = re.compile(r"([A-Z]{2,6}/[A-Z]{2,6}|[A-Z]{2,6})")


def parse_command(text: str) -> Dict[str, Any]:
    if not text:
        return {"action": "unknown"}
    t = text.strip()
    low = t.lower()
    out = {"action": "unknown", "raw": t}

    # analysis commands
    if low.startswith("analyze") or low.startswith("analyse") or "recommend" in low or "analysis" in low:
        out["action"] = "analysis"
        m = SYMBOL_RE.search(t.upper())
        if m:
            out["symbol"] = m.group(1)
        return out

    # trade commands
    if low.startswith("buy") or low.startswith("sell") or low.startswith("order"):
        out["action"] = "trade"
        parts = t.split()
        # try to find amount and symbol
        amount = None
        symbol = None
        side = None
        if parts:
            if parts[0].lower() in ("buy", "sell"):
                side = parts[0].lower()
                # next token might be amount or symbol
                if len(parts) >= 3:
                    # e.g. buy 0.01 BTC/USDT
                    try:
                        amount = float(parts[1])
                        symbol = parts[2].upper()
                    except Exception:
                        symbol = parts[1].upper()
                elif len(parts) == 2:
                    # buy BTC/USDT
                    try:
                        # if second token numeric treat as amount
                        amount = float(parts[1])
                    except Exception:
                        symbol = parts[1].upper()
        # fallback symbol search
        if not symbol:
            m = SYMBOL_RE.search(t.upper())
            if m:
                symbol = m.group(1)
        if side:
            out["side"] = side
        if amount is not None:
            out["amount"] = amount
        if symbol:
            out["symbol"] = symbol
        return out

    # fallback: try to detect a symbol and treat as analysis
    m = SYMBOL_RE.search(t.upper())
    if m:
        return {"action": "analysis", "symbol": m.group(1), "raw": t}

    return out
