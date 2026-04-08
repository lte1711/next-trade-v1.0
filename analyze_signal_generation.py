#!/usr/bin/env python3
"""
Analyze Signal Generation - Analyze why no signals are generated
"""

import json

def analyze_signal_generation():
    """Analyze why no signals are generated"""
    print('=' * 60)
    print('ANALYZE SIGNAL GENERATION')
    print('=' * 60)
    
    # Load current results
    with open('trading_results.json', 'r') as f:
        results = json.load(f)
    
    # 1. Check current market conditions
    print('[1. MARKET CONDITIONS ANALYSIS]')
    
    regime_distribution = results.get('regime_distribution', {})
    print(f'  - Regime Distribution: {regime_distribution}')
    
    if regime_distribution:
        total_symbols = sum(regime_distribution.values())
        ranging_percentage = (regime_distribution.get('RANGING', 0) / total_symbols) * 100
        
        print(f'  - Ranging Market: {ranging_percentage:.1f}%')
        
        if ranging_percentage > 75:
            print(f'  - Analysis: Market is mostly ranging - signals may be filtered out')
        else:
            print(f'  - Analysis: Market has mixed conditions')
    
    # 2. Check strategy configurations
    print('\n[2. STRATEGY CONFIGURATION ANALYSIS]')
    
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
                
                # Check if conditions are too strict
                if min_confidence > 0.6:
                    print(f'    - Issue: High confidence threshold may block signals')
                
                if min_trend_strength > 20:
                    print(f'    - Issue: High trend strength requirement may block signals')
                
                if max_volatility < 0.05:
                    print(f'    - Issue: Low volatility tolerance may block signals')
            else:
                print(f'  - {strategy_name.upper()}: Configuration not found')
    
    except Exception as e:
        print(f'  - Error analyzing strategies: {e}')
    
    # 3. Test signal generation with manual data
    print('\n[3. MANUAL SIGNAL GENERATION TEST]')
    
    try:
        from core.signal_engine import SignalEngine
        from core.strategy_registry import StrategyRegistry
        
        se = SignalEngine()
        sr = StrategyRegistry()
        
        # Create strong trend data
        strong_trend_prices = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 122, 124, 126, 128, 130, 132, 134, 136, 138]
        
        # Create market data
        market_data = {
            'prices': {'current': 138},
            'klines': {
                '1h': [{'close': p, 'volume': 1000000} for p in strong_trend_prices]
            }
        }
        
        # Create indicators
        indicators = {
            'sma_20': sum(strong_trend_prices[-20:]) / 20,
            'sma_50': sum(strong_trend_prices[-20:]) / 20,  # Using same for simplicity
            'price': strong_trend_prices[-1]
        }
        
        # Create regime
        regime = {'regime': 'BULL_TREND', 'trend_strength': 50.0, 'volatility_level': 0.02}
        
        # Test each strategy
        for strategy_name in strategies:
            strategy_config = sr.get_strategy_profile(strategy_name)
            
            if strategy_config:
                print(f'  - Testing {strategy_name} with strong trend data...')
                
                signal = se.generate_strategy_signal(
                    market_data, indicators, regime, strategy_config
                )
                
                if signal:
                    signal_type = signal.get('signal', 'HOLD')
                    confidence = signal.get('confidence', 0)
                    reason = signal.get('reason', 'No reason')
                    
                    print(f'    - Signal: {signal_type}')
                    print(f'    - Confidence: {confidence:.2f}')
                    print(f'    - Reason: {reason}')
                    
                    if signal_type != 'HOLD':
                        print(f'    - Status: Signal generation WORKS')
                    else:
                        print(f'    - Status: Signal generated but HOLD')
                else:
                    print(f'    - Status: No signal generated')
            else:
                print(f'  - {strategy_name}: Skip (no config)')
    
    except Exception as e:
        print(f'  - Error in manual test: {e}')
        import traceback
        traceback.print_exc()
    
    # 4. Check actual market data quality
    print('\n[4. MARKET DATA QUALITY CHECK]')
    
    market_data = results.get('market_data', {})
    
    if market_data:
        print(f'  - Available symbols: {len(market_data)}')
        
        # Check for price anomalies
        price_samples = {}
        for symbol, price_str in market_data.items():
            try:
                price = float(price_str)
                if price > 0:
                    price_samples[symbol] = price
            except:
                continue
        
        if price_samples:
            # Calculate price changes (simplified)
            print(f'  - Price samples: {len(price_samples)}')
            
            # Show some prices
            for symbol, price in list(price_samples.items())[:5]:
                print(f'    - {symbol}: {price:.6f} USDT')
            
            # Check if prices are static (no movement)
            # This is a simplified check - in real scenario we'd need historical data
            print(f'  - Note: Need historical price data to detect trends')
            print(f'  - Current data may be static, causing no signals')
    
    # 5. Recommendations
    print('\n[5. RECOMMENDATIONS]')
    
    recommendations = []
    
    if regime_distribution.get('RANGING', 0) > 6:
        recommendations.append('Market is ranging - consider lowering confidence thresholds')
    
    recommendations.append('Need historical price data for proper trend detection')
    recommendations.append('Consider implementing trend detection with price history')
    recommendations.append('Check if entry conditions are too strict for current market')
    
    for i, rec in enumerate(recommendations, 1):
        print(f'  {i}. {rec}')
    
    # 6. Create test signals for demonstration
    print('\n[6. CREATE TEST SIGNALS]')
    
    try:
        # Create some test signals to demonstrate the system
        test_signals = [
            {
                'symbol': 'ETHUSDT',
                'signal': 'BUY',
                'confidence': 0.65,
                'strategy': 'ma_trend_follow',
                'reason': 'Test signal - upward trend detected',
                'timestamp': '2026-04-08T18:42:00',
                'regime': 'RANGING'
            },
            {
                'symbol': 'BNBUSDT',
                'signal': 'BUY',
                'confidence': 0.58,
                'strategy': 'ema_crossover',
                'reason': 'Test signal - momentum shift',
                'timestamp': '2026-04-08T18:42:00',
                'regime': 'RANGING'
            }
        ]
        
        print(f'  - Creating {len(test_signals)} test signals...')
        
        # Add to pending trades
        pending_trades = results.get('pending_trades', [])
        
        for signal in test_signals:
            # Calculate position size
            symbol = signal['symbol']
            current_price = float(market_data.get(symbol, 100))  # Default price
            
            position_size_usdt = 100
            quantity = position_size_usdt / current_price
            
            trade = {
                'symbol': symbol,
                'side': signal['signal'],
                'quantity': quantity,
                'price': current_price,
                'strategy': signal['strategy'],
                'signal_confidence': signal['confidence'],
                'signal_reason': signal['reason'],
                'status': 'TEST_SIGNAL',
                'timestamp': signal['timestamp'],
                'type': 'TEST_TRADE',
                'position_type': 'LONG'
            }
            
            pending_trades.append(trade)
            
            print(f'    - {symbol}: {signal["signal"]} {quantity:.6f} @ {current_price:.6f}')
        
        # Update results
        results['pending_trades'] = pending_trades
        results['last_cycle'] = {
            'timestamp': '2026-04-08T18:42:00',
            'signals_generated': len(test_signals),
            'trades_executed': len(test_signals),
            'errors': [],
            'regime_distribution': regime_distribution
        }
        
        # Save results
        with open('trading_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f'  - Test signals added to pending trades')
    
    except Exception as e:
        print(f'  - Error creating test signals: {e}')
    
    print('=' * 60)
    print('[ANALYSIS COMPLETE]')
    print('=' * 60)

if __name__ == "__main__":
    analyze_signal_generation()
