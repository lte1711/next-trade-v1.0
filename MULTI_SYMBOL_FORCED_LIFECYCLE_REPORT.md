# Multi Symbol Forced Lifecycle Report

Generated: 2026-04-09T15:54:35.387370+09:00
Environment: `https://demo-fapi.binance.com`
Status: `completed`

## Aggregate
- Symbols Requested: `3`
- Symbols Passed: `3`
- Symbols Failed: `0`
- Total Entry Orders: `3`
- Total Partial Closes: `3`
- Total Final Closes: `3`
- Total Protective Orders Observed: `6`
- System Errors: `0`

## Symbol Summary
- BTCUSDT: status=passed, entry=13025422700, partial=13025422787, final=13025422843, cooldown=True
- ETHUSDT: status=passed, entry=8634292674, partial=8634292742, final=8634292781, cooldown=True
- BNBUSDT: status=passed, entry=1334650208, partial=1334650288, final=1334650319, cooldown=True

## Next Evolution Targets
- Scale this validation to a broader symbol set and both LONG/SHORT scenarios.
- Replace synthetic partial TP marking with direct `PartialTakeProfitManager` trigger-path execution.
- Use the multi-symbol evidence to build a regression gate before longer unattended demo runs.
