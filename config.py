# config.py
import os, json
from dataclasses import dataclass

# ---------- helpers ----------
def _env_str(name: str, default: str) -> str:
    v = os.getenv(name)
    return str(v) if v is not None else default

def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default

def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default

def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return str(v).strip().lower() in {"1", "true", "yes", "on"}

def _parse_list(value: str|None, default: list[str]) -> list[str]:
    if not value:
        return default
    try:
        # accept JSON (["BTC","ETH"]) or CSV (BTC,ETH)
        if value.strip().startswith("["):
            return json.loads(value)
        return [x.strip() for x in value.split(",") if x.strip()]
    except Exception:
        return default

# ---------- raw values from env with sensible defaults ----------
# Exchange + auth
EXCHANGE         = _env_str("EXCHANGE", "binance")
BINANCE_API_KEY  = _env_str("BINANCE_API_KEY", "")
BINANCE_API_SECRET = _env_str("BINANCE_API_SECRET", "")

# Paper/live & position sizing
LIVE_MODE          = _env_bool("LIVE_MODE", False)   # False = paper
ENTRY_AMOUNT_USD   = _env_float("ENTRY_AMOUNT_USD", 25.0)
MIN_NOTIONAL_USD   = _env_float("MIN_NOTIONAL_USD", 10.0)

# Quote currency (fix for your QUOTE error)
UNIVERSE_QUOTE     = _env_str("UNIVERSE_QUOTE", "USDT")
QUOTE              = UNIVERSE_QUOTE  # <— code uses SETTINGS.QUOTE

# Universe build
UNIVERSE_MAX              = _env_int("UNIVERSE_MAX", 120)
UNIVERSE_MIN_24H_VOL_USDT = _env_float("UNIVERSE_MIN_24H_VOL_USDT", 1_000_000)
UNIVERSE_REFRESH_MINUTES  = _env_int("UNIVERSE_REFRESH_MINUTES", 1)  # fast for sniper

UNIVERSE_BLACKLIST = _parse_list(os.getenv("UNIVERSE_BLACKLIST"),
                                 ["USDC","BUSD","FDUSD","TUSD"])
UNIVERSE_WHITELIST = _parse_list(os.getenv("UNIVERSE_WHITELIST"), [])

# Entry / trend filters
ENTRY_SMA_FAST = _env_int("ENTRY_SMA_FAST", 9)
ENTRY_SMA_SLOW = _env_int("ENTRY_SMA_SLOW", 50)
ENTRY_EMA      = _env_int("ENTRY_EMA", 0)  # 0=off; set 21 to enable

# Market guardrails
MAX_SPREAD_PCT        = _env_float("MAX_SPREAD_PCT", 0.006)   # 0.6%
MAX_SLIPPAGE_PCT      = _env_float("MAX_SLIPPAGE_PCT", 0.005) # 0.5%
VOL_GUARD_5M_RANGE_PCT= _env_float("VOL_GUARD_5M_RANGE_PCT", 0.03)  # 3% range min

# Depth guard
DEPTH_TOP_LEVELS = _env_int("DEPTH_TOP_LEVELS", 2)   # very tight (sniper)
DEPTH_MIN_USD    = _env_int("DEPTH_MIN_USD", 1500)   # allow thinner books (sniper)

# Recency
RECENCY_MAX_MINUTES = _env_int("RECENCY_MAX_MINUTES", 8)

# Logging dir (used by utils.logger)
LOG_DIR = _env_str("LOG_DIR", "logs")

# ---------- exported settings object ----------
@dataclass
class Settings:
    # universe 
    # @dataclass
 class Settings:
    # universe
    QUOTE: str = UNIVERSE_QUOTE           # <-- Add this line for backward compatibility
    UNIVERSE_QUOTE: str = UNIVERSE_QUOTE
    UNIVERSE_MAX: int = UNIVERSE_MAX
    UNIVERSE_MIN_24H_VOL_USDT: float = UNIVERSE_MIN_24H_VOL_USDT
    UNIVERSE_REFRESH_MINUTES: int = UNIVERSE_REFRESH_MINUTES
    UNIVERSE_BLACKLIST: list[str] = None
    UNIVERSE_WHITELIST: list[str] = None

    # entry / trend
    ENTRY_SMA_FAST: int = ENTRY_SMA_FAST
    ENTRY_SMA_SLOW: int = ENTRY_SMA_SLOW
    ENTRY_EMA: int = ENTRY_EMA


    # market guardrails
    MAX_SPREAD_PCT: float = MAX_SPREAD_PCT
    MAX_SLIPPAGE_PCT: float = MAX_SLIPPAGE_PCT
    VOL_GUARD_5M_RANGE_PCT: float = VOL_GUARD_5M_RANGE_PCT

    # depth guard
    DEPTH_TOP_LEVELS: int = DEPTH_TOP_LEVELS
    DEPTH_MIN_USD: int = DEPTH_MIN_USD

    # recency
    RECENCY_MAX_MINUTES: int = RECENCY_MAX_MINUTES

    # live/paper
    LIVE_MODE: bool = LIVE_MODE
    ENTRY_AMOUNT_USD: float = ENTRY_AMOUNT_USD
    MIN_NOTIONAL_USD: float = MIN_NOTIONAL_USD

# single instance used everywhere
SETTINGS = Settings(
    UNIVERSE_BLACKLIST=UNIVERSE_BLACKLIST,
    UNIVERSE_WHITELIST=UNIVERSE_WHITELIST,
)
