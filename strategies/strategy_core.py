import time, os
from dotenv import load_dotenv

from utils.exchange_factory import make_exchange
from utils.logger import log_trade, log_msg

from config import SETTINGS
import config as CFG  # access UNIVERSE_* via CFG.UNIVERSE_...

from holdings import has_position, open_position, save_position, get_position, list_symbols
from sell_engine import MarketSnap, execute_sells
from tokens_manager import refresh_symbols

load_dotenv()


def fetch_price(exchange, symbol):
    t = exchange.fetch_ticker(symbol)
    return float(t["last"])


def spread_ok(orderbook, max_spread_pct):
    bid = float(orderbook["bids"][0][0]) if orderbook["bids"] else 0.0
    ask = float(orderbook["asks"][0][0]) if orderbook["asks"] else 0.0
    if bid <= 0 or ask <= 0:
        return False, bid, ask, None
    spread = (ask - bid) / bid
    return spread <= max_spread_pct, bid, ask, spread


def run_strategy(symbols, live=None, entry_usd=None):
    """
    Main loop:
    - For each symbol: pull order book -> compute bid/ask/last -> SELL first if holding
    - If not holding: run spread guard + (placeholder) buy signal -> BUY
    """

    # Optional overrides from function args
    if live is not None:
        SETTINGS.LIVE_MODE = live
    if entry_usd is not None:
        SETTINGS.ENTRY_AMOUNT_USD = entry_usd

    ex = make_exchange()
    quote = SETTINGS.QUOTE
    print(f"Live mode: {SETTINGS.LIVE_MODE}")

    # ------ Initial universe build ------
    # Make sure we start with a sane list. Returns BASE list (e.g. ["BTC","ETH"])
    symbols = refresh_symbols(ex, SETTINGS)
    last_refresh = time.time()

    while True:
        # Periodically refresh the trading universe
        if time.time() - last_refresh >= CFG.UNIVERSE_REFRESH_MINUTES * 60:
            try:
                # keep anything we’re currently holding, even if it falls out of filters
                held = set(list_symbols())
                symbols = refresh_symbols(ex, SETTINGS, held_symbols=held)
                last_refresh = time.time()
                log_msg(f"Universe refreshed: {len(symbols)} symbols")
            except Exception as e:
                log_msg(f"Universe refresh failed: {type(e).__name__}: {e}")

        for base in symbols:
            symbol = f"{base}/{quote}"

            try:
                # ---- Pull order book & derive prices (lightweight)
                ob = ex.fetch_order_book(symbol, limit=10)
                bid = ob["bids"][0][0] if ob.get("bids") else None
                ask = ob["asks"][0][0] if ob.get("asks") else None
                if not bid or not ask:
                    log_msg(f"{symbol}: no bid/ask in book; skipping")
                    continue

                # Mid price and spread (% of bid)
                last = (bid + ask) / 2.0
                spread = (ask - bid) / bid

                # ---- SELL FIRST: if we hold a position, evaluate exits
                if has_position(symbol):
                    snap = MarketSnap(symbol=symbol, bid=bid, ask=ask, last=last, spread=spread)
                    execute_sells(ex, snap)
                    # continue to next symbol; only buy when not holding
                    continue

                # ---- BUY: only if we do NOT currently hold the symbol
                # Spread guard
                if spread > SETTINGS.MAX_SPREAD_PCT:
                    log_msg(f"Spread guard skip {symbol}  spread={spread:.4f}")
                    continue

                # TODO: plug your real entry signal here
                confidence = 0.80
                should_buy = confidence >= 0.75

                if should_buy:
                    # Safety: require configured entry amount
                    if SETTINGS.ENTRY_AMOUNT_USD is None:
                        log_msg("ENTRY_AMOUNT_USD not set; skipping buy")
                        continue

                    amount = SETTINGS.ENTRY_AMOUNT_USD / last

                    if SETTINGS.LIVE_MODE:
                        # LIVE: place a market buy; record order id and avg fill if available
                        order = ex.create_market_buy_order(symbol, amount)
                        order_id = str(order.get("id") or order.get("orderId") or "")
                        avg = float(order.get("average") or last)
                        open_position(symbol, amount=amount, entry_price=avg, order_id=order_id)
                        log_trade(symbol, confidence, "LIVE BUY", order_id)
                    else:
                        # PAPER: assume filled at last
                        open_position(symbol, amount=amount, entry_price=last, order_id=None)
                        log_trade(symbol, confidence, "PAPER BUY", None)

            except Exception as e:
                log_msg(f"Error for {symbol}: {type(e).__name__}: {e}")
                time.sleep(0.4)  # tiny backoff on error

        # pacing between full symbol scans
        time.sleep(2.0)


if __name__ == "__main__":
    # Example local run (paper by default)
    run_strategy(["BTC", "ETH"], live=False, entry_usd=50.0)



