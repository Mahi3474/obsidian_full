import ccxt
from .config_env import get_exchange_name, get_api_keys

def make_exchange():
    name = get_exchange_name()

    if name == "binance":
        api_key, secret = get_api_keys("binance")
        ex = ccxt.binance({
            "apiKey": api_key,
            "secret": secret,
            "enableRateLimit": True,
            "options": {"defaultType": "spot"},
        })
    elif name == "mexc":
        api_key, secret = get_api_keys("mexc")
        ex = ccxt.mexc({
            "apiKey": api_key,
            "secret": secret,
            "enableRateLimit": True,
            "options": {"defaultType": "spot"},
        })
    else:
        raise ValueError(f"Unsupported exchange '{name}'")

    ex.load_markets()
    return ex
