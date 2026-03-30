from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def _json_sidecar_lock_path(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".lock")


class JsonFileLock:
    def __init__(self, path: Path, timeout_sec: float = 5.0) -> None:
        self.path = path
        self.timeout_sec = timeout_sec
        self.fd: int | None = None

    def __enter__(self) -> "JsonFileLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.time() + self.timeout_sec
        while True:
            try:
                self.fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self.fd, str(os.getpid()).encode("utf-8"))
                return self
            except FileExistsError:
                if time.time() >= deadline:
                    raise TimeoutError(f"json lock timeout: {self.path}")
                time.sleep(0.05)

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


@dataclass
class RunnerOutputPaths:
    evidence_path: Path
    summary_path: Path
    runtime_health_summary_path: Path
    portfolio_snapshot_path: Path
    trade_outcomes_path: Path
    strategy_performance_path: Path
    global_risk_monitor_path: Path
    market_regime_path: Path
    portfolio_allocation_path: Path


class RunnerOutputStore:
    def __init__(self, paths: RunnerOutputPaths) -> None:
        self.paths = paths

    def log_event(self, *, symbol: str, profile: str, event_type: str, payload: dict[str, Any], ts: str) -> None:
        row = {
            "ts": ts,
            "event_type": event_type,
            "symbol": symbol,
            "payload": payload,
            "profile": profile,
        }
        append_jsonl(self.paths.evidence_path, row)

    def write_global_risk_monitor(self, payload: dict[str, Any]) -> None:
        self.paths.global_risk_monitor_path.parent.mkdir(parents=True, exist_ok=True)
        self.paths.global_risk_monitor_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def write_market_regime_snapshot(self, payload: dict[str, Any]) -> None:
        self.paths.market_regime_path.parent.mkdir(parents=True, exist_ok=True)
        self.paths.market_regime_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def write_portfolio_allocation_snapshot(self, payload: dict[str, Any]) -> None:
        self.paths.portfolio_allocation_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = _json_sidecar_lock_path(self.paths.portfolio_allocation_path)
        with JsonFileLock(lock_path):
            save_json(self.paths.portfolio_allocation_path, payload)

    def sync_allocation_snapshot_into_runtime_summaries(
        self,
        *,
        payload: dict[str, Any],
        allocation_top: list[dict[str, Any]],
        allocation_target_symbols: list[str],
        allocation_target_symbol_count: int,
    ) -> None:
        if not isinstance(payload, dict) or not payload:
            return

        if self.paths.summary_path.exists():
            summary_lock_path = _json_sidecar_lock_path(self.paths.summary_path)
            with JsonFileLock(summary_lock_path):
                summary = load_json(self.paths.summary_path, {})
                if isinstance(summary, dict) and summary:
                    summary["allocation_top"] = allocation_top
                    summary["allocation_target_symbols"] = allocation_target_symbols
                    summary["allocation_target_symbol_count"] = allocation_target_symbol_count
                    summary["portfolio_allocation_path"] = str(self.paths.portfolio_allocation_path)
                    save_json(self.paths.summary_path, summary)

        if self.paths.runtime_health_summary_path.exists():
            health_lock_path = _json_sidecar_lock_path(self.paths.runtime_health_summary_path)
            with JsonFileLock(health_lock_path):
                health = load_json(self.paths.runtime_health_summary_path, {})
                if isinstance(health, dict) and health:
                    top_allocation = allocation_top[0] if allocation_top else {}
                    health["allocation_target_symbol_count"] = allocation_target_symbol_count
                    health["top_allocation_symbol"] = top_allocation.get("symbol", "-")
                    health["top_allocation_weight"] = top_allocation.get("weight", 0.0)
                    save_json(self.paths.runtime_health_summary_path, health)

    def write_portfolio_snapshot(self, payload: dict[str, Any]) -> None:
        self.paths.portfolio_snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        self.paths.portfolio_snapshot_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def append_trade_outcome(
        self,
        payload: dict[str, Any],
        *,
        normalize_payload: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> None:
        lock_path = _json_sidecar_lock_path(self.paths.trade_outcomes_path)
        with JsonFileLock(lock_path):
            rows = load_json(self.paths.trade_outcomes_path, [])
            if not isinstance(rows, list):
                rows = []
            rows.append(normalize_payload(payload))
            save_json(self.paths.trade_outcomes_path, rows)

    def load_strategy_performance(self) -> dict[str, Any]:
        data = load_json(self.paths.strategy_performance_path, {})
        return data if isinstance(data, dict) else {}

    def save_strategy_performance(self, payload: dict[str, Any]) -> None:
        save_json(self.paths.strategy_performance_path, payload)

    def write_summary(self, payload: dict[str, Any]) -> None:
        lock_path = _json_sidecar_lock_path(self.paths.summary_path)
        with JsonFileLock(lock_path):
            save_json(self.paths.summary_path, payload)

    def write_runtime_health_summary(self, payload: dict[str, Any]) -> None:
        self.paths.runtime_health_summary_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = _json_sidecar_lock_path(self.paths.runtime_health_summary_path)
        with JsonFileLock(lock_path):
            save_json(self.paths.runtime_health_summary_path, payload)
