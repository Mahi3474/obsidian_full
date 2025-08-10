# tokens_manager.py
import json, time
from pathlib import Path
from typing import Dict, List, Optional

import config as CFG  # read UNIVERSE_* knobs via CFG.UNIVERSE_...

TOKENS_PATH = Path("data/tokens.json")


# ---------- File IO helpers ----------
def _safe_load(path: Path = TOKENS_PATH) -> List[str]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _safe_save(symbols: List[str], path: Path = TOKENS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(symbols, indent=2), encoding="utf-8")


# ---------- Filters ----------
def _is_leveraged(base: str) -> bool:
    """Very light detector for leveraged tokens (UP/DOWN, BULL/BEAR, 3L/3S etc.)."""
    b = base.upper()
    if b.endswith(("UP", "DOWN", "BULL", "BEAR")):
        return True
    if b.endswith(("3L", "3S", "4L", "4S", "5L", "5S")):
        return True
    return False


def _is_stable_pair(base: str, quote: str) -> bool:
    """Exclude stable-to-stable pairs (base or quote in the stable set)."""
    stables = {"USDT", "USDC", "BUSD", "FDUSD", "TUSD", CFG.UNIVERSE_QUOTE.upper()}
    return base.upper() in stables or quote.upper() in stables and base.upper() in stables


# ---------- Public helpers ----------
def load_symbols() -> List[str]:
    """Load current universe list (may be empty on first run)."""
    return _safe_load()


def needs_refresh(last_ts: float, minutes: int) -> bool:
    return (time.time() - float(last_ts or 0)) > minutes * 60


def _fetch_universe_from_markets(exchange, quote: str, min_quote_vol: float, limit: int) -> List[str]:
    """
    Use exchange markets metadata where possible.
    Returns BASE list (without quote), respecting quote filter and min 24h volume if available.
    """
    bases: List[str] = []
    try:
        markets = exchange.load_markets()
        for m in markets.values():
            # Basic spot / quote filtering
            if (m.get("quote") or "").upper() != quote.upper():
                continue
            if not m.get("active", True):
                continue

            base = (m.get("base") or "").upper()
            if not base:
                # fallback: parse from "symbol" like "BTC/USDT"
                sym = m.get("symbol") or ""
                if "/" in sym:
                    base = sym.split("/")[0].upper()

            if not base:
                continue

            # Exclude leveraged & pure stable pairs
            if _is_leveraged(base):
                continue
            if _is_stable_pair(base, quote):
                continue

            # Optional volume gate if available
            qv = None
            info = m.get("info") or {}
            for k in ("quoteVolume", "qv", "volumeQuote", "quote_volume"):
                if k in info:
                    try:
                        qv = float(info[k])
                        break
                    except Exception:
                        pass
            if qv is not None and qv < min_quote_vol:
                continue

            bases.append(base)

        # De-dupe but keep order
        bases = list(dict.fromkeys(bases))
        # Respect a max size if configured
        if limit and len(bases) > limit:
            bases = bases[:limit]
        return bases

    except Exception:
        # If anything fails here, fall back to tickers method below
        return []


def _fetch_universe_from_tickers(exchange, quote: str, min_quote_vol: float, limit: int) -> List[str]:
    """
    Fallback using fetch_tickers(). Returns BASE list filtered by quote and volume if present.
    """
    bases: List[str] = []
    try:
        tickers = exchange.fetch_tickers()
        for sym, t in tickers.items():
            # Expect symbols like "BTC/USDT"
            if "/" not in sym:
                continue
            base, q = sym.split("/", 1)
            if q.upper() != quote.upper():
                continue

            baseU = base.upper()
            if _is_leveraged(baseU):
                continue
            if _is_stable_pair(baseU, quote):
                continue

            # Try to read quote volume
            qv = None
            info = t.get("info") or {}
            for k in ("quoteVolume", "qv", "volumeQuote", "quote_volume"):
                if k in info:
                    try:
                        qv = float(info[k])
                        break
                    except Exception:
                        pass
            if qv is not None and qv < min_quote_vol:
                continue

            bases.append(baseU)

        bases = list(dict.fromkeys(bases))
        if limit and len(bases) > limit:
            bases = bases[:limit]
        return bases
    except Exception:
        return []


def refresh_symbols(exchange, settings, held_symbols: Optional[List[str]] = None) -> List[str]:
    """
    Build/refresh the trading universe.
    - Pulls from markets metadata first, then falls back to tickers.
    - Applies blacklist/whitelist.
    - Always keeps currently held symbols (by BASE).
    - Persists to data/tokens.json and returns the BASE list.
    """
    quote = settings.QUOTE or CFG.UNIVERSE_QUOTE
    max_n = int(CFG.UNIVERSE_MAX or 0)
    min_qv = float(CFG.UNIVERSE_MIN_24H_VOL_USDT or 0.0)

    # 1) Discover from markets, else tickers
    bases = _fetch_universe_from_markets(exchange, quote, min_qv, max_n)
    if not bases:
        bases = _fetch_universe_from_tickers(exchange, quote, min_qv, max_n)

    # 2) Apply whitelist/blacklist (lists contain BASE tokens)
    bl = set(CFG.UNIVERSE_BLACKLIST or [])
    wl = list(CFG.UNIVERSE_WHITELIST or [])

    # blacklist: drop any that match
    bases = [b for b in bases if b not in bl]

    # whitelist: prepend, then de-dupe (preserve order)
    if wl:
        bases = list(dict.fromkeys([*wl, *bases]))

    # 3) Never drop currently held symbols (BASE portion)
    if held_symbols:
        held_bases = []
        for sym in held_symbols:
            if "/" in sym:
                held_bases.append(sym.split("/")[0].upper())
        bases = list(dict.fromkeys([*held_bases, *bases]))

    # 4) Cap to max
    if max_n and len(bases) > max_n:
        bases = bases[:max_n]

    _safe_save(bases)
    return bases


