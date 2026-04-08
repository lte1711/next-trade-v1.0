#!/usr/bin/env python3
"""
Check Potential Entries - Check for potential new entry symbols
"""

import json

def check_potential_entries():
    """Check for potential new entry symbols"""
    print('=' * 60)
    print('POTENTIAL ENTRY SYMBOLS CHECK')
    print('=' * 60)
    
    # Load trading results
    with open('trading_results.json', 'r') as f:
        results = json.load(f)
    
    # Check current status
    pending_trades = results.get('pending_trades', [])
    active_positions = results.get('active_positions', {})
    
    print('[CURRENT STATUS]')
    print(f'  - Pending Trades: {len(pending_trades)}')
    print(f'  - Active Positions: {len(active_positions)}')
    print(f'  - Max Positions: 5')
    print(f'  - Available Slots: {5 - len(active_positions)}')
    
    # Check strategy candidates
    print('\n[STRATEGY CANDIDATES] Potential entry symbols:')
    
    try:
        from core.strategy_registry import StrategyRegistry
        from core.market_data_service import MarketDataService
        
        sr = StrategyRegistry()
        
        # Get market data for price info
        market_data = results.get('market_data', {})
        
        # Check each strategy
        strategies = ['ma_trend_follow', 'ema_crossover']
        
        for strategy_name in strategies:
            print(f'\n  {strategy_name.upper()} Strategy:')
            
            # Get strategy profile
            strategy_config = sr.get_strategy_profile(strategy_name)
            if not strategy_config:
                print(f'    - Strategy config not found')
                continue
            
            # Get symbol selection config
            symbol_selection = strategy_config.get('symbol_selection', {})
            candidate_limit = symbol_selection.get('candidate_limit', 0)
            symbol_mode = symbol_selection.get('symbol_mode', 'unknown')
            
            print(f'    - Symbol Mode: {symbol_mode}')
            print(f'    - Candidate Limit: {candidate_limit}')
            
            # Get candidate symbols
            available_symbols = list(market_data.keys())
            candidate_symbols = sr.select_preferred_symbols(strategy_name, available_symbols, 10)
            
            print(f'    - Selected Candidates: {len(candidate_symbols)}')
            
            # Filter out already active/pending symbols
            available_for_entry = []
            for symbol in candidate_symbols:
                if symbol not in active_positions and symbol not in [t.get('symbol') for t in pending_trades]:
                    available_for_entry.append(symbol)
            
            print(f'    - Available for Entry: {len(available_for_entry)}')
            
            # Show top candidates
            for i, symbol in enumerate(available_for_entry[:3], 1):
                current_price = market_data.get(symbol, 'N/A')
                print(f'      {i}. {symbol}: {current_price} USDT')
            
            if len(available_for_entry) > 3:
                print(f'      ... and {len(available_for_entry) - 3} more')
        
        # Check overall potential
        print('\n[OVERALL POTENTIAL] Summary:')
        
        all_candidates = []
        for strategy_name in strategies:
            strategy_config = sr.get_strategy_profile(strategy_name)
            if strategy_config:
                symbol_selection = strategy_config.get('symbol_selection', {})
                candidate_limit = symbol_selection.get('candidate_limit', 0)
                all_candidates.append(candidate_limit)
        
        total_candidate_slots = sum(all_candidates)
        available_slots = 5 - len(active_positions)
        
        print(f'  - Total Candidate Slots: {total_candidate_slots}')
        print(f'  - Available Position Slots: {available_slots}')
        print(f'  - Can Accept New Entries: {available_slots > 0}')
        
        # Check if system is ready for new entries
        if available_slots > 0:
            print(f'  - Status: READY FOR NEW ENTRIES')
            print(f'  - Next cycle should generate new entry signals')
        else:
            print(f'  - Status: AT CAPACITY')
            print(f'  - No new entries until positions close')
        
        # Check last cycle results
        last_cycle = results.get('last_cycle', {})
        if last_cycle:
            signals_generated = last_cycle.get('signals_generated', 0)
            trades_executed = last_cycle.get('trades_executed', 0)
            
            print(f'\n[LAST CYCLE] Results:')
            print(f'  - Signals Generated: {signals_generated}')
            print(f'  - Trades Executed: {trades_executed}')
            
            if signals_generated > 0 and trades_executed == 0:
                print(f'  - Status: SIGNALS GENERATED BUT NO TRADES')
                print(f'  - Possible: Entry conditions not met or duplicates prevented')
            elif signals_generated > 0 and trades_executed > 0:
                print(f'  - Status: TRADES EXECUTED SUCCESSFULLY')
            else:
                print(f'  - Status: NO SIGNALS GENERATED')
        
    except Exception as e:
        print(f'  - Error checking candidates: {e}')
    
    # Check market conditions
    print(f'\n[MARKET CONDITIONS] Current market data:')
    
    market_data = results.get('market_data', {})
    if market_data:
        # Show some key symbols
        key_symbols = ['BTCUSDT', 'ETHUSDT', 'DOGEUSDT', 'XRPUSDT', 'BNBUSDT']
        
        print(f'  - Key Symbols:')
        for symbol in key_symbols:
            if symbol in market_data:
                price = market_data[symbol]
                status = 'ACTIVE' if symbol in active_positions else 'AVAILABLE'
                print(f'    {symbol}: {price} USDT ({status})')
        
        # Show price ranges
        prices = [float(p) for p in market_data.values() if p and str(p).replace('.', '').isdigit()]
        if prices:
            max_price = max(prices)
            min_price = min(prices)
            print(f'  - Price Range: {min_price:.6f} - {max_price:.2f} USDT')
    
    print('=' * 60)
    print('[RESULT] Potential entry symbols check complete')
    print('=' * 60)

if __name__ == "__main__":
    check_potential_entries()
