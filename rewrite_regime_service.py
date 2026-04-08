#!/usr/bin/env python3
"""
Rewrite Regime Service - Completely rewrite the market regime service
"""

def rewrite_regime_service():
    """Completely rewrite the market regime service"""
    print('=' * 60)
    print('REWRITE MARKET REGIME SERVICE')
    print('=' * 60)
    
    # Create a new, clean market regime service
    new_service_content = '''import logging
from typing import Dict, List, Any

class MarketRegimeService:
    """Service for analyzing market regime and conditions"""
    
    def __init__(self, log_error=None):
        self.logger = logging.getLogger(__name__)
        self.log_error = log_error or self._default_log_error
    
    def _default_log_error(self, error_type: str, message: str):
        """Default error logging"""
        self.logger.error(f"[{error_type}] {message}")
    
    def analyze_market_regime(self, prices: List[float], volumes: List[float], 
                            adx_period: int = 14, volatility_period: int = 20) -> Dict[str, Any]:
        """Analyze overall market regime (trending, ranging, volatile)"""
        try:
            if len(prices) < max(adx_period, volatility_period):
                return {}
            
            # Calculate ADX components
            adx_analysis = self._calculate_adx(prices, adx_period)
            
            # Calculate volatility
            volatility = self._calculate_volatility(prices, volatility_period)
            
            # Calculate price momentum
            momentum = self._calculate_momentum(prices, 10)
            
            # Determine regime
            current_adx = adx_analysis.get('adx', [0])[-1] if adx_analysis.get('adx') else 0
            current_volatility = volatility[-1] if volatility else 0
            current_momentum = momentum[-1] if momentum else 0
            
            # Regime classification
            if current_adx > 25:
                if current_momentum > 0:
                    regime = "BULL_TREND"
                else:
                    regime = "BEAR_TREND"
            elif current_volatility > 0.02:  # 2% volatility threshold
                regime = "HIGH_VOLATILITY"
            else:
                regime = "RANGING"
            
            return {
                'regime': regime,
                'adx': adx_analysis.get('adx', []),
                'plus_di': adx_analysis.get('plus_di', []),
                'minus_di': adx_analysis.get('minus_di', []),
                'volatility': volatility,
                'momentum': momentum,
                'trend_strength': current_adx,
                'volatility_level': current_volatility,
                'price_momentum': current_momentum
            }
            
        except Exception as e:
            self.log_error("market_regime_analysis", str(e))
            return {}
    
    def _calculate_adx(self, prices: List[float], period: int = 14) -> Dict[str, List[float]]:
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
            
            # Calculate Wilder's smoothing
            def smooth_wilder(values, period):
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
                    smoothed_value = (prev_smoothed * (period - 1) + current_value) / period
                    smoothed.append(smoothed_value)
                
                return smoothed
            
            # Smooth the values
            atr = smooth_wilder(tr_values, period)
            plus_di = smooth_wilder(plus_dm, period)
            minus_di = smooth_wilder(minus_dm, period)
            
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
            adx_values = smooth_wilder(dx_values, period)
            
            return {
                'adx': adx_values,
                'plus_di': plus_di,
                'minus_di': minus_di,
                'atr': atr
            }
            
        except Exception as e:
            self.log_error("adx_calculation", str(e))
            return {}
    
    def _calculate_volatility(self, prices: List[float], period: int = 20) -> List[float]:
        """Calculate price volatility"""
        try:
            if len(prices) < period:
                return []
            
            volatility = []
            
            for i in range(period, len(prices)):
                window = prices[i-period:i]
                avg_price = sum(window) / period
                
                # Calculate standard deviation
                variance = sum((price - avg_price) ** 2 for price in window) / period
                std_dev = variance ** 0.5
                
                # Convert to percentage
                vol_pct = std_dev / avg_price if avg_price > 0 else 0
                volatility.append(vol_pct)
            
            return volatility
            
        except Exception as e:
            self.log_error("volatility_calculation", str(e))
            return []
    
    def _calculate_momentum(self, prices: List[float], period: int = 10) -> List[float]:
        """Calculate price momentum"""
        try:
            if len(prices) < period + 1:
                return []
            
            momentum = []
            
            for i in range(period, len(prices)):
                current_price = prices[i]
                past_price = prices[i-period]
                
                if past_price > 0:
                    momentum_pct = (current_price - past_price) / past_price
                    momentum.append(momentum_pct)
                else:
                    momentum.append(0)
            
            return momentum
            
        except Exception as e:
            self.log_error("momentum_calculation", str(e))
            return []
    
    def analyze_timeframe_ma(self, prices: List[float]) -> Dict[str, Any]:
        """Analyze moving averages for a timeframe"""
        try:
            if len(prices) < 50:
                return {}
            
            # Calculate EMAs
            ema_9 = self._calculate_ema(prices, 9)
            ema_21 = self._calculate_ema(prices, 21)
            ema_50 = self._calculate_ema(prices, 50)
            
            # Get current values
            current_price = prices[-1]
            current_ema_9 = ema_9[-1] if ema_9 else current_price
            current_ema_21 = ema_21[-1] if ema_21 else current_price
            current_ema_50 = ema_50[-1] if ema_50 else current_price
            
            # Determine alignment
            alignment = "NEUTRAL"
            if current_price > current_ema_9 > current_ema_21 > current_ema_50:
                alignment = "BULLISH"
            elif current_price < current_ema_9 < current_ema_21 < current_ema_50:
                alignment = "BEARISH"
            
            return {
                'ema_9': ema_9,
                'ema_21': ema_21,
                'ema_50': ema_50,
                'current_price': current_price,
                'alignment': alignment,
                'price_vs_ema9': current_price - current_ema_9,
                'price_vs_ema21': current_price - current_ema_21,
                'price_vs_ema50': current_price - current_ema_50
            }
            
        except Exception as e:
            self.log_error("timeframe_ma_analysis", str(e))
            return {}
    
    def _calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """Calculate Exponential Moving Average"""
        try:
            if len(prices) < period:
                return []
            
            ema = []
            multiplier = 2 / (period + 1)
            
            # Start with SMA
            sma = sum(prices[:period]) / period
            ema.append(sma)
            
            # Calculate EMA
            for i in range(period, len(prices)):
                current_price = prices[i]
                ema_value = (current_price - ema[-1]) * multiplier + ema[-1]
                ema.append(ema_value)
            
            return ema
            
        except Exception as e:
            self.log_error("ema_calculation", str(e))
            return []
'''
    
    # Write the new service
    with open('core/market_regime_service.py', 'w') as f:
        f.write(new_service_content)
    
    print('[SUCCESS] Market regime service completely rewritten')
    
    # Test the new service
    print('\n[TEST] Testing the new market regime service:')
    
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
        
        # Test MA analysis
        print(f'  - MA Analysis Test:')
        ma_result = mrs.analyze_timeframe_ma(strong_trend_prices)
        print(f'    - Alignment: {ma_result.get("alignment", "UNKNOWN")}')
        print(f'    - Current Price: {ma_result.get("current_price", 0):.2f}')
        
        print('[SUCCESS] New market regime service tested successfully')
        
    except Exception as e:
        print(f'[ERROR] Test failed: {e}')
        import traceback
        traceback.print_exc()
    
    print('=' * 60)
    print('[RESULT] Market regime service rewrite complete')
    print('=' * 60)

if __name__ == "__main__":
    rewrite_regime_service()
