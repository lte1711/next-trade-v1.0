# NEXT-TRADE Final Cleanup Gate At Stopped Runtime

## Purpose

This document defines the final cleanup gate for legacy role folders when runtime is stopped and snapshot evidence is available.

## Fact Base

```text
CURRENT_COPY_FIRST_MIGRATION = DONE
CURRENT_MANIFEST_VALIDATION = DONE
CURRENT_SIZE_MISMATCHES = PRESENT
CAUSE = ACTIVE_RUNTIME_FILES_CONTINUED_WRITING_AFTER_COPY
```

## Final Cleanup Gate Principle

```text
Final cleanup is blocked while runtime-active files can still append.
Final cleanup may be evaluated only after a stopped-runtime snapshot is captured.
```

## Stopped Runtime Preconditions

All of the following must be true:

```text
1. engine_alive = NO or controlled stop confirmed
2. observer and guard append loops stopped
3. target logs are no longer changing in size
4. snapshot timestamp recorded
5. manifest validation rerun after stop
```

## Snapshot Scope

The stopped-runtime snapshot must capture at least:

```text
runtime_guard_log.txt
phase5_autoguard_log.txt
nt_phase5_multi_symbol_metrics.jsonl
nt_phase5_multi_symbol_status.txt
```

and any other source file that was previously excluded as active runtime evidence.

## Final Cleanup Gate

### GATE-F1 Snapshot Validation

```text
1. rerun manifest validation after stop
2. rerun excluded-active validation after stop
3. confirm missing_targets = 0
4. confirm size_mismatches = 0
```

### GATE-F2 Reversible Hold Only

If snapshot validation passes, allowed first action is still:

```text
rename legacy role folder to *_legacy_verified_hold
```

Final deletion remains blocked.

### GATE-F3 Final Deletion Requires Separate Approval

Even after a stopped-runtime snapshot passes:

```text
permanent deletion = not automatic
```

Required:

```text
1. stopped-runtime validation summary
2. reversible hold completed
3. explicit cleanup approval
4. rollback note retained
```

## Output Requirement

The stopped-runtime cleanup gate run must produce:

```text
STOPPED_RUNTIME_SNAPSHOT_REPORT.txt
LEGACY_ROLE_REPORT_MIGRATION_VALIDATION_POSTSTOP.csv
LEGACY_ROLE_REPORT_MIGRATION_VALIDATION_POSTSTOP_SUMMARY.txt
```

## Current Status

```text
CURRENT_FINAL_CLEANUP_GATE = CLOSED
REASON = ACTIVE_RUNTIME_FILES_STILL_CHANGING
```
