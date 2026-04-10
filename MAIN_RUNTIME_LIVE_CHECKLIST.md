# Main Runtime Live Deployment Checklist

Status Snapshot Date: 2026-04-09
Validated Environment: `https://demo-fapi.binance.com`

## Current Status
- `PASS` Configuration validation
- `PASS` Startup validation
- `PASS` Connectivity validation
- `PASS` Strategy safety validation
- `PASS` Position safety validation
- `PASS` Operational logging validation
- `PASS` Short supervised smoke run
- `PASS` Background supervised probe
- `PASS` Known order status polling
- `PASS` Protective algo order placement
- `PASS` Reduce-only close path
- `PASS` Monitor/stop helper script repair
- `GO` for supervised demo-environment operation

## Configuration
- Verify `.env` or `config.json` contains valid Binance API credentials.
- Confirm `base_url` matches the intended environment.
- Confirm `recv_window` is set appropriately for the target environment.
- Verify `config.json` exists and contains `trading_config` and `api_config` sections.

## Startup Validation
- Run `python -m py_compile main_runtime.py core\trade_orchestrator.py core\account_service.py core\strategy_registry.py core\position_manager.py core\market_data_service.py`
- Instantiate the runtime once before live execution.
- Confirm runtime reports `initialized=True`.
- Confirm `trade_orchestrator` is present.
- Confirm dynamic symbol loading succeeds and returns a non-zero symbol count.
- Confirm capital is loaded from the account and is greater than zero.

## Connectivity
- Confirm account sync succeeds without adding entries to `system_errors`.
- Confirm order status polling works for at least one known order id in the target environment.
- Confirm server-time-based timestamp signing succeeds consistently.

## Strategy Safety
- Verify strategy registry contains the intended enabled strategies only.
- Verify `max_open_positions`, `stop_loss_pct`, and `take_profit_pct` are the intended live values.
- Verify protective order placement succeeds in the target environment.
- Verify pending order refresh does not create duplicate entries.

## Position Safety
- Verify position entry times are persisted in `trading_results["position_entry_times"]`.
- Verify `PositionManager` sees the same `position_entry_times` mapping as the runtime.
- Verify close and partial-close paths attach `reduce_only=True`.
- Verify position sync preserves strategy metadata on existing positions.

## Operational Logging
- Verify error logs contain structured error type and message fields.
- Verify `trading_results.json` is writable in the runtime working directory.
- Verify no repeated startup-only logs appear inside the steady-state loop.

## Dry Run / Smoke Run
- Start the runtime for a short supervised session.
- Confirm the main loop stays alive for at least one cycle interval.
- Confirm `error_count` remains zero during the smoke run.
- Confirm no unexpected active positions are created during a validation-only session.

## Go / No-Go
- Go live only if startup validation, connectivity, strategy safety, and smoke run all pass.
- Do not go live if runtime initialization fails, account sync fails, or order status polling is inconsistent.

## Result
- Current result on 2026-04-09: `GO` for supervised demo runtime.
- Current result on 2026-04-09: production futures endpoint was not validated in this checklist.
