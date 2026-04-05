# Merged Partial V2

This folder is a self-contained merge workspace.

The original project and the test project remain untouched.
Everything needed for the merged partial integration now lives inside this folder.

## Intent

This workspace follows the previously selected "Option 2: partial extraction integration":

- keep only the useful strategy logic from the test project
- rebuild the required exchange bridge locally inside the merge folder
- avoid importing the original `next_trade` package at runtime

## Included Components

### Exchange layer

- `src/merged_partial_v2/exchange/public_read_client.py`
  - public ticker and kline access
- `src/merged_partial_v2/exchange/private_read_client.py`
  - private account and position reads
- `src/merged_partial_v2/exchange/execution_client.py`
  - order submission bridge
  - includes a small `open_and_close_test_order()` health check helper
- `src/merged_partial_v2/exchange/local_binance_bridge.py`
  - copied and simplified local bridge for Binance futures testnet access

### Strategy layer

- `src/merged_partial_v2/services/market_scoring_service.py`
  - extracted market scoring logic from the modular test strategy
- `src/merged_partial_v2/services/symbol_selection_service.py`
  - extracted regime and symbol selection logic
- `src/merged_partial_v2/services/profile_switcher_service.py`
  - remote profile definitions and default/aggressive profile switching logic
- `src/merged_partial_v2/services/risk_gate_service.py`
  - central operational gate checks before new recommendations are allowed
- `src/merged_partial_v2/services/autonomous_state_service.py`
  - persistent managed-position state for autonomous operation
- `src/merged_partial_v2/services/autonomous_trading_service.py`
  - automatic entry/exit cycle runner for operator-free autonomous trading

### Orchestration layer

- `src/merged_partial_v2/simulation/strategy_engine.py`
  - combines extracted strategy logic and local exchange clients
- `src/merged_partial_v2/main.py`
  - builds a merged market/account snapshot
- `run_merged_partial_v2.py`
  - launcher
- `src/merged_partial_v2/dashboard_server.py`
  - local dashboard server for status and start/stop control
- `src/merged_partial_v2/services/process_manager_service.py`
  - manages the background autonomous loop process used by the dashboard

## Local Config

The merge folder includes its own config file:

- `config.json`

Current defaults:

- exchange base: `https://demo-fapi.binance.com`
- credentials are separated by role in `config.json`
  - `public_read`
  - `private_read`
  - `execution`
- local credential values are loaded from:
  - `merged_partial_v2/.env.merged_partial_v2`

## Credential Roles

The merged workspace now supports three separate Binance testnet credential roles:

- `public_read`
  - used by `public_read_client.py`
  - attached to public market-data requests as an optional API key header
- `private_read`
  - used by `private_read_client.py`
  - signs account and position read requests
- `execution`
  - used by `execution_client.py`
  - signs order submission requests
  - market orders can optionally wait for final exchange status polling

## Profile Defaults

- balanced default profile: `v3_remote_default_capital_preserver`
- aggressive alternate profile: `remote_risk_reference`
- automatic selection rule:
  choose the aggressive profile only when max drawdown is at or below `12%`
  and positive months are not fewer than negative months
- aggressive profile selection also requires:
  - aggressive benchmark pnl must exceed the default benchmark pnl
  - aggressive benchmark drawdown must stay within the configured drawdown gap
- the selection thresholds and benchmark risk metrics now live in `config.json`
- current selection metrics are auto-loaded from `profile_reports/remote_profile_metrics.json`
- `current_metrics_profile_name` controls which profile's recorded risk metrics drive the current decision
- generated snapshots include:
  - the active selection inputs from config
  - the chosen profile benchmark metrics
  - all available profile benchmark summaries

## Run

From the repository root:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py
```

Health-check order mode:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py --health-check-order --symbol BTCUSDT --quantity 0.001
```

Paper decision mode:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py --paper-decision
```

Execute the top recommendation safely with dry-run:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py --execute-top-recommendation
```

Re-check guards and execute at most one recommendation with dry-run:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py --guarded-execute
```

Execute only when the account is flat:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py --auto-execute-if-flat
```

Watch for a recommendation over multiple cycles:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py --watch-recommendation --watch-cycles 3 --watch-interval-seconds 5
```

Watch and execute only when a recommendation appears and the account is flat:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py --watch-then-guarded-execute --watch-cycles 3 --watch-interval-seconds 5
```

Run the local management dashboard:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py --dashboard --dashboard-port 8787
```

Then open:

```text
http://127.0.0.1:8787
```

Run one autonomous cycle:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py --autonomous-cycle
```

Run a live-readiness check before any live autonomous transition:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py --live-ready-check
```

Run the full transition checklist, including a dry-run autonomous preview:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py --transition-checklist
```

If the account already has open positions and you intentionally want the autonomous system to adopt them, include:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py --live-ready-check --adopt-active-positions
python .\merged_partial_v2\run_merged_partial_v2.py --transition-checklist --adopt-active-positions
```

Build a Windows v1 executable package:

```powershell
powershell -ExecutionPolicy Bypass -File .\merged_partial_v2\build_v1.ps1
```

Install the built v1 package into the current Windows user profile:

```powershell
powershell -ExecutionPolicy Bypass -File .\merged_partial_v2\install_v1.ps1
```

Installed `v1` behavior:

- source-tree no-argument run: one-shot snapshot and recommendation analysis
- installed frozen no-argument run: automatic live autonomous loop using `config.json -> startup`
- installed package also includes:
  - `Open Merged Partial V2 Dashboard.bat`
  - dashboard shortcuts on desktop and start menu

Create a single portable ZIP package:

```powershell
powershell -ExecutionPolicy Bypass -File .\merged_partial_v2\package_v1.ps1
```

Run an autonomous loop:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py --autonomous-loop --autonomous-cycles 3 --autonomous-interval-seconds 60
```

If you want the autonomous system to adopt already-open exchange positions into its managed state on the first cycle:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py --autonomous-cycle --adopt-active-positions
```

Run a 1-year historical backtest for a merged profile:

```powershell
python .\merged_partial_v2\run_merged_profile_backtest.py --profile-name v3_remote_default_capital_preserver
python .\merged_partial_v2\run_merged_profile_backtest.py --profile-name remote_risk_reference
```

Add `--live` only when you intentionally want to send a real testnet order.

## Output

The launcher writes:

- `merged_partial_v2/merged_snapshot.json`
- `merged_partial_v2/order_logs/orders.jsonl` for execution attempts
- `merged_partial_v2/execution_reports/last_execution_report.json` for the latest execution-mode result
- `merged_partial_v2/autonomous_reports/last_autonomous_report.json` for the latest autonomous-cycle result
- `merged_partial_v2/runtime/autonomous_state.json` for managed autonomous position state
- `merged_partial_v2/SAFE_LIVE_AUTONOMOUS_TRANSITION.md` for the recommended dry-run to live autonomous cutover sequence
- `merged_partial_v2/build_v1.ps1` to build the Windows v1 executable package
- `merged_partial_v2/install_v1.ps1` to install the built package and create shortcuts
- `merged_partial_v2/package_v1.ps1` to create a single ZIP package for distribution
- installed `v1` now starts the configured autonomous live loop by default when launched without arguments

## Notes

- Public market snapshot building works without the original package.
- Private account and order functions require valid Binance testnet credentials in environment variables.
- The launcher also records non-secret credential load status in `merged_snapshot.json`.
- `merged_snapshot.json` now also includes a paper-decision summary and the most recent health-check summary.
- `merged_snapshot.json` also includes the latest saved execution-mode summary.
- `merged_snapshot.json` now stores a compact account snapshot instead of the full raw position payload.
- `merged_snapshot.json` now also includes a recent order-failure summary so operational blocks can distinguish market issues from strategy slot limits.
- Execution reports now include a one-line `alert_summary` suitable for chat/notification tools.
- The public market-data client now caches `klines` in-memory within a launcher run to reduce repeated scoring calls.
- The market scoring service now reuses same-run symbol evaluations when the symbol's price/change/quote-volume inputs have not changed.
- Paper decision output now includes a `risk_gate` section so recommendation blocks can distinguish slot limits from operational safety blocks.
- The risk gate now also reacts to recent critical order failures, not just account/position/health-check state.
- `--autonomous-cycle` runs one full automatic decision/entry/exit pass.
- `--autonomous-loop` repeats autonomous cycles with no operator intervention between runs.
- `--live-ready-check` verifies credential state, recent health checks, current risk-gate status, active-position state, and autonomous config validity before live autonomous use.
- `--transition-checklist` combines live-readiness checks with a dry-run autonomous preview so you can see which positions would be managed after cutover.
- Autonomous exits currently use:
  - `take_profit`
  - `replacement_threshold`
  - optional `close_when_unselected_after_min_hold`
- Autonomous entries use top paper recommendations, limited by `max_new_orders_per_cycle`.
- Existing exchange positions are not adopted by default; use `--adopt-active-positions` on the first cycle if you want the autonomous state to manage them.
- The execution bridge now auto-adjusts non-reduce-only orders for symbol `minQty`, `stepSize`, and `minNotional` when exchange rules require it.
- Symbol trading rules are cached in-memory after the first `exchangeInfo` lookup.
- Execution responses can include `status_check` and `final_status` after short post-submit polling.
- Failure paths now map common Binance error codes to a category, retryability flag, and operator hint.
- Preflight failures are also classified for symbol lookup, price lookup, rule lookup, and invalid local payloads.
- Success and failure order attempts are both logged to `order_logs/orders.jsonl`.
- `--paper-decision` prints recommendation-only entries without sending orders.
- `--execute-top-recommendation` converts the top paper recommendation into an order payload and submits it.
- `--guarded-execute` re-checks current account and slot guards before submitting at most one order.
- `--auto-execute-if-flat` only submits when there are zero active positions.
- `--watch-recommendation` repeats paper-decision checks until a recommendation appears or the watch window ends.
- `--watch-then-guarded-execute` repeats paper-decision checks and executes only if a recommendation appears while the account is flat.
- Both execution modes default to `dry_run`; add `--live` to send a real testnet order.
- The merged runner currently embeds the balanced default remote profile selection.
- This is still a merge staging workspace, not a production engine.
