# Dashboard Runtime Acceptance Decision

## Purpose
Record the current operating decision for the dashboard 2-process / 1-listener pattern.

## Fact Basis
- Dashboard process count currently equals 2.
- Dashboard listener count currently equals 1.
- Dashboard API returns HTTP 200.
- The 2-process pattern was reproduced under controlled relaunch.
- phase5_autoguard is confirmed as an active steady-state restart path.
- Recent phase5_autoguard log tail does not show repeated dashboard start spam; it shows a single `START dashboard_8787` event in the sampled window.

## Decision
### Current Decision
The current dashboard runtime pattern is accepted for operation as:
- `2-process parent-child pattern`
- `single listener`
- `API healthy`

### Why It Is Accepted Now
Because the current operational truth is:
1. one active 8787 listener
2. API HTTP 200
3. stable process/listener pattern under trace
4. no fact-confirmed dashboard restart churn in the sampled autoguard log window

### What Is Not Accepted As Closed
- strict single-process runtime
- strict single-executable runtime
- final low-level root cause of venv-parent/system-python-child split

## Reopen Conditions
Reinvestigation is required if any of the following becomes true:
1. listener_count != 1
2. API /api/runtime fails repeatedly
3. autoguard log shows repeated dashboard restart churn
4. multiple independent dashboard listener chains appear
