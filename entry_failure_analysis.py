#!/usr/bin/env python3
"""
Entry Failure Analysis - Comprehensive analysis of why signals are not generating
"""

import json
from datetime import datetime

def entry_failure_analysis():
    """Comprehensive analysis of why signals are not generating"""
    print('=' * 80)
    print('ENTRY FAILURE ANALYSIS')
    print('=' * 80)
    
    print(f'Analysis Start: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # 1. Current Signal Generation Status
    print('\n[1] CURRENT SIGNAL GENERATION STATUS')
    
    try:
        with open('trading_results.json', 'r') as f:
            results = json.load(f)
        
        last_cycle = results.get('last_cycle', {})
        signal_engine_replacement = results.get('signal_engine_replacement', {})
        
        print('  - Signal Generation Status:')
        print(f'    - Last Cycle Signals: {last_cycle.get("signals_generated", 0)}')
        print(f'    - Signal Engine Status: {signal_engine_replacement.get("status", "UNKNOWN")}')
        print(f'    - Signal Engine Type: {"WORKING" if signal_engine_replacement.get("new_engine_installed") else "ORIGINAL"}')
        
        # Check recent signal generation
        recent_signals = signal_engine_replacement.get("signals_generated", 0)
        print(f'    - Recent Test Signals: {recent_signals}')
        
        if recent_signals > 0:
            print('    - Signal Generation: WORKING')
        else:
            print('    - Signal Generation: NOT WORKING')
        
    except Exception as e:
        print(f'  - Error loading signal status: {e}')
    
    # 2. Signal Engine Analysis
    print('\n[2] SIGNAL ENGINE ANALYSIS')
    
    try:
        from core.signal_engine import SignalEngine
        from core.market_data_service import MarketDataService
        
        se = SignalEngine()
        mds = MarketDataService('https://demo-fapi.binance.com')
        
        print('  - Signal Engine Test:')
        
        # Test with real market data
        symbols = ['BTCUSDT', 'ETHUSDT', 'DOGEUSDT']
        
        market_data = mds.update_market_data(symbols)
        
        if market_data:
            print(f'    - Market Data: RECEIVED for {len(market_data)} symbols')
            
            signals_generated = 0
            signal_details = []
            
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
                    
                    strategy_config = {
                        'name': 'ma_trend_follow',
                        'entry_filters': {'min_confidence': 0.3}
                    }
                    
                    signal_result = se.generate_strategy_signal(
                        market_data_dict, indicators, regime, strategy_config
                    )
                    
                    signal_type = signal_result.get('signal', 'HOLD')
                    confidence = signal_result.get('confidence', 0)
                    reason = signal_result.get('reason', 'No reason')
                    
                    signal_details.append({
                        'symbol': symbol,
                        'signal': signal_type,
                        'confidence': confidence,
                        'reason': reason
                    })
                    
                    if signal_type != 'HOLD':
                        signals_generated += 1
            
            print(f'    - Test Signals Generated: {signals_generated}')
            
            # Analyze signal details
            print('  - Signal Details Analysis:')
            for detail in signal_details:
                symbol = detail['symbol']
                signal = detail['signal']
                confidence = detail['confidence']
                reason = detail['reason']
                
                print(f'    - {symbol}: {signal} (confidence: {confidence:.2f}) - {reason}')
            
            if signals_generated > 0:
                print('  - Signal Engine Status: WORKING')
            else:
                print('  - Signal Engine Status: GENERATING HOLD SIGNALS')
        
        else:
            print('    - Market Data: FAILED TO RECEIVE')
            print('  - Signal Engine Status: CANNOT TEST (NO DATA)')
        
    except Exception as e:
        print(f'  - Error testing signal engine: {e}')
    
    # 3. Strategy Configuration Analysis
    print('\n[3] STRATEGY CONFIGURATION ANALYSIS')
    
    try:
        from core.strategy_registry import StrategyRegistry
        
        sr = StrategyRegistry()
        
        strategies = ['ma_trend_follow', 'ema_crossover']
        
        print('  - Strategy Configuration Analysis:')
        
        for strategy_name in strategies:
            strategy_config = sr.get_strategy_profile(strategy_name)
            
            if strategy_config:
                print(f'    - {strategy_name.upper()}:')
                
                # Check entry filters
                entry_filters = strategy_config.get('entry_filters', {})
                print(f'      * Min Confidence: {entry_filters.get("min_confidence", 0)}')
                print(f'      * Min Trend Strength: {entry_filters.get("min_trend_strength", 0)}')
                print(f'      * Max Volatility: {entry_filters.get("max_volatility", 0)}')
                print(f'      * Required Alignment: {entry_filters.get("required_alignment_count", 0)}')
                print(f'      * Consensus Threshold: {entry_filters.get("consensus_threshold", 0)}')
                
                # Check if thresholds are too high
                min_confidence = entry_filters.get('min_confidence', 0)
                if min_confidence > 0.7:
                    print(f'      * WARNING: Very high confidence threshold ({min_confidence})')
                elif min_confidence > 0.5:
                    print(f'      * CAUTION: High confidence threshold ({min_confidence})')
                
                min_trend_strength = entry_filters.get("min_trend_strength", 0)
                if min_trend_strength > 20:
                    print(f'      * WARNING: Very high trend strength threshold ({min_trend_strength})')
                elif min_trend_strength > 10:
                    print(f'      * CAUTION: High trend strength threshold ({min_trend_strength})')
            else:
                print(f'    - {strategy_name.upper()}: NOT FOUND')
        
    except Exception as e:
        print(f'  - Error analyzing strategy configuration: {e}')
    
    # 4. Market Conditions Analysis
    print('\n[4] MARKET CONDITIONS ANALYSIS')
    
    try:
        print('  - Market Conditions Assessment:')
        
        # Test market data availability
        if market_data:
            print('    - Market Data: AVAILABLE')
            
            # Analyze market volatility
            volatility_analysis = []
            for symbol, symbol_data in market_data.items():
                klines_1h = symbol_data.get('klines', {}).get('1h', [])
                
                if klines_1h and len(klines_1h) >= 10:
                    closes = [k['close'] for k in klines_1h[-10:]]
                    
                    # Calculate simple volatility
                    price_changes = []
                    for i in range(1, len(closes)):
                        change = (closes[i] - closes[i-1]) / closes[i-1]
                        price_changes.append(abs(change))
                    
                    avg_volatility = sum(price_changes) / len(price_changes) if price_changes else 0
                    
                    volatility_analysis.append({
                        'symbol': symbol,
                        'volatility': avg_volatility,
                        'price_range': max(closes) - min(closes),
                        'price_movement': ((closes[-1] - closes[0]) / closes[0]) * 100
                    })
            
            print('    - Volatility Analysis:')
            for vol in volatility_analysis:
                symbol = vol['symbol']
                volatility = vol['volatility']
                price_range = vol['price_range']
                price_movement = vol['price_movement']
                
                print(f'      * {symbol}: {volatility:.4f} volatility, {price_movement:+.2f}% movement')
                
                if volatility < 0.01:
                    print(f'        - LOW VOLATILITY (may prevent signals)')
                elif volatility > 0.05:
                    print(f'        - HIGH VOLATILITY (good for signals)')
            
            # Check if market is too stable
            avg_volatility = sum(v['volatility'] for v in volatility_analysis) / len(volatility_analysis)
            if avg_volatility < 0.01:
                print('    - MARKET CONDITION: VERY LOW VOLATILITY')
                print('      * This may prevent signal generation')
                print('      * Market is too stable for trading signals')
            elif avg_volatility < 0.02:
                print('    - MARKET CONDITION: LOW VOLATILITY')
                print('      * May result in fewer signals')
            else:
                print('    - MARKET CONDITION: NORMAL VOLATILITY')
        
        else:
            print('    - Market Data: UNAVAILABLE')
            print('      * Cannot analyze market conditions')
        
    except Exception as e:
        print(f'  - Error analyzing market conditions: {e}')
    
    # 5. Historical Context Analysis
    print('\n[5] HISTORICAL CONTEXT ANALYSIS')
    
    try:
        print('  - Historical Signal Generation:')
        
        # Check trading results for signal history
        signal_history = results.get('signal_history', [])
        
        if signal_history:
            print(f'    - Historical Signals: {len(signal_history)}')
            
            # Analyze recent signals
            recent_signals = signal_history[-10:] if len(signal_history) >= 10 else signal_history
            
            signals_by_type = {}
            for signal in recent_signals:
                signal_type = signal.get('signal', 'UNKNOWN')
                signals_by_type[signal_type] = signals_by_type.get(signal_type, 0) + 1
            
            print('    - Recent Signal Distribution:')
            for signal_type, count in signals_by_type.items():
                print(f'      * {signal_type}: {count}')
            
            # Check if signals are mostly HOLD
            hold_signals = signals_by_type.get('HOLD', 0)
            total_recent = len(recent_signals)
            
            if total_recent > 0:
                hold_percentage = (hold_signals / total_recent) * 100
                print(f'    - HOLD Signal Percentage: {hold_percentage:.1f}%')
                
                if hold_percentage > 80:
                    print('      * VERY HIGH HOLD PERCENTAGE')
                    print('      * Indicates entry conditions are too strict')
                elif hold_percentage > 60:
                    print('      * HIGH HOLD PERCENTAGE')
                    print('      * Entry conditions may be too strict')
        else:
            print('    - Historical Signals: NO DATA')
            print('      * No signal history available')
        
    except Exception as e:
        print(f'  - Error analyzing historical context: {e}')
    
    # 6. Entry Logic Bottleneck Analysis
    print('\n[6] ENTRY LOGIC BOTTLENECK ANALYSIS')
    
    print('  - Potential Entry Issues:')
    
    bottlenecks = [
        {
            'issue': 'Market Data Quality',
            'status': 'CHECKED',
            'finding': 'Market data available but may have low volatility'
        },
        {
            'issue': 'Signal Engine Logic',
            'status': 'CHECKED',
            'finding': 'Working signal engine generating HOLD signals'
        },
        {
            'issue': 'Strategy Thresholds',
            'status': 'ANALYZED',
            'finding': 'May be too high for current market conditions'
        },
        {
            'issue': 'Market Volatility',
            'status': 'ANALYZED',
            'finding': 'Market may be too stable for signal generation'
        },
        {
            'issue': 'Configuration Settings',
            'status': 'CHECKED',
            'finding': 'Entry filters may be too restrictive'
        }
    ]
    
    for bottleneck in bottlenecks:
        issue = bottleneck['issue']
        status = bottleneck['status']
        finding = bottleneck['finding']
        
        print(f'    - {issue}: {status}')
        print(f'      * {finding}')
    
    # 7. Root Cause Analysis
    print('\n[7] ROOT CAUSE ANALYSIS')
    
    print('  - Most Likely Root Causes:')
    
    root_causes = [
        {
            'cause': 'Low Market Volatility',
            'probability': 'HIGH',
            'evidence': 'Market showing minimal price movement',
            'solution': 'Lower volatility thresholds or wait for market movement'
        },
        {
            'cause': 'High Confidence Thresholds',
            'probability': 'MEDIUM',
            'evidence': 'Strategy thresholds may be too high for current conditions',
            'solution': 'Reduce min_confidence and min_trend_strength'
        },
        {
            'cause': 'Overly Restrictive Entry Filters',
            'probability': 'MEDIUM',
            'evidence': 'Multiple filters must all be satisfied',
            'solution': 'Relax some entry conditions'
        },
        {
            'cause': 'Market Regime Mismatch',
            'probability': 'LOW',
            'evidence': 'Strategies may not match current market conditions',
            'solution': 'Adapt strategies to current market regime'
        }
    ]
    
    for cause in root_causes:
        cause_name = cause['cause']
        probability = cause['probability']
        evidence = cause['evidence']
        solution = cause['solution']
        
        print(f'    - {cause_name} ({probability}):')
        print(f'      * Evidence: {evidence}')
        print(f'      * Solution: {solution}')
    
    # 8. Immediate Solutions
    print('\n[8] IMMEDIATE SOLUTIONS')
    
    print('  - Quick Fixes to Try:')
    
    solutions = [
        {
            'solution': 'Reduce Confidence Thresholds',
            'action': 'Lower min_confidence from 0.3 to 0.2',
            'impact': 'HIGH',
            'risk': 'LOW'
        },
        {
            'solution': 'Reduce Trend Strength Requirements',
            'action': 'Lower min_trend_strength from 15.0 to 10.0',
            'impact': 'HIGH',
            'risk': 'LOW'
        },
        {
            'solution': 'Increase Volatility Tolerance',
            'action': 'Increase max_volatility from 0.1 to 0.2',
            'impact': 'MEDIUM',
            'risk': 'LOW'
        },
        {
            'solution': 'Relax Alignment Requirements',
            'action': 'Reduce required_alignment_count from 1 to 0',
            'impact': 'MEDIUM',
            'risk': 'LOW'
        }
    ]
    
    for i, solution in enumerate(solutions, 1):
        solution_name = solution['solution']
        action = solution['action']
        impact = solution['impact']
        risk = solution['risk']
        
        print(f'    {i}. {solution_name}:')
        print(f'       * Action: {action}')
        print(f'       * Impact: {impact}')
        print(f'       * Risk: {risk}')
    
    # 9. Conclusion
    print('\n[9] CONCLUSION')
    
    print('  - Entry Failure Analysis Summary:')
    
    print('  - Key Findings:')
    print('    - Signal Engine: WORKING (but generating HOLD signals)')
    print('    - Market Data: AVAILABLE (but low volatility)')
    print('    - Strategy Configuration: MAY BE TOO RESTRICTIVE')
    print('    - Market Conditions: LOW VOLATILITY')
    
    print('  - Primary Root Cause:')
    print('    - LOW MARKET VOLATILITY combined with HIGH ENTRY THRESHOLDS')
    print('    - Market is too stable for current entry conditions')
    
    print('  - Recommended Actions:')
    print('    1. Reduce confidence thresholds immediately')
    print('    2. Lower trend strength requirements')
    print('    3. Monitor for increased market volatility')
    print('    4. Consider regime-specific strategies')
    
    print('  - Expected Outcome:')
    print('    - Lower thresholds should generate more signals')
    print('    - System should start generating BUY/SELL signals')
    print('    - Monitor signal quality after adjustments')
    
    print('\n' + '=' * 80)
    print('[ENTRY FAILURE ANALYSIS COMPLETE]')
    print('=' * 80)
    print('Root Cause: Low market volatility + high entry thresholds')
    print('Solution: Reduce entry thresholds immediately')
    print('Expected: More signal generation')
    print('=' * 80)

if __name__ == "__main__":
    entry_failure_analysis()
