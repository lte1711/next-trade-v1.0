# Live Stop Tightening Probe Report

Generated: 2026-04-09T15:56:33.211667+09:00
Environment: `https://demo-fapi.binance.com`
Status: `completed`

## Summary
- Symbol: `BTCUSDT`
- Entry Order: `13025424050`
- Close Order: `13025424200`
- Stop Tightened: `True`
- System Errors: `0`

## Snapshots
- before_entry: active_amount=0.0, managed_stop=None, stop_algo_id=None, take_algo_id=None, open_algo_orders=0
- after_initial_protective_orders: active_amount=0.0016, managed_stop=69494.25, stop_algo_id=1000000044934272, take_algo_id=1000000044934280, open_algo_orders=2
- after_stop_tightening: active_amount=0.0016, managed_stop=70583.2105, stop_algo_id=1000000044934326, take_algo_id=1000000044934280, open_algo_orders=2
- after_cleanup: active_amount=0.0, managed_stop=None, stop_algo_id=None, take_algo_id=None, open_algo_orders=0

## Next Evolution Targets
- Drive stop tightening from real profit observations instead of injected current_price values.
- Add a short-side live stop-tightening scenario and compare algo order replacement symmetry.
