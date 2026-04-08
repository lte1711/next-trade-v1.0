#!/usr/bin/env python3
"""
Check Pending Symbols - Analyze symbols waiting for entry
"""

import json

def check_pending_symbols():
    """Check symbols currently waiting for entry"""
    print('=' * 60)
    print('PENDING SYMBOLS ANALYSIS')
    print('=' * 60)
    
    # Load trading results
    with open('trading_results.json', 'r') as f:
        results = json.load(f)
    
    # Check active strategies and their symbol selections
    strategies = results.get('strategies', {})
    active_strategies = results.get('active_strategies', [])
    
    print('[ACTIVE STRATEGIES] Current symbol selections:')
    
    for strategy_name in active_strategies:
        strategy = strategies.get(strategy_name, {})
        enabled = strategy.get('enabled', False)
        
        print(f'\n  {strategy_name}:')
        print(f'    - Enabled: {enabled}')
        
        # Get symbol selection configuration
        symbol_selection = strategy.get('symbol_selection', {})
        if symbol_selection:
            symbol_mode = symbol_selection.get('symbol_mode', 'unknown')
            candidate_limit = symbol_selection.get('candidate_limit', 0)
            market_bias = symbol_selection.get('market_bias', 'unknown')
            
            print(f'    - Symbol Mode: {symbol_mode}')
            print(f'    - Candidate Limit: {candidate_limit}')
            print(f'    - Market Bias: {market_bias}')
        else:
            print(f'    - Symbol Selection: NOT CONFIGURED')
        
        # Check last signal
        last_signal = strategy.get('last_signal')
        last_trade = strategy.get('last_trade')
        
        print(f'    - Last Signal: {last_signal}')
        print(f'    - Last Trade: {last_trade}')
    
    # Check market data for available symbols
    market_data = results.get('market_data', {})
    
    print(f'\n[MARKET DATA] Available symbols: {len(market_data)}')
    
    if market_data:
        # Show top 10 symbols by price
        sorted_symbols = sorted(market_data.items(), key=lambda x: float(x[1]), reverse=True)
        print(f'  Top 10 symbols by price:')
        for i, (symbol, price) in enumerate(sorted_symbols[:10], 1):
            print(f'    {i}. {symbol}: {price} USDT')
        
        # Show bottom 10 symbols by price
        sorted_symbols_low = sorted(market_data.items(), key=lambda x: float(x[1]))
        print(f'  Bottom 10 symbols by price:')
        for i, (symbol, price) in enumerate(sorted_symbols_low[:10], 1):
            print(f'    {i}. {symbol}: {price} USDT')
    
    # Check current cycle signals
    print(f'\n[CURRENT CYCLE] Signal analysis:')
    
    total_signals = results.get('signals_generated', 0)
    buy_signals = results.get('buy_signals', 0)
    sell_signals = results.get('sell_signals', 0)
    hold_signals = results.get('hold_signals', 0)
    high_confidence_signals = results.get('high_confidence_signals', 0)
    average_confidence = results.get('average_confidence', 0)
    
    print(f'  - Total Signals: {total_signals}')
    print(f'  - Buy Signals: {buy_signals}')
    print(f'  - Sell Signals: {sell_signals}')
    print(f'  - Hold Signals: {hold_signals}')
    print(f'  - High Confidence Signals: {high_confidence_signals}')
    print(f'  - Average Confidence: {average_confidence:.3f}')
    
    # Check regime distribution
    regime_distribution = results.get('regime_distribution', {})
    if regime_distribution:
        print(f'  - Market Regime Distribution:')
        for regime, count in regime_distribution.items():
            print(f'    {regime}: {count} symbols')
    
    # Check pending trades
    pending_trades = results.get('pending_trades', [])
    
    print(f'\n[PENDING TRADES] Currently waiting: {len(pending_trades)}')
    
    for i, trade in enumerate(pending_trades, 1):
        symbol = trade.get('symbol', 'Unknown')
        strategy = trade.get('strategy', 'Unknown')
        side = trade.get('side', 'Unknown')
        quantity = trade.get('quantity', 0)
        status = trade.get('status', 'Unknown')
        confidence = trade.get('signal_confidence', 0)
        reason = trade.get('signal_reason', 'No reason')
        
        print(f'  {i}. {symbol}:')
        print(f'    - Strategy: {strategy}')
        print(f'    - Side: {side}')
        print(f'    - Quantity: {quantity}')
        print(f'    - Status: {status}')
        print(f'    - Confidence: {confidence:.2f}')
        print(f'    - Reason: {reason}')
    
    # Calculate potential entry candidates
    print(f'\n[POTENTIAL ENTRIES] Analysis:')
    
    # Based on strategy configurations
    total_candidates = 0
    for strategy_name in active_strategies:
        strategy = strategies.get(strategy_name, {})
        symbol_selection = strategy.get('symbol_selection', {})
        candidate_limit = symbol_selection.get('candidate_limit', 0)
        total_candidates += candidate_limit
    
    print(f'  - Total Candidate Slots: {total_candidates}')
    print(f'  - Available Market Symbols: {len(market_data)}')
    print(f'  - Current Pending Trades: {len(pending_trades)}')
    print(f'  - Potential New Entries: {total_candidates - len(pending_trades)}')
    
    # Check position capacity
    max_positions = 5  # From config
    active_positions = results.get('active_positions', {})
    current_positions = len(active_positions)
    available_slots = max_positions - current_positions
    
    print(f'  - Max Positions: {max_positions}')
    print(f'  - Current Positions: {current_positions}')
    print(f'  - Available Slots: {available_slots}')
    print(f'  - Can Accept New Positions: {available_slots > 0}')
    
    # Check last cycle results
    last_cycle = results.get('last_cycle', {})
    if last_cycle:
        print(f'\n[LAST CYCLE] Results:')
        print(f'  - Signals Generated: {last_cycle.get("signals_generated", 0)}')
        print(f'  - Trades Executed: {last_cycle.get("trades_executed", 0)}')
        print(f'  - Errors: {len(last_cycle.get("errors", []))}')
        
        # Check if there were any entry attempts
        cycle_signals = last_cycle.get("signals_generated", 0)
        cycle_trades = last_cycle.get("trades_executed", 0)
        
        if cycle_signals > 0 and cycle_trades == 0:
            print(f'  - Entry Status: SIGNALS GENERATED BUT NO TRADES EXECUTED')
        elif cycle_signals > 0 and cycle_trades > 0:
            print(f'  - Entry Status: TRADES EXECUTED SUCCESSFULLY')
        else:
            print(f'  - Entry Status: NO SIGNALS GENERATED')
    
    print('=' * 60)
    print('[RESULT] Pending symbols analysis complete')
    print('=' * 60)

if __name__ == "__main__":
    check_pending_symbols()
