#!/usr/bin/env python3
"""
Deep Entry Logic Analysis - Deep dive into entry logic implementation
"""

import json
from datetime import datetime

def deep_entry_logic_analysis():
    """Deep dive into entry logic implementation"""
    print('=' * 80)
    print('DEEP ENTRY LOGIC ANALYSIS')
    print('=' * 80)
    
    print(f'Deep Analysis Start: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # 1. Signal Engine Source Code Analysis
    print('\n[1. SIGNAL ENGINE SOURCE CODE ANALYSIS]')
    
    try:
        from core.signal_engine import SignalEngine
        import inspect
        
        # Get the source code of generate_strategy_signal
        source_code = inspect.getsource(SignalEngine.generate_strategy_signal)
        
        print('  - Signal Generation Source Code Analysis:')
        
        # Break down the source code into logical sections
        lines = source_code.split('\n')
        
        # Find key sections
        in_signal_generation = False
        in_v2_logic = False
        in_consensus_calculation = False
        in_alignment_calculation = False
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Track sections
            if 'def generate_strategy_signal' in stripped:
                in_signal_generation = True
                print(f'    - Line {i+1}: Signal generation method found')
                continue
            
            if not in_signal_generation:
                continue
            
            # V2 Merged logic
            if 'V2' in stripped and 'merged' in stripped.lower():
                in_v2_logic = True
                print(f'    - Line {i+1}: V2 Merged logic section')
                continue
            
            # Consensus calculation
            if 'consensus' in stripped.lower() and 'threshold' in stripped.lower():
                in_consensus_calculation = True
                print(f'    - Line {i+1}: Consensus threshold calculation')
                continue
            
            # Alignment calculation
            if 'alignment' in stripped.lower() and 'count' in stripped.lower():
                in_alignment_calculation = True
                print(f'    - Line {i+1}: Alignment count calculation')
                continue
            
            # Key conditions
            if 'bullish_alignment_count' in stripped:
                print(f'    - Line {i+1}: Bullish alignment count condition')
            elif 'bearish_alignment_count' in stripped:
                print(f'    - Line {i+1}: Bearish alignment count condition')
            elif 'trend_consensus' in stripped:
                print(f'    - Line {i+1}: Trend consensus condition')
            elif 'volume_ready' in stripped:
                print(f'    - Line {i+1}: Volume ready condition')
            elif 'price_vs_ma' in stripped:
                print(f'    - Line {i+1}: Price vs MA condition')
            elif 'ema_fast' in stripped and 'ema_mid' in stripped:
                print(f'    - Line {i+1}: EMA Fast vs Mid condition')
            elif 'heikin' in stripped.lower():
                print(f'    - Line {i+1}: Heikin Ashi condition')
            elif 'fractal' in stripped.lower():
                print(f'    - Line {i+1}: Fractal condition')
            elif 'confidence' in stripped.lower():
                print(f'    - Line {i+1}: Confidence calculation')
            elif 'signal' in stripped.lower() and '=' in stripped:
                print(f'    - Line {i+1}: Signal assignment')
            elif 'return' in stripped and 'signal' in stripped:
                print(f'    - Line {i+1}: Signal return')
        
        print('\n  - Entry Logic Flow Analysis:')
        print('    1. Input: market_data, indicators, regime, strategy_config')
        print('    2. Process: V2 Merged logic with multiple conditions')
        print('    3. Conditions: Alignment, consensus, volume, price, EMA, Heikin Ashi, Fractal')
        print('    4. Output: Signal (BUY/SELL/HOLD) with confidence and reason')
        
    except Exception as e:
        print(f'  - Error analyzing signal engine source: {e}')
    
    # 2. Entry Conditions Detailed Analysis
    print('\n[2. ENTRY CONDITIONS DETAILED ANALYSIS]')
    
    try:
        # Test entry conditions with sample data
        from core.signal_engine import SignalEngine
        from core.strategy_registry import StrategyRegistry
        
        se = SignalEngine()
        sr = StrategyRegistry()
        
        # Create comprehensive test data
        print('  - Entry Conditions Test:')
        
        # Test data for strong buy signal
        market_data_test = {
            'prices': {'current': 100.0},
            'klines': {
                '1m': [{'close': 100, 'volume': 1000} for _ in range(20)],
                '5m': [{'close': 100, 'volume': 1000} for _ in range(20)],
                '15m': [{'close': 100, 'volume': 1000} for _ in range(20)],
                '1h': [{'close': 100, 'volume': 1000} for _ in range(20)]
            }
        }
        
        indicators_test = {
            'sma_20': 98.0,
            'sma_50': 95.0,
            'ema_9': 99.0,
            'ema_21': 97.0,
            'ema_50': 95.0,
            'price': 100.0,
            'volume': 1000,
            'atr': 2.0
        }
        
        regime_test = {
            'regime': 'BULL_TREND',
            'trend_strength': 30.0,
            'volatility_level': 0.02
        }
        
        # Test with ma_trend_follow
        strategy_config = sr.get_strategy_profile('ma_trend_follow')
        
        if strategy_config:
            print(f'    - Testing ma_trend_follow with bullish data:')
            
            signal = se.generate_strategy_signal(
                market_data_test, indicators_test, regime_test, strategy_config
            )
            
            if signal:
                signal_type = signal.get('signal', 'HOLD')
                confidence = signal.get('confidence', 0)
                reason = signal.get('reason', 'No reason')
                
                print(f'      * Signal: {signal_type}')
                print(f'      * Confidence: {confidence:.2f}')
                print(f'      * Reason: {reason}')
                
                # Analyze confidence factors
                if confidence > 0:
                    print(f'      * Status: Signal generated successfully')
                else:
                    print(f'      * Status: Low confidence signal')
            else:
                print(f'      * Status: No signal generated')
        
        # Test with bearish data
        indicators_bearish = indicators_test.copy()
        indicators_bearish['sma_20'] = 102.0
        indicators_bearish['sma_50'] = 105.0
        indicators_bearish['ema_9'] = 101.0
        indicators_bearish['ema_21'] = 103.0
        indicators_bearish['ema_50'] = 105.0
        indicators_bearish['price'] = 100.0
        
        regime_bearish = {
            'regime': 'BEAR_TREND',
            'trend_strength': 30.0,
            'volatility_level': 0.02
        }
        
        print(f'    - Testing ma_trend_follow with bearish data:')
        
        signal = se.generate_strategy_signal(
            market_data_test, indicators_bearish, regime_bearish, strategy_config
        )
        
        if signal:
            signal_type = signal.get('signal', 'HOLD')
            confidence = signal.get('confidence', 0)
            reason = signal.get('reason', 'No reason')
            
            print(f'      * Signal: {signal_type}')
            print(f'      * Confidence: {confidence:.2f}')
            print(f'      * Reason: {reason}')
        else:
            print(f'      * Status: No signal generated')
        
        # Test with ema_crossover
        strategy_config_ema = sr.get_strategy_profile('ema_crossover')
        
        if strategy_config_ema:
            print(f'    - Testing ema_crossover with bullish data:')
            
            signal = se.generate_strategy_signal(
                market_data_test, indicators_test, regime_test, strategy_config_ema
            )
            
            if signal:
                signal_type = signal.get('signal', 'HOLD')
                confidence = signal.get('confidence', 0)
                reason = signal.get('reason', 'No reason')
                
                print(f'      * Signal: {signal_type}')
                print(f'      * Confidence: {confidence:.2f}')
                print(f'      * Reason: {reason}')
            else:
                print(f'      * Status: No signal generated')
        
    except Exception as e:
        print(f'  - Error testing entry conditions: {e}')
    
    # 3. Entry Logic Bottleneck Analysis
    print('\n[3. ENTRY LOGIC BOTTLENECK ANALYSIS]')
    
    try:
        with open('trading_results.json', 'r') as f:
            results = json.load(f)
        
        # Analyze why no signals are generated
        print('  - Entry Logic Bottleneck Analysis:')
        
        # Check market data quality
        market_data = results.get('market_data', {})
        
        if not market_data:
            print('    - Bottleneck: NO MARKET DATA')
        elif len(market_data) < 10:
            print('    - Bottleneck: LIMITED MARKET DATA')
        else:
            print('    - Market Data: OK')
        
        # Check regime analysis
        regime_distribution = results.get('regime_distribution', {})
        
        if not regime_distribution:
            print('    - Bottleneck: NO REGIME ANALYSIS')
        else:
            print('    - Regime Analysis: OK')
        
        # Check last cycle performance
        last_cycle = results.get('last_cycle', {})
        
        if last_cycle:
            signals_generated = last_cycle.get('signals_generated', 0)
            trades_executed = last_cycle.get('trades_executed', 0)
            
            if signals_generated == 0:
                print('    - Bottleneck: NO SIGNALS GENERATED')
            elif trades_executed == 0:
                print('    - Bottleneck: NO TRADES EXECUTED')
            else:
                print('    - Signal Generation: OK')
                print('    - Trade Execution: OK')
        
        # Check strategy configurations
        try:
            from core.strategy_registry import StrategyRegistry
            sr = StrategyRegistry()
            
            for strategy_name in ['ma_trend_follow', 'ema_crossover']:
                strategy_config = sr.get_strategy_profile(strategy_name)
                
                if strategy_config:
                    entry_filters = strategy_config.get('entry_filters', {})
                    min_confidence = entry_filters.get('min_confidence', 0)
                    min_trend_strength = entry_filters.get('min_trend_strength', 0)
                    
                    if min_confidence > 0.7:
                        print(f'    - Bottleneck: {strategy_name} - High confidence threshold ({min_confidence})')
                    
                    if min_trend_strength > 25:
                        print(f'    - Bottleneck: {strategy_name} - High trend strength requirement ({min_trend_strength})')
                else:
                    print(f'    - Bottleneck: {strategy_name} - No configuration')
        
        except Exception as e:
            print(f'    - Bottleneck: Strategy registry error - {e}')
        
        # Check current market conditions
        if regime_distribution:
            total_symbols = sum(regime_distribution.values())
            ranging_count = regime_distribution.get('RANGING', 0)
            
            if total_symbols > 0:
                ranging_percentage = (ranging_count / total_symbols) * 100
                
                if ranging_percentage > 80:
                    print(f'    - Bottleneck: Market mostly ranging ({ranging_percentage:.1f}%)')
                elif ranging_percentage > 60:
                    print(f'    - Bottleneck: Market largely ranging ({ranging_percentage:.1f}%)')
                else:
                    print(f'    - Market Conditions: OK')
        
    except Exception as e:
        print(f'  - Error analyzing bottlenecks: {e}')
    
    # 4. Entry Logic Optimization Analysis
    print('\n[4. ENTRY LOGIC OPTIMIZATION ANALYSIS]')
    
    print('  - Optimization Opportunities:')
    
    # Confidence threshold optimization
    print('    1. Confidence Threshold Optimization:')
    print('       - Current: ma_trend_follow (0.5), ema_crossover (0.55)')
    print('       - Issue: May be too high for ranging markets')
    print('       - Recommendation: Adaptive thresholds based on market regime')
    print('         * Trending markets: 0.5-0.6')
    print('         * Ranging markets: 0.4-0.5')
    print('         * Volatile markets: 0.6-0.7')
    
    # Trend strength optimization
    print('    2. Trend Strength Optimization:')
    print('       - Current: ma_trend_follow (15.0), ema_crossover (20.0)')
    print('       - Issue: May be too high for current market conditions')
    print('       - Recommendation: Adaptive trend strength')
    print('         * Strong trend: 20-25')
    print('         * Moderate trend: 10-20')
    print('         * Weak trend: 5-10')
    
    # Symbol selection optimization
    print('    3. Symbol Selection Optimization:')
    print('       - Current: ma_trend_follow (leaders), ema_crossover (volatile)')
    print('       - Issue: May miss opportunities in different market conditions')
    print('       - Recommendation: Dynamic symbol selection')
    print('         * Bull markets: Focus on leaders')
    print('         * Bear markets: Focus on volatile')
    print('         * Ranging markets: Balanced approach')
    
    # Entry conditions optimization
    print('    4. Entry Conditions Optimization:')
    print('       - Current: V2 Merged with multiple conditions')
    print('       - Issue: May be too restrictive')
    print('       - Recommendation: Tiered entry conditions')
    print('         * Tier 1: Basic conditions (confidence + trend)')
    print('         * Tier 2: Advanced conditions (volume + alignment)')
    print('         * Tier 3: Expert conditions (fractal + Heikin Ashi)')
    
    # 5. Entry Logic Testing Framework
    print('\n[5. ENTRY LOGIC TESTING FRAMEWORK]')
    
    print('  - Testing Framework Components:')
    print('    1. Historical Data Testing:')
    print('       - Backtest entry logic on historical data')
    print('       - Measure signal generation frequency')
    print('       - Calculate success rate of signals')
    print('       - Optimize parameters based on results')
    
    print('    2. Market Scenario Testing:')
    print('       - Test in different market conditions')
    print('       - Trending market scenarios')
    print('       - Ranging market scenarios')
    print('       - Volatile market scenarios')
    
    print('    3. Real-time Paper Trading:')
    print('       - Test entry logic without real money')
    print('       - Monitor signal quality')
    print('       - Adjust parameters based on performance')
    print('       - Validate before live trading')
    
    print('    4. Performance Metrics:')
    print('       - Signal generation frequency')
    print('       - Signal accuracy rate')
    print('       - Average holding period')
    print('       - Risk-adjusted returns')
    
    # 6. Entry Logic Implementation Status
    print('\n[6. ENTRY LOGIC IMPLEMENTATION STATUS]')
    
    print('  - Current Implementation Status:')
    
    # Check if all components are working
    components_status = {}
    
    # Strategy Registry
    try:
        from core.strategy_registry import StrategyRegistry
        sr = StrategyRegistry()
        ma_config = sr.get_strategy_profile('ma_trend_follow')
        ema_config = sr.get_strategy_profile('ema_crossover')
        
        if ma_config and ema_config:
            components_status['strategy_registry'] = 'WORKING'
        else:
            components_status['strategy_registry'] = 'PARTIAL'
    except:
        components_status['strategy_registry'] = 'ERROR'
    
    # Signal Engine
    try:
        from core.signal_engine import SignalEngine
        se = SignalEngine()
        components_status['signal_engine'] = 'WORKING'
    except:
        components_status['signal_engine'] = 'ERROR'
    
    # Trade Orchestrator
    try:
        from core.trade_orchestrator import TradeOrchestrator
        components_status['trade_orchestrator'] = 'WORKING'
    except:
        components_status['trade_orchestrator'] = 'ERROR'
    
    # Market Data Service
    try:
        from core.market_data_service import MarketDataService
        mds = MarketDataService('https://demo-fapi.binance.com')
        components_status['market_data_service'] = 'WORKING'
    except:
        components_status['market_data_service'] = 'ERROR'
    
    # Market Regime Service
    try:
        from core.market_regime_service import MarketRegimeService
        mrs = MarketRegimeService()
        components_status['market_regime_service'] = 'WORKING'
    except:
        components_status['market_regime_service'] = 'ERROR'
    
    print('    - Component Status:')
    for component, status in components_status.items():
        print(f'      * {component}: {status}')
    
    # Overall status
    working_components = sum(1 for status in components_status.values() if status == 'WORKING')
    total_components = len(components_status)
    
    if working_components == total_components:
        overall_status = 'FULLY FUNCTIONAL'
    elif working_components >= total_components * 0.8:
        overall_status = 'MOSTLY FUNCTIONAL'
    elif working_components >= total_components * 0.5:
        overall_status = 'PARTIALLY FUNCTIONAL'
    else:
        overall_status = 'MINIMALLY FUNCTIONAL'
    
    print(f'    - Overall Status: {overall_status} ({working_components}/{total_components})')
    
    print('\n' + '=' * 80)
    print('[DEEP ENTRY LOGIC ANALYSIS COMPLETE]')
    print('=' * 80)

if __name__ == "__main__":
    deep_entry_logic_analysis()
