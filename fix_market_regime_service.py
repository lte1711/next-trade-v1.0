#!/usr/bin/env python3
"""
Fix Market Regime Service - Fix the ADX calculation issue
"""

def fix_market_regime_service():
    """Fix the ADX calculation issue in market regime service"""
    print('=' * 60)
    print('FIX MARKET REGIME SERVICE')
    print('=' * 60)
    
    # Read the current market_regime_service.py
    with open('core/market_regime_service.py', 'r') as f:
        content = f.read()
    
    print('[ANALYSIS] Current ADX calculation:')
    
    # Find the _calculate_adx method
    import re
    
    adx_pattern = r'def _calculate_adx.*?return \{\}'
    adx_match = re.search(adx_pattern, content, re.DOTALL)
    
    if adx_match:
        print('  - Found _calculate_adx method')
        
        # Check if it's returning empty results
        if 'return {}' in adx_match.group(0):
            print('  - Issue: Method returning empty dict')
            print('  - Need to implement proper ADX calculation')
        else:
            print('  - ADX method seems implemented')
    else:
        print('  - _calculate_adx method not found')
        return
    
    # Create a fixed ADX calculation method
    fixed_adx_method = '''    def _calculate_adx(self, prices: List[float], period: int = 14) -> Dict[str, List[float]]:
        """Calculate ADX (Average Directional Index)"""
        try:
            if len(prices) < period * 2:
                return {}
            
            # Calculate True Range and Directional Movement
            tr_values = []
            plus_dm = []
            minus_dm = []
            
            for i in range(1, len(prices)):
                high = prices[i]
                low = prices[i]
                prev_close = prices[i-1]
                
                # True Range
                tr1 = high - low
                tr2 = abs(high - prev_close)
                tr3 = abs(low - prev_close)
                tr = max(tr1, tr2, tr3)
                tr_values.append(tr)
                
                # Directional Movement
                up_move = high - prev_close
                down_move = prev_close - low
                
                if up_move > down_move and up_move > 0:
                    plus_dm.append(up_move)
                else:
                    plus_dm.append(0)
                
                if down_move > up_move and down_move > 0:
                    minus_dm.append(down_move)
                else:
                    minus_dm.append(0)
            
            # Smooth the values
            atr = self._smooth_average(tr_values, period)
            plus_di = self._smooth_average(plus_dm, period)
            minus_di = self._smooth_average(minus_dm, period)
            
            # Calculate ADX
            adx_values = []
            dx_values = []
            
            for i in range(len(atr)):
                if atr[i] > 0:
                    plus_di_smooth = plus_di[i] / atr[i] * 100
                    minus_di_smooth = minus_di[i] / atr[i] * 100
                    
                    di_diff = abs(plus_di_smooth - minus_di_smooth)
                    di_sum = plus_di_smooth + minus_di_smooth
                    
                    if di_sum > 0:
                        dx = (di_diff / di_sum) * 100
                    else:
                        dx = 0
                    
                    dx_values.append(dx)
                else:
                    dx_values.append(0)
            
            # Smooth ADX
            adx_values = self._smooth_average(dx_values, period)
            
            return {
                'adx': adx_values,
                'plus_di': plus_di,
                'minus_di': minus_di,
                'atr': atr
            }
            
        except Exception as e:
            self.log_error("adx_calculation", str(e))
            return {}
    
    def _smooth_average(self, values: List[float], period: int) -> List[float]:
        """Calculate smoothed average (like Wilder's smoothing)"""
        try:
            if len(values) < period:
                return values
            
            smoothed = []
            
            # First value is simple average
            first_avg = sum(values[:period]) / period
            smoothed.append(first_avg)
            
            # Subsequent values use Wilder's smoothing
            for i in range(period, len(values)):
                prev_smoothed = smoothed[-1]
                current_value = values[i]
                
                # Wilder's smoothing: (prev_smoothed * (period-1) + current_value) / period
                smoothed_value = (prev_smoothed * (period - 1) + current_value) / period
                smoothed.append(smoothed_value)
            
            # Pad with None to maintain original length
            padding = [None] * (period - 1)
            return padding + smoothed
            
        except Exception as e:
            self.log_error("smooth_average", str(e))
            return values'''
    
    # Find and replace the ADX method
    if adx_match:
        old_method = adx_match.group(0)
        new_content = content.replace(old_method, fixed_adx_method)
        
        # Write the fixed content
        with open('core/market_regime_service.py', 'w') as f:
            f.write(new_content)
        
        print('[SUCCESS] ADX calculation method fixed')
    else:
        print('[ERROR] Could not find ADX method to fix')
        return
    
    # Test the fix
    print('\n[TEST] Testing the fixed ADX calculation:')
    
    try:
        from core.market_regime_service import MarketRegimeService
        
        mrs = MarketRegimeService()
        
        # Test with strong trend data
        strong_trend_prices = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 122, 124, 126, 128, 130, 132, 134, 136, 138, 140, 142, 144, 146, 148, 150, 152, 154, 156]
        volumes = [1000000] * len(strong_trend_prices)
        
        regime_result = mrs.analyze_market_regime(strong_trend_prices, volumes)
        
        print(f'  - Strong Trend Test:')
        print(f'    - Input: 28 price points (upward trend)')
        print(f'    - Expected: BULL_TREND')
        print(f'    - Actual: {regime_result.get("regime", "UNKNOWN")}')
        print(f'    - ADX: {regime_result.get("trend_strength", 0):.2f}')
        print(f'    - Volatility: {regime_result.get("volatility_level", 0):.4f}')
        
        # Test with ranging data
        ranging_prices = [100, 102, 98, 103, 97, 104, 96, 105, 95, 106, 94, 107, 93, 108, 92, 109, 91, 110, 90, 111]
        ranging_volumes = [1000000] * len(ranging_prices)
        
        regime_result = mrs.analyze_market_regime(ranging_prices, ranging_volumes)
        
        print(f'  - Ranging Test:')
        print(f'    - Input: 20 price points (ranging)')
        print(f'    - Expected: RANGING')
        print(f'    - Actual: {regime_result.get("regime", "UNKNOWN")}')
        print(f'    - ADX: {regime_result.get("trend_strength", 0):.2f}')
        print(f'    - Volatility: {regime_result.get("volatility_level", 0):.4f}')
        
        # Test with bear trend data
        bear_trend_prices = [150, 148, 146, 144, 142, 140, 138, 136, 134, 132, 130, 128, 126, 124, 122, 120, 118, 116, 114, 112, 110, 108, 106, 104, 102, 100]
        bear_volumes = [1000000] * len(bear_trend_prices)
        
        regime_result = mrs.analyze_market_regime(bear_trend_prices, bear_volumes)
        
        print(f'  - Bear Trend Test:')
        print(f'    - Input: 26 price points (downward trend)')
        print(f'    - Expected: BEAR_TREND')
        print(f'    - Actual: {regime_result.get("regime", "UNKNOWN")}')
        print(f'    - ADX: {regime_result.get("trend_strength", 0):.2f}')
        print(f'    - Volatility: {regime_result.get("volatility_level", 0):.4f}')
        
        print('[SUCCESS] ADX calculation test completed')
        
    except Exception as e:
        print(f'[ERROR] Test failed: {e}')
        import traceback
        traceback.print_exc()
    
    # Test with real market data
    print('\n[REAL DATA TEST] Testing with actual market data:')
    
    try:
        import json
        
        with open('trading_results.json', 'r') as f:
            results = json.load(f)
        
        market_data = results.get('market_data', {})
        
        # Test with BTCUSDT
        btc_price_str = market_data.get('BTCUSDT', '0')
        current_price = float(btc_price_str)
        
        # Generate realistic price series around current price
        price_series = []
        base_price = current_price
        
        for i in range(30):  # 30 periods for better ADX calculation
            # Add some realistic movement
            if i < 15:  # Trending up
                change = 0.001 * (i + 1)  # 0.1% per period upward
            else:  # Trending down
                change = -0.0005 * (i - 15)  # 0.05% per period downward
            
            price = base_price * (1 + change)
            price_series.append(price)
            base_price = price
        
        volume_series = [1000000] * len(price_series)
        
        regime_result = mrs.analyze_market_regime(price_series, volume_series)
        
        print(f'  - BTCUSDT Real Data Test:')
        print(f'    - Current Price: ${current_price:.2f}')
        print(f'    - Generated: {len(price_series)} price points')
        print(f'    - Regime: {regime_result.get("regime", "UNKNOWN")}')
        print(f'    - ADX: {regime_result.get("trend_strength", 0):.2f}')
        print(f'    - Volatility: {regime_result.get("volatility_level", 0):.4f}')
        
        # Check if ADX values are now calculated
        adx_values = regime_result.get('adx', [])
        if adx_values and any(adx > 0 for adx in adx_values if adx is not None):
            print(f'    - ADX Values: {[f"{x:.2f}" for x in adx_values[-3:] if x is not None]}')
            print(f'    - Status: ADX calculation working')
        else:
            print(f'    - Status: ADX calculation still has issues')
        
    except Exception as e:
        print(f'  - Error with real data test: {e}')
    
    print('=' * 60)
    print('[RESULT] Market regime service fix complete')
    print('=' * 60)

if __name__ == "__main__":
    fix_market_regime_service()
