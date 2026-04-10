# Main Runtime Full System Flowchart

Date: 2026-04-09
Timezone: Asia/Seoul
Validated Environment: `https://demo-fapi.binance.com`

## 1. Purpose

This document is the full end-to-end map of the current system.

It includes:

- runtime initialization
- trading cycle logic
- order entry and close flow
- protective algo order flow
- pending order reconciliation
- position management
- shared state structure
- validation and evidence flow
- background probe flow
- monitor / stop / background helper flow
- recently fixed connection points
- current residual risks

## 2. System Scope

The system is centered on:

- [main_runtime.py](/c:/next-trade-ver1.0/main_runtime.py)

The most important collaborating modules are:

- [core/account_service.py](/c:/next-trade-ver1.0/core/account_service.py)
- [core/market_data_service.py](/c:/next-trade-ver1.0/core/market_data_service.py)
- [core/indicator_service.py](/c:/next-trade-ver1.0/core/indicator_service.py)
- [core/market_regime_service.py](/c:/next-trade-ver1.0/core/market_regime_service.py)
- [core/signal_engine.py](/c:/next-trade-ver1.0/core/signal_engine.py)
- [core/strategy_registry.py](/c:/next-trade-ver1.0/core/strategy_registry.py)
- [core/allocation_service.py](/c:/next-trade-ver1.0/core/allocation_service.py)
- [core/trade_orchestrator.py](/c:/next-trade-ver1.0/core/trade_orchestrator.py)
- [core/order_executor.py](/c:/next-trade-ver1.0/core/order_executor.py)
- [core/protective_order_manager.py](/c:/next-trade-ver1.0/core/protective_order_manager.py)
- [core/pending_order_manager.py](/c:/next-trade-ver1.0/core/pending_order_manager.py)
- [core/position_manager.py](/c:/next-trade-ver1.0/core/position_manager.py)
- [core/partial_take_profit_manager.py](/c:/next-trade-ver1.0/core/partial_take_profit_manager.py)

Operational helper scripts now in scope:

- [background_supervised_probe.py](/c:/next-trade-ver1.0/background_supervised_probe.py)
- [run_main_runtime_background.py](/c:/next-trade-ver1.0/run_main_runtime_background.py)
- [monitor_main_runtime.py](/c:/next-trade-ver1.0/monitor_main_runtime.py)
- [stop_main_runtime.py](/c:/next-trade-ver1.0/stop_main_runtime.py)

Validation and conclusion documents:

- [MAIN_RUNTIME_LIVE_CHECKLIST.md](/c:/next-trade-ver1.0/MAIN_RUNTIME_LIVE_CHECKLIST.md)
- [MAIN_RUNTIME_GO_NO_GO_CONCLUSION.md](/c:/next-trade-ver1.0/MAIN_RUNTIME_GO_NO_GO_CONCLUSION.md)
- [MAIN_RUNTIME_LOGIC_FLOWCHART.md](/c:/next-trade-ver1.0/MAIN_RUNTIME_LOGIC_FLOWCHART.md)

## 3. Full Architecture Map

```mermaid
flowchart TD
    RT[TradingRuntime]
    TR[(trading_results)]
    CFG[config.json / .env / api_config]
    EX[(Binance Demo Futures API)]

    RT --> CFG
    RT --> TR
    RT --> AS[AccountService]
    RT --> MDS[MarketDataService]
    RT --> IS[IndicatorService]
    RT --> MRS[MarketRegimeService]
    RT --> SE[SignalEngine]
    RT --> SR[StrategyRegistry]
    RT --> ALS[AllocationService]
    RT --> OE[OrderExecutor]
    RT --> POM[ProtectiveOrderManager]
    RT --> PEND[PendingOrderManager]
    RT --> PM[PositionManager]
    RT --> PTP[PartialTakeProfitManager]
    RT --> TO[TradeOrchestrator]

    AS --> EX
    MDS --> EX
    OE --> EX
    POM --> EX
    RT --> EX

    AS --> TR
    MDS --> TR
    OE --> TR
    POM --> TR
    PEND --> TR
    PM --> TR
    TO --> TR

    TO --> AS
    TO --> MDS
    TO --> IS
    TO --> MRS
    TO --> SE
    TO --> SR
    TO --> ALS
    TO --> OE
    TO --> POM
    TO --> PEND
    TO --> PM
    TO --> PTP
```

## 4. Initialization Sequence

```mermaid
sequenceDiagram
    participant User
    participant RT as TradingRuntime
    participant CFG as config/.env
    participant AS as AccountService
    participant MDS as MarketDataService
    participant ALS as AllocationService
    participant TO as TradeOrchestrator

    User->>RT: instantiate TradingRuntime()
    RT->>CFG: load .env
    RT->>CFG: load config.json
    RT->>RT: resolve api_key / api_secret / base_url
    RT->>RT: create trading_results
    RT->>MDS: create service
    RT->>AS: create service
    RT->>RT: create PositionManager / PendingOrderManager / ProtectiveOrderManager / OrderExecutor
    RT->>MDS: load_valid_symbols()
    RT->>RT: load_strategies()
    RT->>TO: create TradeOrchestrator
    RT->>AS: periodic_sync()
    AS-->>RT: available_balance + positions
    RT->>ALS: refresh_strategy_capital_allocations()
    RT->>RT: initialized = true
```

## 5. Initialization Detail

Initialization in [main_runtime.py](/c:/next-trade-ver1.0/main_runtime.py) does this in order:

1. Load `.env`.
2. Initialize shared `trading_results`.
3. Load `config.json`.
4. Resolve credentials and base URL.
5. Load trading configuration values.
6. Create service layer objects.
7. Load valid symbols from exchange metadata plus 24h tickers.
8. Load enabled strategies into runtime state.
9. Construct `TradeOrchestrator`.
10. Run account sync to get actual capital.
11. Initialize allocation state.
12. Mark runtime as initialized.

## 6. Shared State Structure

The central shared state is `trading_results`.

Main keys currently used:

- `strategies`
- `active_positions`
- `pending_trades`
- `closed_trades`
- `real_orders`
- `total_trades`
- `available_balance`
- `market_regime`
- `market_data`
- `system_errors`
- `error_count`
- `last_error`
- `recently_closed_symbols`
- `position_entry_times`
- `partial_take_profit_state`
- `managed_stop_prices`

Important state relationships:

- `position_entry_times` is now unified and shared by runtime, pending-order manager, and position manager.
- `managed_stop_prices` is now written by the protective order manager into `trading_results` as well as local manager state for the validated stop path.

## 7. Main Runtime Loop

```mermaid
flowchart TD
    A[TradingRuntime.run] --> B{initialized?}
    B -- No --> B1[log runtime_not_initialized]
    B -- Yes --> C[print startup banner]
    C --> D[loop forever]
    D --> E[account_service.periodic_sync]
    E --> F[pending_order_manager.refresh_pending_orders]
    F --> G[trade_orchestrator.run_trading_cycle]
    G --> H[_process_cycle_results]
    H --> I[_display_cycle_status]
    I --> J[sleep 10 seconds]
    J --> D
```

## 8. Trading Cycle Full Flow

```mermaid
flowchart TD
    C1[run_trading_cycle] --> C2[account_service.periodic_sync]
    C2 --> C3[market_data_service.update_market_data]
    C3 --> C4[select preferred symbols per strategy]
    C4 --> C5[write flat current prices to trading_results.market_data]
    C5 --> C6[analyze market regime per symbol]
    C6 --> C7[calculate indicators per selected symbol]
    C7 --> C8[generate strategy signal]
    C8 --> C9[emit signal diagnostic]
    C9 --> C10{signal HOLD?}
    C10 -- Yes --> C11[no trade candidate]
    C10 -- No --> C12[collect trade candidate]
    C11 --> C13[next symbol]
    C12 --> C13
    C13 --> C14[score trade candidates]
    C14 --> C15[sort by final_score]
    C15 --> C16[keep top 3]
    C16 --> C17[execute_strategy_trade]
    C17 --> C18[position_manager.manage_open_positions]
    C18 --> C19[build diagnostic summary]
    C19 --> C20[return cycle_results]
```

## 9. Market Data and Signal Path

Within [core/trade_orchestrator.py](/c:/next-trade-ver1.0/core/trade_orchestrator.py):

1. Market data is refreshed for the symbol list.
2. The runtime stores simplified prices in `trading_results["market_data"]`.
3. Each symbol gets:
   - regime analysis
   - moving averages
   - EMA set
   - Heikin Ashi analysis
   - fractals
   - RSI
   - ATR
4. `SignalEngine.generate_strategy_signal(...)` is called.
5. Diagnostics are printed and summarized.
6. Only non-`HOLD` signals become trade candidates.

## 10. Strategy Selection and Candidate Ranking

Current runtime strategy set:

- `ma_trend_follow`
- `ema_crossover`

Selection and ranking chain:

```mermaid
flowchart TD
    S1[active_strategies] --> S2[StrategyRegistry.select_preferred_symbols]
    S2 --> S3[selected symbols per strategy]
    S3 --> S4[SignalEngine.generate_strategy_signal]
    S4 --> S5[trade candidate list]
    S5 --> S6[SignalEngine.score_trade_candidate]
    S6 --> S7[sort descending final_score]
    S7 --> S8[top 3 candidates sent to execute_strategy_trade]
```

## 11. Entry Execution Path

```mermaid
flowchart TD
    E1[execute_strategy_trade] --> E2[duplicate entry check]
    E2 --> E3[get strategy config]
    E3 --> E4[generate signal]
    E4 --> E5[check min confidence]
    E5 --> E6[account_service.can_open_new_positions]
    E6 --> E7[allocation_service.get_strategy_capital]
    E7 --> E8[allocation_service.calculate_position_size]
    E8 --> E9[convert signal to BUY/SELL]
    E9 --> E10[order_executor.submit_order reduce_only=false]
    E10 --> E11{order accepted?}
    E11 -- No --> E12[return failed reason]
    E11 -- Yes --> E13[create position_info]
    E13 --> E14[write active_positions]
    E14 --> E15[place protective orders]
    E15 --> E16[record capital allocation decision]
    E16 --> E17[return success]
```

## 12. Order Executor Full Detail

The order path in [core/order_executor.py](/c:/next-trade-ver1.0/core/order_executor.py) is:

1. Resolve symbol metadata from exchange info.
2. Parse:
   - `LOT_SIZE`
   - `MIN_NOTIONAL`
   - `NOTIONAL`
3. Read current price from `trading_results["market_data"]`.
4. Adjust quantity to:
   - min quantity
   - step size
   - min notional
   - available balance
5. Get server time.
6. Build signed market order.
7. Send `POST /fapi/v1/order`.
8. Process response into `real_orders`.

### Entry vs Close

- Entry orders use `reduce_only=false`.
- Exit orders use `reduce_only=true`.
- For `reduce_only`, the executor avoids the same quantity growth logic used for entry orders.

## 13. Protective Algo Order Flow

This path was one of the major corrected items.

```mermaid
flowchart TD
    P1[TradeOrchestrator._place_protective_orders] --> P2[compute stop and take-profit]
    P2 --> P3[cancel existing symbol protective orders]
    P3 --> P4[submit STOP_MARKET]
    P4 --> P5[submit TAKE_PROFIT_MARKET]

    P4 --> P6[ProtectiveOrderManager.submit_protective_order]
    P5 --> P6
    P6 --> P7[get server time]
    P7 --> P8[build CONDITIONAL algo params]
    P8 --> P9[POST /fapi/v1/algoOrder]
    P9 --> P10[store managed_stop_prices]
```

### Current Algo Order Parameters

The validated protective order payload now includes:

- `algoType=CONDITIONAL`
- `symbol`
- `side`
- `type` as `STOP_MARKET` or `TAKE_PROFIT_MARKET`
- `triggerPrice`
- `timeInForce=GTC`
- `closePosition=true`
- `workingType=CONTRACT_PRICE`
- signed `timestamp`

### Open / Cancel Protective Orders

Open orders:

- `GET /fapi/v1/openAlgoOrders`

Cancel orders:

- `DELETE /fapi/v1/algoOrder`

Current field usage:

- `algoId`
- `orderType`
- `triggerPrice`

## 14. Pending Order Reconciliation

```mermaid
flowchart TD
    R1[PendingOrderManager.refresh_pending_orders] --> R2[iterate real_orders]
    R2 --> R3[filter NEW / PARTIALLY_FILLED]
    R3 --> R4[get_order_status from runtime]
    R4 --> R5[update status / executed_qty / avgPrice]
    R5 --> R6{status FILLED?}
    R6 -- No --> R7[mark pending or failed]
    R6 -- Yes --> R8[mark ACTUAL_TRADE]
    R8 --> R9{reduce_only?}
    R9 -- No --> R10[save position_entry_times]
    R10 --> R11[cancel and reinstall protective orders]
    R9 -- Yes --> R12[estimate realized_pnl]
    R12 --> R13[sync positions]
    R13 --> R14{full exit?}
    R14 -- Yes --> R15[clear position state]
    R15 --> R16[cancel protective orders]
    R14 -- No --> R17[keep remaining position state]
    R16 --> R18[recompute trade counters]
    R17 --> R18
    R7 --> R18
```

## 15. Position Management Flow

```mermaid
flowchart TD
    M1[PositionManager.manage_open_positions] --> M2[loop active_positions]
    M2 --> M3[refresh current_price]
    M3 --> M4[get position state]
    M4 --> M5[manage partial profit targets]
    M5 --> M6{EMA21 trailing exit?}
    M6 -- Yes --> M7[close_position reduce_only]
    M6 -- No --> M8[hold]
    M7 --> M9[clear state and remove local position]
```

### PositionManager responsibilities

- calculate hold time
- compute unrealized PnL and PnL %
- expose position management state
- manage partial closes
- manage full closes
- manage trailing / EMA21 exit logic
- clear related state after close

## 16. Account Sync Flow

```mermaid
flowchart TD
    A1[AccountService.periodic_sync] --> A2[sync_account_balance]
    A2 --> A3[get_account_info from /fapi/v2/account]
    A3 --> A4[extract wallet / available balances]
    A4 --> A5[write account_balance / total_balance / available_balance]
    A5 --> A6[sync_positions]
    A6 --> A7[get_positions from account payload]
    A7 --> A8[preserve existing local metadata]
    A8 --> A9[rewrite trading_results.active_positions]
```

### Preserved local position metadata on sync

When positions are refreshed from exchange, the system tries to preserve:

- `strategy`
- `entry_time`
- `signal_confidence`
- `stop_loss_pct`
- `take_profit_pct`
- `partial_tp_state`
- `managed_stop_price`

## 17. Runtime State File Flow

```mermaid
flowchart TD
    T1[TradingRuntime._process_cycle_results] --> T2[merge cycle_results into trading_results]
    T2 --> T3[json.dump trading_results.json]
    T3 --> T4[monitor scripts read trading_results.json]
    T4 --> T5[user sees positions / trades / errors]
```

Main state file:

- [trading_results.json](/c:/next-trade-ver1.0/trading_results.json)

## 18. Validation Evidence Flow

```mermaid
flowchart TD
    V1[short smoke validation] --> V2[runtime_smoke_snapshot.json]
    V3[order polling test] --> V4[order_status_polling_snapshot.json]
    V5[protective algo order test] --> V6[protective_order_validation_snapshot.json]
    V7[background probe] --> V8[background_probe_status.json]
    V2 --> V9[GO/NO-GO conclusion]
    V4 --> V9
    V6 --> V9
    V8 --> V9
```

Evidence files:

- [runtime_smoke_snapshot.json](/c:/next-trade-ver1.0/runtime_smoke_snapshot.json)
- [order_status_polling_snapshot.json](/c:/next-trade-ver1.0/order_status_polling_snapshot.json)
- [protective_order_validation_snapshot.json](/c:/next-trade-ver1.0/protective_order_validation_snapshot.json)
- [background_probe_status.json](/c:/next-trade-ver1.0/background_probe_status.json)

## 19. Background Supervised Probe Flow

```mermaid
flowchart TD
    B1[background_supervised_probe.py] --> B2[write starting status]
    B2 --> B3[instantiate TradingRuntime]
    B3 --> B4{initialized?}
    B4 -- No --> B5[write init_failed]
    B4 -- Yes --> B6[write running status]
    B6 --> B7[run 3 supervised cycles]
    B7 --> B8[write each cycle summary]
    B8 --> B9[write completed status]
```

Purpose of the probe:

- validate background execution path
- validate separated process behavior
- validate repeated cycle stability
- produce an explicit machine-readable status file

## 20. Background Operations Tooling Flow

### Start flow

```mermaid
flowchart TD
    S1[run_main_runtime_background.py] --> S2[validate files and config]
    S2 --> S3[write main_runtime_background_loop.py]
    S3 --> S4[verify monitor_main_runtime.py and stop_main_runtime.py exist]
    S4 --> S5[start background python process]
    S5 --> S6[wait initial startup]
    S6 --> S7[inspect trading_results.json]
```

### Monitor flow

```mermaid
flowchart TD
    M1[monitor_main_runtime.py] --> M2[read trading_results.json]
    M2 --> M3[show runtime status / balances / positions / errors]
    M3 --> M4[query Win32_Process via PowerShell]
    M4 --> M5[filter python.exe command lines containing main_runtime_background_loop.py]
    M5 --> M6[display matching process list]
    M6 --> M7[sleep 120 seconds]
    M7 --> M1
```

### Stop flow

```mermaid
flowchart TD
    X1[stop_main_runtime.py] --> X2[query Win32_Process via PowerShell]
    X2 --> X3[filter runtime loop process by command line]
    X3 --> X4[taskkill matching PIDs]
    X4 --> X5[recheck for remaining processes]
    X5 --> X6[update trading_results.json main_runtime_background status]
```

## 21. Recently Fixed Items Included In This Map

### A. Strategy registry compatibility

The missing runtime symbol selection interface in:

- [core/strategy_registry.py](/c:/next-trade-ver1.0/core/strategy_registry.py)

was restored so `TradeOrchestrator` can call:

- `select_preferred_symbols(...)`

### B. Protective order routing

The protective order flow was corrected from the regular order endpoint to the algo order endpoints in:

- [core/protective_order_manager.py](/c:/next-trade-ver1.0/core/protective_order_manager.py)

### C. Shared `position_entry_times`

The entry-time mapping was unified through:

- [main_runtime.py](/c:/next-trade-ver1.0/main_runtime.py)
- [core/pending_order_manager.py](/c:/next-trade-ver1.0/core/pending_order_manager.py)
- [core/position_manager.py](/c:/next-trade-ver1.0/core/position_manager.py)

### D. `update_stop_loss()` algo schema alignment

`update_stop_loss()` now looks for:

- `orderType`
- `algoId`

instead of relying only on legacy:

- `type`
- `orderId`

### E. Operations scripts repair

`tasklist` string matching was replaced for actual command-line-aware process discovery in:

- [monitor_main_runtime.py](/c:/next-trade-ver1.0/monitor_main_runtime.py)
- [stop_main_runtime.py](/c:/next-trade-ver1.0/stop_main_runtime.py)

Missing imports in `stop_main_runtime.py` were also repaired.

## 22. Current Strong Points

- runtime initializes cleanly
- account sync is working
- dynamic symbol loading is working
- known order status polling is working
- protective conditional algo orders are working
- reduce-only close path is working
- short supervised foreground runs are stable
- short background supervised probe is stable
- monitor/stop helper scripts are now internally consistent

## 23. Current Residual Risks

- validation is still limited to demo futures, not production futures
- long-running multi-hour or multi-session behavior remains less exercised than short supervised runs
- the strategy set still produced mostly `HOLD` outcomes during supervised cycles, so broad live-signal variety remains lightly exercised
- [core/partial_take_profit_manager.py](/c:/next-trade-ver1.0/core/partial_take_profit_manager.py) still maintains its own `managed_stop_prices` state separate from `trading_results["managed_stop_prices"]`, so full stop-management unification is not yet complete there

## 24. Recommended Reading Order

If you want to trace the whole system without getting lost, read in this order:

1. [MAIN_RUNTIME_GO_NO_GO_CONCLUSION.md](/c:/next-trade-ver1.0/MAIN_RUNTIME_GO_NO_GO_CONCLUSION.md)
2. [MAIN_RUNTIME_LIVE_CHECKLIST.md](/c:/next-trade-ver1.0/MAIN_RUNTIME_LIVE_CHECKLIST.md)
3. [main_runtime.py](/c:/next-trade-ver1.0/main_runtime.py)
4. [core/trade_orchestrator.py](/c:/next-trade-ver1.0/core/trade_orchestrator.py)
5. [core/order_executor.py](/c:/next-trade-ver1.0/core/order_executor.py)
6. [core/protective_order_manager.py](/c:/next-trade-ver1.0/core/protective_order_manager.py)
7. [core/pending_order_manager.py](/c:/next-trade-ver1.0/core/pending_order_manager.py)
8. [core/position_manager.py](/c:/next-trade-ver1.0/core/position_manager.py)
9. [core/account_service.py](/c:/next-trade-ver1.0/core/account_service.py)
10. [background_supervised_probe.py](/c:/next-trade-ver1.0/background_supervised_probe.py)
11. [run_main_runtime_background.py](/c:/next-trade-ver1.0/run_main_runtime_background.py)
12. [monitor_main_runtime.py](/c:/next-trade-ver1.0/monitor_main_runtime.py)
13. [stop_main_runtime.py](/c:/next-trade-ver1.0/stop_main_runtime.py)

## 25. One-Line End-to-End Summary

The full system flow is:

`TradingRuntime` loads config and shared state -> syncs account and symbols -> `TradeOrchestrator` builds data, regimes, indicators, signals, and candidates -> `OrderExecutor` places entries and exits -> `ProtectiveOrderManager` creates conditional algo stop/take-profit orders -> `PendingOrderManager` reconciles fills and counters -> `PositionManager` manages open positions -> helper scripts monitor, start, probe, and stop the runtime around the same state files and process command lines.
