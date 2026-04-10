# Binance Testnet Execution Plan

Date: 2026-04-09
Environment: `https://demo-fapi.binance.com`
Purpose: prepare the next evolution step with fresh runtime validation data

## Goal

Run a structured testnet validation pass that:

- verifies runtime initialization
- verifies a real trading cycle can execute without runtime errors
- verifies order status polling on a known order id
- verifies protective conditional algo orders
- verifies reduce-only close behavior
- verifies background supervised runtime stability
- collects machine-readable and human-readable evidence for the next development step

## Test Phases

### Phase 1. Initialization
- Instantiate `TradingRuntime`
- Record:
  - `initialized`
  - `base_url`
  - `capital`
  - `valid_symbol_count`
  - `active_strategies`
  - `system_errors`

### Phase 2. Trading Cycle
- Run one supervised trading cycle on a bounded symbol subset
- Record:
  - `signals_generated`
  - `trades_executed`
  - `errors`

### Phase 3. Order Polling
- Place a low-risk deep limit order on testnet
- Poll order status
- Cancel the order
- Confirm final status transition

### Phase 4. Protective Orders
- Open one minimal testnet market position
- Create:
  - `STOP_MARKET` conditional algo order
  - `TAKE_PROFIT_MARKET` conditional algo order
- Confirm open algo orders are visible
- Close the position with `reduce_only=true`
- Confirm protective orders are cleaned up

### Phase 5. Background Stability
- Run `background_supervised_probe.py`
- Wait for `completed`
- Record cycles, errors, and residual positions/orders

## Success Criteria

- `initialized=true`
- `system_errors=0` during validation
- trading cycle returns no runtime exception
- order polling returns consistent status transitions
- protective algo orders are created successfully
- reduce-only close is recorded and filled
- background probe completes with zero cycle errors

## Evidence Files

- `binance_testnet_validation_results.json`
- `BINANCE_TESTNET_VALIDATION_REPORT.md`
- existing runtime evidence files updated by the runtime itself when relevant

## Expected Output

At the end of this run we should have:

- a fresh operational snapshot
- a clear pass/fail result per phase
- concrete next-evolution targets based on observed weak points
