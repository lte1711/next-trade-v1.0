# Live Runtime Execution And Profit Validation

## Result
April 9, 2026 live validation passed at the execution layer, but profit is currently negative.

This means the runtime is behaving correctly as a trading system on the demo exchange, while the strategy layer still needs improvement.

## Situation Check
- A fresh live cycle was executed on April 9, 2026 from `18:02:22 +09:00` to `18:04:14 +09:00`.
- That cycle completed with:
  - `signals_generated=20`
  - `trades_executed=1`
  - `errors=[]`
  - `system_errors=0`
- Intended duplicate-entry blocks were handled as `skips`, not failures.

Observed live transitions:
- `AKEUSDT` opened a new long position.
- `NEIROUSDT` was closed through a reduce-only exit.
- `ZRCUSDT` was closed through a reduce-only exit.

## Current Runtime State
- Current active positions are `HIPPOUSDT` and `AKEUSDT`.
- `HIPPOUSDT` remains a short with a managed stop price at `0.000209`.
- `AKEUSDT` remains a long and is slightly underwater at the latest local mark.
- The runtime itself remains healthy, with no current system errors in the latest probe state.

## Profit Verification
Profit was verified in three layers.

`Current unrealized PnL`

- Local position-state calculation shows total unrealized PnL of about `-0.16278 USDT`.
- Breakdown:
  - `HIPPOUSDT`: about `0.0 USDT`
  - `AKEUSDT`: about `-0.16278 USDT`

`Recent realized PnL`

- Exact recent realized PnL was reconstructed from exchange `allOrders` by pairing the latest filled entry and reduce-only exit orders.
- Reconstructed recent closed-position results:
  - `NEIROUSDT` long: about `-0.5957577 USDT`
  - `ZRCUSDT` short: about `-0.2468 USDT`
- Combined recent realized PnL: about `-0.8425577 USDT`

`Balance delta reference`

- [unattended_live_demo_status.json](/c:/next-trade-ver1.0/unattended_live_demo_status.json) shows a historical available-balance delta of about `-12.5605`.
- This number should not be treated as pure profit because available balance changes with open margin and timing.

## Evaluation
The execution layer is working.

What passed:
- live runtime initialization
- fresh live-cycle execution
- real order placement
- reduce-only exits
- duplicate-entry skip handling
- runtime health with `system_errors=0` in the fresh execution pass

What did not pass:
- profit quality

At this moment, the system is trading correctly but not yet trading profitably.

## Next Action
The next evolution should target strategy performance rather than execution plumbing.

The highest-value follow-ups are:
- improve candidate ranking and entry quality
- add native realized-PnL journaling to local trade records
- use the new live evidence to tune signal thresholds and symbol filtering

The machine-readable source for this report is [LIVE_RUNTIME_EXECUTION_AND_PROFIT_VALIDATION_20260409.json](/c:/next-trade-ver1.0/LIVE_RUNTIME_EXECUTION_AND_PROFIT_VALIDATION_20260409.json).
