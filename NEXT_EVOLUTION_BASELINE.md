# Next Evolution Baseline

Generated: 2026-04-09
Environment: `https://demo-fapi.binance.com`

## Verified Baseline
- Runtime initialization: passed
- Trading cycle execution: passed
- Known order status polling and cancel flow: passed
- Protective algo orders: passed
- Reduce-only close path: passed
- Background 3-cycle probe: passed
- Extended supervised 12-cycle session: passed
- Forced long lifecycle scenario: passed
- Forced multi-symbol lifecycle scenario: passed
- Forced short lifecycle scenario: passed
- Partial take profit trigger-path probe: passed
- Trailing stop threshold probe: passed
- `PartialTakeProfitManager` state maps now share `trading_results["partial_take_profit_state"]` and `trading_results["managed_stop_prices"]`

## Latest Long Session Evidence
- Status file: [supervised_long_session_status.json](/c:/next-trade-ver1.0/supervised_long_session_status.json)
- Report: [SUPERVISED_LONG_SESSION_REPORT.md](/c:/next-trade-ver1.0/SUPERVISED_LONG_SESSION_REPORT.md)
- Started at: `2026-04-09T13:59:31.136679+09:00`
- Completed at: `2026-04-09T14:20:33.289840+09:00`
- Completed cycles: `12`
- Average cycle duration: about `94.233s`
- Total supervised wall-clock duration: about `1240.797s`
- Total signals generated: `240`
- Total trades executed: `0`
- Cycle errors: `0`
- System errors: `0`
- Max active positions observed: `0`
- Max pending trades observed: `0`
- Starting balance: `8547.6035563`
- Ending balance: `8548.38406239`

## What The Data Says
- The runtime loop is stable under repeated supervised execution in the demo futures environment.
- The validated operational path now covers initialization, order polling, protective algo orders, reduce-only close, and extended loop survival.
- The remaining blind spot is no longer runtime stability. It is scenario coverage.
- The current market/strategy mix is producing `HOLD` outcomes during supervised runs, so real entry-to-exit lifecycle coverage is still sparse without targeted tests.

## Highest-Value Next Steps
1. Run a multi-hour supervised demo session using the same evidence format to confirm no late-cycle degradation.
2. Add targeted scenario tests that intentionally create non-HOLD entry conditions and verify full state transitions.
3. Capture scenario-specific evidence for:
   - filled entry -> pending trade conversion
   - active position creation
   - protective order refresh after fill
   - partial take profit state mutation
   - final close and state cleanup
4. Tighten actual protective algo stop orders in a live profit-expansion scenario after trailing conditions are met.

## Suggested Immediate Build Targets
- `scenario_forced_entry_validation.py`
- `multi_hour_supervised_session.py`
- `state_transition_evidence_report.md`
