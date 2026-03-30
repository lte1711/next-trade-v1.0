# Runtime Health Action Runbook

This runbook defines how to interpret runtime health outputs and what action to take.

## Primary Files

- Validation snapshot: `reports/<yyyy-mm-dd>/honey_execution_reports/runtime_health_validation_latest.json`
- Machine health source: `logs/runtime/runtime_health_summary.json`
- Human summary: `logs/runtime/profitmax_v1_summary.json`
- Autoguard log: `reports/<yyyy-mm-dd>/honey_execution_reports/phase5_autoguard_log.txt`
- Restart state: `reports/<yyyy-mm-dd>/honey_execution_reports/runtime_health_restart_state.json`

## Core Fields

- `status`
  - `PASS`: runtime is healthy.
  - `WARN`: degraded but not necessarily restart-worthy.
  - `FAIL`: runtime has at least one hard failure signal.
- `action_class`
  - `none`: no action needed.
  - `restart_immediate`: restart is appropriate immediately.
  - `restart_soft`: restart only after repeated observations or policy threshold.
  - `no_restart`: do not restart based on this issue alone.

## Action Policy

### `action_class = none`

- No restart.
- Continue monitoring.

### `action_class = restart_immediate`

- Expected owner: `BOOT/phase5_autoguard.ps1`
- Action: dispatch `BOOT/restart_engine.ps1`
- Typical causes:
  - `HEALTH_SUMMARY_MISSING`
  - `HEALTH_SUMMARY_INVALID_JSON`
  - `API_8100_NOT_LISTENING`
  - `DASHBOARD_8787_NOT_LISTENING`
  - `ENGINE_NOT_ALIVE`
  - `RUNTIME_NOT_ALIVE`
  - `KILL_SWITCH_ACTIVE`
  - `RUNTIME_HEALTH_VALIDATION_EXECUTION_FAILED`
  - `RUNTIME_HEALTH_VALIDATION_MISSING_REPORT`

### `action_class = restart_soft`

- Do not restart on first observation.
- Let `phase5_autoguard` count repeated failures.
- Restart only when repeated failures cross `WarnRestartThreshold`.
- Typical causes:
  - `ACCOUNT_EQUITY_TOO_LOW`
  - `OPS_HEALTH_NOT_OK`
  - `ENGINE_ERROR_PRESENT`
  - `PORTFOLIO_SNAPSHOT_STALE`
  - `PORTFOLIO_SNAPSHOT_TS_INVALID`

### `action_class = no_restart`

- Never restart from this signal alone.
- Investigate data quality or upstream completeness instead.
- Current example:
  - `ALLOCATION_TARGET_EMPTY`

## Quick Triage

1. Open `runtime_health_validation_latest.json`.
2. Check `status` and `action_class`.
3. If `action_class` is `restart_immediate`, confirm the issue in `phase5_autoguard_log.txt`.
4. If `action_class` is `restart_soft`, check whether the same issue is repeating.
5. If restart happened recently, inspect `runtime_health_restart_state.json` for cooldown context.
6. Confirm recovery by checking that validation returns `status=PASS` and `action_class=none`.

## Operator Checklist

### Immediate Restart Path

1. Open `runtime_health_validation_latest.json`.
2. Verify `action_class = restart_immediate`.
3. Check the latest matching lines in `phase5_autoguard_log.txt`.
4. Confirm `phase5_autoguard` dispatched or attempted `restart_engine.ps1`.
5. Re-check validation until it returns `status=PASS`.

### Soft Restart Path

1. Open `runtime_health_validation_latest.json`.
2. Verify `action_class = restart_soft`.
3. Check whether the same issue repeats in `phase5_autoguard_log.txt`.
4. Confirm whether the issue self-recovers before threshold.
5. If the issue repeats and restart occurs, verify cooldown behavior in `runtime_health_restart_state.json`.

### No Restart Path

1. Open `runtime_health_validation_latest.json`.
2. Verify `action_class = no_restart`.
3. Do not restart solely from this signal.
4. Inspect upstream data completeness and producer logs instead.

## Example Flows

### Example A: Soft Fail Self-Recovery

Observed sequence from `phase5_autoguard_log.txt`:

- `RUNTIME_HEALTH_VALIDATION status=FAIL issues=ACCOUNT_EQUITY_TOO_LOW`
- `HEALTH_POLICY_FAIL_SOFT issue=ACCOUNT_EQUITY_TOO_LOW count=1 threshold=3`
- later: `RUNTIME_HEALTH_VALIDATION status=PASS issues=-`

Interpretation:

- `ACCOUNT_EQUITY_TOO_LOW` can be caused by a transient snapshot anomaly.
- Policy should not immediately restart on the first occurrence.
- If the value recovers and validation returns `PASS`, no restart is needed.

### Example B: Immediate Restart Condition

Expected sequence:

- `RUNTIME_HEALTH_VALIDATION status=FAIL issues=API_8100_NOT_LISTENING`
- `HEALTH_RESTART_TRIGGER status=FAIL reason=FAIL_STATUS issues=API_8100_NOT_LISTENING`

Interpretation:

- Core runtime surface is unavailable.
- `phase5_autoguard` should dispatch `restart_engine.ps1` without waiting for repeated observations.

### Example C: Steady Healthy State

Observed sequence:

- `RUNTIME_HEALTH_VALIDATION status=PASS issues=-`

Interpretation:

- Runtime is healthy.
- Validation file should show `action_class = none`.
- No restart action is needed.

## Current Automation Boundary

- `BOOT/validate_runtime_health_summary.ps1`
  - Produces `status`, `issues`, `action_class`
- `BOOT/phase5_autoguard.ps1`
  - Reads validation result
  - Applies restart policy
  - Enforces restart cooldown
- `BOOT/restart_engine.ps1`
  - Safely restarts engine, runtime guard, and autoguard

## Notes

- `ACCOUNT_EQUITY_TOO_LOW` is intentionally treated as soft by policy because transient snapshot anomalies can produce temporary zero values.
- If a new issue is added to `validate_runtime_health_summary.ps1`, update the issue classification table in `BOOT/phase5_autoguard.ps1` and this runbook together.
