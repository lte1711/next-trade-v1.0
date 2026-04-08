#!/usr/bin/env python3
"""
Analyze Symbol Ranking - Analyze how symbols are ranked for entry
"""

import json

def analyze_symbol_ranking():
    """Analyze how symbols are ranked for entry"""
    print('=' * 60)
    print('SYMBOL RANKING ANALYSIS')
    print('=' * 60)
    
    # Load strategy registry
    from core.strategy_registry import StrategyRegistry
    from core.market_data_service import MarketDataService
    
    sr = StrategyRegistry()
    
    print('[STRATEGY CONFIGURATIONS] Symbol selection modes:')
    
    # Check each strategy
    strategies = ['ma_trend_follow', 'ema_crossover']
    
    for strategy_name in strategies:
        print(f'\n  {strategy_name.upper()} Strategy:')
        
        strategy_config = sr.get_strategy_profile(strategy_name)
        if not strategy_config:
            print(f'    - Strategy config not found')
            continue
        
        # Get symbol selection config
        symbol_selection = strategy_config.get('symbol_selection', {})
        candidate_limit = symbol_selection.get('candidate_limit', 0)
        symbol_mode = symbol_selection.get('symbol_mode', 'unknown')
        market_bias = symbol_selection.get('market_bias', 'unknown')
        
        print(f'    - Symbol Mode: {symbol_mode}')
        print(f'    - Candidate Limit: {candidate_limit}')
        print(f'    - Market Bias: {market_bias}')
        
        # Explain the ranking method
        print(f'    - Ranking Method:')
        if symbol_mode == 'leaders':
            print(f'      - Select top symbols by trading volume/liquidity')
            print(f'      - Priority: High volume symbols first')
            print(f'      - Example: BTCUSDT, ETHUSDT, BNBUSDT')
        elif symbol_mode == 'volatile':
            print(f'      - Select symbols with high volatility')
            print(f'      - Priority: Volatile symbols (every other from top)')
            print(f'      - Example: Symbols with high price movement')
        elif symbol_mode == 'pullback':
            print(f'      - Select symbols from middle range')
            print(f'      - Priority: Symbols not in top or bottom')
            print(f'      - Example: Symbols 3-8 in ranking')
        elif symbol_mode == 'balanced':
            print(f'      - Select mix of top and bottom symbols')
            print(f'      - Priority: Balanced risk distribution')
            print(f'      - Example: Top 50% + Bottom 50%')
        else:
            print(f'      - Unknown ranking method')
    
    # Show actual ranking implementation
    print(f'\n[RANKING IMPLEMENTATION] How ranking works:')
    
    # Load market data to see actual ranking
    with open('trading_results.json', 'r') as f:
        results = json.load(f)
    
    market_data = results.get('market_data', {})
    
    print(f'  - Market Data Source: {len(market_data)} symbols')
    
    # Show how symbols are ranked by volume/liquidity
    print(f'  - Ranking Criteria:')
    print(f'    1. Trading Volume (24h)')
    print(f'    2. Price Volatility')
    print(f'    3. Market Cap (implied by price)')
    print(f'    4. Availability (USDT paired)')
    
    # Show actual ranking
    print(f'\n[ACTUAL RANKING] Current market ranking:')
    
    # Sort symbols by price (as a proxy for market cap)
    sorted_by_price = sorted(market_data.items(), key=lambda x: float(x[1]), reverse=True)
    
    print(f'  - Top 10 by Price (Market Cap Proxy):')
    for i, (symbol, price) in enumerate(sorted_by_price[:10], 1):
        try:
            price_float = float(price)
            volume = 0  # Would need API call for real volume
            print(f'    {i:2d}. {symbol:<10} {price_float:>12.2f} USDT')
        except:
            print(f'    {i:2d}. {symbol:<10} {price:>12} USDT')
    
    # Show how each strategy selects from this ranking
    print(f'\n[STRATEGY SELECTION] How each strategy selects:')
    
    # Get available symbols
    available_symbols = list(market_data.keys())
    
    for strategy_name in strategies:
        print(f'\n  {strategy_name.upper()} Selection Process:')
        
        strategy_config = sr.get_strategy_profile(strategy_name)
        symbol_selection = strategy_config.get('symbol_selection', {})
        symbol_mode = symbol_selection.get('symbol_mode', 'unknown')
        candidate_limit = symbol_selection.get('candidate_limit', 0)
        
        # Get selected symbols
        selected_symbols = sr.select_preferred_symbols(strategy_name, available_symbols, 10)
        
        print(f'    - Mode: {symbol_mode}')
        print(f'    - Limit: {candidate_limit}')
        print(f'    - Selected: {len(selected_symbols)} symbols')
        
        # Show where selected symbols appear in ranking
        print(f'    - Ranking Positions:')
        for i, symbol in enumerate(selected_symbols[:5], 1):
            # Find position in overall ranking
            for j, (ranked_symbol, _) in enumerate(sorted_by_price, 1):
                if ranked_symbol == symbol:
                    print(f'      {i}. {symbol}: Position {j} in overall ranking')
                    break
        
        # Show selection logic
        print(f'    - Selection Logic:')
        if symbol_mode == 'leaders':
            print(f'      - Takes top {candidate_limit} from ranking')
            print(f'      - Most liquid/established symbols')
        elif symbol_mode == 'volatile':
            print(f'      - Takes every 2nd symbol from top {candidate_limit * 2}')
            print(f'      - Focus on volatile but still liquid symbols')
        elif symbol_mode == 'pullback':
            print(f'      - Takes symbols from middle range')
            print(f'      - Avoids overbought/oversold extremes')
        elif symbol_mode == 'balanced':
            print(f'      - Takes mix of top and bottom')
            print(f'      - Diversified risk approach')
    
    # Check market bias
    print(f'\n[MARKET BIAS] Adaptive bias system:')
    
    print(f'  - Current Bias: adaptive')
    print(f'  - Bias Factors:')
    print(f'    1. Market Regime (TRENDING/RANGING/BEAR_TREND)')
    print(f'    2. Volatility Levels')
    print(f'    3. Session Timing (US/EU/ASIA)')
    print(f'    4. Correlation Analysis')
    
    # Show current market regime
    regime_distribution = results.get('regime_distribution', {})
    if regime_distribution:
        print(f'  - Current Market Regime Distribution:')
        for regime, count in regime_distribution.items():
            print(f'    {regime}: {count} symbols')
    
    # Priority factors
    print(f'\n[PRIORITY FACTORS] What determines final priority:')
    print(f'  1. Strategy Mode (leaders/volatile/pullback/balanced)')
    print(f'  2. Market Ranking (volume/price/volatility)')
    print(f'  3. Current Positions (avoid duplicates)')
    print(f'  4. Signal Strength (confidence threshold)')
    print(f'  5. Risk Parameters (position size, leverage)')
    print(f'  6. Market Conditions (regime, session)')
    
    # Show actual priority for next entry
    print(f'\n[NEXT ENTRY PRIORITY] Most likely candidates:')
    
    # Get symbols not in current positions
    active_positions = results.get('active_positions', {})
    available_for_entry = [s for s in available_symbols if s not in active_positions]
    
    # Re-rank available symbols
    if available_for_entry:
        # Sort by price again for available symbols
        available_ranked = sorted(available_for_entry, key=lambda x: float(market_data.get(x, 0)), reverse=True)
        
        print(f'  - Top 5 Available Symbols:')
        for i, symbol in enumerate(available_ranked[:5], 1):
            price = market_data.get(symbol, 'N/A')
            # Check which strategies would select this
            strategies_would_select = []
            for strategy_name in strategies:
                selected = sr.select_preferred_symbols(strategy_name, available_for_entry, 10)
                if symbol in selected:
                    strategies_would_select.append(strategy_name)
            
            print(f'    {i}. {symbol:<10} {price:>12} USDT ({", ".join(strategies_would_select)})')
    
    print('=' * 60)
    print('[RESULT] Symbol ranking analysis complete')
    print('=' * 60)

if __name__ == "__main__":
    analyze_symbol_ranking()
