import json
import os
import sys
from datetime import datetime, timezone, timedelta

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from main_runtime import TradingRuntime


KST = timezone(timedelta(hours=9))
SOURCE_PATH = "EXECUTE_FIRST_CHECKPOINT_20260410_STEP26_STRICT_HOLD_CLOSE_ALL.json"
EVIDENCE_PATH = "EXECUTE_FIRST_CHECKPOINT_20260410_STEP27_REDUCE_ONLY_RECONCILIATION.json"


def main():
    started = datetime.now(KST)
    runtime = TradingRuntime()
    if not runtime.initialized:
        raise RuntimeError("runtime_not_initialized")

    with open(SOURCE_PATH, "r", encoding="utf-8") as handle:
        source = json.load(handle)

    real_orders = runtime.trading_results.setdefault("real_orders", [])
    existing_order_ids = {str(order.get("order_id")) for order in real_orders}
    quality_by_symbol = source.get("quality_by_symbol", {})
    injected_orders = []

    for order in source.get("new_orders", []):
        order_id = order.get("order_id")
        if not order_id or str(order_id) in existing_order_ids:
            continue

        symbol = order.get("symbol")
        quality = quality_by_symbol.get(symbol, {})
        trade_record = {
            "strategy": "ma_trend_follow",
            "symbol": symbol,
            "side": order.get("side"),
            "quantity": order.get("quantity"),
            "price": 0.0,
            "status": order.get("status"),
            "order_id": order_id,
            "executed_qty": order.get("executed_qty", 0.0),
            "timestamp": source.get("finished_at"),
            "type": "PENDING_TRADE",
            "market_regime": {},
            "strategy_signal": order.get("side"),
            "position_type": "LONG" if order.get("side") == "BUY" else "SHORT",
            "reduce_only": True,
            "entry_price": quality.get("entry_price", 0.0),
            "exit_reason": order.get("exit_reason"),
            "reconciliation_source": SOURCE_PATH,
        }
        real_orders.append(trade_record)
        injected_orders.append(trade_record)
        existing_order_ids.add(str(order_id))

    realized_before = len(runtime.trading_results.get("realized_pnl_journal", []))
    reconciliation_summary = runtime.order_executor.reconcile_pending_reduce_only_fills()
    runtime.sync_positions()

    with open("trading_results.json", "w", encoding="utf-8") as handle:
        json.dump(runtime.trading_results, handle, indent=2, default=str)

    finished = datetime.now(KST)
    evidence = {
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "duration_sec": round((finished - started).total_seconds(), 3),
        "mode": "step26_reduce_only_fill_reconciliation",
        "source_path": SOURCE_PATH,
        "injected_order_count": len(injected_orders),
        "injected_orders": injected_orders,
        "reconciliation_summary": reconciliation_summary,
        "active_symbols_after_sync": sorted(runtime.trading_results.get("active_positions", {})),
        "realized_pnl_journal_count_before": realized_before,
        "realized_pnl_journal_count_after": len(runtime.trading_results.get("realized_pnl_journal", [])),
        "new_realized_pnl_events": runtime.trading_results.get("realized_pnl_journal", [])[realized_before:],
        "system_errors": runtime.trading_results.get("system_errors", []),
    }
    with open(EVIDENCE_PATH, "w", encoding="utf-8") as handle:
        json.dump(evidence, handle, indent=2, ensure_ascii=False)
    print(json.dumps(evidence, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
