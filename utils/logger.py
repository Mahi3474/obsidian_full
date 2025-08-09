import csv, os
from datetime import datetime

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

TRADE_LOG = os.path.join(LOG_DIR, "trade_log.csv")
PERF_LOG = os.path.join(LOG_DIR, "performance_logs.csv")
GENERAL_LOG = os.path.join(LOG_DIR, "general_log.txt")

def _ts():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def log_msg(msg: str):
    with open(GENERAL_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{_ts()}] {msg}\n")

def log_trade(symbol: str, confidence: float, status: str, order=None):
    header = ["timestamp", "symbol", "confidence", "status", "order_id"]
    exists = os.path.exists(TRADE_LOG)
    with open(TRADE_LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(header)
        oid = None
        if isinstance(order, dict):
            oid = order.get("id") or order.get("orderId")
        w.writerow([_ts(), symbol, confidence, status, oid])

def log_performance(symbol: str, side: str, amount: float, entry: float, exit_: float, pnl_pct: float, pnl_usd: float, order_id: str | None, loss_cause: str | None = None):
    header = ["timestamp", "symbol", "side", "amount", "entry", "exit", "pnl_pct", "pnl_usd", "order_id", "loss_cause"]
    exists = os.path.exists(PERF_LOG)
    with open(PERF_LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(header)
        w.writerow([_ts(), symbol, side, amount, entry, exit_, pnl_pct, pnl_usd, order_id, loss_cause or ""])
