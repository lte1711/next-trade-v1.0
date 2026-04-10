import json
import subprocess
import sys
import time
from pathlib import Path

from scenario_forced_entry_validation import now_iso


RESULT_JSON = Path("final_gate_runner.json")
RESULT_MD = Path("FINAL_GATE_REPORT.md")

SCRIPTS = [
    "binance_testnet_validation_suite.py",
    "supervised_long_session.py --cycles 4 --sleep-seconds 5",
    "scenario_forced_entry_validation.py",
    "multi_symbol_forced_lifecycle.py",
    "short_bias_and_partial_tp_probe.py",
    "trailing_stop_probe.py",
    "live_stop_tightening_probe.py",
    "live_stop_tightening_probe_short.py",
]


def write_json(payload):
    RESULT_JSON.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def write_report(payload):
    lines = [
        "# Final Gate Report",
        "",
        f"Generated: {payload.get('completed_at') or payload.get('started_at')}",
        f"Status: `{payload.get('status')}`",
        "",
        "## Gate Runs",
    ]

    for run in payload.get("runs", []):
        lines.append(
            "- "
            f"{run.get('command')}: "
            f"status={run.get('status')}, "
            f"exit_code={run.get('exit_code')}, "
            f"duration_sec={run.get('duration_sec')}"
        )

    if payload.get("status") == "completed":
        lines.extend(
            [
                "",
                "## Gate Result",
                "- Final gate passed: all required validation scripts completed successfully.",
            ]
        )

    RESULT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    payload = {
        "started_at": now_iso(),
        "completed_at": None,
        "status": "running",
        "runs": [],
    }
    write_json(payload)

    for command in SCRIPTS:
        run = {"command": command, "started_at": now_iso()}
        payload["runs"].append(run)
        write_json(payload)

        started = time.time()
        proc = subprocess.run(
            [sys.executable, *command.split()],
            capture_output=True,
            text=True,
        )
        run["completed_at"] = now_iso()
        run["exit_code"] = proc.returncode
        run["status"] = "passed" if proc.returncode == 0 else "failed"
        run["duration_sec"] = round(time.time() - started, 3)
        if proc.stdout:
            run["stdout_tail"] = proc.stdout[-2000:]
        if proc.stderr:
            run["stderr_tail"] = proc.stderr[-2000:]
        write_json(payload)

        if proc.returncode != 0:
            payload["status"] = "failed"
            break
    else:
        payload["status"] = "completed"

    payload["completed_at"] = now_iso()
    write_json(payload)
    write_report(payload)


if __name__ == "__main__":
    main()
