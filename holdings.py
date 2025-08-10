# holdings.py
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

# Where we persist open positions
PATH = Path("data/holdings.json")
_LOCK = threading.Lock()


# ---------- low-level IO ----------

def _load() -> Dict[str, Dict[str, Any]]:
    """Load the holdings file (empty dict if missing/corrupt)."""
    try:
        return json.loads(PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(data: Dict[str, Dict[str, Any]]) -> None:
    """Atomic write of the holdings file."""
    PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = PATH.with_suffix(".tmp")
    with _LOCK:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp.replace(PATH)


# ---------- convenience API used by the bot ----------

def has_position(symbol: str) -> bool:
    """Return True if we hold a position for the symbol."""
    return symbol in _load()


def get_position(symbol: str) -> Optional[Dict[str, Any]]:
    """Return the position dict for a given symbol, or None if not held."""
    return _load().get(symbol)


def list_symbols() -> List[str]:
    """Return a list of symbols currently held (e.g., ['BTC/USDT'])."""
    return list(_load().keys())


def open_position(
    symbol: str,
    amount: float,
    entry_price: float,
    order_id: Optional[str] = None,
) -> None:
    """
    Create or overwrite a position record for symbol.
    Also initializes runtime fields used by the sell engine.
    """
    data = _load()
    data[symbol] = {
        "amount": float(amount),
        "entry_price": float(entry_price),
        "order_id": str(order_id or ""),
        # runtime / strategy fields (safe defaults)
        "trail_high": None,   # for trailing stop logic
        "tp_index": 0,        # ladder take-profit index
    }
    _save(data)


def update_amount(symbol: str, new_amount: float) -> None:
    """
    Update only the amount. If <= 0, remove the position.
    """
    data = _load()
    if new_amount <= 0:
        data.pop(symbol, None)
    else:
        pos = data.get(symbol, {})
        pos["amount"] = float(new_amount)
        data[symbol] = pos
    _save(data)


def save_position(symbol: str, pos: Optional[Dict[str, Any]]) -> None:
    """
    Persist a full position dict (used when strategy updates runtime fields).
    If pos is None or amount <= 0, remove the position.
    """
    data = _load()
    if not pos or float(pos.get("amount", 0)) <= 0:
        data.pop(symbol, None)
    else:
        # ensure required keys exist
        pos.setdefault("entry_price", 0.0)
        pos.setdefault("order_id", "")
        pos.setdefault("trail_high", None)
        pos.setdefault("tp_index", 0)
        data[symbol] = pos
    _save(data)


def close_position(symbol: str) -> None:
    """Delete the position, if present."""
    data = _load()
    data.pop(symbol, None)
    _save(data)
