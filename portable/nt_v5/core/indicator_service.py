"""
Indicator Service - Technical indicators calculation
"""

import numpy as np
from decimal import Decimal
from typing import List, Dict, Optional, Tuple

class IndicatorService:
    """Technical indicators calculation service"""
    
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
    
    def calculate_sma(self, prices: List[float], period: int) -> List[float]:
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
    
    def calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """Calculate Exponential Moving Average"""
        try:
            if len(prices) < period:
                return []
            
            multiplier = 2 / (period + 1)
            ema = []
            
            # Start with SMA for first EMA value
            initial_sma = sum(prices[:period]) / period
            ema.append(initial_sma)
            
            # Calculate EMA for remaining values
            for i in range(period, len(prices)):
                current_ema = (prices[i] * multiplier) + (ema[-1] * (1 - multiplier))
                ema.append(current_ema)
            
            # Pad with None to maintain original length
            return [None] * (period - 1) + ema
            
        except Exception as e:
            self.log_error("ema_calculation", str(e))
            return []
    
    def calculate_recent_fractals(self, highs: List[float], lows: List[float], period: int = 5) -> Tuple[List[Optional[float]], List[Optional[float]]]:
        """Calculate recent fractals (high and low pivots)"""
        try:
            if len(highs) < period * 2 + 1 or len(lows) < period * 2 + 1:
                return [], []
            
            high_fractals = [None] * len(highs)
            low_fractals = [None] * len(lows)
            
            for i in range(period, len(highs) - period):
                # High fractal: center is highest in the window
                window_highs = highs[i-period:i+period+1]
                if highs[i] == max(window_highs):
                    high_fractals[i] = highs[i]
                
                # Low fractal: center is lowest in the window
                window_lows = lows[i-period:i+period+1]
                if lows[i] == min(window_lows):
                    low_fractals[i] = lows[i]
            
            return high_fractals, low_fractals
            
        except Exception as e:
            self.log_error("fractal_calculation", str(e))
            return [], []
    
    def calculate_heikin_ashi(self, opens: List[float], highs: List[float], 
                            lows: List[float], closes: List[float]) -> Dict[str, List[float]]:
        """Calculate Heikin Ashi candles"""
        try:
            if not (len(opens) == len(highs) == len(lows) == len(closes)):
                return {}
            
            ha_candles = {
                'open': [],
                'high': [],
                'low': [],
                'close': []
            }
            
            # First HA candle uses regular close
            ha_candles['close'].append((opens[0] + highs[0] + lows[0] + closes[0]) / 4)
            ha_candles['open'].append(closes[0])
            ha_candles['high'].append(highs[0])
            ha_candles['low'].append(lows[0])
            
            # Calculate remaining HA candles
            for i in range(1, len(closes)):
                ha_close = (opens[i] + highs[i] + lows[i] + closes[i]) / 4
                ha_open = (ha_candles['open'][i-1] + ha_candles['close'][i-1]) / 2
                ha_high = max(highs[i], ha_open, ha_close)
                ha_low = min(lows[i], ha_open, ha_close)
                
                ha_candles['open'].append(ha_open)
                ha_candles['high'].append(ha_high)
                ha_candles['low'].append(ha_low)
                ha_candles['close'].append(ha_close)
            
            return ha_candles
            
        except Exception as e:
            self.log_error("heikin_ashi_calculation", str(e))
            return {}
    
    def analyze_heikin_ashi(self, ha_candles: Dict[str, List[float]]) -> Dict[str, List[bool]]:
        """Analyze Heikin Ashi patterns"""
        try:
            if not ha_candles or 'open' not in ha_candles:
                return {}
            
            opens = ha_candles['open']
            highs = ha_candles['high']
            lows = ha_candles['low']
            closes = ha_candles['close']
            
            analysis = {
                'bullish': [],
                'bearish': [],
                'doji': [],
                'strong_bullish': [],
                'strong_bearish': []
            }
            
            for i in range(1, len(closes)):
                # Basic bullish/bearish
                bullish = closes[i] > opens[i]
                bearish = closes[i] < opens[i]
                
                # Doji (very small body)
                body_size = abs(closes[i] - opens[i])
                range_size = highs[i] - lows[i]
                doji = body_size < (range_size * 0.1)
                
                # Strong patterns (large body relative to range)
                strong_bullish = bullish and body_size > (range_size * 0.6)
                strong_bearish = bearish and body_size > (range_size * 0.6)
                
                analysis['bullish'].append(bullish)
                analysis['bearish'].append(bearish)
                analysis['doji'].append(doji)
                analysis['strong_bullish'].append(strong_bullish)
                analysis['strong_bearish'].append(strong_bearish)
            
            # Add None for first candle
            for key in analysis:
                analysis[key] = [None] + analysis[key]
            
            return analysis
            
        except Exception as e:
            self.log_error("ha_analysis", str(e))
            return {}
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """Calculate Relative Strength Index"""
        try:
            if len(prices) < period + 1:
                return []
            
            deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            gains = [delta if delta > 0 else 0 for delta in deltas]
            losses = [-delta if delta < 0 else 0 for delta in deltas]
            
            avg_gain = sum(gains[:period]) / period
            avg_loss = sum(losses[:period]) / period
            
            rsi = []
            
            for i in range(period, len(deltas)):
                if avg_loss == 0:
                    rsi.append(100)
                else:
                    rs = avg_gain / avg_loss
                    rsi.append(100 - (100 / (1 + rs)))
                
                # Update averages for next iteration
                avg_gain = (avg_gain * (period - 1) + gains[i]) / period
                avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            # Pad with None to maintain original length
            return [None] * period + rsi
            
        except Exception as e:
            self.log_error("rsi_calculation", str(e))
            return []
    
    def calculate_atr(self, highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> List[float]:
        """Calculate Average True Range"""
        try:
            if len(highs) < period + 1 or len(lows) < period + 1 or len(closes) < period + 1:
                return []
            
            true_ranges = []
            
            for i in range(1, len(closes)):
                tr1 = highs[i] - lows[i]
                tr2 = abs(highs[i] - closes[i-1])
                tr3 = abs(lows[i] - closes[i-1])
                true_ranges.append(max(tr1, tr2, tr3))
            
            atr = []
            avg_atr = sum(true_ranges[:period]) / period
            atr.append(avg_atr)
            
            for i in range(period, len(true_ranges)):
                avg_atr = (avg_atr * (period - 1) + true_ranges[i]) / period
                atr.append(avg_atr)
            
            # Pad with None to maintain original length
            return [None] * (period + 1) + atr
            
        except Exception as e:
            self.log_error("atr_calculation", str(e))
            return []
