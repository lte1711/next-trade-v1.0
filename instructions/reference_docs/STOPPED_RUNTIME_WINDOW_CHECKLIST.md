# NEXT-TRADE Stopped Runtime Window Checklist

## Purpose

This checklist defines the exact fact checks required before capturing a stopped-runtime snapshot and opening the final cleanup gate.

## Preconditions

```text
1. Controlled stop is planned
2. No active deployment or migration is in progress
3. Snapshot target folder is prepared under reports\YYYY-MM-DD\honey_execution_reports\
```

## Runtime Stop Checklist

### CHECK-S1 Python Process Review

Record:

```text
python_process_count
python_process_ids
```

Pass condition:

```text
all trading/runtime python processes stopped
```

### CHECK-S2 Listener Review

Record:

```text
port 8100 listener status
port 8787 listener status
```

Pass condition:

```text
runtime-related listeners stopped or intentionally excluded by approved scope
```

### CHECK-S3 Active File Drift Review

For the following files, capture size twice with a small delay:

```text
runtime_guard_log.txt
phase5_autoguard_log.txt
nt_phase5_multi_symbol_metrics.jsonl
nt_phase5_multi_symbol_status.txt
worker_watchdog_log.txt
nt_phase5_portfolio_observe_15m.txt
nt_phase5_portfolio_observe_30m.txt
nt_phase5_portfolio_observe_60m.txt
nt_phase5_portfolio_observe_3h.txt
nt_phase5_portfolio_observe_6h.txt
nt_phase5_portfolio_observe_24h.txt
nt_phase5_portfolio_observe_24h_final.txt
```

Pass condition:

```text
no size change between measurements
```

### CHECK-S4 Snapshot Capture

Run:

```text
BOOT\capture_stopped_runtime_snapshot.ps1
```

Pass condition:

```text
snapshot_created = YES
```

### CHECK-S5 Post-Stop Validation

Run:

```text
BOOT\validate_legacy_role_migration.ps1
BOOT\validate_legacy_role_migration_excluding_active.ps1
```

Pass condition:

```text
missing_targets = 0
size_mismatches = 0
```

## Current Fact Snapshot

```text
python_process_count = 21
listener_8100 = ACTIVE
listener_8787 = ACTIVE
stopped_runtime_window = NOT_OPEN
```

## Conclusion

```text
Current snapshot window is not valid for final cleanup.
Use this checklist only when a controlled runtime stop is confirmed.
```
