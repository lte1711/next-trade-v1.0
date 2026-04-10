import json
from datetime import datetime
from pathlib import Path

from main_runtime import TradingRuntime
from scenario_forced_entry_validation import (
    cleanup_symbol,
    enrich_active_position,
    force_sync_positions,
    get_min_trade_quantity,
    now_iso,
    poll_order,
    record_step,
    safe_float,
    snapshot_state,
)


RESULT_JSON = Path("multi_symbol_forced_lifecycle.json")
RESULT_MD = Path("MULTI_SYMBOL_FORCED_LIFECYCLE_REPORT.md")
SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]


def write_json(payload):
    RESULT_JSON.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def write_report(payload):
    lines = [
        "# Multi Symbol Forced Lifecycle Report",
        "",
        f"Generated: {payload.get('completed_at') or payload.get('started_at')}",
        f"Environment: `{payload.get('environment')}`",
        f"Status: `{payload.get('status')}`",
        "",
        "## Aggregate",
        f"- Symbols Requested: `{len(payload.get('symbols', []))}`",
        f"- Symbols Passed: `{payload.get('aggregate', {}).get('symbols_passed', 0)}`",
        f"- Symbols Failed: `{payload.get('aggregate', {}).get('symbols_failed', 0)}`",
        f"- Total Entry Orders: `{payload.get('aggregate', {}).get('entry_orders', 0)}`",
        f"- Total Partial Closes: `{payload.get('aggregate', {}).get('partial_closes', 0)}`",
        f"- Total Final Closes: `{payload.get('aggregate', {}).get('final_closes', 0)}`",
        f"- Total Protective Orders Observed: `{payload.get('aggregate', {}).get('protective_orders_observed', 0)}`",
        f"- System Errors: `{payload.get('system_errors')}`",
        "",
        "## Symbol Summary",
    ]

    for result in payload.get("symbol_results", []):
        lines.append(
            "- "
            f"{result.get('symbol')}: "
            f"status={result.get('status')}, "
            f"entry={result.get('entry_order_id')}, "
            f"partial={result.get('partial_close_order_id')}, "
            f"final={result.get('final_close_order_id')}, "
            f"cooldown={result.get('recently_closed_after_full_close')}"
        )

    if payload.get("next_evolution_targets"):
        lines.extend(["", "## Next Evolution Targets"])
        for item in payload["next_evolution_targets"]:
            lines.append(f"- {item}")

    RESULT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_symbol(runtime, payload, symbol, strategy_name="ma_trend_follow"):
    result = {
        "symbol": symbol,
        "status": "running",
        "started_at": now_iso(),
        "steps": [],
        "snapshots": [],
    }
    payload["symbol_results"].append(result)
    write_json(payload)

    try:
        cleanup_symbol(runtime, symbol)
        snapshot_state(runtime, result, "before_entry", symbol)

        quantity = get_min_trade_quantity(runtime, symbol, target_notional=6.5)
        entry = runtime.order_executor.submit_order(
            strategy_name=strategy_name,
            symbol=symbol,
            side="BUY",
            quantity=quantity,
            reduce_only=False,
            metadata={"multi_symbol_forced_lifecycle": True},
        )
        if not entry:
            raise RuntimeError("Entry order returned None")

        entry_status = poll_order(runtime, symbol, entry.get("orderId"))
        if not entry_status or entry_status.get("status") != "FILLED":
            raise RuntimeError(f"Entry order not filled: {entry_status}")

        entry_price = safe_float(entry_status.get("avgPrice"), 0.0)
        executed_qty = safe_float(entry_status.get("executedQty"), quantity)
        entry_time = now_iso()
        runtime.trading_results.setdefault("position_entry_times", {})[symbol] = entry_time
        force_sync_positions(runtime)
        enrich_active_position(runtime, symbol, strategy_name, entry_price, executed_qty, entry_time)
        result["entry_order_id"] = entry.get("orderId")
        record_step(result, "entry_fill", "passed", "Entry order filled.")
        snapshot_state(runtime, result, "after_entry_fill", symbol)

        runtime.protective_order_manager.place_protective_orders(strategy_name, symbol, "BUY", entry_price)
        snapshot_state(runtime, result, "after_protective_orders", symbol)
        record_step(result, "protective_orders", "passed", "Protective orders placed.")

        state = runtime.partial_take_profit_manager.get_position_management_state(symbol)
        state["tp1_done"] = True
        state["last_partial_close_at"] = now_iso()
        runtime.trading_results.setdefault("partial_take_profit_state", {})[symbol] = state
        snapshot_state(runtime, result, "after_partial_state_mark", symbol)
        record_step(result, "partial_state_mark", "passed", "Partial TP state marked.")

        partial_closed = runtime.position_manager.close_partial_position(
            symbol,
            close_fraction=0.5,
            reason="multi_symbol_partial_close",
        )
        if not partial_closed:
            raise RuntimeError("Partial close request failed")

        partial_order = runtime.trading_results.get("real_orders", [])[-1]
        partial_status = poll_order(runtime, symbol, partial_order.get("order_id"))
        force_sync_positions(runtime)
        runtime.pending_order_manager.refresh_pending_orders()
        force_sync_positions(runtime)
        result["partial_close_order_id"] = partial_order.get("order_id")
        result["partial_close_status"] = partial_status.get("status") if partial_status else None
        snapshot_state(runtime, result, "after_partial_close", symbol)
        record_step(result, "partial_close", "passed", "Partial close completed.")

        full_closed = runtime.position_manager.close_position(symbol, "multi_symbol_final_cleanup")
        if not full_closed:
            raise RuntimeError("Full close request failed")

        full_order = runtime.trading_results.get("real_orders", [])[-1]
        full_status = poll_order(runtime, symbol, full_order.get("order_id"))
        force_sync_positions(runtime)
        runtime.pending_order_manager.refresh_pending_orders()
        force_sync_positions(runtime)
        snapshot_state(runtime, result, "after_full_close", symbol)
        result["final_close_order_id"] = full_order.get("order_id")
        result["final_close_status"] = full_status.get("status") if full_status else None

        final_snapshot = result["snapshots"][-1]
        result["recently_closed_after_full_close"] = final_snapshot.get("recently_closed")
        result["protective_orders_after_entry"] = next(
            (snap.get("open_algo_order_count") for snap in result["snapshots"] if snap.get("label") == "after_protective_orders"),
            0,
        )
        result["status"] = "passed"
        result["completed_at"] = now_iso()
        record_step(result, "full_close", "passed", "Final close completed.")
    except Exception as exc:
        result["status"] = "failed"
        result["error"] = str(exc)
        result["completed_at"] = now_iso()
        record_step(result, "failure", "failed", str(exc), errors=[str(exc)])
    finally:
        try:
            cleanup_symbol(runtime, symbol)
        except Exception:
            pass
        write_json(payload)


def main():
    payload = {
        "started_at": now_iso(),
        "completed_at": None,
        "status": "running",
        "environment": "https://demo-fapi.binance.com",
        "symbols": SYMBOLS,
        "symbol_results": [],
        "aggregate": {
            "symbols_passed": 0,
            "symbols_failed": 0,
            "entry_orders": 0,
            "partial_closes": 0,
            "final_closes": 0,
            "protective_orders_observed": 0,
        },
        "next_evolution_targets": [],
    }
    write_json(payload)

    runtime = None
    try:
        runtime = TradingRuntime()
        if not runtime.initialized:
            payload["status"] = "failed"
            payload["error"] = "TradingRuntime failed to initialize."
            return

        for symbol in SYMBOLS:
            run_symbol(runtime, payload, symbol)

        for result in payload["symbol_results"]:
            if result.get("status") == "passed":
                payload["aggregate"]["symbols_passed"] += 1
            else:
                payload["aggregate"]["symbols_failed"] += 1

            if result.get("entry_order_id"):
                payload["aggregate"]["entry_orders"] += 1
            if result.get("partial_close_order_id"):
                payload["aggregate"]["partial_closes"] += 1
            if result.get("final_close_order_id"):
                payload["aggregate"]["final_closes"] += 1
            payload["aggregate"]["protective_orders_observed"] += int(
                result.get("protective_orders_after_entry", 0)
            )

        payload["status"] = "completed" if payload["aggregate"]["symbols_failed"] == 0 else "partial_failure"
        payload["next_evolution_targets"] = [
            "Scale this validation to a broader symbol set and both LONG/SHORT scenarios.",
            "Replace synthetic partial TP marking with direct `PartialTakeProfitManager` trigger-path execution.",
            "Use the multi-symbol evidence to build a regression gate before longer unattended demo runs.",
        ]
    finally:
        if runtime is not None:
            payload["system_errors"] = len(runtime.trading_results.get("system_errors", []))
        payload["completed_at"] = now_iso()
        write_json(payload)
        write_report(payload)


if __name__ == "__main__":
    main()
