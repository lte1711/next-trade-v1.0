"""
Market Regime Service - Market state analysis and regime detection
"""

from typing import List, Dict, Optional, Tuple
from decimal import Decimal

class MarketRegimeService:
    """Market regime analysis and trend detection"""
    
    def __init__(self, log_error_callback=None):
        self.log_error = log_error_callback or self._default_log_error
    
    def _default_log_error(self, error_type, message):
        """Default error logging"""
        print(f"[ERROR] {error_type}: {message}")
    
    def safe_float_conversion(self, value, default=0.0):
        """Safely convert to float"""
        try:
            if value is None:
                return default
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def analyze_timeframe_ma(self, prices: List[float], fast_period: int = 20, 
                           slow_period: int = 50, signal_period: int = 10) -> Dict[str, List[float]]:
        """Analyze moving averages across timeframes"""
        try:
            if len(prices) < slow_period:
                return {}
            
            # Calculate MAs
            fast_ma = self._calculate_sma(prices, fast_period)
            slow_ma = self._calculate_sma(prices, slow_period)
            signal_ma = self._calculate_sma(prices, signal_period)
            
            # Calculate MA relationships
            ma_analysis = {
                'fast_ma': fast_ma,
                'slow_ma': slow_ma,
                'signal_ma': signal_ma,
                'fast_above_slow': [],
                'fast_above_signal': [],
                'slow_above_signal': [],
                'ma_spread': [],
                'ma_trend': []
            }
            
            for i in range(len(prices)):
                fast_val = fast_ma[i] if i < len(fast_ma) else None
                slow_val = slow_ma[i] if i < len(slow_ma) else None
                signal_val = signal_ma[i] if i < len(signal_ma) else None
                
                if fast_val is not None and slow_val is not None:
                    ma_analysis['fast_above_slow'].append(fast_val > slow_val)
                    ma_analysis['ma_spread'].append(fast_val - slow_val)
                else:
                    ma_analysis['fast_above_slow'].append(None)
                    ma_analysis['ma_spread'].append(None)
                
                if fast_val is not None and signal_val is not None:
                    ma_analysis['fast_above_signal'].append(fast_val > signal_val)
                else:
                    ma_analysis['fast_above_signal'].append(None)
                
                if slow_val is not None and signal_val is not None:
                    ma_analysis['slow_above_signal'].append(slow_val > signal_val)
                else:
                    ma_analysis['slow_above_signal'].append(None)
                
                # MA trend (based on fast MA direction)
                if i > 0 and fast_val is not None and fast_ma[i-1] is not None:
                    ma_analysis['ma_trend'].append(fast_val > fast_ma[i-1])
                else:
                    ma_analysis['ma_trend'].append(None)
            
            return ma_analysis
            
        except Exception as e:
            self.log_error("timeframe_ma_analysis", str(e))
            return {}
    
    def analyze_market_regime(self, prices: List[float], volumes: List[float], 
                            adx_period: int = 14, volatility_period: int = 20) -> Dict[str, any]:
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
    
    def _calculate_sma(self, prices: List[float], period: int) -> List[float]:
        """Calculate Simple Moving Average"""
        try:
            if len(prices) < period:
                return []
            
            sma = []
            for i in range(len(prices) - period + 1):
                avg = sum(prices[i:i+period]) / period
                sma.append(avg)
            
            # Pad with None to maintain original length
            return [None] * (period - 1) + sma
            
        except Exception as e:
            self.log_error("sma_calculation", str(e))
            return []
    
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
                high = prices[i] * 1.001  # Approximate high (since we only have close prices)
                low = prices[i] * 0.999   # Approximate low
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
            
            # Calculate ADX components
            plus_di = []
            minus_di = []
            adx = []
            
            # Initial smoothing
            avg_tr = sum(tr_values[:period]) / period
            avg_plus_dm = sum(plus_dm[:period]) / period
            avg_minus_dm = sum(minus_dm[:period]) / period
            
            for i in range(period, len(tr_values)):
                # Calculate DI
                if avg_tr > 0:
                    plus_di_val = (avg_plus_dm / avg_tr) * 100
                    minus_di_val = (avg_minus_dm / avg_tr) * 100
                else:
                    plus_di_val = 0
                    minus_di_val = 0
                
                plus_di.append(plus_di_val)
                minus_di.append(minus_di_val)
                
                # Calculate DX
                di_sum = plus_di_val + minus_di_val
                if di_sum > 0:
                    dx = abs(plus_di_val - minus_di_val) / di_sum * 100
                else:
                    dx = 0
                
                # Smooth ADX
                if not adx:
                    adx.append(dx)
                else:
                    adx.append((adx[-1] * (period - 1) + dx) / period)
                
                # Update averages for next iteration
                avg_tr = (avg_tr * (period - 1) + tr_values[i]) / period
                avg_plus_dm = (avg_plus_dm * (period - 1) + plus_dm[i]) / period
                avg_minus_dm = (avg_minus_dm * (period - 1) + minus_dm[i]) / period
            
            return {
                'adx': adx,
                'plus_di': plus_di,
                'minus_di': minus_di
            }
            
        except Exception as e:
            self.log_error("adx_calculation", str(e))
            return {}
    
    def _calculate_volatility(self, prices: List[float], period: int = 20) -> List[float]:
        """Calculate price volatility (standard deviation of returns)"""
        try:
            if len(prices) < period + 1:
                return []
            
            returns = []
            for i in range(1, len(prices)):
                ret = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(ret)
            
            volatility = []
            for i in range(period, len(returns)):
                window_returns = returns[i-period:i]
                mean_return = sum(window_returns) / period
                variance = sum((r - mean_return) ** 2 for r in window_returns) / period
                vol = variance ** 0.5
                volatility.append(vol)
            
            # Pad with None to maintain original length
            return [None] * (period + 1) + volatility
            
        except Exception as e:
            self.log_error("volatility_calculation", str(e))
            return []
    
    def _calculate_momentum(self, prices: List[float], period: int = 10) -> List[float]:
        """Calculate price momentum"""
        try:
            if len(prices) <= period:
                return []
            
            momentum = []
            for i in range(period, len(prices)):
                mom = (prices[i] - prices[i-period]) / prices[i-period]
                momentum.append(mom)
            
            # Pad with None to maintain original length
            return [None] * period + momentum
            
        except Exception as e:
            self.log_error("momentum_calculation", str(e))
            return []
