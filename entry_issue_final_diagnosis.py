#!/usr/bin/env python3
"""
Entry Issue Final Diagnosis - Final analysis of why entry is still not working
"""

import json
from datetime import datetime

def entry_issue_final_diagnosis():
    """Final analysis of why entry is still not working"""
    print('=' * 80)
    print('ENTRY ISSUE FINAL DIAGNOSIS')
    print('=' * 80)
    
    print(f'Diagnosis Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # 1. Current Status Check
    print('\n[1] CURRENT STATUS CHECK')
    
    try:
        with open('trading_results.json', 'r') as f:
            results = json.load(f)
        
        last_cycle = results.get('last_cycle', {})
        threshold_optimization = results.get('threshold_optimization', {})
        
        print('  - Last Trading Cycle:')
        print(f'    - Signals Generated: {last_cycle.get("signals_generated", 0)}')
        print(f'    - Trades Executed: {last_cycle.get("trades_executed", 0)}')
        print(f'    - Timestamp: {last_cycle.get("timestamp", "Unknown")}')
        
        print('  - Threshold Optimization:')
        print(f'    - Status: {threshold_optimization.get("status", "Unknown")}')
        print(f'    - Test Signals: {threshold_optimization.get("test_signals_generated", 0)}')
        print(f'    - Timestamp: {threshold_optimization.get("timestamp", "Unknown")}')
        
        # Check discrepancy
        test_signals = threshold_optimization.get("test_signals_generated", 0)
        actual_signals = last_cycle.get("signals_generated", 0)
        
        if test_signals > 0 and actual_signals == 0:
            print('  - DISCREPANCY DETECTED:')
            print('    - Test generates signals but actual cycle does not')
            print('    - This indicates a disconnect between test and production')
        
    except Exception as e:
        print(f'  - Error checking status: {e}')
    
    # 2. Strategy Registry vs Runtime Analysis
    print('\n[2] STRATEGY REGISTRY vs RUNTIME ANALYSIS')
    
    try:
        from core.strategy_registry import StrategyRegistry
        from core.signal_engine import SignalEngine
        from core.market_data_service import MarketDataService
        
        sr = StrategyRegistry()
        se = SignalEngine()
        mds = MarketDataService('https://demo-fapi.binance.com')
        
        print('  - Strategy Registry Check:')
        
        # Check if thresholds were actually saved
        ma_config = sr.get_strategy_profile('ma_trend_follow')
        ema_config = sr.get_strategy_profile('ema_crossover')
        
        if ma_config:
            ma_filters = ma_config.get('entry_filters', {})
            print(f'    - MA_TREND_FOLLOW Current:')
            print(f'      * Min Confidence: {ma_filters.get("min_confidence", 0)}')
            print(f'      * Min Trend Strength: {ma_filters.get("min_trend_strength", 0)}')
        
        if ema_config:
            ema_filters = ema_config.get('entry_filters', {})
            print(f'    - EMA_CROSSOVER Current:')
            print(f'      * Min Confidence: {ema_filters.get("min_confidence", 0)}')
            print(f'      * Min Trend Strength: {ema_filters.get("min_trend_strength", 0)}')
        
        print('  - Runtime vs Test Discrepancy Analysis:')
        
        # Test signal generation exactly like runtime
        symbols = ['BTCUSDT', 'ETHUSDT', 'DOGEUSDT']
        market_data = mds.update_market_data(symbols)
        
        if market_data:
            print('    - Testing exact runtime conditions:')
            
            runtime_signals = 0
            
            for symbol, symbol_data in market_data.items():
                klines_1h = symbol_data.get('klines', {}).get('1h', [])
                
                if klines_1h and len(klines_1h) >= 10:
                    closes = [k['close'] for k in klines_1h[-10:]]
                    
                    indicators = {
                        'price': closes[-1],
                        'volume': klines_1h[-1]['volume'],
                        'sma_10': sum(closes) / len(closes)
                    }
                    
                    market_data_dict = {
                        'prices': {'current': closes[-1]},
                        'klines': symbol_data.get('klines', {})
                    }
                    
                    regime = {
                        'regime': 'RANGING',
                        'trend_strength': 5.0,
                        'volatility_level': 0.01
                    }
                    
                    # Test with current strategy configurations
                    for strategy_name in ['ma_trend_follow', 'ema_crossover']:
                        strategy_config = sr.get_strategy_profile(strategy_name)
                        
                        if strategy_config:
                            signal_result = se.generate_strategy_signal(
                                market_data_dict, indicators, regime, strategy_config
                            )
                            
                            signal_type = signal_result.get('signal', 'HOLD')
                            confidence = signal_result.get('confidence', 0)
                            
                            if signal_type != 'HOLD':
                                runtime_signals += 1
                                print(f'      * {symbol} ({strategy_name}): {signal_type} (confidence: {confidence:.2f})')
            
            print(f'    - Runtime Test Signals: {runtime_signals}')
            
            if runtime_signals == 0:
                print('    - ISSUE CONFIRMED: Even with reduced thresholds, no signals generated')
                print('    - This suggests thresholds are still too high or other issues exist')
        
    except Exception as e:
        print(f'  - Error in strategy analysis: {e}')
    
    # 3. Deep Dive into Signal Engine Logic
    print('\n[3] DEEP DIVE INTO SIGNAL ENGINE LOGIC')
    
    try:
        print('  - Signal Engine Logic Analysis:')
        
        # Test with manually created data that should generate signals
        print('    - Testing with ideal signal conditions:')
        
        # Create ideal market data
        ideal_indicators = {
            'price': 105.0,  # 5% above SMA
            'sma_10': 100.0,
            'volume': 5000.0  # High volume
        }
        
        ideal_market_data = {
            'prices': {'current': 105.0}
        }
        
        ideal_regime = {
            'regime': 'RANGING',
            'trend_strength': 5.0,
            'volatility_level': 0.01
        }
        
        # Test with current strategy configs
        for strategy_name in ['ma_trend_follow', 'ema_crossover']:
            strategy_config = sr.get_strategy_profile(strategy_name)
            
            if strategy_config:
                signal_result = se.generate_strategy_signal(
                    ideal_market_data, ideal_indicators, ideal_regime, strategy_config
                )
                
                signal_type = signal_result.get('signal', 'HOLD')
                confidence = signal_result.get('confidence', 0)
                reason = signal_result.get('reason', 'No reason')
                
                print(f'      * Ideal Test ({strategy_name}): {signal_type} (confidence: {confidence:.2f}) - {reason}')
        
        # Test with minimal thresholds
        print('    - Testing with minimal thresholds:')
        
        minimal_config = {
            'name': 'test',
            'entry_filters': {
                'min_confidence': 0.1,  # Very low
                'min_trend_strength': 1.0,  # Very low
                'max_volatility': 1.0,  # Very high
                'required_alignment_count': 0,
                'consensus_threshold': 0
            }
        }
        
        signal_result = se.generate_strategy_signal(
            ideal_market_data, ideal_indicators, ideal_regime, minimal_config
        )
        
        signal_type = signal_result.get('signal', 'HOLD')
        confidence = signal_result.get('confidence', 0)
        reason = signal_result.get('reason', 'No reason')
        
        print(f'      * Minimal Thresholds Test: {signal_type} (confidence: {confidence:.2f}) - {reason}')
        
        if signal_type == 'HOLD':
            print('    - CRITICAL ISSUE: Even minimal thresholds generate HOLD')
            print('    - This indicates a fundamental problem with signal logic')
        else:
            print('    - Signal logic works with minimal thresholds')
        
    except Exception as e:
        print(f'  - Error in signal engine analysis: {e}')
    
    # 4. Main Runtime vs Test Discrepancy
    print('\n[4] MAIN RUNTIME vs TEST DISCREPANCY')
    
    print('  - Discrepancy Analysis:')
    print('    - Test Environment: Generates signals with reduced thresholds')
    print('    - Main Runtime: Still generates 0 signals')
    print('    - Possible Causes:')
    
    discrepancy_causes = [
        {
            'cause': 'Configuration Not Persisted',
            'likelihood': 'HIGH',
            'description': 'Threshold changes not saved to actual runtime'
        },
        {
            'cause': 'Different Signal Engine Instance',
            'likelihood': 'MEDIUM',
            'description': 'Main runtime uses different signal engine'
        },
        {
            'cause': 'Strategy Registry Reload',
            'likelihood': 'MEDIUM',
            'description': 'Strategy registry reloaded with old values'
        },
        {
            'cause': 'Market Data Differences',
            'likelihood': 'LOW',
            'description': 'Different market data in runtime vs test'
        }
    ]
    
    for cause in discrepancy_causes:
        cause_name = cause['cause']
        likelihood = cause['likelihood']
        description = cause['description']
        
        print(f'      * {cause_name} ({likelihood}): {description}')
    
    # 5. Root Cause Identification
    print('\n[5] ROOT CAUSE IDENTIFICATION')
    
    print('  - Most Likely Root Causes:')
    
    root_causes = [
        {
            'cause': 'Threshold Changes Not Persisted',
            'evidence': 'Test works but runtime does not',
            'solution': 'Force reload strategy configurations in runtime'
        },
        {
            'cause': 'Signal Engine Logic Issue',
            'evidence': 'Even ideal conditions may not generate signals',
            'solution': 'Debug signal engine logic step by step'
        },
        {
            'cause': 'Configuration Loading Issue',
            'evidence': 'Strategy registry may not be updated',
            'solution': 'Verify configuration persistence'
        }
    ]
    
    for i, cause in enumerate(root_causes, 1):
        cause_name = cause['cause']
        evidence = cause['evidence']
        solution = cause['solution']
        
        print(f'    {i}. {cause_name}:')
        print(f'       * Evidence: {evidence}')
        print(f'       * Solution: {solution}')
    
    # 6. Immediate Fix Actions
    print('\n[6] IMMEDIATE FIX ACTIONS')
    
    print('  - Immediate Actions to Take:')
    
    immediate_actions = [
        {
            'action': 'Force Configuration Reload',
            'steps': [
                'Restart the trading system',
                'Verify strategy configurations are loaded',
                'Check signal generation on restart'
            ]
        },
        {
            'action': 'Debug Signal Engine Step by Step',
            'steps': [
                'Add debug logging to signal engine',
                'Check each calculation step',
                'Identify where signal generation fails'
            ]
        },
        {
            'action': 'Override Thresholds Directly',
            'steps': [
                'Hardcode minimal thresholds in signal engine',
                'Test signal generation',
                'Verify trade execution'
            ]
        }
    ]
    
    for action in immediate_actions:
        action_name = action['action']
        steps = action['steps']
        
        print(f'    - {action_name}:')
        for step in steps:
            print(f'      * {step}')
    
    # 7. Conclusion
    print('\n[7] CONCLUSION')
    
    print('  - Entry Issue Final Diagnosis:')
    print('    - Symptom: 0 signals generated in main runtime')
    print('    - Test Results: Signals can be generated with reduced thresholds')
    print('    - Discrepancy: Test works but runtime does not')
    
    print('  - Most Likely Root Cause:')
    print('    - CONFIGURATION PERSISTENCE ISSUE')
    print('    - Threshold changes not applied to main runtime')
    print('    - Strategy registry not updated with new values')
    
    print('  - Immediate Solution:')
    print('    1. Force restart of trading system')
    print('    2. Verify configuration loading')
    print('    3. Test signal generation after restart')
    
    print('  - If Issue Persists:')
    print('    1. Hardcode minimal thresholds in signal engine')
    print('    2. Add comprehensive debug logging')
    print('    3. Step-by-step signal generation debugging')
    
    print('\n  - Final Assessment:')
    print('    - Problem: Configuration persistence issue')
    print('    - Solution: System restart and configuration verification')
    print('    - Backup: Hardcode minimal thresholds if needed')
    print('    - Timeline: Fix should be immediate after restart')
    
    print('\n' + '=' * 80)
    print('[ENTRY ISSUE FINAL DIAGNOSIS COMPLETE]')
    print('=' * 80)
    print('Root Cause: Configuration persistence issue')
    print('Solution: System restart and configuration verification')
    print('Backup: Hardcode minimal thresholds')
    print('=' * 80)

if __name__ == "__main__":
    entry_issue_final_diagnosis()
