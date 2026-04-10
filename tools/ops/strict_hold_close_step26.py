import hashlib
import hmac
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_DOWN, ROUND_UP

import requests

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from main_runtime import TradingRuntime


KST = timezone(timedelta(hours=9))
EVIDENCE_PATH = "EXECUTE_FIRST_CHECKPOINT_20260410_STEP26_STRICT_HOLD_CLOSE_ALL.json"


def to_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def round_to_step(value, step, rounding):
    value_dec = Decimal(str(value))
    step_dec = Decimal(str(step))
    if step_dec <= 0:
        return value_dec
    return (value_dec / step_dec).to_integral_value(rounding=rounding) * step_dec


def decimal_places(value):
    value_dec = Decimal(str(value)).normalize()
    return max(0, -value_dec.as_tuple().exponent)


def symbol_filters(symbol_info):
    filters = {item.get("filterType"): item for item in symbol_info.get("filters", [])}
    lot_filter = filters.get("LOT_SIZE", {})
    price_filter = filters.get("PRICE_FILTER", {})
    percent_filter = filters.get("PERCENT_PRICE", {})
    return {
        "step_size": Decimal(str(lot_filter.get("stepSize", "1"))),
        "tick_size": Decimal(str(price_filter.get("tickSize", "0.00000001"))),
        "multiplier_up": Decimal(str(percent_filter.get("multiplierUp", "1.05"))),
        "multiplier_down": Decimal(str(percent_filter.get("multiplierDown", "0.95"))),
    }


def signed_request(runtime, method, path, params):
    server_time = runtime.order_executor.get_server_time()
    if not server_time:
        raise RuntimeError("server_time_unavailable")
    params = dict(params)
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
    response = requests.request(method, url, headers=headers, timeout=10)
    if response.status_code != 200:
        raise RuntimeError(f"{response.status_code} {response.text}")
    return response.json()


def get_mark_price(runtime, symbol):
    response = requests.get(
        f"{runtime.base_url}/fapi/v1/premiumIndex",
        params={"symbol": symbol},
        timeout=5,
    )
    if response.status_code != 200:
        return Decimal("0")
    return Decimal(str(response.json().get("markPrice", "0")))


def submit_limit_gtc_reduce_only(runtime, symbol, position, reason):
    amount = Decimal(str(position.get("amount", "0")))
    if amount == 0:
        raise RuntimeError("zero_position_amount")

    symbol_info = runtime.get_symbol_info(symbol)
    if not symbol_info:
        raise RuntimeError("symbol_info_missing")

    filters = symbol_filters(symbol_info)
    side = "SELL" if amount > 0 else "BUY"
    quantity = round_to_step(abs(amount), filters["step_size"], ROUND_DOWN)
    if quantity <= 0:
        raise RuntimeError("rounded_quantity_zero")

    mark_price = get_mark_price(runtime, symbol)
    if mark_price <= 0:
        raise RuntimeError("mark_price_unavailable")

    if side == "BUY":
        price = round_to_step(mark_price * filters["multiplier_up"], filters["tick_size"], ROUND_DOWN)
    else:
        price = round_to_step(mark_price * filters["multiplier_down"], filters["tick_size"], ROUND_UP)

    qty_precision = decimal_places(filters["step_size"])
    price_precision = decimal_places(filters["tick_size"])
    result = signed_request(
        runtime,
        "POST",
        "/fapi/v1/order",
        {
            "symbol": symbol,
            "side": side,
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": f"{quantity:.{qty_precision}f}",
            "price": f"{price:.{price_precision}f}",
            "reduceOnly": "true",
        },
    )
    processed = runtime.order_executor._process_order_result(
        result,
        position.get("strategy", "position_management"),
        symbol,
        side,
        float(quantity),
        True,
        {
            "exit_reason": reason,
            "entry_price": position.get("entry_price", 0.0),
            "fallback_close": "limit_gtc_percent_price_bound",
        },
    )
    return {
        "raw_result": result,
        "processed": processed,
        "side": side,
        "quantity": f"{quantity:.{qty_precision}f}",
        "limit_price": f"{price:.{price_precision}f}",
        "mark_price": str(mark_price),
    }


def build_quality_snapshot(runtime, symbols):
    market_data = runtime.market_data_service.update_market_data(symbols)
    runtime.trading_results["market_data"] = {
        symbol: data.get("prices", {}).get("current", 0.0)
        for symbol, data in market_data.items()
    }

    quality_by_symbol = {}
    for symbol in symbols:
        symbol_data = market_data.get(symbol, {})
        indicators = runtime.trade_orchestrator._calculate_symbol_indicators(symbol_data)
        prices = [kline["close"] for kline in symbol_data.get("klines", {}).get("1h", [])]
        volumes = [kline["volume"] for kline in symbol_data.get("klines", {}).get("1h", [])]
        regime = runtime.market_regime_service.analyze_market_regime(prices, volumes) if prices else {}
        quality = runtime.trade_orchestrator._evaluate_symbol_quality(symbol, indicators or {}, regime or {})
        position = runtime.trading_results.get("active_positions", {}).get(symbol, {})
        quality.update(
            {
                "side": "LONG" if to_float(position.get("amount")) > 0 else "SHORT",
                "amount": to_float(position.get("amount")),
                "entry_price": to_float(position.get("entry_price")),
                "current_price": to_float(position.get("current_price")),
            }
        )
        quality_by_symbol[symbol] = quality
    return quality_by_symbol


def coverage_snapshot(runtime):
    coverage = {}
    for symbol in sorted(runtime.trading_results.get("active_positions", {})):
        orders = runtime.protective_order_manager.get_protective_orders(symbol)
        coverage[symbol] = {
            "stop_count": len([order for order in orders if order.get("type") == "STOP_MARKET"]),
            "take_profit_count": len([order for order in orders if order.get("type") == "TAKE_PROFIT_MARKET"]),
        }
    return coverage


def main():
    started = datetime.now(KST)
    runtime = TradingRuntime()
    if not runtime.initialized:
        raise RuntimeError("runtime_not_initialized")

    runtime.sync_positions()
    active_before = sorted(runtime.trading_results.get("active_positions", {}))
    system_errors_before = len(runtime.trading_results.get("system_errors", []))
    realized_before = len(runtime.trading_results.get("realized_pnl_journal", []))
    orders_before = len(runtime.trading_results.get("real_orders", []))

    quality_by_symbol = build_quality_snapshot(runtime, active_before)
    selected = [
        symbol
        for symbol, quality in quality_by_symbol.items()
        if not quality.get("eligible_for_hold", False)
    ]

    close_results = []
    for symbol in selected:
        position = dict(runtime.trading_results.get("active_positions", {}).get(symbol, {}))
        result = {
            "symbol": symbol,
            "quality": quality_by_symbol.get(symbol, {}),
            "market_close_submitted": False,
            "fallback_attempted": False,
            "fallback": None,
            "error": None,
        }
        try:
            result["market_close_submitted"] = bool(
                runtime.position_manager.close_position(symbol, "strict_hold_quality_filter")
            )
        except Exception as exc:
            result["error"] = f"market_close_exception:{exc}"

        if not result["market_close_submitted"]:
            try:
                result["fallback_attempted"] = True
                result["fallback"] = submit_limit_gtc_reduce_only(
                    runtime, symbol, position, "strict_hold_quality_filter"
                )
            except Exception as exc:
                result["error"] = f"{result.get('error') or ''}|fallback_exception:{exc}".strip("|")
        close_results.append(result)
        time.sleep(1)

    time.sleep(12)
    runtime.sync_positions()
    active_after = sorted(runtime.trading_results.get("active_positions", {}))
    pending_after = [
        {
            "symbol": order.get("symbol"),
            "side": order.get("side"),
            "status": order.get("status"),
            "order_id": order.get("order_id"),
            "reduce_only": order.get("reduce_only"),
            "quantity": order.get("quantity"),
            "executed_qty": order.get("executed_qty"),
            "exit_reason": order.get("exit_reason"),
            "fallback_close": order.get("fallback_close"),
        }
        for order in runtime.trading_results.get("real_orders", [])[orders_before:]
        if order.get("status") in {"NEW", "PARTIALLY_FILLED"}
    ]
    new_orders = [
        {
            "symbol": order.get("symbol"),
            "side": order.get("side"),
            "status": order.get("status"),
            "order_id": order.get("order_id"),
            "reduce_only": order.get("reduce_only"),
            "quantity": order.get("quantity"),
            "executed_qty": order.get("executed_qty"),
            "exit_reason": order.get("exit_reason"),
            "fallback_close": order.get("fallback_close"),
            "realized_pnl": order.get("realized_pnl"),
        }
        for order in runtime.trading_results.get("real_orders", [])[orders_before:]
    ]
    coverage_after = coverage_snapshot(runtime)
    unprotected = [
        symbol
        for symbol, coverage in coverage_after.items()
        if coverage.get("stop_count", 0) == 0 or coverage.get("take_profit_count", 0) == 0
    ]

    finished = datetime.now(KST)
    evidence = {
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "duration_sec": round((finished - started).total_seconds(), 3),
        "mode": "strict_hold_quality_filter_close_all_problematic",
        "active_symbols_before": active_before,
        "quality_by_symbol": quality_by_symbol,
        "symbols_selected_for_close": selected,
        "close_results": close_results,
        "new_orders": new_orders,
        "active_symbols_after_sync": active_after,
        "pending_after_sync": pending_after,
        "coverage_after_sync": coverage_after,
        "unprotected_symbols_after_sync": unprotected,
        "system_errors_before": system_errors_before,
        "system_errors_after": len(runtime.trading_results.get("system_errors", [])),
        "new_system_errors": runtime.trading_results.get("system_errors", [])[system_errors_before:],
        "realized_pnl_journal_count_before": realized_before,
        "realized_pnl_journal_count_after": len(runtime.trading_results.get("realized_pnl_journal", [])),
        "new_realized_pnl_events": runtime.trading_results.get("realized_pnl_journal", [])[realized_before:],
    }
    with open(EVIDENCE_PATH, "w", encoding="utf-8") as handle:
        json.dump(evidence, handle, indent=2, ensure_ascii=False)

    print(json.dumps(evidence, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
