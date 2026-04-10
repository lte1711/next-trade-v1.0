# Scenario Forced Entry Validation Report

Generated: 2026-04-09T15:52:38.981690+09:00
Environment: `https://demo-fapi.binance.com`
Status: `completed`

## Summary
- Symbol: `BTCUSDT`
- Entry Side: `BUY`
- Steps Passed: `7` / `7`
- System Errors: `0`

## Steps
- `initialization`: `passed`
  Summary: TradingRuntime initialized successfully.
- `cleanup_before`: `passed`
  Summary: Pre-scenario cleanup completed.
- `entry_fill`: `passed`
  Summary: Entry order filled and active position synchronized.
- `protective_orders`: `passed`
  Summary: Protective algo orders installed.
- `partial_state_mark`: `passed`
  Summary: Partial take profit state map updated for evidence.
- `partial_close`: `passed`
  Summary: Partial reduce-only close completed and position remained active.
- `full_close_and_cleanup`: `passed`
  Summary: Final reduce-only close and cleanup completed.

## Snapshots
- before_entry: active_position=False, active_qty=0.0, open_algo_orders=0, managed_stop=None, pending_trades=0
- after_entry_fill: active_position=True, active_qty=0.0016, open_algo_orders=0, managed_stop=None, pending_trades=0
- after_protective_orders: active_position=True, active_qty=0.0016, open_algo_orders=2, managed_stop=69474.06199999999, pending_trades=0
- after_partial_state_mark: active_position=True, active_qty=0.0016, open_algo_orders=2, managed_stop=69474.06199999999, pending_trades=0
- after_partial_close: active_position=True, active_qty=0.0008, open_algo_orders=2, managed_stop=69474.06199999999, pending_trades=0
- after_full_close: active_position=False, active_qty=0.0, open_algo_orders=0, managed_stop=None, pending_trades=0

## Next Evolution Targets
- Automate multi-symbol forced lifecycle scenarios instead of single-symbol BTCUSDT validation.
- Integrate forced partial-take-profit assertions with live `PartialTakeProfitManager` execution paths.
- Unify partial take profit stop tracking with `trading_results["managed_stop_prices"]`.
