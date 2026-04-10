import json
import time
from pathlib import Path

from main_runtime import TradingRuntime
from scenario_forced_entry_validation import (
    cleanup_symbol,
    enrich_active_position,
    force_sync_positions,
    get_min_trade_quantity,
    now_iso,
    poll_order,
    safe_float,
)


RESULT_JSON = Path("short_bias_and_partial_tp_probe.json")
RESULT_MD = Path("SHORT_BIAS_AND_PARTIAL_TP_PROBE_REPORT.md")


def write_json(payload):
    RESULT_JSON.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def write_report(payload):
    lines = [
        "# Short Bias And Partial TP Probe Report",
        "",
        f"Generated: {payload.get('completed_at') or payload.get('started_at')}",
        f"Environment: `{payload.get('environment')}`",
        f"Status: `{payload.get('status')}`",
        "",
        "## Short Lifecycle",
        f"- Symbol: `{payload.get('short_lifecycle', {}).get('symbol')}`",
        f"- Entry Order: `{payload.get('short_lifecycle', {}).get('entry_order_id')}`",
        f"- Partial Close Order: `{payload.get('short_lifecycle', {}).get('partial_close_order_id')}`",
        f"- Final Close Order: `{payload.get('short_lifecycle', {}).get('final_close_order_id')}`",
        f"- Recently Closed After Full Close: `{payload.get('short_lifecycle', {}).get('recently_closed_after_full_close')}`",
        "",
        "## Partial TP Manager",
    ]

    for case in payload.get("partial_tp_cases", []):
        lines.append(
            "- "
            f"{case.get('name')}: "
            f"executed={case.get('executed')}, "
            f"profit_pct={case.get('profit_pct')}, "
            f"state={case.get('state')}, "
            f"trailing_updated={case.get('trailing_updated')}, "
            f"managed_stop={case.get('managed_stop_price')}"
        )

    if payload.get("errors"):
        lines.extend(["", "## Errors"])
        for item in payload["errors"]:
            lines.append(f"- {item}")

    RESULT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def snapshot_short_state(runtime, symbol):
    force_sync_positions(runtime)
    position = runtime.trading_results.get("active_positions", {}).get(symbol)
    open_algo_orders = runtime.protective_order_manager.get_open_orders(symbol)
    return {
        "has_active_position": bool(position),
        "active_amount": safe_float(position.get("amount"), 0.0) if position else 0.0,
        "entry_price": safe_float(position.get("entry_price"), 0.0) if position else 0.0,
        "managed_stop_price": runtime.trading_results.get("managed_stop_prices", {}).get(symbol),
        "open_algo_order_count": len(open_algo_orders),
        "recently_closed": symbol in runtime.trading_results.get("recently_closed_symbols", {}),
    }


def run_short_lifecycle(runtime, payload, symbol="BTCUSDT", strategy_name="ma_trend_follow"):
    result = {
        "symbol": symbol,
        "snapshots": [],
    }
    payload["short_lifecycle"] = result

    cleanup_symbol(runtime, symbol)
    result["snapshots"].append({"label": "before_entry", **snapshot_short_state(runtime, symbol)})

    quantity = get_min_trade_quantity(runtime, symbol, target_notional=6.5)
    entry = runtime.order_executor.submit_order(
        strategy_name=strategy_name,
        symbol=symbol,
        side="SELL",
        quantity=quantity,
        reduce_only=False,
        metadata={"short_bias_probe": True},
    )
    if not entry:
        raise RuntimeError("Short entry order returned None")

    entry_status = poll_order(runtime, symbol, entry.get("orderId"))
    if not entry_status or entry_status.get("status") != "FILLED":
        raise RuntimeError(f"Short entry not filled: {entry_status}")

    entry_price = safe_float(entry_status.get("avgPrice"), 0.0)
    executed_qty = safe_float(entry_status.get("executedQty"), quantity)
    entry_time = now_iso()
    runtime.trading_results.setdefault("position_entry_times", {})[symbol] = entry_time
    force_sync_positions(runtime)
    enrich_active_position(runtime, symbol, strategy_name, entry_price, -abs(executed_qty), entry_time)
    runtime.trading_results["active_positions"][symbol]["amount"] = -abs(
        safe_float(runtime.trading_results["active_positions"][symbol].get("amount"), executed_qty)
    )
    result["entry_order_id"] = entry.get("orderId")
    result["snapshots"].append({"label": "after_entry_fill", **snapshot_short_state(runtime, symbol)})

    runtime.protective_order_manager.place_protective_orders(strategy_name, symbol, "SELL", entry_price)
    time.sleep(1)
    result["snapshots"].append({"label": "after_protective_orders", **snapshot_short_state(runtime, symbol)})

    partial_closed = runtime.position_manager.close_partial_position(
        symbol,
        close_fraction=0.5,
        reason="short_bias_partial_close",
    )
    if not partial_closed:
        raise RuntimeError("Short partial close failed")

    partial_order = runtime.trading_results.get("real_orders", [])[-1]
    partial_status = poll_order(runtime, symbol, partial_order.get("order_id"))
    force_sync_positions(runtime)
    runtime.pending_order_manager.refresh_pending_orders()
    force_sync_positions(runtime)
    result["partial_close_order_id"] = partial_order.get("order_id")
    result["partial_close_status"] = partial_status.get("status") if partial_status else None
    result["snapshots"].append({"label": "after_partial_close", **snapshot_short_state(runtime, symbol)})

    full_closed = runtime.position_manager.close_position(symbol, "short_bias_final_cleanup")
    if not full_closed:
        raise RuntimeError("Short full close failed")

    full_order = runtime.trading_results.get("real_orders", [])[-1]
    full_status = poll_order(runtime, symbol, full_order.get("order_id"))
    force_sync_positions(runtime)
    runtime.pending_order_manager.refresh_pending_orders()
    force_sync_positions(runtime)
    result["final_close_order_id"] = full_order.get("order_id")
    result["final_close_status"] = full_status.get("status") if full_status else None
    result["snapshots"].append({"label": "after_full_close", **snapshot_short_state(runtime, symbol)})
    result["recently_closed_after_full_close"] = result["snapshots"][-1]["recently_closed"]


def run_partial_tp_cases(runtime, payload):
    manager = runtime.partial_take_profit_manager
    strategy_config = {
        "risk_config": {
            "partial_tp1_pct": 0.008,
            "partial_tp2_pct": 0.015,
            "fast_tp1_pct": 0.005,
            "fast_tp2_pct": 0.012,
            "fast_tp1_close_ratio": 0.5,
        }
    }

    cases = [
        {
            "name": "normal_long_tp1",
            "symbol": "SIM_LONG_A",
            "position": {"markPrice": 101.0, "positionAmt": 2.0, "positionSide": "BOTH"},
            "entry_price": 100.0,
            "entry_mode": "NORMAL",
        },
        {
            "name": "fast_long_tp1",
            "symbol": "SIM_LONG_FAST",
            "position": {"markPrice": 100.7, "positionAmt": 2.0, "positionSide": "BOTH"},
            "entry_price": 100.0,
            "entry_mode": "FAST_LONG",
        },
        {
            "name": "normal_short_tp1",
            "symbol": "SIM_SHORT_A",
            "position": {"markPrice": 98.8, "positionAmt": -3.0, "positionSide": "BOTH"},
            "entry_price": 100.0,
            "entry_mode": "NORMAL",
        },
        {
            "name": "fast_short_tp1",
            "symbol": "SIM_SHORT_FAST",
            "position": {"markPrice": 99.3, "positionAmt": -3.0, "positionSide": "BOTH"},
            "entry_price": 100.0,
            "entry_mode": "FAST_SHORT",
        },
    ]

    for case in cases:
        symbol = case["symbol"]
        manager.clear_position_management_state(symbol)
        executed = manager.check_partial_take_profit(
            symbol=symbol,
            position=case["position"],
            entry_price=case["entry_price"],
            strategy_config=strategy_config,
            entry_mode=case["entry_mode"],
        )
        trailing_updated = manager.update_trailing_stop(
            symbol=symbol,
            position=case["position"],
            entry_price=case["entry_price"],
            trail_pct=0.01,
        )
        payload["partial_tp_cases"].append(
            {
                "name": case["name"],
                "executed": executed,
                "profit_pct": round(
                    manager.get_position_profit_pct(case["position"], case["entry_price"]),
                    6,
                ),
                "state": dict(manager.get_position_management_state(symbol)),
                "trailing_updated": trailing_updated,
                "managed_stop_price": manager.managed_stop_prices.get(symbol),
            }
        )


def main():
    payload = {
        "started_at": now_iso(),
        "completed_at": None,
        "status": "running",
        "environment": "https://demo-fapi.binance.com",
        "errors": [],
        "short_lifecycle": {},
        "partial_tp_cases": [],
        "system_errors": None,
    }
    write_json(payload)

    runtime = None
    try:
        runtime = TradingRuntime()
        if not runtime.initialized:
            raise RuntimeError("TradingRuntime failed to initialize")

        run_short_lifecycle(runtime, payload)
        run_partial_tp_cases(runtime, payload)
        payload["status"] = "completed"
    except Exception as exc:
        payload["status"] = "failed"
        payload["errors"].append(str(exc))
    finally:
        try:
            if runtime is not None:
                cleanup_symbol(runtime, "BTCUSDT")
                payload["system_errors"] = len(runtime.trading_results.get("system_errors", []))
        except Exception:
            pass
        payload["completed_at"] = now_iso()
        write_json(payload)
        write_report(payload)


if __name__ == "__main__":
    main()
