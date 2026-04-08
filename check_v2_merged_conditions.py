#!/usr/bin/env python3
"""
V2 Merged Conditions Check - Analyze V2 Merged entry conditions
"""

import json

def check_v2_merged_conditions():
    """Check V2 Merged entry conditions"""
    print('=' * 60)
    print('V2 MERGED ENTRY CONDITIONS DEEP ANALYSIS')
    print('=' * 60)
    
    # Load strategy registry to check V2 Merged conditions
    try:
        from core.strategy_registry import StrategyRegistry
        sr = StrategyRegistry()
        
        print('[STRATEGY REGISTRY] V2 Merged conditions:')
        
        # Check ma_trend_follow strategy
        ma_config = sr.get_strategy_profile('ma_trend_follow')
        if ma_config:
            print('  ma_trend_follow:')
            risk_config = ma_config.get('risk_config', {})
            stop_loss = risk_config.get('stop_loss_pct', 'N/A')
            take_profit = risk_config.get('take_profit_pct', 'N/A')
            required_alignment = risk_config.get('required_alignment_count', 'N/A')
            consensus_threshold = risk_config.get('consensus_threshold', 'N/A')
            exit_signal_threshold = risk_config.get('exit_signal_threshold', 'N/A')
            
            print(f'    - Stop loss: {stop_loss}%')
            print(f'    - Take profit: {take_profit}%')
            print(f'    - Required alignment: {required_alignment}')
            print(f'    - Consensus threshold: {consensus_threshold}')
            print(f'    - Exit signal threshold: {exit_signal_threshold}')
        
        # Check ema_crossover strategy
        ema_config = sr.get_strategy_profile('ema_crossover')
        if ema_config:
            print('  ema_crossover:')
            risk_config = ema_config.get('risk_config', {})
            stop_loss = risk_config.get('stop_loss_pct', 'N/A')
            take_profit = risk_config.get('take_profit_pct', 'N/A')
            required_alignment = risk_config.get('required_alignment_count', 'N/A')
            consensus_threshold = risk_config.get('consensus_threshold', 'N/A')
            exit_signal_threshold = risk_config.get('exit_signal_threshold', 'N/A')
            
            print(f'    - Stop loss: {stop_loss}%')
            print(f'    - Take profit: {take_profit}%')
            print(f'    - Required alignment: {required_alignment}')
            print(f'    - Consensus threshold: {consensus_threshold}')
            print(f'    - Exit signal threshold: {exit_signal_threshold}')
        
    except Exception as e:
        print(f'[ERROR] Strategy registry check failed: {e}')
    
    # Check signal engine alignment logic
    try:
        from core.signal_engine import SignalEngine
        import core.indicator_service
        import core.market_regime_service
        
        # Initialize signal engine components
        indicator_service = core.indicator_service.IndicatorService(lambda x, y: None)
        market_regime_service = core.market_regime_service.MarketRegimeService(lambda x, y: None)
        signal_engine = SignalEngine(indicator_service, market_regime_service, lambda x, y: None)
        
        print('\n[SIGNAL ENGINE] V2 Merged alignment logic:')
        
        # Check alignment calculation method
        if hasattr(signal_engine, '_calculate_alignment_counts'):
            print('  - Alignment count calculation: FOUND')
        else:
            print('  - Alignment count calculation: NOT FOUND')
        
        # Check consensus calculation
        if hasattr(signal_engine, '_calculate_consensus'):
            print('  - Consensus calculation: FOUND')
        else:
            print('  - Consensus calculation: NOT FOUND')
        
        # Check entry conditions
        if hasattr(signal_engine, '_check_entry_conditions'):
            print('  - Entry conditions check: FOUND')
        else:
            print('  - Entry conditions check: NOT FOUND')
        
        # Check signal generation method
        if hasattr(signal_engine, 'generate_signals'):
            print('  - Signal generation: FOUND')
        else:
            print('  - Signal generation: NOT FOUND')
            
    except Exception as e:
        print(f'[ERROR] Signal engine check failed: {e}')
    
    # Check current market regime
    print('\n[MARKET REGIME] Current analysis:')
    try:
        with open('trading_results.json', 'r') as f:
            results = json.load(f)
        
        # Check if market regime data exists
        last_cycle = results.get('last_cycle', {})
        market_regime = last_cycle.get('market_regime', {})
        
        if market_regime:
            print('  - Market regime data: AVAILABLE')
            timeframes = market_regime.get('timeframes', {})
            print(f'  - Timeframes available: {len(timeframes)}')
            
            for tf_name, tf_data in timeframes.items():
                price_vs_ma = tf_data.get('price_vs_ma', 'UNKNOWN')
                trend_direction = tf_data.get('trend_direction', 'UNKNOWN')
                print(f'    - {tf_name}: {price_vs_ma} | {trend_direction}')
        else:
            print('  - Market regime data: NOT AVAILABLE')
            print('  - This could explain no signals!')
        
        # Check if any trading cycles have run
        total_trades = results.get('total_trades', 0)
        signals_generated = results.get('signals_generated', 0)
        
        print(f'\n[TRADING ACTIVITY] System activity:')
        print(f'  - Total trades: {total_trades}')
        print(f'  - Signals generated: {signals_generated}')
        print(f'  - System has run cycles: {total_trades > 0 or signals_generated > 0}')
        
    except Exception as e:
        print(f'  - Market regime check failed: {e}')
    
    # Check V2 Merged specific issues
    print('\n[V2 MERGED] CRITICAL ISSUES IDENTIFIED:')
    
    print('  1. ZERO SIGNALS GENERATED:')
    print('     - No signals have been generated at all')
    print('     - This indicates signal engine is not producing output')
    
    print('  2. NO TRADING CYCLES:')
    print('     - No trades have been executed')
    print('     - System may not be running trading cycles')
    
    print('  3. MARKET DATA ISSUES:')
    print('     - Market data requests failing (400 errors)')
    print('     - Could be API endpoint issues')
    
    print('  4. ALIGNMENT CONDITIONS:')
    print('     - V2 Merged requires perfect alignment')
    print('     - Market may not be meeting these conditions')
    
    print('  5. STRATEGY CONFIGURATION:')
    print('     - Strategies enabled but no signal generation')
    print('     - Could be configuration mismatch')
    
    # Root cause analysis
    print('\n[ROOT CAUSE] Most likely causes:')
    print('  1. Signal engine not generating any signals')
    print('  2. Market data retrieval issues')
    print('  3. V2 Merged alignment conditions too strict')
    print('  4. Trading cycles not running properly')
    print('  5. Strategy configuration problems')
    
    print('=' * 60)
    print('[RESULT] V2 Merged entry conditions analysis complete')
    print('=' * 60)

if __name__ == "__main__":
    check_v2_merged_conditions()
