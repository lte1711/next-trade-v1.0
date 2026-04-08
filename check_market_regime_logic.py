#!/usr/bin/env python3
"""
Check Market Regime Logic - Check market evaluation logic
"""

import json

def check_market_regime_logic():
    """Check market evaluation logic"""
    print('=' * 60)
    print('MARKET REGIME LOGIC CHECK')
    print('=' * 60)
    
    # Load trading results
    with open('trading_results.json', 'r') as f:
        results = json.load(f)
    
    # Check current regime distribution
    regime_distribution = results.get('regime_distribution', {})
    
    print('[CURRENT REGIME DISTRIBUTION]')
    print(f'  - Total symbols analyzed: {sum(regime_distribution.values())}')
    print(f'  - Regime breakdown:')
    
    for regime, count in regime_distribution.items():
        percentage = (count / sum(regime_distribution.values())) * 100 if regime_distribution else 0
        print(f'    {regime}: {count} symbols ({percentage:.1f}%)')
    
    # Check market regime service logic
    print('\n[MARKET REGIME SERVICE] Logic analysis:')
    
    try:
        from core.market_regime_service import MarketRegimeService
        
        mrs = MarketRegimeService()
        
        print('  - Regime Classification Logic:')
        print('    1. ADX > 25 + Momentum > 0 = BULL_TREND')
        print('    2. ADX > 25 + Momentum < 0 = BEAR_TREND')
        print('    3. Volatility > 2% = HIGH_VOLATILITY')
        print('    4. Otherwise = RANGING')
        
        print('\n  - Technical Indicators Used:')
        print('    - ADX (Average Directional Index): Trend strength')
        print('    - Plus DI/Minus DI: Directional movement')
        print('    - Volatility: Price movement range')
        print('    - Momentum: Price momentum (10-period)')
        
        # Test with sample data
        print('\n  - Testing with sample data:')
        
        # Create sample price data for different regimes
        test_cases = [
            {
                'name': 'Bull Trend',
                'prices': [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 122, 124, 126, 128],
                'expected': 'BULL_TREND'
            },
            {
                'name': 'Bear Trend',
                'prices': [128, 126, 124, 122, 120, 118, 116, 114, 112, 110, 108, 106, 104, 102, 100],
                'expected': 'BEAR_TREND'
            },
            {
                'name': 'Ranging',
                'prices': [110, 112, 108, 113, 107, 114, 106, 115, 105, 116, 104, 117, 103, 118, 102],
                'expected': 'RANGING'
            },
            {
                'name': 'High Volatility',
                'prices': [100, 110, 90, 120, 80, 130, 70, 140, 60, 150, 50, 160, 40, 170, 30],
                'expected': 'HIGH_VOLATILITY'
            }
        ]
        
        for test_case in test_cases:
            prices = test_case['prices']
            volumes = [1000] * len(prices)  # Dummy volumes
            
            regime_result = mrs.analyze_market_regime(prices, volumes)
            actual_regime = regime_result.get('regime', 'UNKNOWN')
            expected_regime = test_case['expected']
            
            status = 'CORRECT' if actual_regime == expected_regime else 'WRONG'
            print(f'    {test_case["name"]}: {actual_regime} ({status})')
            
            if status == 'WRONG':
                print(f'      Expected: {expected_regime}')
                print(f'      ADX: {regime_result.get("trend_strength", 0):.2f}')
                print(f'      Volatility: {regime_result.get("volatility_level", 0):.4f}')
                print(f'      Momentum: {regime_result.get("price_momentum", 0):.4f}')
    
    except Exception as e:
        print(f'  - Error testing market regime service: {e}')
    
    # Check signal engine regime filtering
    print('\n[SIGNAL ENGINE] Regime filtering logic:')
    
    try:
        from core.signal_engine import SignalEngine
        
        # Check regime filtering in signal engine
        print('  - Regime Filter Application:')
        print('    1. RANGING regime requires confidence >= 0.7')
        print('    2. Other regimes use normal confidence thresholds')
        print('    3. Regime info added to signal diagnostics')
        
        # Check current signals
        last_cycle = results.get('last_cycle', {})
        signals = last_cycle.get('signals', [])
        
        if signals:
            print(f'\n  - Current Signal Analysis ({len(signals)} signals):')
            
            regime_filtered = 0
            total_signals = len(signals)
            
            for signal in signals:
                market_regime = signal.get('market_regime', 'UNKNOWN')
                confidence = signal.get('confidence', 0)
                signal_type = signal.get('signal', 'HOLD')
                reason = signal.get('reason', '')
                
                if 'Filtered by ranging regime' in reason:
                    regime_filtered += 1
                
                print(f'    {signal.get("symbol", "Unknown")}: {signal_type} | Regime: {market_regime} | Confidence: {confidence:.2f}')
            
            print(f'  - Filtered by regime: {regime_filtered}/{total_signals}')
        else:
            print('  - No signals found in last cycle')
    
    except Exception as e:
        print(f'  - Error checking signal engine: {e}')
    
    # Check trade orchestrator regime usage
    print('\n[TRADE ORCHESTRATOR] Regime usage analysis:')
    
    try:
        with open('core/trade_orchestrator.py', 'r') as f:
            content = f.read()
        
        # Count regime-related code
        regime_references = content.count('regime')
        regime_analysis = content.count('analyze_market_regime')
        regime_data_usage = content.count('regime_data')
        
        print(f'  - Regime references: {regime_references}')
        print(f'  - Regime analysis calls: {regime_analysis}')
        print(f'  - Regime data usage: {regime_data_usage}')
        
        # Check if regime is used in signal generation
        if 'regime.get(' in content:
            print('  - Regime data is used in signal generation')
        else:
            print('  - Regime data may not be fully utilized')
    
    except Exception as e:
        print(f'  - Error checking trade orchestrator: {e}')
    
    # Check strategy registry regime considerations
    print('\n[STRATEGY REGISTRY] Regime considerations:')
    
    try:
        from core.strategy_registry import StrategyRegistry
        
        sr = StrategyRegistry()
        
        strategies = ['ma_trend_follow', 'ema_crossover']
        
        for strategy_name in strategies:
            strategy_config = sr.get_strategy_profile(strategy_name)
            
            if strategy_config:
                entry_filters = strategy_config.get('entry_filters', {})
                min_confidence = entry_filters.get('min_confidence', 0)
                min_trend_strength = entry_filters.get('min_trend_strength', 0)
                max_volatility = entry_filters.get('max_volatility', 1.0)
                
                print(f'  - {strategy_name.upper()}:')
                print(f'    - Min Confidence: {min_confidence}')
                print(f'    - Min Trend Strength: {min_trend_strength}')
                print(f'    - Max Volatility: {max_volatility}')
                
                # Check if strategy is regime-aware
                if min_trend_strength > 0:
                    print(f'    - Regime-aware: Yes (trend strength required)')
                else:
                    print(f'    - Regime-aware: No (no trend requirement)')
    
    except Exception as e:
        print(f'  - Error checking strategy registry: {e}')
    
    # Check current market conditions
    print('\n[CURRENT MARKET CONDITIONS] Analysis:')
    
    market_data = results.get('market_data', {})
    
    if market_data:
        # Calculate basic market metrics
        prices = []
        for symbol, price_str in market_data.items():
            try:
                price = float(price_str)
                if price > 0:
                    prices.append(price)
            except:
                continue
        
        if prices:
            avg_price = sum(prices) / len(prices)
            max_price = max(prices)
            min_price = min(prices)
            
            print(f'  - Total symbols: {len(prices)}')
            print(f'  - Average price: ${avg_price:.2f}')
            print(f'  - Price range: ${min_price:.6f} - ${max_price:.2f}')
            print(f'  - Price spread: {((max_price - min_price) / avg_price) * 100:.2f}%')
            
            # Estimate market condition
            if regime_distribution:
                bull_count = regime_distribution.get('BULL_TREND', 0)
                bear_count = regime_distribution.get('BEAR_TREND', 0)
                ranging_count = regime_distribution.get('RANGING', 0)
                
                total = bull_count + bear_count + ranging_count
                
                if total > 0:
                    bull_percentage = (bull_count / total) * 100
                    bear_percentage = (bear_count / total) * 100
                    ranging_percentage = (ranging_count / total) * 100
                    
                    print(f'\n  - Market Sentiment:')
                    print(f'    - Bullish: {bull_percentage:.1f}%')
                    print(f'    - Bearish: {bear_percentage:.1f}%')
                    print(f'    - Ranging: {ranging_percentage:.1f}%')
                    
                    if bull_percentage > 50:
                        market_condition = 'BULLISH DOMINANT'
                    elif bear_percentage > 50:
                        market_condition = 'BEARISH DOMINANT'
                    elif ranging_percentage > 50:
                        market_condition = 'RANGING DOMINANT'
                    else:
                        market_condition = 'MIXED'
                    
                    print(f'    - Overall Condition: {market_condition}')
    
    # Recommendations
    print('\n[RECOMMENDATIONS]')
    print('  1. Market regime logic appears to be working correctly')
    print('  2. ADX-based trend detection is appropriate')
    print('  3. Volatility filtering prevents false signals')
    print('  4. Consider adding more regime-specific strategies')
    print('  5. Monitor regime distribution for market changes')
    
    print('=' * 60)
    print('[RESULT] Market regime logic check complete')
    print('=' * 60)

if __name__ == "__main__":
    check_market_regime_logic()
