"""CLI launcher for the merged partial v2 workspace."""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict

if getattr(sys, "frozen", False):
    ROOT = Path(sys.executable).resolve().parent
else:
    ROOT = Path(__file__).resolve().parent
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from merged_partial_v2.main import load_merge_config, load_profile_metrics, main  # noqa: E402
from merged_partial_v2.dashboard_server import serve_dashboard  # noqa: E402
from merged_partial_v2.exchange.credential_store import describe_credentials  # noqa: E402
from merged_partial_v2.exchange.local_binance_bridge import (  # noqa: E402
    get_recent_health_check_summary,
    get_recent_order_failure_summary,
)
from merged_partial_v2.services.process_manager_service import (  # noqa: E402
    finalize_autonomous_process,
    get_process_status,
    heartbeat_autonomous_process,
)
from merged_partial_v2.services.autonomous_trading_service import AutonomousTradingService  # noqa: E402
from merged_partial_v2.simulation.strategy_engine import MergedPartialStrategyEngine  # noqa: E402


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def _crash_log_path() -> Path:
    path = ROOT / "runtime" / "dashboard_crash.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _write_crash_log(exc: BaseException) -> None:
    log_path = _crash_log_path()
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        traceback.print_exc(file=handle)


def _last_execution_report_path() -> Path:
    path = ROOT / "execution_reports" / "last_execution_report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _write_execution_report(payload: Dict[str, Any]) -> Path:
    report_path = _last_execution_report_path()
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
    return report_path


def _build_engine() -> tuple[MergedPartialStrategyEngine, Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    config = load_merge_config()
    selection_config, benchmark_metrics = load_profile_metrics(config)
    engine = MergedPartialStrategyEngine(
        exchange_base_url=config.get("exchange_base_url", "https://demo-fapi.binance.com"),
        symbol_count=config.get("default_symbol_count", 10),
        profile_name=selection_config.get("default_profile_name"),
        selection_config=selection_config,
        benchmark_metrics=benchmark_metrics,
    )
    profile_selection = engine.select_profile_from_metrics(
        max_drawdown_percent=selection_config.get("current_metrics", {}).get("max_drawdown_percent"),
        positive_months=selection_config.get("current_metrics", {}).get("positive_months"),
        negative_months=selection_config.get("current_metrics", {}).get("negative_months"),
        prefer_aggressive=selection_config.get("prefer_aggressive", False),
    )
    return engine, config, selection_config, profile_selection


def _is_port_open(host: str, port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    try:
        return sock.connect_ex((host, port)) == 0
    finally:
        sock.close()


def _start_background_dashboard_if_needed(config: Dict[str, Any]) -> None:
    startup = dict(config.get("startup", {}))
    if not bool(startup.get("dashboard_autostart_when_installed", True)):
        return
    dashboard_port = int(startup.get("dashboard_port_when_installed", 8787) or 8787)
    if _is_port_open("127.0.0.1", dashboard_port):
        return

    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS  # type: ignore[attr-defined]

    if getattr(sys, "frozen", False):
        command = [str(Path(sys.executable).resolve()), "--dashboard", "--dashboard-port", str(dashboard_port)]
    else:
        command = [sys.executable, str(ROOT / "run_merged_partial_v2.py"), "--dashboard", "--dashboard-port", str(dashboard_port)]

    subprocess.Popen(  # noqa: S603
        command,
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=creationflags,
        close_fds=True,
    )


def _build_autonomous_service(engine: MergedPartialStrategyEngine, config: Dict[str, Any]) -> AutonomousTradingService:
    return AutonomousTradingService(
        engine=engine,
        merged_root=ROOT,
        autonomous_config=config.get("autonomous", {}),
    )


def _has_action_args(args: argparse.Namespace) -> bool:
    return any(
        [
            args.live_ready_check,
            args.transition_checklist,
            args.health_check_order,
            args.paper_decision,
            args.execute_top_recommendation,
            args.guarded_execute,
            args.auto_execute_if_flat,
            args.watch_recommendation,
            args.watch_then_guarded_execute,
            args.autonomous_cycle,
            args.autonomous_loop,
            args.dashboard,
        ]
    )


def _build_recommended_order(recommendation: Dict[str, Any], *, dry_run: bool) -> Dict[str, Any]:
    return {
        "symbol": recommendation["symbol"],
        "side": recommendation.get("side", "BUY"),
        "type": "MARKET",
        "qty": recommendation.get("estimated_quantity", 0.0),
        "trace_id": f"paper-exec-{recommendation['symbol'].lower()}",
        "dry_run": dry_run,
        "wait_for_fill": not dry_run,
        "status_timeout_seconds": 8.0,
    }


def _build_alert_summary(payload: Dict[str, Any]) -> str:
    mode = payload.get("mode") or "-"
    profile = (
        payload.get("paper_decision", {}).get("profile_name")
        or payload.get("profile_name")
        or payload.get("selected_profile")
        or "-"
    )
    reason = payload.get("reason") or "-"
    symbol = payload.get("symbol") or payload.get("payload", {}).get("symbol") or "-"

    if mode == "health_check_order":
        open_status = payload.get("open_final_status") or payload.get("open_result", {}).get("final_status") or "-"
        close_status = payload.get("close_final_status") or payload.get("close_result", {}).get("final_status") or "-"
        return f"health-check complete | symbol={symbol} | open={open_status} | close={close_status}"

    if mode == "live_ready_check":
        ready = payload.get("ready_for_live_autonomous")
        active_positions = payload.get("active_position_count", "-")
        return (
            f"live-ready check {'passed' if ready else 'blocked'}"
            f" | profile={profile} | active_positions={active_positions} | reason={reason}"
        )

    if mode == "transition_checklist":
        ready = payload.get("ready_for_live_autonomous")
        managed_count = payload.get("managed_position_count_preview", "-")
        return (
            f"transition checklist {'passed' if ready else 'blocked'}"
            f" | profile={profile} | managed_preview={managed_count} | reason={reason}"
        )

    if payload.get("executed") is True:
        final_status = (
            payload.get("final_status")
            or payload.get("result", {}).get("final_status")
            or payload.get("result", {}).get("status")
            or "-"
        )
        return f"execution complete | mode={mode} | profile={profile} | symbol={symbol} | status={final_status}"

    if payload.get("guard_passed") is False:
        active_count = (
            payload.get("paper_decision", {}).get("active_position_count")
            if isinstance(payload.get("paper_decision"), dict)
            else None
        )
        active_text = f" | active_positions={active_count}" if active_count is not None else ""
        return f"guard blocked | mode={mode} | profile={profile} | reason={reason}{active_text}"

    return f"waiting or no action | mode={mode} | profile={profile} | reason={reason}"


def _finalize_and_print(payload: Dict[str, Any]) -> Dict[str, Any]:
    payload["alert_summary"] = _build_alert_summary(payload)
    report_path = _write_execution_report(payload)
    payload["report_path"] = str(report_path)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return payload


def _print_autonomous_report(report: Dict[str, Any]) -> Dict[str, Any]:
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report


def run_live_ready_check(
    engine: MergedPartialStrategyEngine,
    config: Dict[str, Any],
    *,
    adopt_active_positions: bool,
) -> Dict[str, Any]:
    snapshot = engine.build_paper_decision(limit=80)
    decision = snapshot["paper_decision"]
    account = snapshot["account"]["account"]
    positions = snapshot["account"]["positions"]
    credential_status = describe_credentials()
    recent_health_check = get_recent_health_check_summary()
    recent_order_failures = get_recent_order_failure_summary()
    autonomous_config = dict(config.get("autonomous", {}))

    active_position_count = int(positions.get("active_position_count", 0) or 0)
    credentials_ok = all(
        bool(role_status.get("api_key_loaded")) and bool(role_status.get("api_secret_loaded"))
        for role_status in credential_status.values()
    )
    risk_gate = dict(decision.get("risk_gate", {}))
    risk_gate_ok = bool(risk_gate.get("ok", False))
    profile_name = snapshot["market"]["profile"]["name"]
    autonomous_config_ok = (
        float(autonomous_config.get("cycle_interval_seconds", 0.0) or 0.0) > 0
        and int(autonomous_config.get("scan_limit", 0) or 0) > 0
        and int(autonomous_config.get("max_new_orders_per_cycle", 0) or 0) > 0
    )
    account_state_ok = active_position_count == 0 or adopt_active_positions

    checks = [
        {
            "name": "credentials_loaded",
            "ok": credentials_ok,
            "detail": "All three credential roles are loaded with key and secret.",
        },
        {
            "name": "recent_health_check_ok",
            "ok": bool(recent_health_check.get("ok", False)),
            "detail": "A recent health-check summary exists and is readable.",
        },
        {
            "name": "risk_gate_ok",
            "ok": risk_gate_ok,
            "detail": risk_gate.get("decision_line") or "Risk gate must allow new entries.",
        },
        {
            "name": "profile_resolved",
            "ok": bool(profile_name),
            "detail": f"Resolved autonomous profile: {profile_name or '-'}",
        },
        {
            "name": "autonomous_config_valid",
            "ok": autonomous_config_ok,
            "detail": "Autonomous scan limit, cycle interval, and max new orders are positive.",
        },
        {
            "name": "account_position_state_ok",
            "ok": account_state_ok,
            "detail": (
                "Account is flat."
                if active_position_count == 0
                else (
                    "Active positions will be adopted into autonomous state."
                    if adopt_active_positions
                    else "Active positions exist and adoption is not enabled."
                )
            ),
        },
    ]

    failed_checks = [item for item in checks if not item["ok"]]
    payload = {
        "mode": "live_ready_check",
        "dry_run": True,
        "executed": False,
        "ready_for_live_autonomous": not failed_checks,
        "profile_name": profile_name,
        "adopt_active_positions": adopt_active_positions,
        "active_position_count": active_position_count,
        "checks": checks,
        "credential_status": credential_status,
        "recent_health_check": recent_health_check,
        "recent_order_failures": recent_order_failures,
        "risk_gate": risk_gate,
        "paper_decision": decision,
        "account_equity": account.get("account_equity"),
        "wallet_balance": account.get("wallet_balance"),
        "reason": (
            "All live-readiness checks passed."
            if not failed_checks
            else f"Live-readiness blocked by {len(failed_checks)} check(s)."
        ),
    }
    return _finalize_and_print(payload)


def run_transition_checklist(
    engine: MergedPartialStrategyEngine,
    config: Dict[str, Any],
    *,
    adopt_active_positions: bool,
) -> Dict[str, Any]:
    live_ready = run_live_ready_check(
        engine,
        config,
        adopt_active_positions=adopt_active_positions,
    )
    service = _build_autonomous_service(engine, config)
    autonomous_preview = service.run_cycle(
        dry_run=True,
        adopt_existing_positions=adopt_active_positions,
    )
    can_cutover = bool(live_ready.get("ready_for_live_autonomous", False))
    managed_preview = dict(autonomous_preview.get("state_after", {}))
    payload = {
        "mode": "transition_checklist",
        "dry_run": True,
        "executed": False,
        "ready_for_live_autonomous": can_cutover,
        "adopt_active_positions": adopt_active_positions,
        "live_ready_check": live_ready,
        "autonomous_preview": autonomous_preview,
        "managed_position_count_preview": managed_preview.get("managed_position_count", 0),
        "managed_symbols_preview": managed_preview.get("managed_symbols", []),
        "reason": (
            "Transition checklist passed."
            if can_cutover
            else "Transition checklist found at least one live cutover blocker."
        ),
    }
    return _finalize_and_print(payload)


def run_health_check_order(engine: MergedPartialStrategyEngine, *, symbol: str, quantity: float, dry_run: bool) -> Dict[str, Any]:
    if dry_run:
        payload = {
            "mode": "health_check_order",
            "dry_run": True,
            "executed": False,
            "symbol": symbol,
            "requested_quantity": quantity,
            "reason": "Health-check order requires --live. Dry-run returns a preview only.",
        }
        return _finalize_and_print(payload)

    result = engine.execution_client.open_and_close_test_order(symbol=symbol, side="BUY", quantity=quantity)
    payload = {
        "mode": "health_check_order",
        "dry_run": False,
        "executed": True,
        "symbol": symbol,
        "requested_quantity": quantity,
        "submitted_quantity": result.get("submitted_quantity"),
        "open_final_status": result.get("open_result", {}).get("final_status"),
        "close_final_status": result.get("close_result", {}).get("final_status"),
        **result,
    }
    return _finalize_and_print(payload)


def run_paper_decision(engine: MergedPartialStrategyEngine) -> Dict[str, Any]:
    result = engine.build_paper_decision(limit=80)
    payload = {
        "mode": "paper_decision",
        "dry_run": True,
        "executed": False,
        "paper_decision": result["paper_decision"],
        "market_regime": result["market"]["market_regime"],
        "profile_name": result["market"]["profile"]["name"],
        "reason": result["paper_decision"]["decision_line"],
    }
    return _finalize_and_print(payload)


def run_execute_top_recommendation(engine: MergedPartialStrategyEngine, *, dry_run: bool) -> Dict[str, Any]:
    snapshot = engine.build_paper_decision(limit=80)
    decision = snapshot["paper_decision"]
    recommendations = list(decision.get("recommendations", []))
    if not recommendations:
        payload = {
            "mode": "execute_top_recommendation",
            "dry_run": dry_run,
            "executed": False,
            "paper_decision": decision,
            "reason": "No executable recommendation is available.",
        }
        return _finalize_and_print(payload)

    order_payload = _build_recommended_order(recommendations[0], dry_run=dry_run)
    result = engine.submit_order(order_payload)
    payload = {
        "mode": "execute_top_recommendation",
        "dry_run": dry_run,
        "executed": True,
        "paper_decision": decision,
        "payload": order_payload,
        "symbol": order_payload["symbol"],
        "profile_name": decision.get("profile_name"),
        "result": result,
        "final_status": result.get("final_status") or result.get("status"),
        "reason": result.get("reason") or "Submitted top recommendation.",
    }
    return _finalize_and_print(payload)


def run_guarded_execute(engine: MergedPartialStrategyEngine, *, dry_run: bool) -> Dict[str, Any]:
    snapshot = engine.build_paper_decision(limit=80)
    decision = snapshot["paper_decision"]
    recommendations = list(decision.get("recommendations", []))

    if not recommendations:
        payload = {
            "mode": "guarded_execute",
            "dry_run": dry_run,
            "executed": False,
            "guard_passed": False,
            "paper_decision": decision,
            "reason": "No executable recommendation passed the current guards.",
        }
        return _finalize_and_print(payload)

    order_payload = _build_recommended_order(recommendations[0], dry_run=dry_run)
    result = engine.submit_order(order_payload)
    payload = {
        "mode": "guarded_execute",
        "dry_run": dry_run,
        "executed": True,
        "guard_passed": True,
        "paper_decision": decision,
        "payload": order_payload,
        "symbol": order_payload["symbol"],
        "profile_name": decision.get("profile_name"),
        "result": result,
        "final_status": result.get("final_status") or result.get("status"),
        "reason": result.get("reason") or "Guarded execution submitted.",
    }
    return _finalize_and_print(payload)


def run_auto_execute_if_flat(engine: MergedPartialStrategyEngine, *, dry_run: bool) -> Dict[str, Any]:
    snapshot = engine.build_paper_decision(limit=80)
    decision = snapshot["paper_decision"]
    active_count = int(decision.get("active_position_count", 0) or 0)
    if active_count != 0:
        payload = {
            "mode": "auto_execute_if_flat",
            "dry_run": dry_run,
            "executed": False,
            "guard_passed": False,
            "paper_decision": decision,
            "reason": "Account is not flat. Auto-execute-if-flat requires zero active positions.",
        }
        return _finalize_and_print(payload)

    recommendations = list(decision.get("recommendations", []))
    if not recommendations:
        payload = {
            "mode": "auto_execute_if_flat",
            "dry_run": dry_run,
            "executed": False,
            "guard_passed": False,
            "paper_decision": decision,
            "reason": "Account is flat, but no executable recommendation is available.",
        }
        return _finalize_and_print(payload)

    order_payload = _build_recommended_order(recommendations[0], dry_run=dry_run)
    result = engine.submit_order(order_payload)
    payload = {
        "mode": "auto_execute_if_flat",
        "dry_run": dry_run,
        "executed": True,
        "guard_passed": True,
        "paper_decision": decision,
        "payload": order_payload,
        "symbol": order_payload["symbol"],
        "profile_name": decision.get("profile_name"),
        "result": result,
        "final_status": result.get("final_status") or result.get("status"),
        "reason": result.get("reason") or "Flat-account execution submitted.",
    }
    return _finalize_and_print(payload)


def run_watch_recommendation(
    engine: MergedPartialStrategyEngine,
    *,
    max_cycles: int,
    interval_seconds: float,
) -> Dict[str, Any]:
    last_snapshot: Dict[str, Any] | None = None
    for _ in range(max_cycles):
        last_snapshot = engine.build_paper_decision(limit=80)
        decision = last_snapshot["paper_decision"]
        if decision.get("recommendations"):
            payload = {
                "mode": "watch_recommendation",
                "dry_run": True,
                "executed": False,
                "triggered": True,
                "paper_decision": decision,
                "profile_name": decision.get("profile_name"),
                "reason": "A recommendation became available during the watch window.",
            }
            return _finalize_and_print(payload)
        time.sleep(interval_seconds)

    payload = {
        "mode": "watch_recommendation",
        "dry_run": True,
        "executed": False,
        "triggered": False,
        "paper_decision": (last_snapshot or {}).get("paper_decision", {}),
        "reason": "No recommendation became available during the configured watch window.",
    }
    return _finalize_and_print(payload)


def run_watch_then_guarded_execute(
    engine: MergedPartialStrategyEngine,
    *,
    dry_run: bool,
    max_cycles: int,
    interval_seconds: float,
) -> Dict[str, Any]:
    last_snapshot: Dict[str, Any] | None = None
    for _ in range(max_cycles):
        last_snapshot = engine.build_paper_decision(limit=80)
        decision = last_snapshot["paper_decision"]
        if decision.get("recommendations") and int(decision.get("active_position_count", 0) or 0) == 0:
            order_payload = _build_recommended_order(decision["recommendations"][0], dry_run=dry_run)
            result = engine.submit_order(order_payload)
            payload = {
                "mode": "watch_then_guarded_execute",
                "dry_run": dry_run,
                "triggered": True,
                "executed": True,
                "guard_passed": True,
                "paper_decision": decision,
                "payload": order_payload,
                "symbol": order_payload["symbol"],
                "profile_name": decision.get("profile_name"),
                "result": result,
                "final_status": result.get("final_status") or result.get("status"),
                "reason": result.get("reason") or "Watch window found an executable recommendation.",
            }
            return _finalize_and_print(payload)
        time.sleep(interval_seconds)

    payload = {
        "mode": "watch_then_guarded_execute",
        "dry_run": dry_run,
        "triggered": False,
        "executed": False,
        "guard_passed": False,
        "paper_decision": (last_snapshot or {}).get("paper_decision", {}),
        "reason": "No flat-account executable recommendation appeared during the configured watch window.",
    }
    return _finalize_and_print(payload)


def run_autonomous_cycle(
    engine: MergedPartialStrategyEngine,
    config: Dict[str, Any],
    *,
    dry_run: bool,
    adopt_active_positions: bool,
) -> Dict[str, Any]:
    service = _build_autonomous_service(engine, config)
    report = service.run_cycle(
        dry_run=dry_run,
        adopt_existing_positions=adopt_active_positions,
    )
    return _print_autonomous_report(report)


def run_autonomous_loop(
    engine: MergedPartialStrategyEngine,
    config: Dict[str, Any],
    *,
    dry_run: bool,
    adopt_active_positions: bool,
    cycles: int,
    interval_seconds: float,
) -> Dict[str, Any]:
    service = _build_autonomous_service(engine, config)
    last_report: Dict[str, Any] = {}
    current_pid = os.getpid()
    tracked_process = int(get_process_status().get("pid", 0) or 0) == current_pid
    exit_reason = "manual_stop"
    cycle_index = 0
    try:
        while True:
            try:
                last_report = service.run_cycle(
                    dry_run=dry_run,
                    adopt_existing_positions=adopt_active_positions if cycle_index == 0 else False,
                )
                if tracked_process:
                    heartbeat_autonomous_process(current_pid, last_cycle_at=last_report.get("ts"))
                print(json.dumps(last_report, indent=2, ensure_ascii=False))
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                last_report = service.write_loop_error_report(
                    error=exc,
                    dry_run=dry_run,
                    cycle_index=cycle_index,
                    retry_sleep_seconds=max(interval_seconds, 0.0),
                )
                if tracked_process:
                    heartbeat_autonomous_process(current_pid, last_cycle_at=last_report.get("ts"))
                _write_crash_log(exc)
                print(json.dumps(last_report, indent=2, ensure_ascii=False))
            cycle_index += 1
            if cycles > 0 and cycle_index >= cycles:
                break
            if max(interval_seconds, 0.0) > 0:
                time.sleep(max(interval_seconds, 0.0))
    except KeyboardInterrupt:
        exit_reason = "keyboard_interrupt"
    finally:
        if tracked_process:
            finalize_autonomous_process(current_pid, exit_reason=exit_reason)
    return last_report


def run_installed_startup_default(
    engine: MergedPartialStrategyEngine,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    startup = dict(config.get("startup", {}))
    default_mode = str(startup.get("default_mode_when_installed", "autonomous_loop")).strip().lower()
    
    # 환경에 따른 dry_run 설정
    environment = config.get("environment", "testnet").lower()
    is_testnet = "testnet" in environment
    dry_run = not bool(startup.get("live_by_default_when_installed", False)) and is_testnet
    
    adopt_active_positions = bool(startup.get("adopt_active_positions_when_installed", False))
    cycles = int(startup.get("autonomous_cycles_when_installed", 0) or 0)
    interval_seconds = float(startup.get("autonomous_interval_seconds_when_installed", 60.0) or 60.0)

    if default_mode == "autonomous_cycle":
        return run_autonomous_cycle(
            engine,
            config,
            dry_run=dry_run,
            adopt_active_positions=adopt_active_positions,
        )

    return run_autonomous_loop(
        engine,
        config,
        dry_run=dry_run,
        adopt_active_positions=adopt_active_positions,
        cycles=max(cycles, 1),
        interval_seconds=max(interval_seconds, 0.0),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merged partial v2 launcher")
    parser.add_argument("--live-ready-check", action="store_true")
    parser.add_argument("--transition-checklist", action="store_true")
    parser.add_argument("--health-check-order", action="store_true")
    parser.add_argument("--paper-decision", action="store_true")
    parser.add_argument("--execute-top-recommendation", action="store_true")
    parser.add_argument("--guarded-execute", action="store_true")
    parser.add_argument("--auto-execute-if-flat", action="store_true")
    parser.add_argument("--watch-recommendation", action="store_true")
    parser.add_argument("--watch-then-guarded-execute", action="store_true")
    parser.add_argument("--autonomous-cycle", action="store_true")
    parser.add_argument("--autonomous-loop", action="store_true")
    parser.add_argument("--dashboard", action="store_true")
    parser.add_argument("--dashboard-port", type=int, default=8787)
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--quantity", type=float, default=0.001)
    parser.add_argument("--watch-cycles", type=int, default=3)
    parser.add_argument("--watch-interval-seconds", type=float, default=5.0)
    parser.add_argument("--autonomous-cycles", type=int, default=3)
    parser.add_argument("--autonomous-interval-seconds", type=float, default=60.0)
    parser.add_argument("--adopt-active-positions", action="store_true")
    parser.add_argument("--live", action="store_true")
    return parser.parse_args()


def cli_main() -> None:
    args = parse_args()
    engine, config, _, _ = _build_engine()
    
    # 환경에 따른 dry_run 설정
    environment = config.get("environment", "testnet").lower()
    is_testnet = "testnet" in environment
    dry_run = not args.live and is_testnet
    
    if not _has_action_args(args):
        startup = dict(config.get("startup", {}))
        if getattr(sys, "frozen", False) and bool(startup.get("autorun_when_installed", False)):
            _start_background_dashboard_if_needed(config)
            run_installed_startup_default(engine, config)
            return
        main()
        return

    if args.live_ready_check:
        run_live_ready_check(
            engine,
            config,
            adopt_active_positions=args.adopt_active_positions,
        )
        return
    if args.transition_checklist:
        run_transition_checklist(
            engine,
            config,
            adopt_active_positions=args.adopt_active_positions,
        )
        return
    if args.health_check_order:
        run_health_check_order(engine, symbol=args.symbol, quantity=args.quantity, dry_run=dry_run)
        return
    if args.paper_decision:
        run_paper_decision(engine)
        return
    if args.execute_top_recommendation:
        run_execute_top_recommendation(engine, dry_run=dry_run)
        return
    if args.guarded_execute:
        run_guarded_execute(engine, dry_run=dry_run)
        return
    if args.auto_execute_if_flat:
        run_auto_execute_if_flat(engine, dry_run=dry_run)
        return
    if args.watch_recommendation:
        run_watch_recommendation(
            engine,
            max_cycles=max(args.watch_cycles, 1),
            interval_seconds=max(args.watch_interval_seconds, 0.0),
        )
        return
    if args.watch_then_guarded_execute:
        run_watch_then_guarded_execute(
            engine,
            dry_run=dry_run,
            max_cycles=max(args.watch_cycles, 1),
            interval_seconds=max(args.watch_interval_seconds, 0.0),
        )
        return
    if args.autonomous_cycle:
        run_autonomous_cycle(
            engine,
            config,
            dry_run=dry_run,
            adopt_active_positions=args.adopt_active_positions,
        )
        return
    if args.autonomous_loop:
        run_autonomous_loop(
            engine,
            config,
            dry_run=dry_run,
            adopt_active_positions=args.adopt_active_positions,
            cycles=int(args.autonomous_cycles),
            interval_seconds=max(args.autonomous_interval_seconds, 0.0),
        )
        return
    if args.dashboard:
        serve_dashboard(port=args.dashboard_port)
        return


if __name__ == "__main__":
    try:
        cli_main()
    except Exception as exc:  # noqa: BLE001
        _write_crash_log(exc)
        raise
