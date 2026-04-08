"""
Enhanced Signal Engine - With minimal hardcoded thresholds
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

class SignalEngine:
    """Enhanced signal engine with minimal thresholds"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.minimal_thresholds = {
            'min_confidence': 0.1,  # Very low threshold
            'min_trend_strength': 1.0,  # Very low threshold
            'max_volatility': 1.0,  # Very high tolerance
            'required_alignment_count': 0,  # No alignment required
            'consensus_threshold': 0  # No consensus required
        }
    
    def generate_strategy_signal(self, market_data: Dict[str, Any], 
                               indicators: Dict[str, Any], 
                               regime: Dict[str, Any], 
                               strategy_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate strategy signal with minimal thresholds"""
        try:
            # Use minimal thresholds instead of strategy config
            entry_filters = self.minimal_thresholds
            
            # Get basic indicators
            current_price = indicators.get('price', 0)
            volume = indicators.get('volume', 0)
            sma_10 = indicators.get('sma_10', 0)
            
            # Simple signal logic with minimal thresholds
            signal = 'HOLD'
            confidence = 0.0
            reason = 'No signal conditions met'
            
            # Very simple BUY signal logic
            if current_price > 0 and sma_10 > 0:
                price_vs_sma = (current_price - sma_10) / sma_10
                
                # BUY if price is above SMA (even by 0.1%)
                if price_vs_sma > 0.001:  # 0.1% above SMA
                    signal = 'BUY'
                    confidence = 0.5  # Fixed confidence
                    reason = f'Price {price_vs_sma*100:.2f}% above SMA with volume'
                
                # SELL if price is below SMA (even by 0.1%)
                elif price_vs_sma < -0.001:  # 0.1% below SMA
                    signal = 'SELL'
                    confidence = 0.5  # Fixed confidence
                    reason = f'Price {price_vs_sma*100:.2f}% below SMA with volume'
            
            # Volume check (very relaxed)
            if volume > 0 and signal != 'HOLD':
                confidence = min(0.8, confidence + 0.1)  # Boost confidence slightly
                reason += ' and volume present'
            
            # Ensure minimum confidence is met (very low threshold)
            if confidence >= self.minimal_thresholds['min_confidence']:
                return {
                    'signal': signal,
                    'confidence': confidence,
                    'reason': reason,
                    'timestamp': datetime.now().isoformat(),
                    'indicators': indicators,
                    'regime': regime
                }
            else:
                return {
                    'signal': 'HOLD',
                    'confidence': 0.0,
                    'reason': 'Confidence below minimal threshold',
                    'timestamp': datetime.now().isoformat(),
                    'indicators': indicators,
                    'regime': regime
                }
        
        except Exception as e:
            self.logger.error(f"Signal generation error: {e}")
            return {
                'signal': 'HOLD',
                'confidence': 0.0,
                'reason': f'Error in signal generation: {str(e)}',
                'timestamp': datetime.now().isoformat(),
                'indicators': indicators,
                'regime': regime
            }
    
    def generate_signals(self, market_data: Dict[str, Any], 
                        strategies: List[str]) -> Dict[str, Any]:
        """Generate signals for multiple strategies"""
        try:
            signals = {}
            
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
                    
                    symbol_signals = {}
                    
                    for strategy_name in strategies:
                        signal_result = self.generate_strategy_signal(
                            market_data_dict, indicators, regime, {}
                        )
                        
                        if signal_result['signal'] != 'HOLD':
                            symbol_signals[strategy_name] = signal_result
                    
                    if symbol_signals:
                        signals[symbol] = symbol_signals
            
            return {
                'signals': signals,
                'timestamp': datetime.now().isoformat(),
                'total_signals': len(signals)
            }
        
        except Exception as e:
            self.logger.error(f"Multi-strategy signal generation error: {e}")
            return {
                'signals': {},
                'timestamp': datetime.now().isoformat(),
                'total_signals': 0,
                'error': str(e)
            }
    
    def get_signal_statistics(self) -> Dict[str, Any]:
        """Get signal generation statistics"""
        return {
            'minimal_thresholds': self.minimal_thresholds,
            'engine_type': 'ENHANCED_WITH_MINIMAL_THRESHOLDS',
            'timestamp': datetime.now().isoformat()
        }
