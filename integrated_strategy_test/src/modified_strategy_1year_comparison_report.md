# Modified Strategy 1-Year Comparison Report

## What Was Fixed
- Random synthetic data is now deterministic via a fixed seed.
- Market regime thresholds are bar-aligned (5.0 / 2.5 average absolute daily change).
- Entry thresholds are regime-aware, time-frame adjusted, and no longer hard-coded to 70.0.
- Cooldown semantics are explicit: 20 minutes becomes 1 daily bar in this simulator.
- Results now include rebalancing events, market-regime counts, and individual performance.

## Current Run Summary
- Final capital: $999.46
- Final PnL: $-0.54 (-0.05%)
- Fees paid: $0.48
- Realized PnL: $-0.54
- Unrealized PnL: $+0.00
- Entries: 6
- Take profits: 3
- Loss exits: 2
- Potential-drop exits: 1
- Market regime counts: {'NORMAL': 105, 'HIGH_VOLATILITY': 204, 'EXTREME': 57}

## Strategy Alignment Notes
- Take profit remains 1.5%, matching the tuned modular strategy.
- Entry thresholds now vary by regime: {'EXTREME': 66.0, 'HIGH_VOLATILITY': 70.0, 'NORMAL': 68.0}.
- Regime volatility thresholds now use {'EXTREME': 5.0, 'HIGH_VOLATILITY': 2.5}, which fit daily bars.
- Reentry cooldown is documented as 1 daily bar(s).

## Previous vs Current
- Previous final capital: $838.96
- Current final capital: $999.46
- Previous final PnL: $-161.04
- Current final PnL: $-0.54
- Previous entries: 617
- Current entries: 6
- Previous take profits: 297
- Current take profits: 3
- Previous loss exits: 317
- Current loss exits: 2

## Important Caveat
- The previous run mixed daily bars with minute-labeled cooldown and regime thresholds that never triggered.
- The current run is still synthetic, but its semantics are internally consistent and reproducible.
