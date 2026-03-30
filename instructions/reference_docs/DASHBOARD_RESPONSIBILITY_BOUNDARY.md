# Dashboard Responsibility Boundary

## Purpose
Lock the runtime responsibility boundary between boot_watchdog and phase5_autoguard for dashboard 8787 management.

## Fact Basis
- phase5_autoguard was confirmed as an active dashboard restart path.
- boot_watchdog is a bootstrap-oriented script.
- Both scripts previously had dashboard-start logic.

## Boundary
### Rule B1: boot_watchdog Role
boot_watchdog is bootstrap-only for dashboard management.
It may assist only when phase5_autoguard is not yet active.

### Rule B2: phase5_autoguard Role
phase5_autoguard owns steady-state dashboard availability after runtime is live.

### Rule B3: Defer Rule
If phase5_autoguard is running, boot_watchdog must defer dashboard responsibility to it.

### Rule B4: Shared Launch Mechanism
Both scripts must use the same launch wrapper:
`BOOT\start_dashboard_8787.ps1`

### Rule B5: Health Truth
Dashboard runtime truth is defined by:
1. single 8787 listener
2. API HTTP 200
3. dashboard process presence
not by raw single-process count alone.
