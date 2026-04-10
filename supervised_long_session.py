import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path

from main_runtime import TradingRuntime


DEFAULT_STATUS_PATH = Path("supervised_long_session_status.json")
DEFAULT_REPORT_PATH = Path("SUPERVISED_LONG_SESSION_REPORT.md")


def now_iso():
    return datetime.now().astimezone().isoformat()


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def write_json(path, payload):
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def write_report(path, payload):
    lines = [
        "# Supervised Long Session Report",
        "",
        f"Generated: {payload.get('completed_at') or payload.get('started_at')}",
        f"Environment: `{payload.get('base_url')}`",
        f"Status: `{payload.get('status')}`",
        "",
        "## Session",
        f"- PID: `{payload.get('pid')}`",
        f"- Requested Cycles: `{payload.get('requested_cycles')}`",
        f"- Completed Cycles: `{payload.get('completed_cycles')}`",
        f"- Sleep Seconds: `{payload.get('sleep_seconds')}`",
        f"- Started At: `{payload.get('started_at')}`",
        f"- Completed At: `{payload.get('completed_at')}`",
        "",
        "## Aggregate",
        f"- System Errors: `{payload.get('system_errors')}`",
        f"- Total Signals: `{payload.get('aggregate', {}).get('signals_generated', 0)}`",
        f"- Total Trades: `{payload.get('aggregate', {}).get('trades_executed', 0)}`",
        f"- Cycles With Errors: `{payload.get('aggregate', {}).get('cycles_with_errors', 0)}`",
        f"- Max Active Positions: `{payload.get('aggregate', {}).get('max_active_positions', 0)}`",
        f"- Max Pending Trades: `{payload.get('aggregate', {}).get('max_pending_trades', 0)}`",
        f"- Starting Balance: `{payload.get('starting_balance')}`",
        f"- Ending Balance: `{payload.get('ending_balance')}`",
        "",
        "## Cycle Summary",
    ]

    for cycle in payload.get("cycles", []):
        lines.append(
            "- "
            f"Cycle {cycle.get('cycle_no')}: "
            f"duration={cycle.get('duration_sec')}s, "
            f"signals={cycle.get('signals_generated')}, "
            f"trades={cycle.get('trades_executed')}, "
            f"errors={len(cycle.get('errors', []))}, "
            f"skips={len(cycle.get('skips', []))}, "
            f"balance={cycle.get('available_balance')}, "
            f"active_positions={cycle.get('active_positions')}, "
            f"pending_trades={cycle.get('pending_trades')}"
        )

    if payload.get("errors"):
        lines.extend(["", "## Errors"])
        for item in payload["errors"]:
            lines.append(f"- {item}")

    if payload.get("next_evolution_targets"):
        lines.extend(["", "## Next Evolution Targets"])
        for item in payload["next_evolution_targets"]:
            lines.append(f"- {item}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycles", type=int, default=12)
    parser.add_argument("--sleep-seconds", type=int, default=10)
    parser.add_argument("--status-file", default=str(DEFAULT_STATUS_PATH))
    parser.add_argument("--report-file", default=str(DEFAULT_REPORT_PATH))
    args = parser.parse_args()

    status_path = Path(args.status_file)
    report_path = Path(args.report_file)

    payload = {
        "started_at": now_iso(),
        "completed_at": None,
        "pid": os.getpid(),
        "status": "starting",
        "requested_cycles": args.cycles,
        "completed_cycles": 0,
        "sleep_seconds": args.sleep_seconds,
        "errors": [],
        "cycles": [],
        "aggregate": {
            "signals_generated": 0,
            "trades_executed": 0,
            "cycles_with_errors": 0,
            "max_active_positions": 0,
            "max_pending_trades": 0,
        },
        "next_evolution_targets": [],
    }
    write_json(status_path, payload)

    runtime = TradingRuntime()
    payload["initialized"] = getattr(runtime, "initialized", False)
    payload["base_url"] = getattr(runtime, "base_url", None)
    payload["valid_symbol_count"] = len(getattr(runtime, "valid_symbols", []) or [])
    payload["active_strategies"] = list(getattr(runtime, "active_strategies", []) or [])
    payload["starting_balance"] = safe_float(getattr(runtime, "total_capital", 0.0), 0.0)
    payload["ending_balance"] = payload["starting_balance"]
    write_json(status_path, payload)

    if not runtime.initialized:
        payload["status"] = "init_failed"
        payload["errors"].append("TradingRuntime failed to initialize.")
        payload["completed_at"] = now_iso()
        write_json(status_path, payload)
        write_report(report_path, payload)
        return

    payload["status"] = "running"
    write_json(status_path, payload)

    for cycle_no in range(1, args.cycles + 1):
        cycle_started_at = time.time()
        cycle_record = {
            "cycle_no": cycle_no,
            "started_at": now_iso(),
            "finished_at": None,
            "duration_sec": 0.0,
            "signals_generated": 0,
            "trades_executed": 0,
            "errors": [],
            "skips": [],
            "available_balance": None,
            "active_positions": 0,
            "pending_trades": 0,
            "real_orders": 0,
            "system_errors": 0,
        }

        try:
            runtime.account_service.periodic_sync(runtime.trading_results)
            runtime.pending_order_manager.refresh_pending_orders()
            cycle_results = runtime.trade_orchestrator.run_trading_cycle(
                runtime.valid_symbols,
                runtime.active_strategies,
            )
            runtime._process_cycle_results(cycle_results)
            runtime._display_cycle_status(cycle_results)

            cycle_record["signals_generated"] = cycle_results.get("signals_generated", 0)
            cycle_record["trades_executed"] = cycle_results.get("trades_executed", 0)
            cycle_record["errors"] = list(cycle_results.get("errors", []))
            cycle_record["skips"] = list(cycle_results.get("skips", []))
        except Exception as exc:
            cycle_record["errors"] = [str(exc)]
            payload["errors"].append(f"Cycle {cycle_no}: {exc}")

        cycle_record["duration_sec"] = round(time.time() - cycle_started_at, 3)
        cycle_record["finished_at"] = now_iso()
        cycle_record["available_balance"] = safe_float(
            runtime.trading_results.get("available_balance"),
            safe_float(getattr(runtime, "total_capital", 0.0), 0.0),
        )
        cycle_record["active_positions"] = len(runtime.trading_results.get("active_positions", {}))
        cycle_record["pending_trades"] = len(runtime.trading_results.get("pending_trades", []))
        cycle_record["real_orders"] = len(runtime.trading_results.get("real_orders", []))
        cycle_record["system_errors"] = len(runtime.trading_results.get("system_errors", []))

        payload["cycles"].append(cycle_record)
        payload["completed_cycles"] = cycle_no
        payload["ending_balance"] = cycle_record["available_balance"]
        payload["aggregate"]["signals_generated"] += cycle_record["signals_generated"]
        payload["aggregate"]["trades_executed"] += cycle_record["trades_executed"]
        if cycle_record["errors"]:
            payload["aggregate"]["cycles_with_errors"] += 1
        payload["aggregate"]["max_active_positions"] = max(
            payload["aggregate"]["max_active_positions"],
            cycle_record["active_positions"],
        )
        payload["aggregate"]["max_pending_trades"] = max(
            payload["aggregate"]["max_pending_trades"],
            cycle_record["pending_trades"],
        )
        write_json(status_path, payload)

        if cycle_no < args.cycles:
            time.sleep(args.sleep_seconds)

    payload["status"] = "completed"
    payload["completed_at"] = now_iso()
    payload["system_errors"] = len(runtime.trading_results.get("system_errors", []))

    if payload["aggregate"]["cycles_with_errors"] > 0:
        payload["next_evolution_targets"].append(
            "Investigate cycle-level errors before extending session duration."
        )
    else:
        payload["next_evolution_targets"].append(
            "Extend to a multi-hour supervised session with the same evidence format."
        )

    if payload["aggregate"]["trades_executed"] == 0:
        payload["next_evolution_targets"].append(
            "Induce more real non-HOLD trading scenarios to validate entry/exit diversity."
        )

    if payload["aggregate"]["max_active_positions"] == 0:
        payload["next_evolution_targets"].append(
            "Add targeted scenario tests that force active position state transitions."
        )

    write_json(status_path, payload)
    write_report(report_path, payload)


if __name__ == "__main__":
    main()
