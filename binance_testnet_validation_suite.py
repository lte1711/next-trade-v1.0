import json
import subprocess
import time
from datetime import datetime
from decimal import Decimal, ROUND_UP
from pathlib import Path

import requests

from main_runtime import TradingRuntime


RESULT_JSON = Path("binance_testnet_validation_results.json")
RESULT_MD = Path("BINANCE_TESTNET_VALIDATION_REPORT.md")
BACKGROUND_STATUS = Path("background_probe_status.json")


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


def write_markdown(payload):
    lines = [
        "# Binance Testnet Validation Report",
        "",
        f"Generated: {payload['generated_at']}",
        f"Environment: `{payload.get('environment')}`",
        "",
        "## Overall",
        f"- Success: `{payload.get('success')}`",
        f"- Failed Phases: `{', '.join(payload.get('failed_phases', [])) or 'None'}`",
        "",
        "## Phase Summary",
    ]
    for phase in payload.get("phases", []):
        lines.append(f"- `{phase['name']}`: `{phase['status']}`")
        if phase.get("summary"):
            lines.append(f"  Summary: {phase['summary']}")
    lines.extend(
        [
            "",
            "## Next Evolution Targets",
        ]
    )
    for item in payload.get("next_evolution_targets", []):
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Notes",
        ]
    )
    for item in payload.get("notes", []):
        lines.append(f"- {item}")

    RESULT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def phase_record(name):
    return {
        "name": name,
        "status": "pending",
        "started_at": now_iso(),
        "finished_at": None,
        "summary": "",
        "details": {},
        "errors": [],
    }


def finish_phase(phase, status, summary):
    phase["status"] = status
    phase["summary"] = summary
    phase["finished_at"] = now_iso()


def fetch_current_price(runtime, symbol):
    response = requests.get(
        f"{runtime.base_url}/fapi/v1/ticker/price",
        params={"symbol": symbol},
        timeout=10,
    )
    response.raise_for_status()
    price = float(response.json()["price"])
    runtime.trading_results.setdefault("market_data", {})[symbol] = price
    return price


def poll_order_status(runtime, symbol, order_id, attempts=10, delay=1.0):
    last = None
    for _ in range(attempts):
        last = runtime.get_order_status(symbol, order_id)
        if last and last.get("status") in {
            "FILLED",
            "CANCELED",
            "REJECTED",
            "EXPIRED",
            "PARTIALLY_FILLED",
            "NEW",
        }:
            if last.get("status") != "NEW":
                return last
        time.sleep(delay)
    return last


def cleanup_symbol_position(runtime, symbol):
    runtime.account_service.periodic_sync(runtime.trading_results)
    position = runtime.trading_results.get("active_positions", {}).get(symbol)
    if not position:
        return {"had_position": False, "closed": True}

    amount = safe_float(position.get("amount"), 0.0)
    if amount == 0:
        return {"had_position": False, "closed": True}

    fetch_current_price(runtime, symbol)
    side = "SELL" if amount > 0 else "BUY"
    result = runtime.order_executor.submit_order(
        strategy_name="validation_cleanup",
        symbol=symbol,
        side=side,
        quantity=abs(amount),
        reduce_only=True,
        metadata={
            "cleanup": True,
            "entry_price": safe_float(position.get("entry_price"), 0.0),
        },
    )
    return {
        "had_position": True,
        "closed": bool(result),
        "result": result,
    }


def run_suite():
    results = {
        "generated_at": now_iso(),
        "environment": "https://demo-fapi.binance.com",
        "success": False,
        "failed_phases": [],
        "phases": [],
        "next_evolution_targets": [],
        "notes": [],
    }

    runtime = None

    # Phase 1
    phase = phase_record("initialization")
    results["phases"].append(phase)
    try:
        runtime = TradingRuntime()
        phase["details"] = {
            "initialized": getattr(runtime, "initialized", False),
            "base_url": getattr(runtime, "base_url", None),
            "capital": getattr(runtime, "total_capital", None),
            "valid_symbol_count": len(getattr(runtime, "valid_symbols", []) or []),
            "active_strategies": list(getattr(runtime, "active_strategies", []) or []),
            "system_errors": len(runtime.trading_results.get("system_errors", [])),
        }
        if runtime.initialized:
            finish_phase(phase, "passed", "Runtime initialized successfully.")
        else:
            phase["errors"].append("TradingRuntime failed to initialize.")
            finish_phase(phase, "failed", "Runtime initialization failed.")
    except Exception as exc:
        phase["errors"].append(str(exc))
        finish_phase(phase, "failed", "Runtime initialization raised an exception.")

    if not runtime or not runtime.initialized:
        results["failed_phases"].append("initialization")
        results["next_evolution_targets"].append("Fix runtime initialization path before further testnet execution.")
        write_json(results)
        write_markdown(results)
        return results

    # Phase 2
    phase = phase_record("trading_cycle")
    results["phases"].append(phase)
    try:
        cycle = runtime.trade_orchestrator.run_trading_cycle(
            runtime.valid_symbols[:10],
            runtime.active_strategies,
        )
        phase["details"] = cycle
        if not cycle.get("errors"):
            finish_phase(
                phase,
                "passed",
                f"Cycle completed with {cycle.get('signals_generated', 0)} signals and {cycle.get('trades_executed', 0)} trades.",
            )
        else:
            finish_phase(phase, "failed", "Cycle returned runtime errors.")
    except Exception as exc:
        phase["errors"].append(str(exc))
        finish_phase(phase, "failed", "Cycle execution raised an exception.")

    # Phase 3
    phase = phase_record("order_status_polling")
    results["phases"].append(phase)
    try:
        symbol = "BTCUSDT"
        info = runtime.get_symbol_info(symbol)
        current_price = Decimal(str(fetch_current_price(runtime, symbol)))
        tick_size = Decimal("0.1")
        step_size = Decimal("0.001")
        min_qty = Decimal("0.001")
        min_notional = Decimal("5")
        price_precision = int(info.get("pricePrecision", 2))
        qty_precision = int(info.get("quantityPrecision", 3))

        for filt in info.get("filters", []):
            if filt.get("filterType") == "PRICE_FILTER":
                tick_size = Decimal(str(filt.get("tickSize", tick_size)))
            elif filt.get("filterType") == "LOT_SIZE":
                step_size = Decimal(str(filt.get("stepSize", step_size)))
                min_qty = Decimal(str(filt.get("minQty", min_qty)))
            elif filt.get("filterType") == "MIN_NOTIONAL" and filt.get("notional"):
                min_notional = Decimal(str(filt["notional"]))
            elif filt.get("filterType") == "NOTIONAL" and filt.get("minNotional"):
                min_notional = Decimal(str(filt["minNotional"]))

        limit_price = Decimal(str(round_to_step(current_price * Decimal("0.50"), tick_size, ROUND_UP)))
        target_notional = max(min_notional * Decimal("1.10"), Decimal("6"))
        quantity = max(
            round_to_step(target_notional / limit_price, step_size, ROUND_UP),
            float(min_qty),
        )

        server_time = runtime.order_executor.get_server_time()
        timestamp = int(server_time) - 100
        params = {
            "symbol": symbol,
            "side": "BUY",
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": f"{quantity:.{qty_precision}f}",
            "price": f"{float(limit_price):.{price_precision}f}",
            "timestamp": timestamp,
            "recvWindow": runtime.recv_window,
        }
        query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
        import hmac
        import hashlib

        signature = hmac.new(
            runtime.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        response = requests.post(
            f"{runtime.base_url}/fapi/v1/order?{query_string}&signature={signature}",
            headers={"X-MBX-APIKEY": runtime.api_key},
            timeout=15,
        )
        response.raise_for_status()
        placed = response.json()
        order_id = placed.get("orderId")
        polled = runtime.get_order_status(symbol, order_id)
        cancelled = runtime.cancel_order(symbol, order_id)
        final_polled = runtime.get_order_status(symbol, order_id)
        phase["details"] = {
            "symbol": symbol,
            "order_id": order_id,
            "placement_status": placed.get("status"),
            "polled_status": polled.get("status") if polled else None,
            "cancelled": cancelled,
            "final_status": final_polled.get("status") if final_polled else None,
        }
        if cancelled and final_polled and final_polled.get("status") == "CANCELED":
            finish_phase(phase, "passed", "Known order polling and cancel flow succeeded.")
        else:
            finish_phase(phase, "failed", "Order polling or cancel flow was inconsistent.")
    except Exception as exc:
        phase["errors"].append(str(exc))
        finish_phase(phase, "failed", "Order polling phase raised an exception.")

    # Phase 4
    phase = phase_record("protective_orders_and_reduce_only_close")
    results["phases"].append(phase)
    try:
        symbol = "BTCUSDT"
        cleanup_before = cleanup_symbol_position(runtime, symbol)
        current_price = Decimal(str(fetch_current_price(runtime, symbol)))
        info = runtime.get_symbol_info(symbol)
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

        quantity = max(
            round_to_step((min_notional * Decimal("1.10")) / current_price, step_size, ROUND_UP),
            float(min_qty),
        )

        entry = runtime.order_executor.submit_order(
            strategy_name="ma_trend_follow",
            symbol=symbol,
            side="BUY",
            quantity=quantity,
            reduce_only=False,
            metadata={"validation_suite": True},
        )
        if not entry:
            raise RuntimeError("Entry order returned None")
        entry_status = poll_order_status(runtime, symbol, entry.get("orderId"))
        entry_price = safe_float((entry_status or entry).get("avgPrice"), safe_float(current_price))
        if entry_price <= 0:
            entry_price = safe_float(current_price)
        executed_qty = safe_float((entry_status or entry).get("executedQty"), quantity)
        if executed_qty <= 0:
            executed_qty = quantity

        stop_result = runtime.protective_order_manager.submit_protective_order(
            symbol, "SELL", "STOP_MARKET", round(entry_price * (1 - 0.02), 2)
        )
        take_result = runtime.protective_order_manager.submit_protective_order(
            symbol, "SELL", "TAKE_PROFIT_MARKET", round(entry_price * (1 + 0.04), 2)
        )
        time.sleep(2)
        open_algo_orders = runtime.protective_order_manager.get_open_orders(symbol)

        close_result = runtime.order_executor.submit_order(
            strategy_name="ma_trend_follow",
            symbol=symbol,
            side="SELL",
            quantity=executed_qty,
            reduce_only=True,
            metadata={"entry_price": entry_price, "validation_suite": True},
        )
        close_status = poll_order_status(runtime, symbol, close_result.get("orderId")) if close_result else None
        runtime.protective_order_manager.cancel_symbol_protective_orders(symbol)
        remaining_open = runtime.protective_order_manager.get_open_orders(symbol)

        reduce_only_recorded = any(
            str(order.get("order_id")) == str(close_result.get("orderId"))
            and order.get("reduce_only")
            for order in runtime.trading_results.get("real_orders", [])
        )

        phase["details"] = {
            "cleanup_before": cleanup_before,
            "entry_order_id": entry.get("orderId"),
            "entry_status": entry_status.get("status") if entry_status else entry.get("status"),
            "stop_algo_id": stop_result.get("algoId") if isinstance(stop_result, dict) else None,
            "take_algo_id": take_result.get("algoId") if isinstance(take_result, dict) else None,
            "open_algo_order_count": len(open_algo_orders),
            "close_order_id": close_result.get("orderId") if close_result else None,
            "close_status": close_status.get("status") if close_status else None,
            "reduce_only_recorded": reduce_only_recorded,
            "remaining_open_algo_orders": len(remaining_open),
        }
        if (
            stop_result
            and take_result
            and len(open_algo_orders) >= 2
            and close_status
            and close_status.get("status") == "FILLED"
            and reduce_only_recorded
            and len(remaining_open) == 0
        ):
            finish_phase(phase, "passed", "Protective algo orders and reduce-only close path succeeded.")
        else:
            finish_phase(phase, "failed", "Protective order or reduce-only close validation failed.")
    except Exception as exc:
        phase["errors"].append(str(exc))
        finish_phase(phase, "failed", "Protective order validation raised an exception.")
    finally:
        try:
            cleanup_symbol_position(runtime, "BTCUSDT")
            runtime.protective_order_manager.cancel_symbol_protective_orders("BTCUSDT")
        except Exception:
            pass

    # Phase 5
    phase = phase_record("background_probe")
    results["phases"].append(phase)
    try:
        if BACKGROUND_STATUS.exists():
            BACKGROUND_STATUS.unlink()
        proc = subprocess.Popen(
            [str(Path(".venv") / "Scripts" / "python.exe"), "background_supervised_probe.py"],
            cwd=str(Path.cwd()),
        )
        deadline = time.time() + 8 * 60
        background_payload = None
        while time.time() < deadline:
            if BACKGROUND_STATUS.exists():
                try:
                    background_payload = json.loads(BACKGROUND_STATUS.read_text(encoding="utf-8"))
                    if background_payload.get("status") in {"completed", "init_failed"}:
                        break
                except Exception:
                    pass
            time.sleep(5)
        proc.wait(timeout=30)
        phase["details"] = background_payload or {}
        if background_payload and background_payload.get("status") == "completed":
            finish_phase(
                phase,
                "passed",
                f"Background probe completed {len(background_payload.get('cycles', []))} cycles with no phase errors.",
            )
        else:
            finish_phase(phase, "failed", "Background probe did not complete successfully.")
    except Exception as exc:
        phase["errors"].append(str(exc))
        finish_phase(phase, "failed", "Background probe raised an exception.")

    # Final rollup
    for phase in results["phases"]:
        if phase["status"] != "passed":
            results["failed_phases"].append(phase["name"])

    results["success"] = not results["failed_phases"]

    if runtime:
        results["notes"].append(
            f"Final system_errors count during suite runtime: {len(runtime.trading_results.get('system_errors', []))}"
        )

    if results["success"]:
        results["next_evolution_targets"].append("Run a longer supervised demo session to capture multi-hour runtime behavior.")
        results["next_evolution_targets"].append("Exercise more real non-HOLD trading scenarios to validate broader strategy behavior.")
        results["next_evolution_targets"].append("Unify partial take profit stop tracking with trading_results managed_stop_prices.")
    else:
        results["next_evolution_targets"].append("Resolve failed phases before extending runtime duration.")

    write_json(results)
    write_markdown(results)
    return results


if __name__ == "__main__":
    suite_results = run_suite()
    print(json.dumps(suite_results, ensure_ascii=False, indent=2, default=str))
