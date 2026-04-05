"""Minimal local dashboard server for merged_partial_v2."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

from merged_partial_v2.main import (
    build_snapshot_payload,
    load_merge_config,
    load_profile_metrics,
    write_snapshot_payload,
)
from merged_partial_v2.pathing import merged_root, resolve_resource
from merged_partial_v2.services.process_manager_service import (
    get_process_status,
    start_autonomous_process,
    stop_autonomous_process,
)
from merged_partial_v2.simulation.strategy_engine import MergedPartialStrategyEngine


def _dashboard_asset(name: str) -> Path:
    return resolve_resource(f"dashboard_assets/{name}")


def _last_execution_report_path() -> Path:
    path = merged_root() / "execution_reports" / "last_execution_report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _write_execution_report(payload: dict) -> Path:
    report_path = _last_execution_report_path()
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
    return report_path


def _build_alert_summary(payload: dict) -> str:
    mode = payload.get("mode") or "-"
    symbol = payload.get("symbol") or payload.get("payload", {}).get("symbol") or "-"
    reason = payload.get("reason") or "-"
    if payload.get("executed") is True:
        final_status = (
            payload.get("final_status")
            or payload.get("result", {}).get("final_status")
            or payload.get("result", {}).get("status")
            or payload.get("open_final_status")
            or "-"
        )
        return f"execution complete | mode={mode} | symbol={symbol} | status={final_status}"
    if mode == "health_check_order":
        open_status = payload.get("open_final_status") or payload.get("open_result", {}).get("final_status") or "-"
        close_status = payload.get("close_final_status") or payload.get("close_result", {}).get("final_status") or "-"
        return f"health-check complete | symbol={symbol} | open={open_status} | close={close_status}"
    return f"waiting or no action | mode={mode} | reason={reason}"


def _persist_execution_report(payload: dict) -> dict:
    report_payload = dict(payload)
    report_payload["alert_summary"] = _build_alert_summary(report_payload)
    report_path = _write_execution_report(report_payload)
    report_payload["report_path"] = str(report_path)
    return report_payload


def _validate_autonomous_start_payload(payload: dict) -> tuple[bool, str]:
    """자동매매 시작 페이로드 검증"""
    if not isinstance(payload, dict):
        return False, "payload must be a dictionary"
    
    adopt_active_positions = payload.get("adopt_active_positions")
    if adopt_active_positions is not None and not isinstance(adopt_active_positions, bool):
        return False, "adopt_active_positions must be a boolean"
    
    interval_seconds = payload.get("interval_seconds")
    if interval_seconds is not None:
        try:
            interval = float(interval_seconds)
            if interval < 1.0 or interval > 3600.0:  # 1초에서 1시간 사이
                return False, "interval_seconds must be between 1.0 and 3600.0"
        except (ValueError, TypeError):
            return False, "interval_seconds must be a valid number"
    
    return True, ""

def _validate_health_check_payload(payload: dict) -> tuple[bool, str]:
    """헬스체크 페이로드 검증"""
    if not isinstance(payload, dict):
        return False, "payload must be a dictionary"
    
    symbol = payload.get("symbol")
    if not symbol or not isinstance(symbol, str):
        return False, "symbol is required and must be a string"
    
    side = payload.get("side")
    if side not in ["BUY", "SELL"]:
        return False, "side must be either 'BUY' or 'SELL'"
    
    quantity = payload.get("quantity")
    try:
        qty = float(quantity or 0.001)
        if qty <= 0 or qty > 1000:  # 합리적인 수량 범위
            return False, "quantity must be between 0 and 1000"
    except (ValueError, TypeError):
        return False, "quantity must be a valid number"
    
    return True, ""

def _read_json_body(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0") or 0)
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}")


def build_dashboard_payload() -> dict:
    snapshot = build_snapshot_payload()
    snapshot = _apply_runtime_overlay(snapshot)
    write_snapshot_payload(snapshot)
    config = load_merge_config()
    return {
        "ok": True,
        "snapshot": snapshot,
        "autonomous_process": get_process_status(),
        "environment": {
            "type": config.get("environment", "unknown"),
            "exchange_base_url": config.get("exchange_base_url", ""),
            "is_testnet": "testnet" in config.get("environment", "").lower(),
        },
    }


def _load_json_if_exists(path: Path) -> dict | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _parse_iso_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _report_sort_key(payload: dict | None, path: Path) -> tuple[float, float]:
    ts_value = None
    if isinstance(payload, dict):
        ts_value = payload.get("ts") or payload.get("payload", {}).get("ts")
    parsed_ts = _parse_iso_ts(ts_value)
    ts_key = parsed_ts.timestamp() if parsed_ts else 0.0
    mtime_key = path.stat().st_mtime if path.exists() else 0.0
    return ts_key, mtime_key


def _managed_positions_from_state(state_payload: dict | None) -> list[dict]:
    managed = dict((state_payload or {}).get("managed_positions", {}))
    rows: list[dict] = []
    for symbol, item in managed.items():
        rows.append(
            {
                "symbol": symbol,
                "positionAmt": item.get("position_amt"),
                "entryPrice": item.get("entry_price"),
                "markPrice": item.get("mark_price"),
                "unRealizedProfit": item.get("unrealized_profit"),
                "positionSide": item.get("position_side"),
                "leverage": item.get("leverage"),
                "marginType": item.get("margin_type"),
            }
        )
    return rows


def _active_notional(active_positions: list[dict]) -> float:
    total = 0.0
    for position in active_positions:
        amount = abs(float(position.get("positionAmt", 0.0) or 0.0))
        mark_price = float(position.get("markPrice", 0.0) or 0.0)
        total += amount * mark_price
    return total


def _apply_runtime_overlay(snapshot: dict) -> dict:
    """런타임 상태 소스를 단순화하여 일관성 확보"""
    # 주요 상태 파일 경로
    report_path = merged_root() / "autonomous_reports" / "last_autonomous_report.json"
    state_path = merged_root() / "runtime" / "autonomous_state.json"
    
    # 파일 로드 (존재하지 않으면 None)
    last_report = _load_json_if_exists(report_path)
    state_payload = _load_json_if_exists(state_path)

    # 자동매매 보고서 처리
    if last_report:
        snapshot["last_autonomous_report"] = {
            "ok": True,
            "path": str(report_path),
            "mode": last_report.get("mode"),
            "dry_run": last_report.get("dry_run"),
            "entry_count": last_report.get("entry_count"),
            "exit_count": last_report.get("exit_count"),
            "decision_line": last_report.get("decision_line"),
            "payload": last_report,
        }
        
        # 페이퍼 디시전 정보 처리
        if isinstance(last_report.get("paper_decision"), dict):
            paper_decision = last_report["paper_decision"]
            snapshot["paper_decision"] = paper_decision
            snapshot["paper_decision_summary"] = {
                "recommended_orders": len(paper_decision.get("recommendations", [])),
                "blocked_candidates": len(paper_decision.get("blocked", [])),
                "top_recommendation_symbol": (
                    paper_decision.get("recommendations", [{}])[0].get("symbol")
                    if paper_decision.get("recommendations")
                    else None
                ),
                "decision_line": paper_decision.get("decision_line"),
            }

    # 상태 정보 처리 (포지션 정보)
    if state_payload:
        active_positions = _managed_positions_from_state(state_payload)
        snapshot.setdefault("account", {}).setdefault("positions", {})
        snapshot["account"]["positions"]["active_positions"] = active_positions
        snapshot["account"]["positions"]["active_position_count"] = len(active_positions)
        snapshot["account"]["positions"]["position_count"] = len(active_positions)
        snapshot["account"]["positions"]["ts"] = state_payload.get("last_synced_at")
        snapshot["account"]["positions"]["source"] = "autonomous_state"
        
        # 투자 정보 계산
        current_invested_notional = _active_notional(active_positions)
        if isinstance(snapshot.get("paper_decision"), dict):
            snapshot["paper_decision"]["active_position_count"] = len(active_positions)
            snapshot["paper_decision"]["current_invested_notional"] = current_invested_notional
            target_symbol_count = int(snapshot["paper_decision"].get("target_symbol_count", 0) or 0)
            snapshot["paper_decision"]["available_slots"] = max(target_symbol_count - len(active_positions), 0)

    return snapshot


def _snapshot_is_materialized(snapshot: dict) -> bool:
    market = dict(snapshot.get("market") or {})
    operational = dict(snapshot.get("operational_summary") or {})
    account = dict((snapshot.get("account") or {}).get("account") or {})
    return any(
        [
            market.get("profile"),
            market.get("selected_symbols"),
            operational.get("selected_profile"),
            account.get("account_equity") is not None,
            account.get("wallet_balance") is not None,
        ]
    )


def load_cached_dashboard_payload() -> dict:
    snapshot_path = merged_root() / "merged_snapshot.json"
    if snapshot_path.exists():
        with snapshot_path.open("r", encoding="utf-8-sig") as handle:
            snapshot = json.load(handle)
    else:
        snapshot = build_snapshot_payload()
        write_snapshot_payload(snapshot)
    snapshot = _apply_runtime_overlay(snapshot)
    return {
        "ok": True,
        "snapshot": snapshot,
        "autonomous_process": get_process_status(),
    }


def load_fast_dashboard_payload() -> dict:
    snapshot_path = merged_root() / "merged_snapshot.json"
    config = load_merge_config()
    snapshot: dict
    if snapshot_path.exists():
        with snapshot_path.open("r", encoding="utf-8-sig") as handle:
            snapshot = json.load(handle)
    else:
        snapshot = {
            "paper_decision": {"recommendations": [], "blocked": [], "risk_gate": {}},
            "paper_decision_summary": {"recommended_orders": 0, "blocked_candidates": 0},
            "operational_summary": {},
            "market": {},
            "account": {"account": {}, "positions": {"active_positions": [], "active_position_count": 0}},
            "last_execution_report": {"ok": False, "reason": "no_execution_report"},
            "last_autonomous_report": {"ok": False, "reason": "no_autonomous_report"},
        }
    if not _snapshot_is_materialized(snapshot):
        return build_dashboard_payload()
    snapshot = _apply_runtime_overlay(snapshot)
    return {
        "ok": True,
        "snapshot": snapshot,
        "autonomous_process": get_process_status(),
        "environment": {
            "type": config.get("environment", "unknown"),
            "exchange_base_url": config.get("exchange_base_url", ""),
            "is_testnet": "testnet" in config.get("environment", "").lower(),
        },
    }


def _build_engine() -> MergedPartialStrategyEngine:
    config = load_merge_config()
    selection_config, benchmark_metrics = load_profile_metrics(config)
    engine = MergedPartialStrategyEngine(
        exchange_base_url=config.get("exchange_base_url", "https://demo-fapi.binance.com"),
        symbol_count=config.get("default_symbol_count", 5),
        profile_name=selection_config.get("default_profile_name"),
        selection_config=selection_config,
        benchmark_metrics=benchmark_metrics,
    )
    engine.select_profile_from_metrics(
        max_drawdown_percent=selection_config.get("current_metrics", {}).get("max_drawdown_percent"),
        positive_months=selection_config.get("current_metrics", {}).get("positive_months"),
        negative_months=selection_config.get("current_metrics", {}).get("negative_months"),
        prefer_aggressive=selection_config.get("prefer_aggressive", False),
    )
    return engine


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "MergedPartialV2Dashboard/1.0"

    def _send_not_found(self, *, method: str, path: str) -> None:
        self._send_json(
            {
                "ok": False,
                "reason": "not_found",
                "method": method,
                "path": path,
                "available_endpoints": {
                    "GET": [
                        "/",
                        "/index.html",
                        "/app.js",
                        "/styles.css",
                        "/api/status",
                        "/api/process",
                    ],
                    "POST": [
                        "/api/autonomous/start",
                        "/api/autonomous/stop",
                        "/api/autonomous/start-live",
                        "/api/actions/health-check",
                        "/api/actions/stop-and-close-all",
                        "/api/status/refresh",
                    ],
                },
            },
            status=HTTPStatus.NOT_FOUND,
        )

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            self._send_file(_dashboard_asset("index.html"), "text/html; charset=utf-8")
            return
        if parsed.path == "/app.js":
            self._send_file(_dashboard_asset("app.js"), "application/javascript; charset=utf-8")
            return
        if parsed.path == "/styles.css":
            self._send_file(_dashboard_asset("styles.css"), "text/css; charset=utf-8")
            return
        if parsed.path == "/api/status":
            self._send_json(load_fast_dashboard_payload())
            return
        if parsed.path == "/api/process":
            self._send_json({"ok": True, "autonomous_process": get_process_status()})
            return
        self._send_not_found(method="GET", path=parsed.path)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            if parsed.path in {"/api/autonomous/start", "/api/autonomous/start-live"}:
                payload = _read_json_body(self)
                is_valid, error_msg = _validate_autonomous_start_payload(payload)
                if not is_valid:
                    self._send_json({
                        "ok": False,
                        "reason": "invalid_payload",
                        "error": error_msg,
                    }, status=400)
                    return
                
                result = start_autonomous_process(
                    live=True,
                    adopt_active_positions=bool(payload.get("adopt_active_positions", True)),
                    interval_seconds=float(payload.get("interval_seconds", 60.0) or 60.0),
                )
                self._send_json(result, status=200 if result.get("ok") else 400)
                return
            if parsed.path == "/api/autonomous/stop":
                result = stop_autonomous_process()
                self._send_json(result, status=200 if result.get("ok") else 400)
                return
            if parsed.path == "/api/actions/health-check":
                payload = _read_json_body(self)
                is_valid, error_msg = _validate_health_check_payload(payload)
                if not is_valid:
                    self._send_json({
                        "ok": False,
                        "reason": "invalid_payload",
                        "error": error_msg,
                    }, status=400)
                    return
                
                engine = _build_engine()
                symbol = str(payload.get("symbol", "BTCUSDT"))
                side = str(payload.get("side", "BUY"))
                quantity = float(payload.get("quantity", 0.001) or 0.001)
                result = engine.execution_client.open_and_close_test_order(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                )
                response_payload = _persist_execution_report(
                    {
                        "mode": "health_check_order",
                        "dry_run": False,
                        "executed": True,
                        "symbol": symbol,
                        "requested_quantity": quantity,
                        "submitted_quantity": result.get("submitted_quantity"),
                        "open_final_status": result.get("open_result", {}).get("final_status"),
                        "close_final_status": result.get("close_result", {}).get("final_status"),
                        "live": True,
                        "result": result,
                        "open_result": result.get("open_result"),
                        "close_result": result.get("close_result"),
                        "reason": "Health-check order completed.",
                    }
                )
                self._send_json({"ok": True, "live": True, "result": result, "report": response_payload})
                return
            if parsed.path == "/api/actions/execute-top":
                self._send_json(
                    {
                        "ok": False,
                        "reason": "manual_execute_disabled_use_autonomous",
                        "detail": "추천 실행은 자동매매 사이클에서 자동 처리됩니다. 자동 시작 버튼을 사용하세요.",
                    },
                    status=410,
                )
                return
            if parsed.path == "/api/actions/stop-and-close-all":
                stop_result = stop_autonomous_process()
                engine = _build_engine()
                close_result = engine.close_all_active_positions(dry_run=False)
                report_payload = _persist_execution_report(
                    {
                        "mode": "stop_and_close_all",
                        "dry_run": False,
                        "executed": True,
                        "symbol": None,
                        "result": close_result,
                        "stop_result": stop_result,
                        "reason": "Stop and close-all requested from dashboard.",
                        "final_status": "COMPLETED" if close_result.get("ok") else "FAILED",
                    }
                )
                self._send_json(
                    {
                        "ok": True,
                        "dry_run": False,
                        "stop_result": stop_result,
                        "close_result": close_result,
                        "report": report_payload,
                    }
                )
                return
            if parsed.path == "/api/status/refresh":
                self._send_json(build_dashboard_payload())
                return
            self._send_not_found(method="POST", path=parsed.path)
        except ValueError as exc:
            self._send_json(
                {
                    "ok": False,
                    "error": "invalid_json",
                    "reason": str(exc),
                    "path": parsed.path,
                },
                status=400,
            )
        except (OSError, IOError) as exc:
            self._send_json(
                {
                    "ok": False,
                    "error": "io_error",
                    "reason": str(exc),
                    "path": parsed.path,
                },
                status=500,
            )
        except Exception as exc:  # pragma: no cover - defensive runtime guard
            self._send_json(
                {
                    "ok": False,
                    "error": "dashboard_post_failed",
                    "reason": f"Unexpected error: {type(exc).__name__}: {exc}",
                    "path": parsed.path,
                },
                status=500,
            )

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def serve_dashboard(host: str = "127.0.0.1", port: int = 8787) -> None:
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    print(f"Dashboard running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
