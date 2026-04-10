import json
import time
from pathlib import Path

from main_runtime import TradingRuntime
from scenario_forced_entry_validation import (
    cleanup_symbol,
    enrich_active_position,
    fetch_price,
    force_sync_positions,
    get_min_trade_quantity,
    now_iso,
    poll_order,
    safe_float,
)


RESULT_JSON = Path("live_stop_tightening_probe_short.json")
RESULT_MD = Path("LIVE_STOP_TIGHTENING_PROBE_SHORT_REPORT.md")


def write_json(payload):
    RESULT_JSON.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def write_report(payload):
    lines = [
        "# Live Stop Tightening Probe Short Report",
        "",
        f"Generated: {payload.get('completed_at') or payload.get('started_at')}",
        f"Environment: `{payload.get('environment')}`",
        f"Status: `{payload.get('status')}`",
        "",
        "## Summary",
        f"- Symbol: `{payload.get('symbol')}`",
        f"- Entry Order: `{payload.get('entry_order_id')}`",
        f"- Close Order: `{payload.get('close_order_id')}`",
        f"- Stop Tightened: `{payload.get('stop_tightened')}`",
        f"- System Errors: `{payload.get('system_errors')}`",
        "",
        "## Snapshots",
    ]

    for snap in payload.get("snapshots", []):
        lines.append(
            "- "
            f"{snap.get('label')}: "
            f"active_amount={snap.get('active_amount')}, "
            f"managed_stop={snap.get('managed_stop_price')}, "
            f"stop_algo_id={snap.get('stop_algo_id')}, "
            f"take_algo_id={snap.get('take_algo_id')}, "
            f"open_algo_orders={snap.get('open_algo_order_count')}"
        )

    if payload.get("next_evolution_targets"):
        lines.extend(["", "## Next Evolution Targets"])
        for item in payload["next_evolution_targets"]:
            lines.append(f"- {item}")

    RESULT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def snapshot(runtime, payload, label, symbol):
    force_sync_positions(runtime)
    position = runtime.trading_results.get("active_positions", {}).get(symbol)
    open_orders = runtime.protective_order_manager.get_open_orders(symbol)
    stop_order = next((o for o in open_orders if (o.get("orderType") or o.get("type")) == "STOP_MARKET"), None)
    take_order = next((o for o in open_orders if (o.get("orderType") or o.get("type")) == "TAKE_PROFIT_MARKET"), None)
    payload["snapshots"].append(
        {
            "label": label,
            "timestamp": now_iso(),
            "active_amount": safe_float(position.get("amount"), 0.0) if position else 0.0,
            "entry_price": safe_float(position.get("entry_price"), 0.0) if position else 0.0,
            "current_price": safe_float(position.get("current_price"), 0.0) if position else 0.0,
            "managed_stop_price": runtime.trading_results.get("managed_stop_prices", {}).get(symbol),
            "open_algo_order_count": len(open_orders),
            "stop_algo_id": (stop_order or {}).get("algoId"),
            "stop_trigger_price": (stop_order or {}).get("triggerPrice"),
            "take_algo_id": (take_order or {}).get("algoId"),
            "take_trigger_price": (take_order or {}).get("triggerPrice"),
        }
    )
    write_json(payload)


def main():
    payload = {
        "started_at": now_iso(),
        "completed_at": None,
        "status": "running",
        "environment": "https://demo-fapi.binance.com",
        "symbol": "BTCUSDT",
        "snapshots": [],
        "stop_tightened": False,
        "next_evolution_targets": [],
    }
    write_json(payload)

    runtime = None
    symbol = payload["symbol"]
    strategy_name = "ma_trend_follow"

    try:
        runtime = TradingRuntime()
        if not runtime.initialized:
            raise RuntimeError("TradingRuntime failed to initialize")

        cleanup_symbol(runtime, symbol)
        snapshot(runtime, payload, "before_entry", symbol)

        quantity = get_min_trade_quantity(runtime, symbol, target_notional=6.5)
        entry = runtime.order_executor.submit_order(
            strategy_name=strategy_name,
            symbol=symbol,
            side="SELL",
            quantity=quantity,
            reduce_only=False,
            metadata={"live_stop_tightening_probe_short": True},
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
        enrich_active_position(runtime, symbol, strategy_name, entry_price, -abs(executed_qty), entry_time)
        runtime.trading_results["active_positions"][symbol]["amount"] = -abs(
            safe_float(runtime.trading_results["active_positions"][symbol].get("amount"), executed_qty)
        )
        payload["entry_order_id"] = entry.get("orderId")

        runtime.protective_order_manager.place_protective_orders(strategy_name, symbol, "SELL", entry_price)
        time.sleep(2)
        snapshot(runtime, payload, "after_initial_protective_orders", symbol)

        position = runtime.trading_results.get("active_positions", {}).get(symbol, {})
        if not position:
            raise RuntimeError("Active position missing before stop tightening")

        actual_market_price = fetch_price(runtime, symbol)
        position["current_price"] = actual_market_price
        initial_managed_stop = runtime.trading_results.get("managed_stop_prices", {}).get(symbol)
        if not initial_managed_stop:
            raise RuntimeError("Initial managed stop price missing before tightening")

        # For shorts, tighten by lowering stop while keeping it above the actual market price.
        target_stop_price = min(
            initial_managed_stop,
            actual_market_price * 1.005,
        )
        if target_stop_price <= actual_market_price:
            target_stop_price = actual_market_price * 1.01

        tightened = runtime.protective_order_manager.update_stop_loss(
            symbol=symbol,
            new_stop_price=target_stop_price,
            amount=position.get("amount", 0.0),
        )
        payload["stop_tightened"] = bool(tightened)
        time.sleep(2)
        snapshot(runtime, payload, "after_stop_tightening", symbol)

        before = next(s for s in payload["snapshots"] if s["label"] == "after_initial_protective_orders")
        after = next(s for s in payload["snapshots"] if s["label"] == "after_stop_tightening")
        payload["initial_stop_algo_id"] = before.get("stop_algo_id")
        payload["tightened_stop_algo_id"] = after.get("stop_algo_id")
        payload["initial_stop_price"] = before.get("managed_stop_price")
        payload["tightened_stop_price"] = after.get("managed_stop_price")
        payload["actual_market_price_before_tightening"] = actual_market_price

        close_result = runtime.order_executor.submit_order(
            strategy_name=strategy_name,
            symbol=symbol,
            side="BUY",
            quantity=executed_qty,
            reduce_only=True,
            metadata={"entry_price": entry_price, "live_stop_tightening_probe_short": True},
        )
        if close_result:
            close_status = poll_order(runtime, symbol, close_result.get("orderId"))
            payload["close_order_id"] = close_result.get("orderId")
            payload["close_status"] = close_status.get("status") if close_status else None

        runtime.protective_order_manager.cancel_symbol_protective_orders(symbol)
        force_sync_positions(runtime)
        runtime.pending_order_manager.refresh_pending_orders()
        snapshot(runtime, payload, "after_cleanup", symbol)

        payload["status"] = "completed"
        payload["next_evolution_targets"] = [
            "Drive short-side stop tightening from real profit observations instead of injected current_price values.",
            "Promote long/short live stop-tightening probes into the final pre-run gate."
        ]
    except Exception as exc:
        payload["status"] = "failed"
        payload["error"] = str(exc)
    finally:
        try:
            if runtime is not None:
                cleanup_symbol(runtime, symbol)
                payload["system_errors"] = len(runtime.trading_results.get("system_errors", []))
        except Exception:
            pass
        payload["completed_at"] = now_iso()
        write_json(payload)
        write_report(payload)


if __name__ == "__main__":
    main()
