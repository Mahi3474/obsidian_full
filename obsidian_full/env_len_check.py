import os
from dotenv import load_dotenv

# Load from .env in current directory
load_dotenv()

# List of required variables for the selected exchange
required_vars = [
    "EXCHANGE",
    "LIVE_MODE",
    "TAKE_PROFIT_PCT",
    "TP_LADDER",
    "TP_LADDER_FRACTIONS",
    "TRAIL_ENABLE",
    "TRAIL_DISTANCE_PCT",
    "STOP_LOSS_PCT",
    "MAX_SPREAD_PCT",
    "MAX_SLIPPAGE_PCT",
    "VOL_GUARD_5M_RANGE_PCT",
]

exchange = os.getenv("EXCHANGE", "").lower().strip()
if exchange == "binance":
    required_vars.extend(["BINANCE_API_KEY", "BINANCE_SECRET"])
elif exchange == "mexc":
    required_vars.extend(["MEXC_API_KEY", "MEXC_SECRET"])
else:
    print(f"[WARN] Unknown exchange set in EXCHANGE: '{exchange}'")
    required_vars.extend(["BINANCE_API_KEY", "BINANCE_SECRET"])  # default check

# Check and print results
print(f"Checking environment variables for exchange: {exchange or 'NOT SET'}\n")

missing = False
for var in required_vars:
    value = os.getenv(var)
    if not value:
        print(f"❌ Missing: {var}")
        missing = True
    else:
        print(f"✅ {var} present")

if missing:
    print("\n[RESULT] ❌ One or more required variables are missing or empty.")
else:
    print("\n[RESULT] ✅ All required environment variables are set.")
