from dataclasses import dataclass

@dataclass
class Settings:
    # Battle-tested thresholds
    TAKE_PROFIT_PCT: float = 0.20
    TP_LADDER: tuple = (0.20, 0.30, 0.40)
    TP_LADDER_FRACTIONS: tuple = (0.50, 0.25, 0.25)
    TRAIL_ENABLE: bool = True
    TRAIL_DISTANCE_PCT: float = 0.08
    STOP_LOSS_PCT: float = 0.10

    # Market guards
    MAX_SPREAD_PCT: float = 0.005
    MAX_SLIPPAGE_PCT: float = 0.004
    VOL_GUARD_5M_RANGE_PCT: float = 0.03

    # Runtime
    LIVE_MODE: bool = False
    ENTRY_AMOUNT_USD: float | None = None
    QUOTE: str = "USDT"

SETTINGS = Settings()
