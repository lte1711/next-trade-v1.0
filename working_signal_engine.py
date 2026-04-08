"""
Working Signal Engine - Simplified but functional signal generation
"""

import logging
from typing import Dict, Any

class WorkingSignalEngine:
    """Working signal engine with simplified logic"""
    
    def __init__(self, log_error=None):
        self.logger = logging.getLogger(__name__)
        self.log_error = log_error or self._default_log_error
    
    def _default_log_error(self, error_type: str, message: str):
        """Default error logging"""
        self.logger.error(f"[{error_type}] {message}")
    
    def generate_strategy_signal(self, market_data: Dict[str, Any], indicators: Dict[str, Any], 
                               regime: Dict[str, Any], strategy_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate working trading signals"""
        try:
            # Extract basic data
            current_price = indicators.get('price', 0)
            volume = indicators.get('volume', 0)
            
            # Calculate basic indicators if not provided
            if 'sma_10' not in indicators:
                # Try to get from market data
                klines = market_data.get('klines', {}).get('1h', [])
                if klines and len(klines) >= 10:
                    closes = [k['close'] for k in klines[-10:]]
                    indicators['sma_10'] = sum(closes) / len(closes)
                else:
                    indicators['sma_10'] = current_price
            
            sma_10 = indicators.get('sma_10', current_price)
            
            # Get strategy-specific settings
            entry_filters = strategy_config.get('entry_filters', {})
            min_confidence = entry_filters.get('min_confidence', 0.3)
            
            # Basic signal logic
            signal = 'HOLD'
            confidence = 0.0
            reason = 'No clear signal'
            
            if current_price > 0 and sma_10 > 0:
                price_above_sma = current_price > sma_10
                price_below_sma = current_price < sma_10
                volume_ok = volume > 1000
                
                # Calculate price deviation from SMA
                price_deviation = (current_price - sma_10) / sma_10 if sma_10 > 0 else 0
                
                # Determine signal based on conditions
                if price_above_sma and volume_ok and abs(price_deviation) > 0.001:
                    signal = 'BUY'
                    confidence = min(0.8, 0.3 + abs(price_deviation) * 10)
                    reason = f'Price {price_deviation:+.2%} above SMA with volume'
                elif price_below_sma and volume_ok and abs(price_deviation) > 0.001:
                    signal = 'SELL'
                    confidence = min(0.8, 0.3 + abs(price_deviation) * 10)
                    reason = f'Price {price_deviation:+.2%} below SMA with volume'
                else:
                    signal = 'HOLD'
                    confidence = 0.0
                    reason = 'Price too close to SMA or low volume'
            
            # Apply confidence threshold
            if confidence < min_confidence:
                signal = 'HOLD'
                confidence = 0.0
                reason = f'Confidence {confidence:.2f} below threshold {min_confidence}'
            
            return {
                'signal': signal,
                'confidence': confidence,
                'reason': reason,
                'indicators_used': ['price', 'sma_10', 'volume'],
                'price_deviation': price_deviation,
                'strategy': strategy_config.get('name', 'unknown')
            }
            
        except Exception as e:
            self.log_error("signal_generation", str(e))
            return {
                'signal': 'HOLD',
                'confidence': 0.0,
                'reason': f'Error: {e}',
                'indicators_used': [],
                'strategy': strategy_config.get('name', 'unknown')
            }
