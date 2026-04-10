# Operational Launch Report - 2026-04-10

## Status

The trading runtime is now running on Binance Futures demo/testnet.

- Endpoint: `https://demo-fapi.binance.com`
- Mode: `testnet`
- Runtime status: `running`
- Runtime actual PID: `11072`
- Runtime launcher PID: `12504`
- Max open positions: `10`
- Active strategies: `ma_trend_follow`, `ema_crossover`
- Evidence: `EXECUTE_FIRST_CHECKPOINT_20260410_STEP28_OPERATIONAL_LAUNCH_VERIFY.json`

## Live Testnet Positions

At `2026-04-10T12:00:18+09:00`, exchange sync showed 2 active testnet positions.

- `AKEUSDT`: SHORT `91169`, entry `0.0003868`
- `FUNUSDT`: LONG `71506`, entry `0.00089`

Both positions are protected by conditional algo orders.

- `AKEUSDT`: 1 `STOP_MARKET`, 1 `TAKE_PROFIT_MARKET`
- `FUNUSDT`: 1 `STOP_MARKET`, 1 `TAKE_PROFIT_MARKET`
- Unprotected symbols: none
- Standard open orders: none
- System errors: none

## What Was Done

- Added headless runtime operations tool: `tools/ops/runtime_ops.py`
- Verified compile for runtime and core trading modules.
- Verified no standard orphan orders before launch.
- Started the runtime in background.
- Detected a Windows launcher/interpreter process pair and treated it as one runtime chain.
- Temporarily stopped runtime when protection coverage needed confirmation.
- Confirmed protective orders via `openAlgoOrders`, not standard `openOrders`.
- Added missing `FUNUSDT` take-profit protection.
- Restarted runtime and verified protected operation.

## Operations Commands

Check status:

```powershell
.\.venv\Scripts\python.exe tools\ops\runtime_ops.py status
```

Stop runtime:

```powershell
.\.venv\Scripts\python.exe tools\ops\runtime_ops.py stop
```

Runtime log:

```powershell
Get-Content logs\main_runtime_testnet.log -Tail 200
```

## Note

This launch is testnet/demo operation only. Mainnet real-money operation has not been enabled.
