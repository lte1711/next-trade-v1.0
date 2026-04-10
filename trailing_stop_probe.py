import json
from pathlib import Path

from main_runtime import TradingRuntime
from scenario_forced_entry_validation import now_iso


RESULT_JSON = Path("trailing_stop_probe.json")
RESULT_MD = Path("TRAILING_STOP_PROBE_REPORT.md")


def write_json(payload):
    RESULT_JSON.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def write_report(payload):
    lines = [
        "# Trailing Stop Probe Report",
        "",
        f"Generated: {payload.get('completed_at') or payload.get('started_at')}",
        f"Status: `{payload.get('status')}`",
        "",
        "## Cases",
    ]

    for case in payload.get("cases", []):
        lines.append(
            "- "
            f"{case.get('name')}: "
            f"profit_pct={case.get('profit_pct')}, "
            f"updated={case.get('updated')}, "
            f"managed_stop={case.get('managed_stop_price')}, "
            f"expected_direction={case.get('expected_direction')}"
        )

    if payload.get("next_evolution_targets"):
        lines.extend(["", "## Next Evolution Targets"])
        for item in payload["next_evolution_targets"]:
            lines.append(f"- {item}")

    RESULT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    payload = {
        "started_at": now_iso(),
        "completed_at": None,
        "status": "running",
        "cases": [],
        "system_errors": None,
        "next_evolution_targets": [],
    }
    write_json(payload)

    runtime = None
    try:
        runtime = TradingRuntime()
        if not runtime.initialized:
            raise RuntimeError("TradingRuntime failed to initialize")

        manager = runtime.partial_take_profit_manager
        cases = [
            {
                "name": "long_trailing_above_2pct",
                "symbol": "TRAIL_LONG",
                "position": {"markPrice": 103.0, "positionAmt": 2.0, "positionSide": "BOTH"},
                "entry_price": 100.0,
                "trail_pct": 0.01,
                "expected_direction": "raise_long_stop",
            },
            {
                "name": "short_trailing_above_2pct",
                "symbol": "TRAIL_SHORT",
                "position": {"markPrice": 97.0, "positionAmt": -2.0, "positionSide": "BOTH"},
                "entry_price": 100.0,
                "trail_pct": 0.01,
                "expected_direction": "lower_short_stop",
            },
            {
                "name": "long_trailing_below_threshold",
                "symbol": "TRAIL_LONG_LOW",
                "position": {"markPrice": 101.5, "positionAmt": 2.0, "positionSide": "BOTH"},
                "entry_price": 100.0,
                "trail_pct": 0.01,
                "expected_direction": "no_update",
            },
        ]

        for case in cases:
            manager.clear_position_management_state(case["symbol"])
            updated = manager.update_trailing_stop(
                symbol=case["symbol"],
                position=case["position"],
                entry_price=case["entry_price"],
                trail_pct=case["trail_pct"],
            )
            payload["cases"].append(
                {
                    "name": case["name"],
                    "symbol": case["symbol"],
                    "profit_pct": round(
                        manager.get_position_profit_pct(case["position"], case["entry_price"]),
                        6,
                    ),
                    "updated": updated,
                    "managed_stop_price": manager.managed_stop_prices.get(case["symbol"]),
                    "expected_direction": case["expected_direction"],
                }
            )

        payload["status"] = "completed"
        payload["next_evolution_targets"] = [
            "Add a live scenario that tightens actual protective algo stop orders after profit expansion.",
            "Promote the trailing-stop probe into the regression gate summary for routine demo validation."
        ]
    except Exception as exc:
        payload["status"] = "failed"
        payload["error"] = str(exc)
    finally:
        if runtime is not None:
            payload["system_errors"] = len(runtime.trading_results.get("system_errors", []))
        payload["completed_at"] = now_iso()
        write_json(payload)
        write_report(payload)


if __name__ == "__main__":
    main()
