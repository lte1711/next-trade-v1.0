# Unattended Demo Live Checkpoint

Generated: 2026-04-09
Environment: `https://demo-fapi.binance.com`

## Current Runtime
- Launch metadata: [unattended_live_demo_launch.json](/c:/next-trade-ver1.0/unattended_live_demo_launch.json)
- Live status: [unattended_live_demo_status.json](/c:/next-trade-ver1.0/unattended_live_demo_status.json)
- Live report target: [UNATTENDED_LIVE_DEMO_REPORT.md](/c:/next-trade-ver1.0/UNATTENDED_LIVE_DEMO_REPORT.md)
- Runtime runbook: [UNATTENDED_DEMO_RUNBOOK.md](/c:/next-trade-ver1.0/UNATTENDED_DEMO_RUNBOOK.md)

## Latest Checkpoint
- Runtime status: `running`
- Completed cycles: `1 / 36`
- Latest cycle duration: `87.948s`
- Signals generated so far: `20`
- Trades executed so far: `0`
- Cycle errors so far: `0`
- System errors so far: `0`
- Active positions: `0`
- Pending trades: `0`
- Starting balance: `8547.81396612`
- Current ending balance snapshot: `8547.81396612`

## Monitoring Commands
- Status check:
```powershell
.\.venv\Scripts\python.exe monitor_unattended_demo_runtime.py
```

- Stop runtime:
```powershell
.\.venv\Scripts\python.exe stop_unattended_demo_runtime.py
```

## Immediate Interpretation
- Current unattended demo runtime is healthy.
- The session has passed initialization and completed its first cycle without errors.
- No intervention is warranted at this checkpoint.
