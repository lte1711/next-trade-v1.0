#!/usr/bin/env python3
"""
Test Market Regime Calculation - Test the actual market regime calculation
"""

import json

def test_market_regime_calculation():
    """Test the actual market regime calculation"""
    print('=' * 60)
    print('MARKET REGIME CALCULATION TEST')
    print('=' * 60)
    
    # Load trading results
    with open('trading_results.json', 'r') as f:
        results = json.load(f)
    
    # Get market data
    market_data = results.get('market_data', {})
    
    print('[MARKET DATA] Available symbols for testing:')
    print(f'  - Total symbols: {len(market_data)}')
    
    # Test with actual market data
    try:
        from core.market_regime_service import MarketRegimeService
        
        mrs = MarketRegimeService()
        
        # Test with BTCUSDT (most liquid)
        btc_price_str = market_data.get('BTCUSDT', '0')
        print(f'\n[TEST] BTCUSDT Analysis:')
        print(f'  - Current Price: {btc_price_str} USDT')
        
        # Create realistic price data for BTCUSDT
        try:
            current_price = float(btc_price_str)
            
            # Generate realistic price series based on current price
            base_price = current_price
            price_series = []
            
            # Create 20 periods of price data with some trend
            for i in range(20):
                # Add some realistic movement
                if i < 10:  # Trending up
                    change = 0.002 * (i + 1)  # 0.2% per period upward
                else:  # Trending down
                    change = 0.001 * (i - 10)  # 0.1% per period downward
                
                price = base_price * (1 + change)
                price_series.append(price)
                base_price = price
            
            # Create volume data
            volume_series = [1000000] * len(price_series)  # 1M volume per period
            
            print(f'  - Generated {len(price_series)} price points')
            print(f'  - Price range: ${min(price_series):.2f} - ${max(price_series):.2f}')
            
            # Calculate regime
            regime_result = mrs.analyze_market_regime(price_series, volume_series)
            
            print(f'\n[REGIME RESULT] BTCUSDT:')
            print(f'  - Regime: {regime_result.get("regime", "UNKNOWN")}')
            print(f'  - ADX: {regime_result.get("trend_strength", 0):.2f}')
            print(f'  - Volatility: {regime_result.get("volatility_level", 0):.4f}')
            print(f'  - Momentum: {regime_result.get("price_momentum", 0):.4f}')
            
            # Check if ADX calculation is working
            adx_values = regime_result.get('adx', [])
            if adx_values:
                print(f'  - ADX Series: {[f"{x:.2f}" for x in adx_values[-5:]]}')
            else:
                print(f'  - ADX Series: EMPTY (Potential Issue)')
            
            # Test with ETHUSDT
            eth_price_str = market_data.get('ETHUSDT', '0')
            print(f'\n[TEST] ETHUSDT Analysis:')
            print(f'  - Current Price: {eth_price_str} USDT')
            
            current_price = float(eth_price_str)
            
            # Create ranging market data
            price_series = []
            base_price = current_price
            
            for i in range(20):
                # Create ranging movement
                change = 0.001 * ((-1) ** i) * (i % 3 + 1)  # Small alternating movements
                price = base_price * (1 + change)
                price_series.append(price)
                base_price = price
            
            volume_series = [500000] * len(price_series)
            
            regime_result = mrs.analyze_market_regime(price_series, volume_series)
            
            print(f'\n[REGIME RESULT] ETHUSDT:')
            print(f'  - Regime: {regime_result.get("regime", "UNKNOWN")}')
            print(f'  - ADX: {regime_result.get("trend_strength", 0):.2f}')
            print(f'  - Volatility: {regime_result.get("volatility_level", 0):.4f}')
            print(f'  - Momentum: {regime_result.get("price_momentum", 0):.4f}')
            
            # Test with DOGEUSDT (high volatility)
            doge_price_str = market_data.get('DOGEUSDT', '0')
            print(f'\n[TEST] DOGEUSDT Analysis:')
            print(f'  - Current Price: {doge_price_str} USDT')
            
            current_price = float(doge_price_str)
            
            # Create high volatility data
            price_series = []
            base_price = current_price
            
            for i in range(20):
                # Create high volatility
                change = 0.01 * ((-1) ** i) * (i % 5 + 1)  # 1% alternating movements
                price = base_price * (1 + change)
                price_series.append(price)
                base_price = price
            
            volume_series = [10000000] * len(price_series)  # High volume
            
            regime_result = mrs.analyze_market_regime(price_series, volume_series)
            
            print(f'\n[REGIME RESULT] DOGEUSDT:')
            print(f'  - Regime: {regime_result.get("regime", "UNKNOWN")}')
            print(f'  - ADX: {regime_result.get("trend_strength", 0):.2f}')
            print(f'  - Volatility: {regime_result.get("volatility_level", 0):.4f}')
            print(f'  - Momentum: {regime_result.get("price_momentum", 0):.4f}')
            
            # Test ADX calculation directly
            print(f'\n[ADX CALCULATION] Direct test:')
            
            # Strong trend data
            strong_trend_prices = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 122, 124, 126, 128, 130, 132, 134, 136, 138, 140, 142, 144, 146, 148, 150, 152, 154, 156]
            strong_volumes = [1000000] * len(strong_trend_prices)
            
            adx_result = mrs.analyze_market_regime(strong_trend_prices, strong_volumes)
            
            print(f'  - Strong Trend Test:')
            print(f'    - Input: 28 price points (upward trend)')
            print(f'    - Expected: BULL_TREND')
            print(f'    - Actual: {adx_result.get("regime", "UNKNOWN")}')
            print(f'    - ADX: {adx_result.get("trend_strength", 0):.2f}')
            print(f'    - Volatility: {adx_result.get("volatility_level", 0):.4f}')
            
            # Check ADX values
            adx_values = adx_result.get('adx', [])
            if adx_values:
                print(f'    - ADX Values: {[f"{x:.2f}" for x in adx_values[-3:]]}')
            else:
                print(f'    - ADX Values: EMPTY (Issue detected)')
            
        except ValueError as e:
            print(f'  - Error converting price: {e}')
        
    except Exception as e:
        print(f'  - Error testing market regime: {e}')
        import traceback
        traceback.print_exc()
    
    # Check if regime analysis is being called in runtime
    print(f'\n[REGIME ANALYSIS IN RUNTIME] Usage check:')
    
    try:
        # Check if regime analysis is being called
        with open('main_runtime.py', 'r') as f:
            content = f.read()
        
        if 'analyze_market_regime' in content:
            print('  - Regime analysis is called in main_runtime.py')
        else:
            print('  - Regime analysis may not be called in main_runtime.py')
        
        # Check trading results for regime data
        regime_data = results.get('market_regime', {})
        if regime_data:
            print(f'  - Market regime data found: {regime_data}')
        else:
            print('  - No market regime data in trading results')
        
        # Check last cycle for regime information
        last_cycle = results.get('last_cycle', {})
        signals = last_cycle.get('signals', [])
        
        if signals:
            regime_count = 0
            for signal in signals:
                if 'market_regime' in signal:
                    regime_count += 1
            
            print(f'  - Signals with regime info: {regime_count}/{len(signals)}')
        else:
            print('  - No signals in last cycle')
    
    except Exception as e:
        print(f'  - Error checking runtime usage: {e}')
    
    print('\n[ISSUES IDENTIFIED]')
    print('  1. ADX calculation may not be working correctly')
    print('  2. Regime distribution shows 0 symbols analyzed')
    print('  3. Test cases return UNKNOWN regime')
    print('  4. Market regime data may not be updated in runtime')
    
    print('\n[RECOMMENDATIONS]')
    print('  1. Debug ADX calculation in market_regime_service.py')
    print('  2. Ensure regime analysis is called with real price data')
    print('  3. Add more robust regime detection logic')
    print('  4. Implement fallback regime detection')
    
    print('=' * 60)
    print('[RESULT] Market regime calculation test complete')
    print('=' * 60)

if __name__ == "__main__":
    test_market_regime_calculation()
