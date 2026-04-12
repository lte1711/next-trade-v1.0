import hashlib
import hmac
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_DOWN
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from main_runtime import TradingRuntime


KST = timezone(timedelta(hours=9))


def to_decimal(value: object, default: str = "0") -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


def decimal_places(value: Decimal) -> int:
    normalized = value.normalize()
    return max(0, -normalized.as_tuple().exponent)


def round_to_step(value: Decimal, step: Decimal) -> Decimal:
    if step <= 0:
        return value
    return (value / step).to_integral_value(rounding=ROUND_DOWN) * step


def signed_request(runtime: TradingRuntime, method: str, path: str, params: dict | None = None):
    params = dict(params or {})
    server_time = runtime.order_executor.get_server_time()
    if not server_time:
        raise RuntimeError("server_time_unavailable")
    params["timestamp"] = int(server_time) - 100
    params["recvWindow"] = getattr(runtime.order_executor, "recv_window", 5000)
    query = "&".join(f"{key}={value}" for key, value in sorted(params.items()))
    signature = hmac.new(
        runtime.api_secret.encode("utf-8"),
        query.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    url = f"{runtime.base_url}{path}?{query}&signature={signature}"
    headers = {"X-MBX-APIKEY": runtime.api_key}
    response = requests.request(method, url, headers=headers, timeout=15)
    if response.status_code != 200:
        raise RuntimeError(f"{method} {path} failed: {response.status_code} {response.text}")
    return response.json()


def get_step_size(runtime: TradingRuntime, symbol: str) -> Decimal:
    info = runtime.get_symbol_info(symbol) or {}
    filters = {item.get("filterType"): item for item in info.get("filters", [])}
    return to_decimal(filters.get("LOT_SIZE", {}).get("stepSize", "1"), "1")


def nonzero_exchange_positions(runtime: TradingRuntime) -> list[dict]:
    positions = signed_request(runtime, "GET", "/fapi/v2/positionRisk", {})
    active = []
    for position in positions:
        amount = to_decimal(position.get("positionAmt"))
        if amount == 0:
            continue
        active.append(position)
    return active


def cancel_all_open_orders(runtime: TradingRuntime) -> dict:
    open_orders = signed_request(runtime, "GET", "/fapi/v1/openOrders", {})
    symbols = sorted({order.get("symbol") for order in open_orders if order.get("symbol")})
    results = []
    for symbol in symbols:
        try:
            result = signed_request(runtime, "DELETE", "/fapi/v1/allOpenOrders", {"symbol": symbol})
            results.append({"symbol": symbol, "cancelled": True, "result": result})
        except Exception as exc:
            results.append({"symbol": symbol, "cancelled": False, "error": str(exc)})
        time.sleep(0.2)
    return {"open_orders_before": open_orders, "cancel_results": results}


def close_all_positions(runtime: TradingRuntime) -> dict:
    positions_before = nonzero_exchange_positions(runtime)
    close_results = []
    for position in positions_before:
        symbol = position.get("symbol")
        amount = to_decimal(position.get("positionAmt"))
        if not symbol or amount == 0:
            continue
        step = get_step_size(runtime, symbol)
        quantity = round_to_step(abs(amount), step)
        if quantity <= 0:
            close_results.append({
                "symbol": symbol,
                "closed": False,
                "error": "rounded_quantity_zero",
                "positionAmt": str(amount),
            })
            continue
        side = "SELL" if amount > 0 else "BUY"
        qty_precision = decimal_places(step)
        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": f"{quantity:.{qty_precision}f}",
            "reduceOnly": "true",
        }
        position_side = position.get("positionSide")
        if position_side and position_side != "BOTH":
            params["positionSide"] = position_side
        try:
            result = signed_request(runtime, "POST", "/fapi/v1/order", params)
            close_results.append({
                "symbol": symbol,
                "closed": True,
                "side": side,
                "quantity": params["quantity"],
                "positionAmt": str(amount),
                "positionSide": position_side,
                "result": result,
            })
        except Exception as exc:
            close_results.append({
                "symbol": symbol,
                "closed": False,
                "side": side,
                "quantity": params["quantity"],
                "positionAmt": str(amount),
                "positionSide": position_side,
                "error": str(exc),
            })
        time.sleep(0.5)

    time.sleep(3)
    positions_after = nonzero_exchange_positions(runtime)
    return {
        "positions_before": positions_before,
        "close_results": close_results,
        "positions_after": positions_after,
    }


def main() -> int:
    started = datetime.now(KST)
    runtime = TradingRuntime()
    if not runtime.initialized:
        raise RuntimeError("runtime_not_initialized")
    if "demo-fapi.binance.com" not in runtime.base_url:
        raise RuntimeError(f"refusing_non_testnet_base_url:{runtime.base_url}")

    reports_root = REPO_ROOT / "reports" / "2026-04-10" / "entry_cross_gate_validation"
    latest_pointer = REPO_ROOT / "reports" / "latest_entry_cross_gate_validation.txt"
    if latest_pointer.exists():
        latest_path = latest_pointer.read_text(encoding="utf-8-sig").strip().lstrip("\ufeff")
        output_dir = Path(latest_path)
    else:
        output_dir = reports_root / started.strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)

    cancel_summary = cancel_all_open_orders(runtime)
    close_summary = close_all_positions(runtime)
    cancel_after_close = cancel_all_open_orders(runtime)
    runtime.sync_positions()
    open_orders_after = signed_request(runtime, "GET", "/fapi/v1/openOrders", {})
    positions_final = nonzero_exchange_positions(runtime)

    evidence = {
        "mode": "close_all_testnet_exchange_state",
        "started_at": started.isoformat(),
        "finished_at": datetime.now(KST).isoformat(),
        "base_url": runtime.base_url,
        "execution_mode": getattr(runtime, "execution_mode", None),
        "cancel_before_close": cancel_summary,
        "close_summary": close_summary,
        "cancel_after_close": cancel_after_close,
        "open_orders_after": open_orders_after,
        "positions_final": positions_final,
        "remaining_open_order_count": len(open_orders_after),
        "remaining_position_count": len(positions_final),
        "active_symbols_after_runtime_sync": sorted(runtime.trading_results.get("active_positions", {})),
        "available_balance_after_sync": runtime.trading_results.get("available_balance"),
        "system_errors": runtime.trading_results.get("system_errors", []),
    }

    out_path = output_dir / "exchange_full_shutdown_evidence.json"
    out_path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps({"output_path": str(out_path), **evidence}, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
