#!/usr/bin/env python3
"""
Moving Average Trading Analysis - Check if program uses moving averages for trading
"""

import json
import os
from datetime import datetime

def analyze_moving_average_usage():
    """Analyze moving average usage in trading logic"""
    print('=' * 80)
    print('MOVING AVERAGE TRADING ANALYSIS')
    print('=' * 80)
    
    print(f'Analysis Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 80)
    
    # 1. Check strategy configuration
    print('\n[1] STRATEGY CONFIGURATION ANALYSIS')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        strategies = trading_results.get('strategies', {})
        
        print(f'  - Active Strategies: {len(strategies)}')
        
        for strategy_name, strategy_config in strategies.items():
            enabled = strategy_config.get('enabled', False)
            name = strategy_config.get('name', 'Unknown')
            
            print(f'\n  Strategy: {strategy_name}')
            print(f'    - Name: {name}')
            print(f'    - Enabled: {enabled}')
            
            if 'ma' in strategy_name.lower() or 'ema' in strategy_name.lower():
                print(f'    - Moving Average Strategy: YES')
                
                if 'ma_trend_follow' in strategy_name:
                    print(f'    - Type: MA Trend Following')
                    print(f'    - Description: Uses moving averages for trend following')
                elif 'ema_crossover' in strategy_name:
                    print(f'    - Type: EMA Crossover')
                    print(f'    - Description: Uses exponential moving average crossovers')
            else:
                print(f'    - Moving Average Strategy: NO')
    
    except Exception as e:
        print(f'  - Error reading trading results: {e}')
    
    # 2. Check current trading results for MA usage
    print('\n[2] CURRENT TRADING ACTIVITY ANALYSIS')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        active_positions = trading_results.get('active_positions', {})
        closed_trades = trading_results.get('closed_trades', [])
        
        print(f'  - Active Positions: {len(active_positions)}')
        print(f'  - Closed Trades: {len(closed_trades)}')
        
        # Check if positions were opened using MA strategies
        ma_positions = 0
        ema_positions = 0
        
        for symbol, position in active_positions.items():
            strategy = position.get('strategy', 'Unknown')
            if 'ma' in strategy.lower():
                ma_positions += 1
                print(f'    - {symbol}: Using MA strategy ({strategy})')
            elif 'ema' in strategy.lower():
                ema_positions += 1
                print(f'    - {symbol}: Using EMA strategy ({strategy})')
        
        print(f'  - MA Strategy Positions: {ma_positions}')
        print(f'  - EMA Strategy Positions: {ema_positions}')
        print(f'  - Total MA-based Positions: {ma_positions + ema_positions}')
        
    except Exception as e:
        print(f'  - Error analyzing positions: {e}')
    
    # 3. Check signal engine configuration
    print('\n[3] SIGNAL ENGINE ANALYSIS')
    
    # Read signal engine file
    try:
        with open('core/signal_engine.py', 'r') as f:
            signal_engine_content = f.read()
        
        # Check for MA-related code
        ma_indicators = ['sma_10', 'ema_12', 'ema_26', 'ema_21', 'moving_average', 'calculate_ema', 'calculate_sma']
        ma_usage_count = 0
        
        for indicator in ma_indicators:
            if indicator in signal_engine_content:
                ma_usage_count += 1
                print(f'    - Found: {indicator}')
        
        print(f'  - MA Indicators Found: {ma_usage_count}/{len(ma_indicators)}')
        
        # Check for MA-based signal logic
        if 'price_vs_sma' in signal_engine_content:
            print(f'    - MA Signal Logic: YES (price_vs_sma)')
        else:
            print(f'    - MA Signal Logic: NO')
        
        if 'above SMA' in signal_engine_content or 'below SMA' in signal_engine_content:
            print(f'    - MA Trading Signals: YES')
        else:
            print(f'    - MA Trading Signals: NO')
    
    except Exception as e:
        print(f'  - Error reading signal engine: {e}')
    
    # 4. Check trade orchestrator for MA usage
    print('\n[4] TRADE ORCHESTRATOR ANALYSIS')
    
    try:
        with open('core/trade_orchestrator.py', 'r') as f:
            orchestrator_content = f.read()
        
        # Check for MA calculations
        ma_calculations = ['calculate_ema', 'calculate_sma', 'ema_12', 'ema_26', 'ema_21', 'sma_10']
        ma_calc_count = 0
        
        for calc in ma_calculations:
            if calc in orchestrator_content:
                ma_calc_count += 1
                print(f'    - Found: {calc}')
        
        print(f'  - MA Calculations Found: {ma_calc_count}/{len(ma_calculations)}')
        
        # Check for MA-based filtering
        if 'price_vs_sma_pct' in orchestrator_content:
            print(f'    - MA Price Analysis: YES')
        else:
            print(f'    - MA Price Analysis: NO')
        
        if 'flat_price_vs_sma' in orchestrator_content:
            print(f'    - MA Filtering Logic: YES')
        else:
            print(f'    - MA Filtering Logic: NO')
    
    except Exception as e:
        print(f'  - Error reading trade orchestrator: {e}')
    
    # 5. Check indicator service
    print('\n[5] INDICATOR SERVICE ANALYSIS')
    
    try:
        with open('core/indicator_service.py', 'r') as f:
            indicator_content = f.read()
        
        # Check for MA calculation methods
        ma_methods = ['calculate_sma', 'calculate_ema']
        ma_method_count = 0
        
        for method in ma_methods:
            if method in indicator_content:
                ma_method_count += 1
                print(f'    - Found: {method}')
        
        print(f'  - MA Calculation Methods: {ma_method_count}/{len(ma_methods)}')
        
        # Check for MA implementation
        if 'Simple Moving Average' in indicator_content:
            print(f'    - SMA Implementation: YES')
        else:
            print(f'    - SMA Implementation: NO')
        
        if 'Exponential Moving Average' in indicator_content:
            print(f'    - EMA Implementation: YES')
        else:
            print(f'    - EMA Implementation: NO')
    
    except Exception as e:
        print(f'  - Error reading indicator service: {e}')
    
    # 6. Check recent trading activity for MA signals
    print('\n[6] RECENT TRADING SIGNALS ANALYSIS')
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        # Check last cycle results
        last_cycle = trading_results.get('last_cycle', {})
        signals_generated = last_cycle.get('signals_generated', 0)
        
        print(f'  - Last Cycle Signals: {signals_generated}')
        
        # Check for MA-based signals in recent activity
        market_data = trading_results.get('market_data', {})
        
        if 'sma_10' in str(market_data):
            print(f'    - SMA Data in Market Data: YES')
        else:
            print(f'    - SMA Data in Market Data: NO')
        
        if 'ema_data' in str(market_data):
            print(f'    - EMA Data in Market Data: YES')
        else:
            print(f'    - EMA Data in Market Data: NO')
    
    except Exception as e:
        print(f'  - Error analyzing recent signals: {e}')
    
    # 7. Summary analysis
    print('\n[7] MOVING AVERAGE USAGE SUMMARY')
    
    ma_strategies = ['ma_trend_follow', 'ema_crossover']
    ma_active = False
    
    try:
        with open('trading_results.json', 'r') as f:
            trading_results = json.load(f)
        
        strategies = trading_results.get('strategies', {})
        
        for strategy_name in ma_strategies:
            if strategy_name in strategies:
                enabled = strategies[strategy_name].get('enabled', False)
                if enabled:
                    ma_active = True
                    print(f'    - {strategy_name}: ACTIVE')
                else:
                    print(f'    - {strategy_name}: INACTIVE')
    except:
        pass
    
    # Final conclusion
    print(f'\n[8] FINAL CONCLUSION')
    
    if ma_active:
        print(f'  - Moving Average Trading: YES')
        print(f'  - Status: ACTIVE')
        print(f'  - Strategies: {", ".join(ma_strategies)}')
        print(f'  - Implementation: MA-based signal generation and filtering')
    else:
        print(f'  - Moving Average Trading: NO')
        print(f'  - Status: INACTIVE')
        print(f'  - Reason: MA strategies not enabled or not configured')
    
    print('\n' + '=' * 80)
    print('MOVING AVERAGE TRADING ANALYSIS COMPLETE')
    print('=' * 80)

if __name__ == "__main__":
    analyze_moving_average_usage()
