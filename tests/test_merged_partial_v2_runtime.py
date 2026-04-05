from __future__ import annotations

import sys
import tempfile
import unittest
import json
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "merged_partial_v2" / "src"))
sys.path.insert(0, str(ROOT / "merged_partial_v2"))

import run_merged_partial_v2 as launcher  # noqa: E402
from merged_partial_v2 import dashboard_server  # noqa: E402
from merged_partial_v2 import main as merged_main  # noqa: E402
from merged_partial_v2.simulation.strategy_engine import MergedPartialStrategyEngine  # noqa: E402
from merged_partial_v2.services.symbol_selection_service import SymbolSelectionService  # noqa: E402
from merged_partial_v2.services.paper_decision_service import PaperDecisionService  # noqa: E402
from merged_partial_v2.services import process_manager_service  # noqa: E402
from merged_partial_v2.services.autonomous_trading_service import AutonomousTradingService  # noqa: E402
from merged_partial_v2.services.autonomous_state_service import AutonomousStateService  # noqa: E402


class MergedPartialV2RuntimeTests(unittest.TestCase):
    def test_build_market_snapshot_uses_top_100_then_evaluates_top_40_and_selects_rise_rate_80_plus(self) -> None:
        engine = MergedPartialStrategyEngine(
            profile_name="remote_risk_reference",
            selection_config={},
            benchmark_metrics={},
        )

        top_symbols = [
            {
                "symbol": f"SYM{i:03d}USDT",
                "quote_volume": float(10_000_000 - i),
                "volume": float(1_000_000 - i),
                "price": 1.0 + i,
                "change_percent": 5.0,
            }
            for i in range(100)
        ]
        evaluated_symbols = []
        for index, row in enumerate(top_symbols[:40]):
            evaluated_symbols.append(
                {
                    **row,
                    "bullish_score": 85.0 if index < 5 else 79.0,
                    "profit_potential": 82.0 if index < 5 else 79.0,
                }
            )

        with patch.object(
            engine.public_read_client,
            "get_top_quote_volume_symbols",
            return_value=top_symbols,
        ), patch.object(
            engine.symbol_selection_service,
            "analyze_market_regime",
            return_value="NORMAL",
        ), patch.object(
            engine.market_scoring_service,
            "evaluate_symbols",
            return_value=evaluated_symbols,
        ):
            snapshot = engine.build_market_snapshot(limit=100)

        self.assertEqual(len(snapshot["top_symbols"]), 100)
        self.assertEqual(len(snapshot["evaluation_universe"]), 40)
        self.assertEqual(len(snapshot["evaluated_symbols"]), 40)
        self.assertEqual(len(snapshot["selected_symbols"]), 5)
        self.assertTrue(all(item["profit_potential"] >= 80.0 for item in snapshot["selected_symbols"]))

    def test_symbol_selection_prefers_highest_quote_volume_top_n(self) -> None:
        service = SymbolSelectionService()
        profitable = [
            {"symbol": "AAAUSDT", "quote_volume": 1000.0, "volume": 10.0, "bullish_score": 80.0},
            {"symbol": "BBBUSDT", "quote_volume": 5000.0, "volume": 5.0, "bullish_score": 70.0},
            {"symbol": "CCCUSDT", "quoteVolume": 3000.0, "volume": 30.0, "bullish_score": 90.0},
        ]

        selected = service.select_symbols(profitable, "NORMAL", 2)

        self.assertEqual([row["symbol"] for row in selected], ["BBBUSDT", "CCCUSDT"])

    def test_paper_decision_splits_total_capital_across_up_to_five_symbols(self) -> None:
        profile = {
            "name": "remote_risk_reference",
            "capital_utilization_percent": 100.0,
            "reserve_cash_percent": 0.0,
            "min_allocation": 100.0,
            "max_symbols_by_regime": {"NORMAL": 5, "HIGH_VOLATILITY": 5, "EXTREME": 5},
        }
        service = PaperDecisionService(profile)
        market_snapshot = {
            "market_regime": "NORMAL",
            "selected_symbols": [
                {"symbol": "AAAUSDT", "price": 10.0, "bullish_score": 90.0, "profit_potential": 85.0},
                {"symbol": "BBBUSDT", "price": 20.0, "bullish_score": 91.0, "profit_potential": 86.0},
                {"symbol": "CCCUSDT", "price": 25.0, "bullish_score": 92.0, "profit_potential": 87.0},
                {"symbol": "DDDUSDT", "price": 40.0, "bullish_score": 93.0, "profit_potential": 88.0},
                {"symbol": "EEEUSDT", "price": 50.0, "bullish_score": 94.0, "profit_potential": 89.0},
            ],
        }
        account_context = {
            "account": {"wallet_balance": 1000.0, "account_equity": 1000.0},
            "positions": {
                "active_positions": [
                    {"symbol": "AAAUSDT", "positionAmt": 10.0, "markPrice": 10.0},
                ]
            },
        }

        decision = service.build_decision(market_snapshot, account_context, {"ok": True, "block_new_entries": False})

        self.assertEqual(decision["target_symbol_count"], 5)
        self.assertEqual(decision["available_slots"], 0)
        self.assertAlmostEqual(decision["target_allocation_per_symbol"], 200.0)
        self.assertEqual(len(decision["recommendations"]), 5)
        new_entries = [item for item in decision["recommendations"] if item["action"] == "new_entry"]
        scale_ins = [item for item in decision["recommendations"] if item["action"] == "scale_in"]
        self.assertEqual(len(new_entries), 4)
        self.assertEqual(len(scale_ins), 1)

    def test_persist_execution_report_writes_dashboard_action_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            payload = {
                "mode": "execute_top_recommendation",
                "dry_run": False,
                "executed": True,
                "symbol": "BTCUSDT",
                "result": {"final_status": "FILLED"},
                "reason": "Submitted top recommendation.",
            }

            with patch.object(dashboard_server, "merged_root", return_value=root):
                saved = dashboard_server._persist_execution_report(payload)

            report_path = root / "execution_reports" / "last_execution_report.json"
            self.assertTrue(report_path.exists())
            written = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(written["mode"], "execute_top_recommendation")
            self.assertEqual(written["symbol"], "BTCUSDT")
            self.assertEqual(written["result"]["final_status"], "FILLED")
            self.assertIn("execution complete", written["alert_summary"])
            self.assertEqual(saved["report_path"], str(report_path))

    def test_load_fast_dashboard_payload_builds_full_snapshot_when_cache_missing_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            snapshot_path = root / "merged_snapshot.json"
            snapshot_path.write_text(
                json.dumps(
                    {
                        "paper_decision": {"recommendations": [], "blocked": [], "risk_gate": {}},
                        "paper_decision_summary": {"recommended_orders": 0, "blocked_candidates": 0},
                        "operational_summary": {},
                        "market": {},
                        "account": {"account": {}, "positions": {"active_positions": [], "active_position_count": 0}},
                        "last_execution_report": {"ok": False, "reason": "no_execution_report"},
                        "last_autonomous_report": {"ok": False, "reason": "no_autonomous_report"},
                    }
                ),
                encoding="utf-8",
            )
            built_payload = {
                "ok": True,
                "snapshot": {
                    "operational_summary": {"selected_profile": "remote_risk_reference"},
                    "market": {"profile": {"name": "remote_risk_reference"}},
                    "account": {"account": {"account_equity": 100.0}},
                },
                "autonomous_process": {"ok": True, "running": False},
            }

            with patch.object(dashboard_server, "merged_root", return_value=root), patch.object(
                dashboard_server,
                "build_dashboard_payload",
                return_value=built_payload,
            ):
                result = dashboard_server.load_fast_dashboard_payload()

            self.assertEqual(result, built_payload)

    def test_runtime_overlay_prefers_newer_autonomous_action_over_stale_execution_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            execution_dir = root / "execution_reports"
            autonomous_dir = root / "autonomous_reports"
            runtime_dir = root / "runtime"
            execution_dir.mkdir(parents=True, exist_ok=True)
            autonomous_dir.mkdir(parents=True, exist_ok=True)
            runtime_dir.mkdir(parents=True, exist_ok=True)

            execution_report = {
                "mode": "health_check_order",
                "dry_run": True,
                "executed": False,
                "symbol": "BTCUSDT",
                "reason": "dry preview",
                "alert_summary": "health-check complete | symbol=BTCUSDT | open=- | close=-",
            }
            autonomous_report = {
                "mode": "autonomous_cycle",
                "ts": "2026-04-05T13:36:14+00:00",
                "dry_run": False,
                "entry_count": 1,
                "exit_count": 0,
                "decision_line": "autonomous cycle | entries=1 | exits=0 | managed=5",
                "entries": [
                    {
                        "symbol": "HIPPOUSDT",
                        "result": {
                            "final_status": "FILLED",
                        },
                    }
                ],
                "exits": [],
            }

            (execution_dir / "last_execution_report.json").write_text(
                json.dumps(execution_report),
                encoding="utf-8",
            )
            (autonomous_dir / "last_autonomous_report.json").write_text(
                json.dumps(autonomous_report),
                encoding="utf-8",
            )

            snapshot = {
                "last_execution_report": {
                    "ok": True,
                    "path": str(execution_dir / "last_execution_report.json"),
                    "mode": "health_check_order",
                    "executed": False,
                    "alert_summary": execution_report["alert_summary"],
                    "payload": execution_report,
                }
            }

            with patch.object(dashboard_server, "merged_root", return_value=root):
                result = dashboard_server._apply_runtime_overlay(snapshot)

            self.assertEqual(result["last_execution_report"]["mode"], "autonomous_cycle")
            self.assertEqual(result["last_execution_report"]["symbol"], "HIPPOUSDT")
            self.assertIn("auto entry", result["last_execution_report"]["alert_summary"])

    def test_build_backtest_scope_summary_aggregates_active_symbols(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            report_dir = root / "backtest_reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            report_payload = {
                "trade_history": [
                    {"date": "2026-01-01", "symbol": "BTCUSDT", "action": "ENTRY", "allocation": 100.0},
                    {"date": "2026-01-02", "symbol": "BTCUSDT", "action": "TAKE_PROFIT", "pnl_percent": 10.0, "realized_pnl": 10.0},
                    {"date": "2026-01-03", "symbol": "ETHUSDT", "action": "ENTRY", "allocation": 200.0},
                    {"date": "2026-01-04", "symbol": "ETHUSDT", "action": "LOSS_THRESHOLD", "pnl_percent": -20.0, "realized_pnl": -40.0},
                ]
            }
            (report_dir / "remote_risk_reference_1year_backtest.json").write_text(
                json.dumps(report_payload),
                encoding="utf-8",
            )

            with patch.object(merged_main, "merged_root", return_value=root), patch.object(
                merged_main,
                "resolve_resource",
                side_effect=lambda path: root / path,
            ):
                summary = merged_main.build_backtest_scope_summary(
                    {
                        "selected_profile": "remote_risk_reference",
                        "selected_profile_benchmark": {
                            "final_pnl_percent": 44.0,
                            "max_drawdown_percent": -16.54,
                        },
                    },
                    {"selected_symbols": []},
                    {
                        "positions": {
                            "active_positions": [
                                {"symbol": "BTCUSDT"},
                                {"symbol": "ETHUSDT"},
                            ]
                        }
                    },
                )

            self.assertEqual(summary["scope"], "active_symbols")
            self.assertEqual(summary["matched_symbol_count"], 2)
            self.assertAlmostEqual(summary["final_pnl_percent"], -10.0)
            self.assertAlmostEqual(summary["max_drawdown_percent"], -20.0)

    def test_build_backtest_scope_summary_falls_back_to_price_path_for_untraded_symbols(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            report_dir = root / "backtest_reports"
            input_dir = root / "integrated_strategy_test" / "src"
            report_dir.mkdir(parents=True, exist_ok=True)
            input_dir.mkdir(parents=True, exist_ok=True)
            report_payload = {
                "analysis_basis": {
                    "source_path": str(input_dir / "real_market_backtest_input.json"),
                },
                "trade_history": [],
            }
            input_payload = [
                {"date": "2026-01-01", "symbols": {"BTCUSDT": {"price": 100.0}, "ETHUSDT": {"price": 100.0}}},
                {"date": "2026-01-02", "symbols": {"BTCUSDT": {"price": 120.0}, "ETHUSDT": {"price": 80.0}}},
                {"date": "2026-01-03", "symbols": {"BTCUSDT": {"price": 110.0}, "ETHUSDT": {"price": 70.0}}},
            ]
            (report_dir / "remote_risk_reference_1year_backtest.json").write_text(
                json.dumps(report_payload),
                encoding="utf-8",
            )
            (input_dir / "real_market_backtest_input.json").write_text(
                json.dumps(input_payload),
                encoding="utf-8",
            )

            with patch.object(merged_main, "merged_root", return_value=root), patch.object(
                merged_main,
                "resolve_resource",
                side_effect=lambda path: root / path,
            ):
                summary = merged_main.build_backtest_scope_summary(
                    {
                        "selected_profile": "remote_risk_reference",
                        "selected_profile_benchmark": {
                            "final_pnl_percent": 44.0,
                            "max_drawdown_percent": -16.54,
                        },
                    },
                    {"selected_symbols": []},
                    {
                        "positions": {
                            "active_positions": [
                                {"symbol": "BTCUSDT"},
                                {"symbol": "ETHUSDT"},
                            ]
                        }
                    },
                )

            self.assertEqual(summary["scope"], "active_symbols_price_path")
            self.assertEqual(summary["matched_symbol_count"], 2)
            self.assertAlmostEqual(summary["final_pnl_percent"], -10.0)
            self.assertAlmostEqual(summary["max_drawdown_percent"], -30.0)

    def test_finalize_autonomous_process_clears_matching_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = Path(tmpdir)
            record_path = runtime_dir / "autonomous_process.json"
            payload = {
                "pid": 4242,
                "mode": "autonomous_loop",
                "live": True,
                "started_at": "2026-04-05T12:19:56+00:00",
            }

            with patch.object(process_manager_service, "_runtime_dir", return_value=runtime_dir):
                process_manager_service.write_process_record(payload)
                result = process_manager_service.finalize_autonomous_process(4242, exit_reason="crashed")

            self.assertTrue(result["ok"])
            self.assertEqual(result["exit_reason"], "crashed")
            self.assertFalse(record_path.exists())

    def test_finalize_autonomous_process_rejects_pid_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = Path(tmpdir)

            with patch.object(process_manager_service, "_runtime_dir", return_value=runtime_dir):
                process_manager_service.write_process_record({"pid": 1111, "mode": "autonomous_loop"})
                result = process_manager_service.finalize_autonomous_process(2222, exit_reason="crashed")

            self.assertFalse(result["ok"])
            self.assertEqual(result["reason"], "pid_mismatch")

    def test_dashboard_not_found_payload_lists_post_endpoints(self) -> None:
        sent: list[tuple[int, dict]] = []

        class DummyHandler:
            def _send_json(self, payload: dict, status: int = 200) -> None:
                sent.append((status, payload))

        dashboard_server.DashboardHandler._send_not_found(  # type: ignore[misc]
            DummyHandler(),
            method="POST",
            path="/wrong",
        )

        self.assertEqual(sent[0][0], 404)
        self.assertIn("/api/autonomous/start", sent[0][1]["available_endpoints"]["POST"])
        self.assertIn("/api/autonomous/start-live", sent[0][1]["available_endpoints"]["POST"])
        self.assertNotIn("/api/autonomous/start-dry", sent[0][1]["available_endpoints"]["POST"])
        self.assertNotIn("/api/actions/execute-top", sent[0][1]["available_endpoints"]["POST"])

    def test_installed_startup_default_forces_live_autonomous_loop(self) -> None:
        calls: list[dict] = []

        with patch.object(
            launcher,
            "run_autonomous_loop",
            side_effect=lambda engine, config, dry_run, adopt_active_positions, cycles, interval_seconds: calls.append(
                {
                    "dry_run": dry_run,
                    "adopt_active_positions": adopt_active_positions,
                    "cycles": cycles,
                    "interval_seconds": interval_seconds,
                }
            ) or {"ok": True},
        ):
            launcher.run_installed_startup_default(
                engine=object(),
                config={
                    "startup": {
                        "default_mode_when_installed": "autonomous_loop",
                        "live_by_default_when_installed": False,
                        "autonomous_cycles_when_installed": 0,
                        "autonomous_interval_seconds_when_installed": 60.0,
                    }
                },
            )

        self.assertEqual(len(calls), 1)
        self.assertFalse(calls[0]["dry_run"])
        self.assertEqual(calls[0]["cycles"], 1)

    def test_start_autonomous_process_forces_live_process_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = Path(tmpdir)

            with patch.object(process_manager_service, "_runtime_dir", return_value=runtime_dir), patch.object(
                process_manager_service,
                "get_process_status",
                return_value={"ok": True, "running": False},
            ), patch.object(
                process_manager_service.threading.Thread,
                "start",
                lambda self: None,
            ):
                result = process_manager_service.start_autonomous_process(
                    live=False,
                    adopt_active_positions=True,
                    interval_seconds=60.0,
                )

            self.assertTrue(result["ok"])
            self.assertTrue(result["record"]["live"])
            self.assertIn("--live", result["record"]["command"])

    def test_autonomous_cycle_persists_latest_execution_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            service = AutonomousTradingService(engine=object(), merged_root=root, autonomous_config={})
            report = {
                "mode": "autonomous_cycle",
                "ts": "2026-04-06T00:00:00+00:00",
                "dry_run": True,
                "decision_line": "autonomous cycle | entries=1 | exits=0 | managed=1",
                "entries": [
                    {
                        "symbol": "SIRENUSDT",
                        "result": {"final_status": "FILLED"},
                    }
                ],
                "exits": [],
            }

            service._persist_last_execution_report(report)

            report_path = root / "execution_reports" / "last_execution_report.json"
            self.assertTrue(report_path.exists())
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["mode"], "autonomous_cycle")
            self.assertEqual(payload["symbol"], "SIRENUSDT")
            self.assertIn("auto entry", payload["alert_summary"])

    def test_register_entry_marks_dry_run_simulated_position(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            service = AutonomousStateService(Path(tmpdir))
            state = service.register_entry(
                service.load(),
                symbol="SIRENUSDT",
                order_result={"dry_run": True, "quantity": 10, "price": 1.23, "final_status": "FILLED"},
                position_snapshot={
                    "symbol": "SIRENUSDT",
                    "positionAmt": 10,
                    "entryPrice": 1.23,
                    "markPrice": 1.23,
                    "unRealizedProfit": 0.0,
                    "positionSide": "BOTH",
                    "leverage": 20,
                    "marginType": "cross",
                },
                recommendation={"allocation": 100.0},
            )
            managed = state["managed_positions"]["SIRENUSDT"]
            self.assertTrue(managed["dry_run_simulated"])

    def test_dry_run_autonomous_state_is_saved_and_visible(self) -> None:
        class _PrivateReadClient:
            def get_positions(self) -> dict:
                return {"active_positions": []}

        class _Engine:
            def __init__(self) -> None:
                self.private_read_client = _PrivateReadClient()

            def build_paper_decision(self, limit: int = 80) -> dict:
                return {
                    "market": {
                        "profile": {"name": "remote_risk_reference", "minimum_hold_bars": 2, "take_profit": 3.0, "replacement_threshold": -1.3},
                        "market_regime": "NORMAL",
                        "evaluated_symbols": [],
                        "selected_symbols": [{"symbol": "SIRENUSDT"}],
                    },
                    "account": {"positions": {"active_positions": []}},
                    "paper_decision": {
                        "risk_gate": {"ok": True, "block_new_entries": False},
                        "recommendations": [
                            {
                                "symbol": "SIRENUSDT",
                                "side": "BUY",
                                "action": "new_entry",
                                "allocation": 100.0,
                                "estimated_quantity": 10.0,
                                "entry_price_reference": 1.23,
                                "profile_name": "remote_risk_reference",
                                "market_regime": "NORMAL",
                            }
                        ],
                    },
                }

            def submit_order(self, payload: dict) -> dict:
                return {
                    "ok": True,
                    "dry_run": True,
                    "trace_id": payload["trace_id"],
                    "symbol": payload["symbol"],
                    "side": payload["side"],
                    "quantity": payload["qty"],
                    "price": 1.23,
                    "status": "FILLED",
                    "final_status": "FILLED",
                }

        with tempfile.TemporaryDirectory() as tmpdir:
            service = AutonomousTradingService(
                engine=_Engine(),
                merged_root=Path(tmpdir),
                autonomous_config={"cycle_interval_seconds": 60.0},
            )

            service.run_cycle(dry_run=True, adopt_existing_positions=False)

            state_path = Path(tmpdir) / "runtime" / "autonomous_state.json"
            self.assertTrue(state_path.exists())
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertIn("SIRENUSDT", state["managed_positions"])

    def test_run_autonomous_loop_continues_after_cycle_exception(self) -> None:
        class FakeService:
            def __init__(self) -> None:
                self.run_cycle_calls = 0
                self.error_reports: list[dict] = []

            def run_cycle(self, *, dry_run: bool, adopt_existing_positions: bool | None = None) -> dict:
                self.run_cycle_calls += 1
                if self.run_cycle_calls == 1:
                    raise RuntimeError("boom")
                return {"mode": "autonomous_cycle", "ts": f"2026-04-05T12:00:0{self.run_cycle_calls}Z"}

            def write_loop_error_report(
                self,
                *,
                error: BaseException,
                dry_run: bool,
                cycle_index: int,
                retry_sleep_seconds: float,
            ) -> dict:
                payload = {
                    "mode": "autonomous_cycle_error",
                    "ts": "2026-04-05T12:00:00Z",
                    "error": str(error),
                    "cycle_index": cycle_index,
                    "retry_sleep_seconds": retry_sleep_seconds,
                }
                self.error_reports.append(payload)
                return payload

        service = FakeService()
        heartbeats: list[tuple[int, str | None]] = []
        finalized: list[str] = []

        with patch.object(launcher, "_build_autonomous_service", return_value=service), patch.object(
            launcher,
            "get_process_status",
            return_value={"pid": 999},
        ), patch.object(
            launcher,
            "os",
        ) as mock_os, patch.object(
            launcher,
            "heartbeat_autonomous_process",
            side_effect=lambda pid, last_cycle_at=None: heartbeats.append((pid, last_cycle_at)),
        ), patch.object(
            launcher,
            "finalize_autonomous_process",
            side_effect=lambda pid, exit_reason: finalized.append(exit_reason),
        ), patch.object(
            launcher,
            "_write_crash_log",
            lambda exc: None,
        ), patch.object(
            launcher.time,
            "sleep",
            lambda secs: None,
        ):
            mock_os.getpid.return_value = 999
            result = launcher.run_autonomous_loop(
                engine=object(),
                config={},
                dry_run=False,
                adopt_active_positions=True,
                cycles=2,
                interval_seconds=0.0,
            )

        self.assertEqual(service.run_cycle_calls, 2)
        self.assertEqual(service.error_reports[0]["cycle_index"], 0)
        self.assertEqual(result["mode"], "autonomous_cycle")
        self.assertEqual(finalized, ["manual_stop"])
        self.assertEqual(len(heartbeats), 2)

    def test_run_autonomous_loop_stops_on_keyboard_interrupt(self) -> None:
        class FakeService:
            def run_cycle(self, *, dry_run: bool, adopt_existing_positions: bool | None = None) -> dict:
                raise KeyboardInterrupt()

        finalized: list[str] = []

        with patch.object(launcher, "_build_autonomous_service", return_value=FakeService()), patch.object(
            launcher,
            "get_process_status",
            return_value={"pid": 999},
        ), patch.object(
            launcher,
            "os",
        ) as mock_os, patch.object(
            launcher,
            "finalize_autonomous_process",
            side_effect=lambda pid, exit_reason: finalized.append(exit_reason),
        ):
            mock_os.getpid.return_value = 999
            result = launcher.run_autonomous_loop(
                engine=object(),
                config={},
                dry_run=False,
                adopt_active_positions=True,
                cycles=1,
                interval_seconds=0.0,
            )

        self.assertEqual(result, {})
        self.assertEqual(finalized, ["keyboard_interrupt"])

    def test_run_autonomous_loop_uses_infinite_mode_when_cycles_zero(self) -> None:
        class FakeService:
            def __init__(self) -> None:
                self.run_cycle_calls = 0

            def run_cycle(self, *, dry_run: bool, adopt_existing_positions: bool | None = None) -> dict:
                self.run_cycle_calls += 1
                if self.run_cycle_calls >= 3:
                    raise KeyboardInterrupt()
                return {"mode": "autonomous_cycle", "ts": f"2026-04-05T12:00:0{self.run_cycle_calls}Z"}

        service = FakeService()
        finalized: list[str] = []

        with patch.object(launcher, "_build_autonomous_service", return_value=service), patch.object(
            launcher,
            "get_process_status",
            return_value={"pid": 999},
        ), patch.object(
            launcher,
            "os",
        ) as mock_os, patch.object(
            launcher,
            "heartbeat_autonomous_process",
            lambda pid, last_cycle_at=None: None,
        ), patch.object(
            launcher,
            "finalize_autonomous_process",
            side_effect=lambda pid, exit_reason: finalized.append(exit_reason),
        ), patch.object(
            launcher.time,
            "sleep",
            lambda secs: None,
        ):
            mock_os.getpid.return_value = 999
            result = launcher.run_autonomous_loop(
                engine=object(),
                config={},
                dry_run=False,
                adopt_active_positions=True,
                cycles=0,
                interval_seconds=0.0,
            )

        self.assertEqual(service.run_cycle_calls, 3)
        self.assertEqual(result["mode"], "autonomous_cycle")
        self.assertEqual(finalized, ["keyboard_interrupt"])


if __name__ == "__main__":
    unittest.main()
