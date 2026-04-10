# Unattended Demo Runbook

Environment: `https://demo-fapi.binance.com`

## Preflight
- Confirm [FINAL_OPERATIONAL_READINESS.md](/c:/next-trade-ver1.0/FINAL_OPERATIONAL_READINESS.md) is current.
- Confirm [FINAL_GATE_REPORT.md](/c:/next-trade-ver1.0/FINAL_GATE_REPORT.md) is `PASS`.

## Start
- Command:
```powershell
.\.venv\Scripts\python.exe launch_unattended_demo_runtime.py
```

Artifacts:
- Launch metadata: [unattended_live_demo_launch.json](/c:/next-trade-ver1.0/unattended_live_demo_launch.json)
- Runtime status: [unattended_live_demo_status.json](/c:/next-trade-ver1.0/unattended_live_demo_status.json)
- Runtime report: [UNATTENDED_LIVE_DEMO_REPORT.md](/c:/next-trade-ver1.0/UNATTENDED_LIVE_DEMO_REPORT.md)

## Monitor
- Command:
```powershell
.\.venv\Scripts\python.exe monitor_unattended_demo_runtime.py
```

Watch for:
- `status=running` or `status=completed`
- `system_errors=0`
- `cycles_with_errors=0`
- no unexpected active positions or pending trades unless intentionally produced by live signals

## Stop
- Command:
```powershell
.\.venv\Scripts\python.exe stop_unattended_demo_runtime.py
```

## Operational Rule
- If final gate is not `PASS`, do not start unattended demo runtime.
- If unattended status shows `system_errors > 0`, pause further runtime extension and inspect the latest evidence first.
