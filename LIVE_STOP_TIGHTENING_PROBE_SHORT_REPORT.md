# Live Stop Tightening Probe Short Report

Generated: 2026-04-09T15:57:19.773525+09:00
Environment: `https://demo-fapi.binance.com`
Status: `completed`

## Summary
- Symbol: `BTCUSDT`
- Entry Order: `13025424506`
- Close Order: `13025424597`
- Stop Tightened: `True`
- System Errors: `0`

## Snapshots
- before_entry: active_amount=0.0, managed_stop=None, stop_algo_id=None, take_algo_id=None, open_algo_orders=0
- after_initial_protective_orders: active_amount=-0.0016, managed_stop=72378.996, stop_algo_id=1000000044934597, take_algo_id=1000000044934610, open_algo_orders=2
- after_stop_tightening: active_amount=-0.0016, managed_stop=71315.00099999999, stop_algo_id=1000000044934652, take_algo_id=1000000044934610, open_algo_orders=2
- after_cleanup: active_amount=0.0, managed_stop=None, stop_algo_id=None, take_algo_id=None, open_algo_orders=0

## Next Evolution Targets
- Drive short-side stop tightening from real profit observations instead of injected current_price values.
- Promote long/short live stop-tightening probes into the final pre-run gate.
