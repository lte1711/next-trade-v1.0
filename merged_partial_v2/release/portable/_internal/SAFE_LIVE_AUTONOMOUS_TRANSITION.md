# Safe Live Autonomous Transition

This runbook describes the recommended order for moving `merged_partial_v2`
from dry-run validation into live Binance testnet autonomous operation.

The goal is to reduce surprise at cutover time and make each transition step
explicitly observable.

## Scope

This procedure assumes:

- `merged_partial_v2` is the only tool you will use for the transition
- Binance testnet credentials for all three roles are already loaded
- recent health-check order flow has already succeeded at least once
- you understand whether the current exchange account already has active positions

## Step 1: Confirm the current merged snapshot

Run:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py
```

Check:

- `merged_partial_v2/merged_snapshot.json` is updated
- `profile_selection.selected_profile` is present
- `paper_decision.risk_gate.ok` is `true`
- `recent_health_check.latest_open.final_status` is `FILLED`
- `recent_health_check.latest_close.final_status` is `FILLED`

Do not continue if:

- credentials are missing
- the risk gate is blocked
- health-check open or close did not fill

## Step 2: Run live-readiness check

If the account should remain flat before cutover:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py --live-ready-check
```

If you intentionally want the autonomous system to take over currently active positions:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py --live-ready-check --adopt-active-positions
```

Check:

- `ready_for_live_autonomous` is `true`
- every item in `checks` has `ok=true`

Interpretation:

- if `active_position_count > 0` and adoption is not enabled, the check should block
- if adoption is enabled and all other checks pass, the system is ready for live autonomous cutover

## Step 3: Validate recommendation logic without sending orders

Run:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py --paper-decision
```

Check:

- `paper_decision.profile_name` matches the expected current profile
- `paper_decision.decision_line` is sensible for the current market
- blocked reasons look operationally correct

This step confirms that recommendation logic still behaves as expected
immediately before live transition.

## Step 4: Validate one autonomous cycle in dry-run

Without adoption:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py --autonomous-cycle
```

With adoption:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py --autonomous-cycle --adopt-active-positions
```

Check:

- `entry_count` and `exit_count` match expectations
- `risk_gate.ok` remains `true`
- `state_after.managed_position_count` is sensible
- no unexpected symbol appears in `entries` or `exits`

Do not continue if:

- unexpected exits appear
- adoption would capture positions you do not want this system to manage

## Step 5: Validate a short autonomous loop in dry-run

Run a short dry-run loop first:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py --autonomous-loop --autonomous-cycles 3 --autonomous-interval-seconds 60
```

Or, with adoption:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py --autonomous-loop --autonomous-cycles 3 --autonomous-interval-seconds 60 --adopt-active-positions
```

Check:

- repeated cycles remain stable
- risk gate does not oscillate unexpectedly
- no stale failure or health-check condition starts blocking new entries

This is the last dry-run checkpoint before live order submission.

## Step 6: Cut over to live testnet autonomous operation

Flat-account cutover:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py --live --autonomous-cycle
```

Adopt-and-manage cutover:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py --live --autonomous-cycle --adopt-active-positions
```

If the first live cycle behaves correctly, move to loop mode:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py --live --autonomous-loop --autonomous-cycles 10 --autonomous-interval-seconds 60
```

Or with adoption:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py --live --autonomous-loop --autonomous-cycles 10 --autonomous-interval-seconds 60 --adopt-active-positions
```

## Files to inspect during transition

- `merged_partial_v2/merged_snapshot.json`
- `merged_partial_v2/execution_reports/last_execution_report.json`
- `merged_partial_v2/autonomous_reports/last_autonomous_report.json`
- `merged_partial_v2/runtime/autonomous_state.json`
- `merged_partial_v2/order_logs/orders.jsonl`

## Recommended interpretation of current account state

Use this rule:

- if active positions already belong to this merged system, adopt them
- if active positions were opened elsewhere and should remain manually managed, do not adopt them

## Abort conditions

Stop the transition and return to dry-run if any of the following happens:

- health-check open or close no longer reaches `FILLED`
- `risk_gate.ok` becomes `false`
- a new non-retryable operational failure appears in recent order failures
- autonomous dry-run proposes exits for positions you do not want to hand over
- live cycle opens or closes an unexpected symbol

## Minimal safe sequence

For quick reference:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py
python .\merged_partial_v2\run_merged_partial_v2.py --live-ready-check --adopt-active-positions
python .\merged_partial_v2\run_merged_partial_v2.py --paper-decision
python .\merged_partial_v2\run_merged_partial_v2.py --autonomous-cycle --adopt-active-positions
python .\merged_partial_v2\run_merged_partial_v2.py --autonomous-loop --autonomous-cycles 3 --autonomous-interval-seconds 60 --adopt-active-positions
python .\merged_partial_v2\run_merged_partial_v2.py --live --autonomous-cycle --adopt-active-positions
```
