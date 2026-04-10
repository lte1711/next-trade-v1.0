import hashlib
import hmac
import json
import os
import sys
from datetime import datetime, timezone, timedelta

import requests

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from main_runtime import TradingRuntime


KST = timezone(timedelta(hours=9))
EVIDENCE_PATH = "EXECUTE_FIRST_CHECKPOINT_20260410_STEP26_ORPHAN_OPEN_ORDER_CLEANUP.json"


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


def main():
    started = datetime.now(KST)
    runtime = TradingRuntime()
    if not runtime.initialized:
        raise RuntimeError("runtime_not_initialized")

    runtime.sync_positions()
    active_before = sorted(runtime.trading_results.get("active_positions", {}))
    open_before = signed_request(runtime, "GET", "/fapi/v1/openOrders", {})

    orphan_orders = []
    active_set = set(active_before)
    for order in open_before:
        symbol = order.get("symbol")
        if symbol not in active_set:
            orphan_orders.append(order)

    cancel_results = []
    for order in orphan_orders:
        symbol = order.get("symbol")
        order_id = order.get("orderId")
        try:
            result = signed_request(
                runtime,
                "DELETE",
                "/fapi/v1/order",
                {"symbol": symbol, "orderId": order_id},
            )
            cancel_results.append({
                "symbol": symbol,
                "order_id": order_id,
                "cancelled": True,
                "result": result,
            })
        except Exception as exc:
            cancel_results.append({
                "symbol": symbol,
                "order_id": order_id,
                "cancelled": False,
                "error": str(exc),
            })

    runtime.sync_positions()
    open_after = signed_request(runtime, "GET", "/fapi/v1/openOrders", {})
    finished = datetime.now(KST)
    evidence = {
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "duration_sec": round((finished - started).total_seconds(), 3),
        "mode": "orphan_open_order_cleanup_after_strict_hold_close",
        "active_symbols_before": active_before,
        "open_orders_before": open_before,
        "orphan_orders_selected": orphan_orders,
        "cancel_results": cancel_results,
        "active_symbols_after": sorted(runtime.trading_results.get("active_positions", {})),
        "open_orders_after": open_after,
        "remaining_open_order_count": len(open_after),
        "system_errors": runtime.trading_results.get("system_errors", []),
    }
    with open(EVIDENCE_PATH, "w", encoding="utf-8") as handle:
        json.dump(evidence, handle, indent=2, ensure_ascii=False)
    print(json.dumps(evidence, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
