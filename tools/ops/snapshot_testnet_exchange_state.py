import json
import io
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path

from close_all_testnet_exchange_state import nonzero_exchange_positions, signed_request
from main_runtime import TradingRuntime


KST = timezone(timedelta(hours=9))
REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with redirect_stdout(io.StringIO()):
        runtime = TradingRuntime()
    if not runtime.initialized:
        raise RuntimeError("runtime_not_initialized")
    if "demo-fapi.binance.com" not in runtime.base_url:
        raise RuntimeError(f"refusing_non_testnet_base_url:{runtime.base_url}")

    with redirect_stdout(io.StringIO()):
        runtime.sync_positions()
    open_orders = signed_request(runtime, "GET", "/fapi/v1/openOrders", {})
    positions = nonzero_exchange_positions(runtime)
    payload = {
        "captured_at": datetime.now(KST).isoformat(),
        "base_url": runtime.base_url,
        "status": {
            "open_order_count": len(open_orders),
            "exchange_position_count": len(positions),
            "runtime_active_position_count": len(runtime.trading_results.get("active_positions", {}) or {}),
            "available_balance": runtime.trading_results.get("available_balance"),
            "system_errors_count": len(runtime.trading_results.get("system_errors", []) or []),
        },
        "open_orders": open_orders,
        "exchange_positions": positions,
        "runtime_active_symbols": sorted(runtime.trading_results.get("active_positions", {}) or {}),
        "system_errors": runtime.trading_results.get("system_errors", []),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
