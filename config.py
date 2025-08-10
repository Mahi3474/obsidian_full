# config.py

from dataclasses import dataclass
import os
import json

# --- Universe (token list) configuration ---
UNIVERSE_QUOTE = os.getenv("UNIVERSE_QUOTE", "USDT")
UNIVERSE_MAX = int(os.getenv("UNIVERSE_MAX", "60"))
UNIVERSE_MIN_24H_VOL_USDT = float(os.getenv("UNIVERSE_MIN_24H_VOL_USDT", "10000000"))
UNIVERSE_REFRESH_MINUTES = int(os.getenv("UNIVERSE_REFRESH_MINUTES", "360"))

def parse_list(value, default):
    """Parse a JSON-style list from env or return default."""
    try:
        return json.loads(value)
    except Exception:
        return default

UNIVERSE_BLACKLIST = parse_list(
    os.getenv("UNIVERSE_BLACKLIST", '["USDC", "BUSD", "FDUSD", "TUSD"]'),
    []
)

UNIVERSE_WHITELIST = parse_list(
    os.getenv("UNIVERSE_WHITELIST", "[]"),
    []
)

# --- Strategy / runtime settings ---
@dataclass
class Settings:
    # Battle-tested thresholds
    TAKE_PROFIT_PCT: float = 0.20
    TP_LADDER: tuple = (0.20, 0.30, 0.40)
    TP_LADDER_FRACTIONS: tuple = (0.50, 0.25, 0.25)
    TRAIL_ENABLE: bool = True
    TRAIL_DISTANCE_PCT: float = 0.10
    STOP_LOSS_PCT: float = 0.10
    MAX_SPREAD_PCT: float = 0.05
    MAX_SLIPPAGE_PCT: float = 0.04
    VOL_GUARD_5M_RANGE_PCT: float = 0.03

    # Live/paper settings
    LIVE_MODE: bool = False
    ENTRY_AMOUNT_USD: float = None
    QUOTE: str = UNIVERSE_QUOTE


# Create a default settings instance for import
SETTINGS = Settings()

