from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
import time

from config import SETTINGS
from utils.logger import log_trade, log_msg
from utils.exchange_factory import make_exchange
from holdings import get_position, save_position, has_position


@dataclass
class MarketSnap:
    symbol: str
    bid: float
    ask: float
    last: float
    spread: float


def pct_change(entry: float, price: float) -> float:
    if entry <= 0:
        return 0.0
    return (price - entry) / entry


def _trail_hit(trail_high: float, last: float, trail_dist: float) -> bool:
    if trail_high <= 0:
        return False
    drop = (trail_high - last) / trail_high
    return drop >= trail_dist


def _calc_tp_hit(entry: float, last: float, thresholds: list[float]) -> Optional[int]:
    """Return index of highest TP level hit, or None."""
    gain = pct_change(entry, last)
    idx = None
    for i, level in enumerate(thresholds):
        if gain >= level:
            idx = i
    return idx


def _sell_fractional(exchange, symbol: str, qty: float) -> Tuple[str, float, str]:
    """Place a market sell if live, otherwise simulate. Return (order_id, avg_price, status)."""
    if qty <= 0:
        return ("", 0.0, "SKIP_ZERO_QTY")

    if SETTINGS.LIVE_MODE:
        try:
            order = exchange.create_market_sell_order(symbol, qty)
            order_id = str(order.get("id") or order.get("orderId") or "?")
            avg = float(order.get("average") or order.get("avgPx") or order.get("price") or 0.0)
            status = order.get("status") or "FILLED"
            return (order_id, avg, status)
        except Exception as e:
            log_msg(f"SELL error for {symbol}: {type(e).__name__} — {e}")
            return ("", 0.0, "ERROR")
    else:
        # paper: use last as avg, fake id
        return (f"PAPER-{int(time.time()*1000)}", 0.0, "PAPER_FILLED")


def evaluate_sell(symbol: str, last: float) -> None:
    """
    Evaluate and execute sells according to:
      • Laddered TP (SETTINGS.TP_LADDER with SETTINGS.TP_LADDER_FRACTIONS)
      • Trailing TP (after TP1) with SETTINGS.TRAIL_DISTANCE_PCT
      • Hard stop-loss SETTINGS.STOP_LOSS_PCT
    Mutates holdings via save_position.
    """
    pos = get_position(symbol)
    if not pos:
        return

    entry = float(pos.get("entry_price", 0.0))
    qty   = float(pos.get("qty", 0.0))
    if qty <= 0 or entry <= 0:
        return

    # ensure we have runtime fields
    pos.setdefault("tp_index", -1)         # last completed TP index (-1 = none)
    pos.setdefault("trail_high", 0.0)      # running high after TP1

    # update trail high if allowed
    if SETTINGS.TRAIL_ENABLE and last > pos["trail_high"]:
        pos["trail_high"] = last

    exchange = make_exchange()

    # STOP-LOSS
    loss_pct = -pct_change(entry, last)
    if loss_pct >= SETTINGS.STOP_LOSS_PCT:
        order_id, avg, status = _sell_fractional(exchange, symbol, qty)
        log_trade(symbol, reason="SL", side="SELL", order_id=order_id, status=status, avg=avg,
                  pct_gain_pct=pct_change(entry, last))
        # position cleared
        pos["qty"] = 0.0
        pos["trail_high"] = 0.0
        pos["tp_index"] = -1
        save_position(symbol, pos)
        return

    # TAKE-PROFIT ladder
    tp_levels = list(SETTINGS.TP_LADDER)
    tp_fracs  = list(SETTINGS.TP_LADDER_FRACTIONS)
    idx_hit = _calc_tp_hit(entry, last, tp_levels)

    if idx_hit is not None and idx_hit > pos["tp_index"]:
        # sell this step
        # fraction is of ORIGINAL position size
        orig_qty = float(pos.get("orig_qty", qty))
        if "orig_qty" not in pos:
            pos["orig_qty"] = orig_qty
        sell_qty = max(0.0, min(qty, orig_qty * tp_fracs[idx_hit]))
        if sell_qty > 0:
            order_id, avg, status = _sell_fractional(exchange, symbol, sell_qty)
            pos["qty"] = max(0.0, qty - sell_qty)
            pos["tp_index"] = idx_hit
            # start trailing once TP1 is achieved
            if SETTINGS.TRAIL_ENABLE and idx_hit >= 0:
                pos["trail_high"] = max(pos.get("trail_high", 0.0), last)
            save_position(symbol, pos)
            log_trade(symbol, reason=f"TP{idx_hit+1}", side="SELL", order_id=order_id, status=status, avg=avg,
                      pct_gain_pct=pct_change(entry, last))
            # if cleared ladder and no qty left, we are done
            if pos["qty"] <= 0:
                pos["trail_high"] = 0.0
                save_position(symbol, pos)
                return

    # TRAILING (only after at least TP1 hit)
    if SETTINGS.TRAIL_ENABLE and pos.get("tp_index", -1) >= 0 and pos["qty"] > 0:
        if _trail_hit(pos["trail_high"], last, SETTINGS.TRAIL_DISTANCE_PCT):
            order_id, avg, status = _sell_fractional(exchange, symbol, pos["qty"])
            log_trade(symbol, reason="TRAIL", side="SELL", order_id=order_id, status=status, avg=avg,
                      pct_gain_pct=pct_change(entry, last))
            pos["qty"] = 0.0
            pos["trail_high"] = 0.0
            pos["tp_index"] = -1
            save_position(symbol, pos)
            return

    # no action — persist any updated runtime fields
    save_position(symbol, pos)

# --- compatibility alias for strategy_core ---
try:
    evaluate_sell  # check if the function exists
except NameError:
    pass
else:
    def execute_sells(ex, snap):
        """Alias for evaluate_sell to keep strategy_core.py working."""
        return evaluate_sell(ex, snap)
