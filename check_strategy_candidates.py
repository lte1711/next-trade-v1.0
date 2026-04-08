#!/usr/bin/env python3
"""
Check Strategy Candidates - Check actual candidate symbols for each strategy
"""

import json

def check_strategy_candidates():
    """Check actual candidate symbols for each strategy"""
    print('=' * 60)
    print('STRATEGY CANDIDATES ANALYSIS')
    print('=' * 60)
    
    # Load strategy registry
    from core.strategy_registry import StrategyRegistry
    sr = StrategyRegistry()
    
    # Load market data service
    from core.market_data_service import MarketDataService
    mds = MarketDataService('https://demo-fapi.binance.com')
    
    # Get available symbols
    symbols = mds.get_available_symbols()
    
    # Convert like trade_orchestrator does
    symbol_list = []
    for symbol_data in symbols:
        if isinstance(symbol_data, dict):
            symbol_list.append(symbol_data.get('symbol', ''))
        elif isinstance(symbol_data, str):
            symbol_list.append(symbol_data)
        else:
            symbol_list.append(str(symbol_data))
    
    print(f'[SYMBOLS] Total available: {len(symbol_list)}')
    
    # Check each strategy
    strategies = ['ma_trend_follow', 'ema_crossover']
    
    for strategy_name in strategies:
        print(f'\n[{strategy_name.upper()}] Candidate symbols:')
        
        # Get strategy profile
        strategy_config = sr.get_strategy_profile(strategy_name)
        if not strategy_config:
            print(f'  - Strategy config not found')
            continue
        
        # Get symbol selection configuration
        symbol_selection = strategy_config.get('symbol_selection', {})
        if symbol_selection:
            symbol_mode = symbol_selection.get('symbol_mode', 'unknown')
            candidate_limit = symbol_selection.get('candidate_limit', 0)
            market_bias = symbol_selection.get('market_bias', 'unknown')
            
            print(f'  - Symbol Mode: {symbol_mode}')
            print(f'  - Candidate Limit: {candidate_limit}')
            print(f'  - Market Bias: {market_bias}')
            
            # Get actual candidate symbols
            candidate_symbols = sr.select_preferred_symbols(strategy_name, symbol_list, 10)
            
            print(f'  - Selected Candidates ({len(candidate_symbols)}):')
            for i, symbol in enumerate(candidate_symbols, 1):
                # Get current price from market data
                with open('trading_results.json', 'r') as f:
                    results = json.load(f)
                market_data = results.get('market_data', {})
                price = market_data.get(symbol, 'N/A')
                
                print(f'    {i}. {symbol}: {price} USDT')
        else:
            print(f'  - Symbol selection not configured')
    
    # Check current active positions
    with open('trading_results.json', 'r') as f:
        results = json.load(f)
    
    active_positions = results.get('active_positions', {})
    
    print(f'\n[ACTIVE POSITIONS] Current positions: {len(active_positions)}')
    for symbol, position in active_positions.items():
        strategy = position.get('strategy', 'None')
        side = position.get('side', 'UNKNOWN')
        amount = position.get('amount', 0)
        entry_price = position.get('entry_price', 0)
        
        print(f'  - {symbol}: {amount} ({side}) | Strategy: {strategy} | Entry: {entry_price}')
    
    # Check pending trades
    pending_trades = results.get('pending_trades', [])
    
    print(f'\n[PENDING TRADES] Currently waiting: {len(pending_trades)}')
    for i, trade in enumerate(pending_trades, 1):
        symbol = trade.get('symbol', 'Unknown')
        strategy = trade.get('strategy', 'Unknown')
        side = trade.get('side', 'Unknown')
        quantity = trade.get('quantity', 0)
        status = trade.get('status', 'Unknown')
        
        print(f'  {i}. {symbol}: {quantity} ({side}) | Strategy: {strategy} | Status: {status}')
    
    # Calculate total candidates
    print(f'\n[CANDIDATE SUMMARY] Total potential entries:')
    
    total_candidates = 0
    for strategy_name in strategies:
        strategy_config = sr.get_strategy_profile(strategy_name)
        if strategy_config:
            symbol_selection = strategy_config.get('symbol_selection', {})
            candidate_limit = symbol_selection.get('candidate_limit', 0)
            total_candidates += candidate_limit
    
    print(f'  - Total Candidate Slots: {total_candidates}')
    print(f'  - Current Active Positions: {len(active_positions)}')
    print(f'  - Current Pending Trades: {len(pending_trades)}')
    print(f'  - Available Slots: {5 - len(active_positions)}')
    print(f'  - Can Accept New Entries: {len(active_positions) < 5}')
    
    # Check if any candidates are already in positions
    print(f'\n[CANDIDATE OVERLAP] Check for duplicates:')
    
    all_candidates = []
    for strategy_name in strategies:
        candidate_symbols = sr.select_preferred_symbols(strategy_name, symbol_list, 10)
        all_candidates.extend(candidate_symbols)
    
    # Remove duplicates
    unique_candidates = list(set(all_candidates))
    
    print(f'  - Total Candidates (with duplicates): {len(all_candidates)}')
    print(f'  - Unique Candidates: {len(unique_candidates)}')
    
    # Check overlap with active positions
    active_symbols = list(active_positions.keys())
    overlap = set(unique_candidates) & set(active_symbols)
    
    if overlap:
        print(f'  - Candidates already in positions: {list(overlap)}')
    else:
        print(f'  - No candidates overlap with active positions')
    
    # Check overlap with pending trades
    pending_symbols = [trade.get('symbol') for trade in pending_trades]
    pending_overlap = set(unique_candidates) & set(pending_symbols)
    
    if pending_overlap:
        print(f'  - Candidates already pending: {list(pending_overlap)}')
    else:
        print(f'  - No candidates overlap with pending trades')
    
    print('=' * 60)
    print('[RESULT] Strategy candidates analysis complete')
    print('=' * 60)

if __name__ == "__main__":
    check_strategy_candidates()
