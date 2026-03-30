# Dashboard Low-Level Root Cause Investigation Track

## Purpose
Separate low-level launcher/root-cause investigation from normal runtime acceptance.

## Current Accepted Runtime Facts
- Dashboard runtime is currently accepted when:
  - listener_count = 1
  - API HTTP 200
  - dashboard process present
- The current observed steady-state pattern is 2 dashboard python processes in a parent-child chain.
- phase5_autoguard is a confirmed steady-state restart path.

## Investigation Scope
This track is for investigation only and must not change runtime acceptance criteria by itself.

### Investigation Questions
1. Why does the venv-launched parent result in a system-Python child listener process?
2. Is the child process created by Windows launcher behavior, Python launcher behavior, or a library side effect?
3. Does the same pattern appear when launching outside phase5_autoguard?
4. Can strict single-executable runtime be achieved without destabilizing listener health?

## Fact-Locked Non-Goals
- Do not treat current 2-process runtime as a production fault by default.
- Do not weaken single-listener/API health criteria while investigating root cause.
- Do not change boot_watchdog/phase5_autoguard ownership boundary without new evidence.

## Evidence to Collect
1. Controlled relaunch traces.
2. Parent-child process trees.
3. Listener ownership over time.
4. Executable path of each process.
5. Any Windows/Python launcher-specific behavior confirmed by reproducible tests.

## Exit Criteria
This investigation track may be closed only when one of the following is true:
1. root cause is directly reproduced and explained by evidence, or
2. runtime decision formally accepts the pattern long-term and investigation is archived as low priority.
