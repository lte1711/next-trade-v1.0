# Binance Testnet Validation Report

Generated: 2026-04-09T15:38:29.837687+09:00
Environment: `https://demo-fapi.binance.com`

## Overall
- Success: `True`
- Failed Phases: `None`

## Phase Summary
- `initialization`: `passed`
  Summary: Runtime initialized successfully.
- `trading_cycle`: `passed`
  Summary: Cycle completed with 20 signals and 0 trades.
- `order_status_polling`: `passed`
  Summary: Known order polling and cancel flow succeeded.
- `protective_orders_and_reduce_only_close`: `passed`
  Summary: Protective algo orders and reduce-only close path succeeded.
- `background_probe`: `passed`
  Summary: Background probe completed 3 cycles with no phase errors.

## Next Evolution Targets
- Run a longer supervised demo session to capture multi-hour runtime behavior.
- Exercise more real non-HOLD trading scenarios to validate broader strategy behavior.
- Unify partial take profit stop tracking with trading_results managed_stop_prices.

## Notes
- Final system_errors count during suite runtime: 0
