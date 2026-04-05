"""Minimal local dashboard server for merged_partial_v2."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
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


def _read_json_body(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0") or 0)
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def build_dashboard_payload() -> dict:
    snapshot = build_snapshot_payload()
    write_snapshot_payload(snapshot)
    return {
        "ok": True,
        "snapshot": snapshot,
        "autonomous_process": get_process_status(),
    }


def load_cached_dashboard_payload() -> dict:
    snapshot_path = merged_root() / "merged_snapshot.json"
    if snapshot_path.exists():
        with snapshot_path.open("r", encoding="utf-8-sig") as handle:
            snapshot = json.load(handle)
    else:
        snapshot = build_snapshot_payload()
        write_snapshot_payload(snapshot)
    return {
        "ok": True,
        "snapshot": snapshot,
        "autonomous_process": get_process_status(),
    }


def _build_engine() -> MergedPartialStrategyEngine:
    config = load_merge_config()
    selection_config, benchmark_metrics = load_profile_metrics(config)
    engine = MergedPartialStrategyEngine(
        exchange_base_url=config.get("exchange_base_url", "https://demo-fapi.binance.com"),
        symbol_count=config.get("default_symbol_count", 10),
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
            self._send_json(load_cached_dashboard_payload())
            return
        if parsed.path == "/api/process":
            self._send_json({"ok": True, "autonomous_process": get_process_status()})
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/autonomous/start":
            payload = _read_json_body(self)
            result = start_autonomous_process(
                live=bool(payload.get("live", False)),
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
            live = bool(payload.get("live", False))
            engine = _build_engine()
            symbol = str(payload.get("symbol", "BTCUSDT"))
            side = str(payload.get("side", "BUY"))
            quantity = float(payload.get("quantity", 0.001) or 0.001)
            if live:
                result = engine.execution_client.open_and_close_test_order(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                )
                self._send_json({"ok": True, "live": True, "result": result})
                return
            preview = {
                "mode": "health_check_preview",
                "symbol": symbol,
                "side": side,
                "requested_quantity": quantity,
                "reason": "Dry mode preview only. Toggle live mode to send the testnet order.",
            }
            self._send_json({"ok": True, "live": False, "result": {"preview": preview}})
            return
        if parsed.path == "/api/actions/execute-top":
            payload = _read_json_body(self)
            dry_run = not bool(payload.get("live", False))
            engine = _build_engine()
            snapshot = engine.build_paper_decision(limit=80)
            recommendations = list(snapshot["paper_decision"].get("recommendations", []))
            if not recommendations:
                self._send_json(
                    {"ok": False, "reason": "no_recommendation", "paper_decision": snapshot["paper_decision"]},
                    status=400,
                )
                return
            recommendation = recommendations[0]
            order_payload = {
                "symbol": recommendation["symbol"],
                "side": recommendation.get("side", "BUY"),
                "type": "MARKET",
                "qty": recommendation.get("estimated_quantity", 0.0),
                "trace_id": f"dashboard-exec-{recommendation['symbol'].lower()}",
                "dry_run": dry_run,
                "wait_for_fill": not dry_run,
                "status_timeout_seconds": 8.0,
            }
            result = engine.submit_order(order_payload)
            self._send_json(
                {
                    "ok": True,
                    "dry_run": dry_run,
                    "recommendation": recommendation,
                    "order_payload": order_payload,
                    "result": result,
                }
            )
            return
        if parsed.path == "/api/actions/stop-and-close-all":
            payload = _read_json_body(self)
            dry_run = not bool(payload.get("live", False))
            stop_result = stop_autonomous_process()
            engine = _build_engine()
            close_result = engine.close_all_active_positions(dry_run=dry_run)
            self._send_json(
                {
                    "ok": True,
                    "dry_run": dry_run,
                    "stop_result": stop_result,
                    "close_result": close_result,
                }
            )
            return
        if parsed.path == "/api/status/refresh":
            self._send_json(build_dashboard_payload())
            return
        self.send_error(HTTPStatus.NOT_FOUND)

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
