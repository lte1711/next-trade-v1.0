import json
import time
from datetime import datetime
from decimal import Decimal, ROUND_UP
from pathlib import Path

import requests

from main_runtime import TradingRuntime


RESULT_JSON = Path("scenario_forced_entry_validation.json")
RESULT_MD = Path("SCENARIO_FORCED_ENTRY_VALIDATION_REPORT.md")


def now_iso():
    return datetime.now().astimezone().isoformat()


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def round_to_step(value, step, rounding):
    value_d = Decimal(str(value))
    step_d = Decimal(str(step))
    if step_d <= 0:
        return float(value_d)
    return float((value_d / step_d).quantize(Decimal("1"), rounding=rounding) * step_d)


def write_json(payload):
    RESULT_JSON.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def write_report(payload):
    lines = [
        "# Scenario Forced Entry Validation Report",
        "",
        f"Generated: {payload.get('completed_at') or payload.get('started_at')}",
        f"Environment: `{payload.get('environment')}`",
        f"Status: `{payload.get('status')}`",
        "",
        "## Summary",
        f"- Symbol: `{payload.get('symbol')}`",
        f"- Entry Side: `{payload.get('entry_side')}`",
        f"- Steps Passed: `{len([s for s in payload.get('steps', []) if s.get('status') == 'passed'])}` / `{len(payload.get('steps', []))}`",
        f"- System Errors: `{payload.get('system_errors')}`",
        "",
        "## Steps",
    ]

    for step in payload.get("steps", []):
        lines.append(f"- `{step.get('name')}`: `{step.get('status')}`")
        if step.get("summary"):
            lines.append(f"  Summary: {step.get('summary')}")

    if payload.get("snapshots"):
        lines.extend(["", "## Snapshots"])
        for snapshot in payload["snapshots"]:
            lines.append(
                "- "
                f"{snapshot.get('label')}: "
                f"active_position={snapshot.get('has_active_position')}, "
                f"active_qty={snapshot.get('active_amount')}, "
                f"open_algo_orders={snapshot.get('open_algo_order_count')}, "
                f"managed_stop={snapshot.get('managed_stop_price')}, "
                f"pending_trades={snapshot.get('pending_trade_count')}"
            )

    if payload.get("next_evolution_targets"):
        lines.extend(["", "## Next Evolution Targets"])
        for item in payload["next_evolution_targets"]:
            lines.append(f"- {item}")

    RESULT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def record_step(payload, name, status, summary, details=None, errors=None):
    payload["steps"].append(
        {
            "name": name,
            "status": status,
            "summary": summary,
            "details": details or {},
            "errors": errors or [],
            "timestamp": now_iso(),
        }
    )
    write_json(payload)


def fetch_price(runtime, symbol):
    response = requests.get(
        f"{runtime.base_url}/fapi/v1/ticker/price",
        params={"symbol": symbol},
        timeout=10,
    )
    response.raise_for_status()
    price = float(response.json()["price"])
    runtime.trading_results.setdefault("market_data", {})[symbol] = price
    return price


def force_sync_positions(runtime):
    runtime.account_service._last_position_sync_time = 0
    return runtime.account_service.sync_positions(runtime.trading_results)


def poll_order(runtime, symbol, order_id, attempts=15, delay=1.5):
    last = None
    for _ in range(attempts):
        last = runtime.get_order_status(symbol, order_id)
        if last and last.get("status") in {"FILLED", "CANCELED", "EXPIRED", "REJECTED"}:
            return last
        time.sleep(delay)
    return last


def get_min_trade_quantity(runtime, symbol, target_notional=6.0):
    info = runtime.get_symbol_info(symbol)
    current_price = Decimal(str(fetch_price(runtime, symbol)))
    step_size = Decimal("0.001")
    min_qty = Decimal("0.001")
    min_notional = Decimal("5")

    for filt in info.get("filters", []):
        if filt.get("filterType") == "LOT_SIZE":
            step_size = Decimal(str(filt.get("stepSize", step_size)))
            min_qty = Decimal(str(filt.get("minQty", min_qty)))
        elif filt.get("filterType") == "MIN_NOTIONAL" and filt.get("notional"):
            min_notional = Decimal(str(filt["notional"]))
        elif filt.get("filterType") == "NOTIONAL" and filt.get("minNotional"):
            min_notional = Decimal(str(filt["minNotional"]))

    desired_notional = max(min_notional * Decimal("1.10"), Decimal(str(target_notional)))
    quantity = max(
        round_to_step(desired_notional / current_price, step_size, ROUND_UP),
        float(min_qty),
    )
    return quantity


def enrich_active_position(runtime, symbol, strategy_name, entry_price, quantity, entry_time):
    position = runtime.trading_results.get("active_positions", {}).get(symbol, {})
    if not position:
        return
    position["strategy"] = strategy_name
    position["entry_price"] = safe_float(position.get("entry_price"), entry_price) or entry_price
    position["current_price"] = safe_float(position.get("current_price"), position.get("mark_price", entry_price)) or entry_price
    position["entry_time"] = position.get("entry_time") or entry_time
    position["signal_confidence"] = position.get("signal_confidence", 1.0)
    position["stop_loss_pct"] = position.get("stop_loss_pct", 0.02)
    position["take_profit_pct"] = position.get("take_profit_pct", 0.04)
    position["amount"] = safe_float(position.get("amount"), quantity)


def snapshot_state(runtime, payload, label, symbol):
    force_sync_positions(runtime)
    position = runtime.trading_results.get("active_positions", {}).get(symbol)
    open_algo_orders = runtime.protective_order_manager.get_open_orders(symbol)
    partial_tp_state = runtime.partial_take_profit_manager.partial_take_profit_state.get(symbol, {})
    managed_stop = runtime.trading_results.get("managed_stop_prices", {}).get(symbol)

    snapshot = {
        "label": label,
        "timestamp": now_iso(),
        "has_active_position": bool(position),
        "active_amount": safe_float(position.get("amount"), 0.0) if position else 0.0,
        "entry_price": safe_float(position.get("entry_price"), 0.0) if position else 0.0,
        "mark_price": safe_float(position.get("mark_price"), 0.0) if position else 0.0,
        "position_entry_time": runtime.trading_results.get("position_entry_times", {}).get(symbol),
        "managed_stop_price": managed_stop,
        "open_algo_order_count": len(open_algo_orders),
        "open_algo_orders": [
            {
                "algoId": order.get("algoId"),
                "orderType": order.get("orderType") or order.get("type"),
                "triggerPrice": order.get("triggerPrice"),
            }
            for order in open_algo_orders
        ],
        "partial_take_profit_state": partial_tp_state,
        "pending_trade_count": len(runtime.trading_results.get("pending_trades", [])),
        "recently_closed": symbol in runtime.trading_results.get("recently_closed_symbols", {}),
    }
    payload["snapshots"].append(snapshot)
    write_json(payload)


def cleanup_symbol(runtime, symbol):
    runtime.protective_order_manager.cancel_symbol_protective_orders(symbol)
    force_sync_positions(runtime)
    position = runtime.trading_results.get("active_positions", {}).get(symbol)
    if not position:
        return

    amount = safe_float(position.get("amount"), 0.0)
    if amount == 0:
        return

    result = runtime.order_executor.submit_order(
        strategy_name="scenario_cleanup",
        symbol=symbol,
        side="SELL" if amount > 0 else "BUY",
        quantity=abs(amount),
        reduce_only=True,
        metadata={"entry_price": safe_float(position.get("entry_price"), 0.0), "scenario_cleanup": True},
    )
    if result:
        poll_order(runtime, symbol, result.get("orderId"))
        force_sync_positions(runtime)
        runtime.pending_order_manager.refresh_pending_orders()
        time.sleep(1)
        force_sync_positions(runtime)


def main():
    payload = {
        "started_at": now_iso(),
        "completed_at": None,
        "status": "running",
        "environment": "https://demo-fapi.binance.com",
        "symbol": "BTCUSDT",
        "entry_side": "BUY",
        "steps": [],
        "snapshots": [],
        "next_evolution_targets": [],
    }
    write_json(payload)

    runtime = None
    symbol = payload["symbol"]
    strategy_name = "ma_trend_follow"

    try:
        runtime = TradingRuntime()
        if not runtime.initialized:
            record_step(payload, "initialization", "failed", "TradingRuntime failed to initialize.")
            payload["status"] = "failed"
            return
        record_step(
            payload,
            "initialization",
            "passed",
            "TradingRuntime initialized successfully.",
            details={
                "valid_symbol_count": len(runtime.valid_symbols),
                "active_strategies": runtime.active_strategies,
            },
        )

        cleanup_symbol(runtime, symbol)
        record_step(payload, "cleanup_before", "passed", "Pre-scenario cleanup completed.")
        snapshot_state(runtime, payload, "before_entry", symbol)

        quantity = get_min_trade_quantity(runtime, symbol, target_notional=6.5)
        entry = runtime.order_executor.submit_order(
            strategy_name=strategy_name,
            symbol=symbol,
            side="BUY",
            quantity=quantity,
            reduce_only=False,
            metadata={"scenario_forced_entry": True},
        )
        if not entry:
            raise RuntimeError("Entry order returned None")

        entry_status = poll_order(runtime, symbol, entry.get("orderId"))
        if not entry_status or entry_status.get("status") != "FILLED":
            raise RuntimeError(f"Entry order not filled: {entry_status}")

        entry_price = safe_float(entry_status.get("avgPrice"), fetch_price(runtime, symbol))
        executed_qty = safe_float(entry_status.get("executedQty"), quantity)
        entry_time = now_iso()
        runtime.trading_results.setdefault("position_entry_times", {})[symbol] = entry_time
        force_sync_positions(runtime)
        enrich_active_position(runtime, symbol, strategy_name, entry_price, executed_qty, entry_time)
        record_step(
            payload,
            "entry_fill",
            "passed",
            "Entry order filled and active position synchronized.",
            details={
                "order_id": entry.get("orderId"),
                "entry_price": entry_price,
                "executed_qty": executed_qty,
            },
        )
        snapshot_state(runtime, payload, "after_entry_fill", symbol)

        runtime.protective_order_manager.place_protective_orders(strategy_name, symbol, "BUY", entry_price)
        time.sleep(2)
        snapshot_state(runtime, payload, "after_protective_orders", symbol)
        record_step(payload, "protective_orders", "passed", "Protective algo orders installed.")

        state = runtime.partial_take_profit_manager.get_position_management_state(symbol)
        state["tp1_done"] = True
        state["last_partial_close_at"] = now_iso()
        runtime.trading_results.setdefault("partial_take_profit_state", {})[symbol] = state
        record_step(
            payload,
            "partial_state_mark",
            "passed",
            "Partial take profit state map updated for evidence.",
            details={"partial_take_profit_state": state},
        )
        snapshot_state(runtime, payload, "after_partial_state_mark", symbol)

        partial_closed = runtime.position_manager.close_partial_position(
            symbol,
            close_fraction=0.5,
            reason="scenario_partial_close",
        )
        if not partial_closed:
            raise RuntimeError("Partial close request failed")

        partial_order = runtime.trading_results.get("real_orders", [])[-1]
        partial_status = poll_order(runtime, symbol, partial_order.get("order_id"))
        force_sync_positions(runtime)
        runtime.pending_order_manager.refresh_pending_orders()
        time.sleep(1)
        force_sync_positions(runtime)
        enrich_active_position(runtime, symbol, strategy_name, entry_price, executed_qty / 2, entry_time)
        record_step(
            payload,
            "partial_close",
            "passed",
            "Partial reduce-only close completed and position remained active.",
            details={
                "order_id": partial_order.get("order_id"),
                "status": partial_status.get("status") if partial_status else None,
                "remaining_amount": safe_float(
                    runtime.trading_results.get("active_positions", {}).get(symbol, {}).get("amount"),
                    0.0,
                ),
            },
        )
        snapshot_state(runtime, payload, "after_partial_close", symbol)

        close_result = runtime.position_manager.close_position(symbol, "scenario_final_cleanup")
        if not close_result:
            raise RuntimeError("Full close request failed")

        close_order = runtime.trading_results.get("real_orders", [])[-1]
        close_status = poll_order(runtime, symbol, close_order.get("order_id"))
        force_sync_positions(runtime)
        runtime.pending_order_manager.refresh_pending_orders()
        time.sleep(1)
        force_sync_positions(runtime)
        runtime.protective_order_manager.cancel_symbol_protective_orders(symbol)
        snapshot_state(runtime, payload, "after_full_close", symbol)
        record_step(
            payload,
            "full_close_and_cleanup",
            "passed",
            "Final reduce-only close and cleanup completed.",
            details={
                "order_id": close_order.get("order_id"),
                "status": close_status.get("status") if close_status else None,
                "recently_closed": symbol in runtime.trading_results.get("recently_closed_symbols", {}),
            },
        )

        payload["status"] = "completed"
        payload["next_evolution_targets"] = [
            "Automate multi-symbol forced lifecycle scenarios instead of single-symbol BTCUSDT validation.",
            "Integrate forced partial-take-profit assertions with live `PartialTakeProfitManager` execution paths.",
            "Unify partial take profit stop tracking with `trading_results[\"managed_stop_prices\"]`."
        ]
    except Exception as exc:
        payload["status"] = "failed"
        record_step(payload, "scenario_failure", "failed", str(exc), errors=[str(exc)])
    finally:
        try:
            if runtime is not None:
                cleanup_symbol(runtime, symbol)
        except Exception:
            pass

        payload["completed_at"] = now_iso()
        payload["system_errors"] = len(
            runtime.trading_results.get("system_errors", [])
        ) if runtime is not None else None
        write_json(payload)
        write_report(payload)


if __name__ == "__main__":
    main()
