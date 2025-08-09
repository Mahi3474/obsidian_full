import argparse
from strategies.strategy_core import run_strategy

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--live", type=str, default="false")
    p.add_argument("--entry_usd", type=float, default=None)
    p.add_argument("--symbols", type=str, default="BTC,ETH")
    args = p.parse_args()

    live = str(args.live).lower() in ("1","true","yes","y")
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    run_strategy(symbols, live=live, entry_usd=args.entry_usd)

if __name__ == "__main__":
    main()
