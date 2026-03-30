# Phase5 Autoguard Dashboard Restart Policy

## Purpose
Define the steady-state dashboard restart policy owned by phase5_autoguard.

## Fact-Aligned Ownership
- phase5_autoguard is confirmed as an active dashboard restart path in current runtime.
- Dashboard runtime health is currently best represented by:
  - one listener on 8787
  - dashboard API HTTP 200
  - at least one dashboard process present

## Policy
### Rule A1: Steady-State Owner
phase5_autoguard is the steady-state dashboard availability owner during live runtime.

### Rule A2: Healthy State
If there is exactly one 8787 listener and at least one dashboard process exists, phase5_autoguard must not restart or deduplicate the dashboard.

### Rule A3: Restart Cooldown
If listener count is 0 but dashboard processes still exist, phase5_autoguard must respect a restart cooldown before attempting another dashboard start.

### Rule A4: Duplicate Cleanup Bound
Process-count duplicate cleanup must not run while the dashboard already has a single active listener and at least one matching process.

### Rule A5: Launch Path
All dashboard starts from phase5_autoguard must go through BOOT\start_dashboard_8787.ps1.
