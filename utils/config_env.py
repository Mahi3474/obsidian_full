import os

def get_exchange_name() -> str:
    return (os.getenv("EXCHANGE") or "binance").strip().lower()

def get_api_keys(exchange_name: str) -> tuple[str, str]:
    if exchange_name == "binance":
        return (
            os.getenv("BINANCE_API_KEY", "").strip(),
            os.getenv("BINANCE_SECRET", "").strip(),
        )
    elif exchange_name == "mexc":
        return (
            os.getenv("MEXC_API_KEY", "").strip(),
            os.getenv("MEXC_SECRET", "").strip(),
        )
    else:
        raise ValueError(f"Unsupported EXCHANGE '{exchange_name}'")
