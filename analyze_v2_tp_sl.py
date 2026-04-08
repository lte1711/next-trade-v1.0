#!/usr/bin/env python3
"""
Analyze V2 Merged TP/SL - Detailed analysis of V2 Merged take profit and stop loss
"""

import json

def analyze_v2_tp_sl():
    """Analyze V2 Merged take profit and stop loss configurations"""
    print('=' * 60)
    print('V2 MERGED TP/SL ANALYSIS')
    print('=' * 60)
    
    # Load strategy registry
    from core.strategy_registry import StrategyRegistry
    sr = StrategyRegistry()
    
    # Get strategy profiles
    strategies = ['ma_trend_follow', 'ema_crossover']
    
    for strategy_name in strategies:
        print(f'\n[{strategy_name.upper()}] V2 Merged TP/SL Configuration:')
        
        strategy_config = sr.get_strategy_profile(strategy_name)
        if not strategy_config:
            print('  - Strategy config not found')
            continue
        
        risk_config = strategy_config.get('risk_config', {})
        
        if not risk_config:
            print('  - Risk config not found')
            continue
        
        # Basic TP/SL
        stop_loss_pct = risk_config.get('stop_loss_pct')
        take_profit_pct = risk_config.get('take_profit_pct')
        
        print(f'  - Basic Stop Loss: {stop_loss_pct:.2%}' if stop_loss_pct else '  - Basic Stop Loss: NOT SET')
        print(f'  - Basic Take Profit: {take_profit_pct:.2%}' if take_profit_pct else '  - Basic Take Profit: NOT SET')
        
        # Partial take profit settings
        partial_tp1_pct = risk_config.get('partial_tp1_pct')
        partial_tp2_pct = risk_config.get('partial_tp2_pct')
        fast_tp1_pct = risk_config.get('fast_tp1_pct')
        fast_tp2_pct = risk_config.get('fast_tp2_pct')
        fast_tight_stop_loss_pct = risk_config.get('fast_tight_stop_loss_pct')
        fast_tp1_close_ratio = risk_config.get('fast_tp1_close_ratio')
        
        print(f'\n  - Partial TP1: {partial_tp1_pct:.2%}' if partial_tp1_pct else '  - Partial TP1: NOT SET')
        print(f'  - Partial TP2: {partial_tp2_pct:.2%}' if partial_tp2_pct else '  - Partial TP2: NOT SET')
        print(f'  - Fast TP1: {fast_tp1_pct:.2%}' if fast_tp1_pct else '  - Fast TP1: NOT SET')
        print(f'  - Fast TP2: {fast_tp2_pct:.2%}' if fast_tp2_pct else '  - Fast TP2: NOT SET')
        print(f'  - Fast Tight Stop Loss: {fast_tight_stop_loss_pct:.2%}' if fast_tight_stop_loss_pct else '  - Fast Tight Stop Loss: NOT SET')
        print(f'  - Fast TP1 Close Ratio: {fast_tp1_close_ratio:.2%}' if fast_tp1_close_ratio else '  - Fast TP1 Close Ratio: NOT SET')
        
        # Session multipliers
        session_multipliers = risk_config.get('session_multipliers', {})
        if session_multipliers:
            print(f'\n  - Session Multipliers:')
            for session, multipliers in session_multipliers.items():
                stop_mult = multipliers.get('stop', 1.0)
                take_mult = multipliers.get('take', 1.0)
                print(f'    {session}: Stop x{stop_mult}, Take x{take_mult}')
                
                # Calculate adjusted TP/SL for this session
                if stop_loss_pct:
                    adjusted_stop = stop_loss_pct * stop_mult
                    print(f'      Adjusted Stop Loss: {adjusted_stop:.2%}')
                
                if take_profit_pct:
                    adjusted_take = take_profit_pct * take_mult
                    print(f'      Adjusted Take Profit: {adjusted_take:.2%}')
        
        # Risk per trade
        risk_per_trade = risk_config.get('risk_per_trade')
        if risk_per_trade:
            print(f'  - Risk Per Trade: {risk_per_trade:.2%}')
        
        # Max position size
        max_position_size = risk_config.get('max_position_size_usdt')
        if max_position_size:
            print(f'  - Max Position Size: {max_position_size} USDT')
        
        # Leverage
        leverage = risk_config.get('leverage')
        if leverage:
            print(f'  - Leverage: {leverage}x')
    
    # Check actual implementation
    print(f'\n[IMPLEMENTATION] How TP/SL is applied:')
    
    # Load trading results to see actual values
    with open('trading_results.json', 'r') as f:
        results = json.load(f)
    
    active_positions = results.get('active_positions', {})
    
    for symbol, position in active_positions.items():
        strategy = position.get('strategy')
        stop_loss_pct = position.get('stop_loss_pct')
        take_profit_pct = position.get('take_profit_pct')
        
        print(f'\n  {symbol}:')
        print(f'    - Strategy: {strategy}')
        print(f'    - Applied Stop Loss: {stop_loss_pct:.2%}' if stop_loss_pct else '    - Applied Stop Loss: NOT SET')
        print(f'    - Applied Take Profit: {take_profit_pct:.2%}' if take_profit_pct else '    - Applied Take Profit: NOT SET')
        
        # Check if values match strategy defaults
        if strategy and strategy in strategies:
            strategy_config = sr.get_strategy_profile(strategy)
            if strategy_config:
                risk_config = strategy_config.get('risk_config', {})
                
                default_stop = risk_config.get('stop_loss_pct')
                default_take = risk_config.get('take_profit_pct')
                
                print(f'    - Default Stop Loss: {default_stop:.2%}' if default_stop else '    - Default Stop Loss: NOT SET')
                print(f'    - Default Take Profit: {default_take:.2%}' if default_take else '    - Default Take Profit: NOT SET')
                
                # Check if applied values match defaults
                if stop_loss_pct and default_stop:
                    if abs(stop_loss_pct - default_stop) < 0.0001:
                        print(f'    - Stop Loss: MATCHES DEFAULT')
                    else:
                        print(f'    - Stop Loss: DIFFERENT FROM DEFAULT')
                
                if take_profit_pct and default_take:
                    if abs(take_profit_pct - default_take) < 0.0001:
                        print(f'    - Take Profit: MATCHES DEFAULT')
                    else:
                        print(f'    - Take Profit: DIFFERENT FROM DEFAULT')
    
    print(f'\n[ISSUES] Identified problems:')
    
    # Check for missing TP/SL
    missing_tp_sl = []
    for symbol, position in active_positions.items():
        stop_loss_pct = position.get('stop_loss_pct')
        take_profit_pct = position.get('take_profit_pct')
        
        if stop_loss_pct is None or take_profit_pct is None:
            missing_tp_sl.append(symbol)
    
    if missing_tp_sl:
        print(f'  - Positions without TP/SL: {missing_tp_sl}')
    else:
        print(f'  - All positions have TP/SL set')
    
    # Check for old positions without strategy
    old_positions = []
    for symbol, position in active_positions.items():
        strategy = position.get('strategy')
        if strategy is None:
            old_positions.append(symbol)
    
    if old_positions:
        print(f'  - Old positions without strategy: {old_positions}')
    else:
        print(f'  - All positions have strategy assigned')
    
    print('=' * 60)
    print('[RESULT] V2 Merged TP/SL analysis complete')
    print('=' * 60)

if __name__ == "__main__":
    analyze_v2_tp_sl()
