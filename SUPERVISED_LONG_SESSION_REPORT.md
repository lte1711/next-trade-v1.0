# Supervised Long Session Report

Generated: 2026-04-09T15:51:41.588423+09:00
Environment: `https://demo-fapi.binance.com`
Status: `completed`

## Session
- PID: `12976`
- Requested Cycles: `4`
- Completed Cycles: `4`
- Sleep Seconds: `5`
- Started At: `2026-04-09T15:44:46.498978+09:00`
- Completed At: `2026-04-09T15:51:41.588423+09:00`

## Aggregate
- System Errors: `0`
- Total Signals: `80`
- Total Trades: `0`
- Cycles With Errors: `0`
- Max Active Positions: `0`
- Max Pending Trades: `0`
- Starting Balance: `8547.47136124`
- Ending Balance: `8547.66256645`

## Cycle Summary
- Cycle 1: duration=90.312s, signals=20, trades=0, errors=0, balance=8547.47136124, active_positions=0, pending_trades=0
- Cycle 2: duration=93.22s, signals=20, trades=0, errors=0, balance=8547.60040333, active_positions=0, pending_trades=0
- Cycle 3: duration=92.727s, signals=20, trades=0, errors=0, balance=8547.67258542, active_positions=0, pending_trades=0
- Cycle 4: duration=103.856s, signals=20, trades=0, errors=0, balance=8547.66256645, active_positions=0, pending_trades=0

## Next Evolution Targets
- Extend to a multi-hour supervised session with the same evidence format.
- Induce more real non-HOLD trading scenarios to validate entry/exit diversity.
- Add targeted scenario tests that force active position state transitions.
