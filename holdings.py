import json, os, threading
from typing import Optional

PATH = "data/holdings.json"
_lock = threading.Lock()

def _load() -> dict:
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    if not os.path.exists(PATH):
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2)
    with open(PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _save(data: dict) -> None:
    with _lock:
        tmp = PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, PATH)

def get_position(symbol: str):
    """Return the position dict for a given symbol, or None if not held."""
    data = _load()
    return data.get(symbol)

def save_position(symbol: str, position: dict):
    """Save or update a position for the given symbol."""
    data = _load()
    data[symbol] = position
    _save(data)

def has_position(symbol: str) -> bool:
    """Return True if we hold a position for the symbol."""
    return get_position(symbol) is not None



def open_position(symbol: str, amount: float, entry_price: float, order_id: Optional[str] = None):
    data = _load()
    data[symbol] = {"amount": float(amount), "entry_price": float(entry_price), "order_id": order_id}
    _save(data)

def update_amount(symbol: str, new_amount: float):
    data = _load()
    if symbol in data:
        data[symbol]["amount"] = float(new_amount)
        if new_amount <= 0:
            data.pop(symbol, None)
    _save(data)

def close_position(symbol: str):
    data = _load()
    data.pop(symbol, None)
    _save(data)

def get_position(symbol: str):
    """Return the position dict for a given symbol, or None if not held."""
    data = _load()
    return data.get(symbol)

