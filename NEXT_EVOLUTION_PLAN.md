# Next Evolution Plan

Generated: 2026-04-09
Environment Baseline: `https://demo-fapi.binance.com`

## Current Baseline
- Final gate: `PASS`
- Demo unattended runtime readiness: `GO`
- Covered paths:
  - runtime initialization
  - supervised stability runs
  - known order polling and cancel
  - long/short forced lifecycle
  - multi-symbol lifecycle
  - protective algo orders
  - reduce-only close
  - partial take profit trigger-path
  - trailing stop threshold logic
  - live long/short stop tightening

## Strategic Direction
- The next bottleneck is no longer runtime survival.
- The highest-value evolution now is broader behavioral coverage and safer operational automation.
- We should evolve in three tracks:
  1. scenario diversity
  2. unattended operations
  3. production promotion readiness

## Track 1. Scenario Diversity
Goal:
- Validate more real entry/exit behavior than the current mostly-`HOLD` live market path provides.

Planned work:
- Build `scenario_matrix_runner.py`
- Add forced lifecycle coverage for:
  - more symbols
  - both long and short
  - staggered partial close ratios
  - stop tightening after profit expansion
  - delayed fill / pending-to-filled conversion
- Add state assertions for:
  - `active_positions`
  - `pending_trades`
  - `position_entry_times`
  - `partial_take_profit_state`
  - `managed_stop_prices`
  - `recently_closed_symbols`

Success criteria:
- At least 10 symbol-direction scenarios complete successfully
- zero unexpected system errors
- no orphan protective orders after cleanup
- no stale position management state after full close

Artifacts:
- `scenario_matrix_results.json`
- `SCENARIO_MATRIX_REPORT.md`

## Track 2. Unattended Operations
Goal:
- Turn the current demo runtime into a repeatable, low-friction operational loop.

Planned work:
- Add `unattended_demo_health_check.py`
- Add automatic checkpoint summarizer for long sessions
- Add stop/restart recovery notes
- Add evidence rollup that merges:
  - final gate result
  - unattended runtime status
  - latest long-session summary

Success criteria:
- unattended demo runs can be started, monitored, and stopped from one small command set
- health summary can be generated without manual parsing
- failure states clearly identify whether the issue is runtime, order flow, or process management

Artifacts:
- `unattended_demo_health.json`
- `UNATTENDED_DEMO_HEALTH_REPORT.md`

## Track 3. Production Promotion Readiness
Goal:
- Prepare a controlled path for production-endpoint validation without jumping directly into full-risk operation.

Planned work:
- Define a reduced production gate:
  - initialization
  - account sync
  - symbol load
  - dry operational checks
  - no full unattended production runtime at first step
- Add explicit risk controls:
  - minimum size constraints
  - symbol allowlist
  - max order count per window
  - single-position cap
  - manual promotion checklist

Success criteria:
- production preflight can run with zero destructive surprises
- promotion decision is based on checklist evidence, not ad hoc judgment

Artifacts:
- `PRODUCTION_PRE_FLIGHT_CHECKLIST.md`
- `production_promotion_gate.py`

## Recommended Order
1. Build scenario matrix runner
2. Build unattended health summary layer
3. Run a longer unattended demo session with the new health reporting
4. Draft reduced production gate
5. Decide on production preflight timing

## Immediate Build Targets
- `scenario_matrix_runner.py`
- `unattended_demo_health_check.py`
- `PRODUCTION_PRE_FLIGHT_CHECKLIST.md`

## Operational Decision Rule
- Do not prioritize production promotion before scenario diversity coverage improves.
- If unattended demo remains healthy but still signal-sparse, the correct next move is scenario expansion, not more repeated stability loops.
