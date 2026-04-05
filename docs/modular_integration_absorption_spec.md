# Modular Strategy Integration Absorption Spec

## Purpose

This document defines the concrete work needed to absorb the useful parts of
`integrated_strategy_test` into the main `next_trade` project.

The goal is not to copy the modular simulator as-is. The goal is to:

- preserve the original `next_trade` package/runtime structure
- split exchange access into `Public Read`, `Private Read`, and `Execution`
- move reusable scoring and selection logic into `src/next_trade`
- avoid direct `requests` calls from strategy and simulation logic

## Integration Target

Target package root:

- `C:/next-trade-ver1.0/src/next_trade`

Reference source to absorb from:

- `C:/next-trade-ver1.0/integrated_strategy_test/src/modules/market_analyzer.py`
- `C:/next-trade-ver1.0/integrated_strategy_test/src/modules/realtime_data.py`
- `C:/next-trade-ver1.0/integrated_strategy_test/src/modules/portfolio_manager.py`
- `C:/next-trade-ver1.0/integrated_strategy_test/src/modules/simulator.py`
- `C:/next-trade-ver1.0/integrated_strategy_test/src/improved_real_market_simulator.py`

Existing original project anchors:

- `C:/next-trade-ver1.0/src/next_trade/api/app.py`
- `C:/next-trade-ver1.0/src/next_trade/api/investor_service.py`
- `C:/next-trade-ver1.0/src/next_trade/execution/binance_testnet_adapter.py`
- `C:/next-trade-ver1.0/src/next_trade/execution/exchange_adapter.py`

## Design Decision

Absorb only these categories:

- market scoring logic
- symbol selection logic
- lightweight portfolio state calculation
- rebalance decision logic
- display/report formatting for simulation status

Do not absorb these categories directly:

- direct `requests` exchange calls
- standalone script entrypoints
- blocking `time.sleep()` orchestration inside API-facing code
- ad-hoc result file writing outside original runtime conventions

## New Files To Create

### Exchange Layer

1. `C:/next-trade-ver1.0/src/next_trade/exchange/__init__.py`
- package marker

2. `C:/next-trade-ver1.0/src/next_trade/exchange/public_read_client.py`
- public market data access only
- ticker
- klines
- exchange info
- top-volume symbol list

3. `C:/next-trade-ver1.0/src/next_trade/exchange/private_read_client.py`
- private account reads only
- balances
- positions
- open orders
- account status

4. `C:/next-trade-ver1.0/src/next_trade/exchange/execution_client.py`
- execution facade wrapping the original adapter
- place order
- cancel order
- cancel all
- amend order when supported

### Services Layer

5. `C:/next-trade-ver1.0/src/next_trade/services/__init__.py`
- package marker

6. `C:/next-trade-ver1.0/src/next_trade/services/market_scoring_service.py`
- RSI
- MACD
- SMA
- Bollinger Bands
- volatility
- bullish score
- profit potential

7. `C:/next-trade-ver1.0/src/next_trade/services/symbol_selection_service.py`
- market regime calculation
- threshold mapping
- profitable symbol filtering
- final symbol selection

8. `C:/next-trade-ver1.0/src/next_trade/services/portfolio_state_service.py`
- cash balance state
- initial investment tracking
- pnl and pnl percent calculation
- UI/report row formatting

9. `C:/next-trade-ver1.0/src/next_trade/services/rebalance_service.py`
- removal decision rules
- replacement candidate rules
- replacement threshold handling

10. `C:/next-trade-ver1.0/src/next_trade/services/risk_gate.py`
- kill switch checks
- order size checks
- symbol allowlist checks
- duplicate order prevention

### Simulation Layer

11. `C:/next-trade-ver1.0/src/next_trade/simulation/__init__.py`
- package marker

12. `C:/next-trade-ver1.0/src/next_trade/simulation/models.py`
- typed models for symbol score, portfolio row, simulation snapshot

13. `C:/next-trade-ver1.0/src/next_trade/simulation/modular_simulation_service.py`
- orchestration service for simulation mode only
- must depend on the 3 exchange clients
- must not directly call `requests`

### Tests

14. `C:/next-trade-ver1.0/tests/test_public_read_client.py`
- read-only client tests

15. `C:/next-trade-ver1.0/tests/test_market_scoring_service.py`
- scoring unit tests

16. `C:/next-trade-ver1.0/tests/test_symbol_selection_service.py`
- regime and selection tests

17. `C:/next-trade-ver1.0/tests/test_portfolio_state_service.py`
- pnl state calculation tests

18. `C:/next-trade-ver1.0/tests/test_rebalance_service.py`
- removal/addition decision tests

## Existing Files To Modify

1. `C:/next-trade-ver1.0/src/next_trade/execution/binance_testnet_adapter.py`
- expose a narrower execution facade for use by `ExecutionClient`
- keep safety and run-artifact behavior unchanged

2. `C:/next-trade-ver1.0/src/next_trade/api/investor_service.py`
- move account-read responsibilities behind `PrivateReadClient`
- reduce direct transport logic inside service functions where possible

3. `C:/next-trade-ver1.0/src/next_trade/api/routes_v1_ops.py`
- add simulation status/read-only strategy observation routes only if needed
- avoid blocking execution inside routes

4. `C:/next-trade-ver1.0/src/next_trade/api/app.py`
- include new routers only if a new simulation/strategy endpoint is introduced

5. `C:/next-trade-ver1.0/pyproject.toml`
- no package-name change expected
- only update if new subpackages require explicit packaging adjustments

## Source Mapping

### From `market_analyzer.py`

Move into:

- `market_scoring_service.py`
- `public_read_client.py`

Mapping:

- `get_top_volume_symbols()` -> `PublicReadClient.get_top_volume_symbols()`
- `_calculate_indicators_from_symbol()` -> split:
  - data fetch -> `PublicReadClient.get_klines()`
  - calculations -> `MarketScoringService`
- `_calculate_rsi()` -> `MarketScoringService`
- `_calculate_macd_signal()` -> `MarketScoringService`
- `_calculate_bollinger_bands()` -> `MarketScoringService`
- `_calculate_bullish_score()` -> `MarketScoringService`

### From `realtime_data.py`

Move into:

- `public_read_client.py`
- `market_scoring_service.py`

Mapping:

- `get_real_time_symbol_data()` -> `PublicReadClient.get_symbol_snapshot_batch()`
- `calculate_real_time_rsi()` -> `MarketScoringService`
- `calculate_real_time_macd()` -> `MarketScoringService`
- `calculate_real_time_bullish_score()` -> `MarketScoringService`
- `_calculate_profit_potential()` -> `MarketScoringService`

### From `portfolio_manager.py`

Move into:

- `portfolio_state_service.py`

Mapping:

- allocation and state shape -> keep conceptually
- local virtual portfolio state -> turn into typed service models
- direct investment mutation helpers -> adapt for simulation mode only

### From `simulator.py`

Move into:

- `symbol_selection_service.py`
- `rebalance_service.py`
- `modular_simulation_service.py`

Mapping:

- `analyze_market_regime()` -> `SymbolSelectionService`
- `evaluate_profitability_potential()` -> `SymbolSelectionService`
- `select_optimal_symbols()` -> `SymbolSelectionService`
- `dynamic_portfolio_rebalancing()` -> `RebalanceService`
- `run_simulation()` -> `ModularSimulationService`

## Work Breakdown

### Phase 1: Exchange Layer Split

Deliverables:

- create `exchange/` package
- implement `PublicReadClient`
- implement `PrivateReadClient`
- implement `ExecutionClient`

Acceptance criteria:

- no new strategy/simulation code directly calls `requests`
- execution still goes through original adapter protections

### Phase 2: Scoring Absorption

Deliverables:

- create `market_scoring_service.py`
- port indicator and scoring formulas

Acceptance criteria:

- scoring service can run using pre-fetched candle/ticker data
- no transport dependency inside scoring service

### Phase 3: Selection and Portfolio Logic

Deliverables:

- create `symbol_selection_service.py`
- create `portfolio_state_service.py`
- create `rebalance_service.py`

Acceptance criteria:

- symbol selection works from service inputs only
- portfolio rows support these fields:
  - symbol
  - initial investment
  - change amount
  - change percent
  - profit potential

### Phase 4: Simulation Orchestration

Deliverables:

- create `modular_simulation_service.py`
- move simulation-only orchestration here

Acceptance criteria:

- orchestration depends only on services and exchange clients
- orchestration can be invoked without API route blocking redesign

### Phase 5: API/Runtime Hookup

Deliverables:

- connect read-only status exposure through original API when needed
- integrate runtime metrics/logging conventions

Acceptance criteria:

- no standalone result-file convention becomes primary runtime output
- original `next_trade` process model remains intact

## Output Standard

The absorbed simulation/status formatting must support this row format:

```text
심볼 | 초기진입액 | 변화액 | 변화 % | 상승평가율
```

This display format should be produced by `portfolio_state_service.py` or a
small formatter helper under `simulation/`.

## Non-Goals

- replacing the original FastAPI app structure
- replacing the original adapter with direct HTTP calls
- making `integrated_strategy_test` the new package root
- moving all experimental scripts into `src/next_trade`

## Retirement / Post-Absorption Status

After absorption:

- `integrated_strategy_test` remains as reference and regression material
- canonical implementation lives only under `src/next_trade`
- future fixes should target `src/next_trade`, not the experimental modules

## Recommended First Execution Slice

If implementation starts immediately, the first slice should be:

1. create `exchange/public_read_client.py`
2. create `services/market_scoring_service.py`
3. migrate `MarketAnalyzer` read and scoring logic into those two files
4. add tests for ticker/klines mocking plus score calculation

This gives the highest-value integration with the lowest operational risk.
