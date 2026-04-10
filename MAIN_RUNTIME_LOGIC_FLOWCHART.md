# Main Runtime Logic Flowchart

Date: 2026-04-09
Target: `main_runtime.py` centered runtime flow

## 1. Big Picture

This runtime is organized around one central object:

- `TradingRuntime`

It owns shared state:

- `trading_results`

And wires together these main services:

- `AccountService`
- `MarketDataService`
- `IndicatorService`
- `MarketRegimeService`
- `SignalEngine`
- `StrategyRegistry`
- `AllocationService`
- `OrderExecutor`
- `ProtectiveOrderManager`
- `PendingOrderManager`
- `PositionManager`
- `TradeOrchestrator`

## 2. Runtime Dependency Map

```mermaid
flowchart TD
    A[TradingRuntime] --> TR[(trading_results)]
    A --> AS[AccountService]
    A --> MDS[MarketDataService]
    A --> IS[IndicatorService]
    A --> MRS[MarketRegimeService]
    A --> SE[SignalEngine]
    A --> SR[StrategyRegistry]
    A --> ALS[AllocationService]
    A --> OE[OrderExecutor]
    A --> POM[ProtectiveOrderManager]
    A --> PEND[PendingOrderManager]
    A --> PM[PositionManager]
    A --> TO[TradeOrchestrator]
    A --> PTP[PartialTakeProfitManager]

    TO --> AS
    TO --> MDS
    TO --> IS
    TO --> MRS
    TO --> SE
    TO --> SR
    TO --> ALS
    TO --> OE
    TO --> PM
    TO --> POM
    TO --> PTP
    TO --> TR

    PEND --> POM
    PEND --> TR
    PM --> OE
    PM --> POM
    PM --> TR
    OE --> TR
    AS --> TR
```

## 3. Initialization Flow

```mermaid
flowchart TD
    S[TradingRuntime.__init__] --> E1[load .env]
    E1 --> E2[init trading_results]
    E2 --> E3[load config.json]
    E3 --> E4[resolve api_key / api_secret / base_url]
    E4 --> D1{API valid?}
    D1 -- No --> X1[print error and return]
    D1 -- Yes --> E5[load trading_config / api_config]
    E5 --> E6[create services and managers]
    E6 --> E7[load_valid_symbols]
    E7 --> E8[load_strategies]
    E8 --> E9[create TradeOrchestrator]
    E9 --> E10[account_service.periodic_sync]
    E10 --> E11[set total_capital]
    E11 --> E12[_initialize_trading_system]
    E12 --> E13[initialized = true]
```

## 4. Main Loop Flow

```mermaid
flowchart TD
    R1[TradingRuntime.run] --> R2{initialized?}
    R2 -- No --> RX[log runtime_not_initialized]
    R2 -- Yes --> R3[while True]
    R3 --> R4[account_service.periodic_sync]
    R4 --> R5[pending_order_manager.refresh_pending_orders]
    R5 --> R6[trade_orchestrator.run_trading_cycle]
    R6 --> R7[_process_cycle_results]
    R7 --> R8[_display_cycle_status]
    R8 --> R9[sleep 10 seconds]
    R9 --> R3
```

## 5. Trading Cycle Flow

```mermaid
flowchart TD
    C1[TradeOrchestrator.run_trading_cycle] --> C2[account_service.periodic_sync]
    C2 --> C3[market_data_service.update_market_data]
    C3 --> C4[strategy_registry.select_preferred_symbols per strategy]
    C4 --> C5[store flat current prices into trading_results.market_data]
    C5 --> C6[market_regime_service.analyze_market_regime per symbol]
    C6 --> C7[calculate indicators per selected symbol]
    C7 --> C8[signal_engine.generate_strategy_signal]
    C8 --> C9{signal != HOLD?}
    C9 -- No --> C10[diagnostic only]
    C9 -- Yes --> C11[collect candidate]
    C10 --> C12[next symbol]
    C11 --> C12
    C12 --> C13[score candidates]
    C13 --> C14[sort and keep top 3]
    C14 --> C15[execute_strategy_trade per candidate]
    C15 --> C16[position_manager.manage_open_positions]
    C16 --> C17[build diagnostic summary]
    C17 --> C18[return cycle_results]
```

## 6. Trade Execution Flow

```mermaid
flowchart TD
    T1[execute_strategy_trade] --> T2[duplicate entry check]
    T2 --> T3[get strategy profile]
    T3 --> T4[generate signal]
    T4 --> T5[confidence filter]
    T5 --> T6[account_service.can_open_new_positions]
    T6 --> T7[allocation_service.calculate_position_size]
    T7 --> T8[order_executor.submit_order]
    T8 --> D2{order status in FILLED/NEW/PARTIALLY_FILLED?}
    D2 -- No --> T9[return failed reason]
    D2 -- Yes --> T10[create position_info]
    T10 --> T11[write active_positions]
    T11 --> T12[_place_protective_orders]
    T12 --> T13[record capital allocation decision]
    T13 --> T14[return success]
```

## 7. Order Path

```mermaid
flowchart TD
    O1[OrderExecutor.submit_order] --> O2[get symbol info]
    O2 --> O3[read LOT_SIZE / NOTIONAL filters]
    O3 --> O4[get current price from trading_results.market_data]
    O4 --> O5[normalize quantity to step size]
    O5 --> O6[validate min notional]
    O6 --> O7[cap by available_balance]
    O7 --> O8[get server time]
    O8 --> O9[build signed MARKET order]
    O9 --> O10[POST /fapi/v1/order]
    O10 --> O11[_process_order_result]
    O11 --> O12[append record to trading_results.real_orders]
```

## 8. Protective Order Path

```mermaid
flowchart TD
    P1[_place_protective_orders] --> P2[cancel existing symbol protective orders]
    P2 --> P3[compute stop and take-profit prices]
    P3 --> P4[submit STOP_MARKET algo order]
    P4 --> P5[submit TAKE_PROFIT_MARKET algo order]

    P4 --> P6[ProtectiveOrderManager.submit_protective_order]
    P5 --> P6
    P6 --> P7[get server time]
    P7 --> P8[build signed CONDITIONAL algo order]
    P8 --> P9[POST /fapi/v1/algoOrder]
    P9 --> P10[Binance demo futures algo order created]
```

## 9. Pending Order Refresh Path

```mermaid
flowchart TD
    Q1[PendingOrderManager.refresh_pending_orders] --> Q2[iterate trading_results.real_orders]
    Q2 --> Q3[only NEW / PARTIALLY_FILLED]
    Q3 --> Q4[get_order_status]
    Q4 --> Q5[update status / executed_qty / price]
    Q5 --> Q6{became FILLED?}
    Q6 -- No --> Q7[set pending or failed trade type]
    Q6 -- Yes --> Q8[mark ACTUAL_TRADE]
    Q8 --> Q9{reduce_only?}
    Q9 -- No --> Q10[save entry time]
    Q10 --> Q11[cancel and reinstall protective orders]
    Q9 -- Yes --> Q12[estimate realized pnl]
    Q12 --> Q13[sync positions]
    Q13 --> Q14{full exit?}
    Q14 -- Yes --> Q15[clear position state and cancel protective orders]
    Q14 -- No --> Q16[keep remaining position state]
    Q15 --> Q17[recompute counters]
    Q16 --> Q17
    Q7 --> Q17
```

## 10. Position Management Path

```mermaid
flowchart TD
    M1[PositionManager.manage_open_positions] --> M2[loop active_positions]
    M2 --> M3[refresh current_price from market_data]
    M3 --> M4[get position management state]
    M4 --> M5[manage_profit_targets]
    M5 --> M6{EMA21 trailing exit?}
    M6 -- Yes --> M7[close_position reduce_only]
    M6 -- No --> M8[keep position]
    M7 --> M9[clear local position state]
```

## 11. Shared State Connections

These are the most important shared structures inside `trading_results`:

- `active_positions`
  Used by `TradeOrchestrator`, `AccountService`, `PositionManager`, `PendingOrderManager`
- `real_orders`
  Produced by `OrderExecutor`, consumed by `PendingOrderManager`
- `pending_trades`
  Recomputed by `PendingOrderManager`
- `closed_trades`
  Recomputed by `PendingOrderManager`
- `market_data`
  Written by `TradeOrchestrator`, read by `OrderExecutor`
- `system_errors`
  Written through `TradingRuntime.log_system_error`
- `position_entry_times`
  Intended to connect runtime, pending fills, and position management

## 12. Practical Reading Order

If you want to understand the code quickly, read in this order:

1. [main_runtime.py](/c:/next-trade-ver1.0/main_runtime.py)
2. [core/trade_orchestrator.py](/c:/next-trade-ver1.0/core/trade_orchestrator.py)
3. [core/order_executor.py](/c:/next-trade-ver1.0/core/order_executor.py)
4. [core/protective_order_manager.py](/c:/next-trade-ver1.0/core/protective_order_manager.py)
5. [core/pending_order_manager.py](/c:/next-trade-ver1.0/core/pending_order_manager.py)
6. [core/position_manager.py](/c:/next-trade-ver1.0/core/position_manager.py)
7. [core/account_service.py](/c:/next-trade-ver1.0/core/account_service.py)

## 13. Connection Notes

### A. `position_entry_times` is now unified

In [main_runtime.py](/c:/next-trade-ver1.0/main_runtime.py), `PendingOrderManager` now receives the same shared mapping stored in `trading_results["position_entry_times"]`.

That means:

- `TradingRuntime`
- `PendingOrderManager`
- `PositionManager`

now all refer to the same position entry time state.

### B. `update_stop_loss()` is aligned to algo orders

In [core/protective_order_manager.py](/c:/next-trade-ver1.0/core/protective_order_manager.py), `update_stop_loss()` now reads algo-order fields using:

- `orderType`
- `algoId`

and also keeps `managed_stop_prices` synchronized both in the manager object and in `trading_results["managed_stop_prices"]`.

This brings the stop-tightening branch into the same state model as the validated protective order path.

## 14. One-Line Summary

The runtime flow is:

`TradingRuntime` syncs account -> refreshes pending orders -> `TradeOrchestrator` pulls market data and signals -> `OrderExecutor` places entry/exit orders -> `ProtectiveOrderManager` installs algo stop/take-profit orders -> `PendingOrderManager` reconciles fills -> `PositionManager` manages open positions.
