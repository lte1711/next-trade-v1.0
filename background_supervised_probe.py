import json
import os
import time
from datetime import datetime

from main_runtime import TradingRuntime


STATUS_FILE = "background_probe_status.json"


def write_status(payload):
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, default=str)


def main():
    started_at = datetime.now().astimezone()
    status = {
        "started_at": started_at.isoformat(),
        "pid": os.getpid(),
        "status": "starting",
        "cycles": [],
        "errors": [],
    }
    write_status(status)

    runtime = TradingRuntime()
    status["initialized"] = getattr(runtime, "initialized", False)
    status["base_url"] = getattr(runtime, "base_url", None)
    status["valid_symbol_count"] = len(getattr(runtime, "valid_symbols", []) or [])
    status["active_strategies"] = list(getattr(runtime, "active_strategies", []) or [])
    write_status(status)

    if not runtime.initialized:
        status["status"] = "init_failed"
        write_status(status)
        return

    status["status"] = "running"
    write_status(status)

    for cycle_no in range(1, 4):
        cycle_started = time.time()
        try:
            runtime.account_service.periodic_sync(runtime.trading_results)
            runtime.pending_order_manager.refresh_pending_orders()
            cycle_results = runtime.trade_orchestrator.run_trading_cycle(
                runtime.valid_symbols,
                runtime.active_strategies,
            )
            runtime._process_cycle_results(cycle_results)
            runtime._display_cycle_status(cycle_results)
            status["cycles"].append(
                {
                    "cycle_no": cycle_no,
                    "duration_sec": round(time.time() - cycle_started, 3),
                    "signals_generated": cycle_results.get("signals_generated", 0),
                    "trades_executed": cycle_results.get("trades_executed", 0),
                    "errors": cycle_results.get("errors", []),
                }
            )
        except Exception as exc:
            status["errors"].append(str(exc))
            status["cycles"].append(
                {
                    "cycle_no": cycle_no,
                    "duration_sec": round(time.time() - cycle_started, 3),
                    "signals_generated": 0,
                    "trades_executed": 0,
                    "errors": [str(exc)],
                }
            )
        write_status(status)
        if cycle_no < 3:
            time.sleep(10)

    status["status"] = "completed"
    status["completed_at"] = datetime.now().astimezone().isoformat()
    status["system_errors"] = len(runtime.trading_results.get("system_errors", []))
    status["active_positions"] = len(runtime.trading_results.get("active_positions", {}))
    status["pending_trades"] = len(runtime.trading_results.get("pending_trades", []))
    status["real_orders"] = len(runtime.trading_results.get("real_orders", []))
    write_status(status)


if __name__ == "__main__":
    main()
