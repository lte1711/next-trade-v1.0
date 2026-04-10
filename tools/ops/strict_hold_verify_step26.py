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
SOURCE_PATH = "EXECUTE_FIRST_CHECKPOINT_20260410_STEP26_STRICT_HOLD_CLOSE_ALL.json"
EVIDENCE_PATH = "EXECUTE_FIRST_CHECKPOINT_20260410_STEP26_STRICT_HOLD_CLOSE_ALL_SYNC_VERIFY.json"


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

    with open(SOURCE_PATH, "r", encoding="utf-8") as handle:
        source = json.load(handle)

    runtime.sync_positions()
    active_symbols = sorted(runtime.trading_results.get("active_positions", {}))
    submitted_orders = source.get("new_orders", [])
    order_statuses = []
    for order in submitted_orders:
        symbol = order.get("symbol")
        order_id = order.get("order_id")
        if not symbol or not order_id:
            continue
        status = runtime.get_order_status(symbol, order_id)
        order_statuses.append({
            "symbol": symbol,
            "order_id": order_id,
            "submitted_status": order.get("status"),
            "exchange_status": status,
        })

    open_orders = signed_request(runtime, "GET", "/fapi/v1/openOrders", {})
    strict_symbols = set(source.get("symbols_selected_for_close", []))
    relevant_open_orders = [
        order for order in open_orders if order.get("symbol") in strict_symbols
    ]
    finished = datetime.now(KST)
    evidence = {
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "duration_sec": round((finished - started).total_seconds(), 3),
        "mode": "strict_hold_quality_filter_sync_verify",
        "active_symbols_after_sync_verify": active_symbols,
        "strict_symbols_checked": sorted(strict_symbols),
        "order_statuses": order_statuses,
        "relevant_open_orders": relevant_open_orders,
        "all_open_order_count": len(open_orders),
        "system_errors": runtime.trading_results.get("system_errors", []),
        "realized_pnl_journal_count": len(runtime.trading_results.get("realized_pnl_journal", [])),
    }
    with open(EVIDENCE_PATH, "w", encoding="utf-8") as handle:
        json.dump(evidence, handle, indent=2, ensure_ascii=False)
    print(json.dumps(evidence, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
