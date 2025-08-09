import time, os
from dotenv import load_dotenv

from utils.exchange_factory import make_exchange
from utils.logger import log_trade, log_msg
from config import SETTINGS
from holdings import has_position, open_position, save_position, get_position
from sell_engine import MarketSnap, execute_sells



load_dotenv()

def fetch_price(exchange, symbol):
    t = exchange.fetch_ticker(symbol)
    return float(t["last"])

def spread_ok(orderbook, max_spread_pct):
    bid = float(orderbook["bids"][0][0]) if orderbook["bids"] else 0.0
    ask = float(orderbook["asks"][0][0]) if orderbook["asks"] else 0.0
    if bid <= 0 or ask <= 0:
        return False, bid, ask, None
    spread = (ask - bid) / ask
    return spread <= max_spread_pct, bid, ask, spread

def run_strategy(symbols, live=None, entry_usd=None):
    """
    Main loop:
      - For each symbol: pull order book → compute bid/ask/last → SELL first if holding
      - If not holding: run spread guard → (placeholder) buy signal → BUY
    """

    # Optional overrides from function args
    if live is not None:
        SETTINGS.LIVE_MODE = live
    if entry_usd is not None:
        SETTINGS.ENTRY_AMOUNT_USD = entry_usd

    ex = make_exchange()
    quote = SETTINGS.QUOTE
    print(f"Live mode: {SETTINGS.LIVE_MODE}")

def run_strategy(symbols, live=None, entry_usd=None):
    """
    Main loop:
      - For each symbol: pull order book → compute bid/ask/last → SELL first if holding
      - If not holding: run spread guard → (placeholder) buy signal → BUY
    """

    # Optional overrides from function args
    if live is not None:
        SETTINGS.LIVE_MODE = live
    if entry_usd is not None:
        SETTINGS.ENTRY_AMOUNT_USD = entry_usd

    ex = make_exchange()
    quote = SETTINGS.QUOTE
    print(f"Live mode: {SETTINGS.LIVE_MODE}")

    while True:
        for base in symbols:
            symbol = f"{base}/{quote}"
            try:
                # Pull order book & derive prices
                ob = ex.fetch_order_book(symbol, limit=10)
                bid = ob["bids"][0][0] if ob.get("bids") else None
                ask = ob["asks"][0][0] if ob.get("asks") else None
                if not bid or not ask:
                    log_msg(f"{symbol}: no bid/ask in book; skipping")
                    continue

                last = (bid + ask) / 2.0
                spread = (ask - bid) / bid

                # SELL FIRST: if we hold a position, evaluate exits
                if has_position(symbol):
                    snap = MarketSnap(symbol=symbol, bid=bid, ask=ask, last=last, spread=spread)
                    execute_sells(ex, snap)
                    # After managing an open position, move to next symbol
                    continue

                # BUY: only if we do NOT currently hold the symbol
                # Spread guard
                if spread > SETTINGS.MAX_SPREAD_PCT:
                    log_msg(f"Spread guard skip {symbol}  spread={spread:.4f}")
                    continue

                # TODO: plug in your real entry signal
                confidence = 0.80
                should_buy = confidence >= 0.75

                if should_buy:
                    if SETTINGS.ENTRY_AMOUNT_USD is None:
                        log_msg("ENTRY_AMOUNT_USD not set; skipping buy")
                        continue

                    amount = SETTINGS.ENTRY_AMOUNT_USD / last

                    if SETTINGS.LIVE_MODE:
                        order = ex.create_market_buy_order(symbol, amount)
                        order_id = str(order.get("id") or order.get("orderId") or "")
                        avg = float(order.get("average") or last)
                        open_position(symbol, amount, avg, order_id)
                        log_trade(symbol, confidence, "LIVE_BUY", order_id)
                    else:
                        open_position(symbol, amount, last, None)
                        log_trade(symbol, confidence, "PAPER_BUY", None)

            except Exception as e:
                log_msg(f"Error for {symbol}: {type(e).__name__} - {e}")
                time.sleep(0.4)  # tiny backoff on error

        time.sleep(2.0)  # pacing between full symbol scans


if __name__ == "__main__":
    run_strategy(["BTC","ETH"], live=False, entry_usd=50.0)
