"""
Signal Engine - Trading signal generation and candidate evaluation
"""

from typing import List, Dict, Optional, Tuple
from decimal import Decimal
import json

class SignalEngine:
    """Trading signal generation and evaluation"""
    
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
    
    def get_ma_trade_decision(self, ma_analysis: Dict[str, List[float]], 
                            current_price: float, index: int = -1) -> Dict[str, any]:
        """Make trade decision based on moving average analysis"""
        try:
            if not ma_analysis or index >= len(ma_analysis.get('fast_ma', [])):
                return {'signal': 'HOLD', 'confidence': 0.0, 'reason': 'Invalid MA data'}
            
            fast_ma = ma_analysis['fast_ma'][index]
            slow_ma = ma_analysis['slow_ma'][index]
            signal_ma = ma_analysis['signal_ma'][index]
            
            if fast_ma is None or slow_ma is None or signal_ma is None:
                return {'signal': 'HOLD', 'confidence': 0.0, 'reason': 'MA values not available'}
            
            # Price relative to MAs
            price_above_fast = current_price > fast_ma
            price_above_slow = current_price > slow_ma
            price_above_signal = current_price > signal_ma
            
            # MA alignment
            fast_above_slow = ma_analysis['fast_above_slow'][index] if index < len(ma_analysis.get('fast_above_slow', [])) else False
            fast_above_signal = ma_analysis['fast_above_signal'][index] if index < len(ma_analysis.get('fast_above_signal', [])) else False
            
            # MA trend
            ma_trend = ma_analysis['ma_trend'][index] if index < len(ma_analysis.get('ma_trend', [])) else False
            
            # Signal logic
            if price_above_fast and price_above_slow and fast_above_slow and ma_trend:
                signal = 'BUY'
                confidence = 0.8
                reason = 'Bullish MA alignment with uptrend'
            elif not price_above_fast and not price_above_slow and not fast_above_slow and not ma_trend:
                signal = 'SELL'
                confidence = 0.8
                reason = 'Bearish MA alignment with downtrend'
            elif price_above_fast and fast_above_slow and not price_above_slow:
                signal = 'BUY'
                confidence = 0.6
                reason = 'Price above fast MA, fast above slow MA'
            elif not price_above_fast and not fast_above_slow and price_above_slow:
                signal = 'SELL'
                confidence = 0.6
                reason = 'Price below fast MA, fast below slow MA'
            else:
                signal = 'HOLD'
                confidence = 0.3
                reason = 'Mixed MA signals'
            
            return {
                'signal': signal,
                'confidence': confidence,
                'reason': reason,
                'price_above_fast': price_above_fast,
                'price_above_slow': price_above_slow,
                'fast_above_slow': fast_above_slow,
                'ma_trend': ma_trend
            }
            
        except Exception as e:
            self.log_error("ma_decision", str(e))
            return {'signal': 'HOLD', 'confidence': 0.0, 'reason': f'Error: {str(e)}'}
    
    def generate_strategy_signal(self, market_data: Dict[str, any], 
                               indicators: Dict[str, any], 
                               regime: Dict[str, any],
                               strategy_config: Dict[str, any]) -> Dict[str, any]:
        """Generate comprehensive trading signal"""
        try:
            symbol = market_data.get('symbol', 'UNKNOWN')
            current_price = market_data.get('prices', {}).get('current', 0.0)
            
            # Extract indicator data
            ma_analysis = indicators.get('ma_analysis', {})
            ha_analysis = indicators.get('ha_analysis', {})
            fractals = indicators.get('fractals', {})
            rsi = indicators.get('rsi', [])
            atr = indicators.get('atr', [])
            
            # Get MA decision
            ma_decision = self.get_ma_trade_decision(ma_analysis, current_price)
            
            # Heikin Ashi analysis
            ha_signal = self._analyze_ha_signal(ha_analysis, -1)
            
            # Fractal analysis
            fractal_signal = self._analyze_fractal_signal(fractals, -1)
            
            # RSI analysis
            rsi_signal = self._analyze_rsi_signal(rsi, -1)
            
            # ATR for risk management
            current_atr = atr[-1] if atr and atr[-1] is not None else 0.0
            
            # Market regime filter
            market_regime = regime.get('regime', 'UNKNOWN')
            trend_strength = regime.get('trend_strength', 0.0)
            
            # Combine signals
            signals = {
                'ma': ma_decision,
                'ha': ha_signal,
                'fractal': fractal_signal,
                'rsi': rsi_signal
            }
            
            # Weighted signal combination
            signal_weights = strategy_config.get('signal_weights', {
                'ma': 0.4,
                'ha': 0.3,
                'fractal': 0.2,
                'rsi': 0.1
            })
            
            combined_signal = self._combine_signals(signals, signal_weights)
            
            # Apply regime filter
            if market_regime == 'RANGING' and combined_signal['confidence'] < 0.7:
                combined_signal['signal'] = 'HOLD'
                combined_signal['reason'] += ' | Filtered by ranging regime'
            
            # Add additional context
            combined_signal.update({
                'symbol': symbol,
                'current_price': current_price,
                'market_regime': market_regime,
                'trend_strength': trend_strength,
                'atr': current_atr,
                'timestamp': market_data.get('timestamp')
            })
            
            return combined_signal
            
        except Exception as e:
            self.log_error("signal_generation", str(e))
            return {
                'signal': 'HOLD',
                'confidence': 0.0,
                'reason': f'Error in signal generation: {str(e)}'
            }
    
    def score_trade_candidate(self, signal: Dict[str, any], 
                            market_data: Dict[str, any],
                            risk_config: Dict[str, any]) -> Dict[str, any]:
        """Score a trade candidate for selection"""
        try:
            base_score = signal.get('confidence', 0.0)
            signal_type = signal.get('symbol', 'UNKNOWN')
            
            # Risk-adjusted scoring
            trend_strength = signal.get('trend_strength', 0.0)
            volatility = market_data.get('volatility', 0.0)
            volume = market_data.get('volume', 0.0)
            
            # Adjust score based on trend strength
            trend_bonus = min(trend_strength / 50.0, 0.3)  # Max 0.3 bonus
            
            # Adjust score based on volatility (penalize extreme volatility)
            volatility_penalty = 0.0
            if volatility > 0.05:  # 5% volatility threshold
                volatility_penalty = min((volatility - 0.05) * 2, 0.2)
            
            # Volume bonus
            volume_bonus = 0.0
            if volume > risk_config.get('min_volume_threshold', 1000000):
                volume_bonus = 0.1
            
            # Final score
            final_score = base_score + trend_bonus - volatility_penalty + volume_bonus
            final_score = max(0.0, min(1.0, final_score))  # Clamp between 0 and 1
            
            return {
                'symbol': signal_type,
                'base_score': base_score,
                'trend_bonus': trend_bonus,
                'volatility_penalty': volatility_penalty,
                'volume_bonus': volume_bonus,
                'final_score': final_score,
                'recommendation': 'BUY' if signal.get('signal') == 'BUY' else 'SELL' if signal.get('signal') == 'SELL' else 'HOLD'
            }
            
        except Exception as e:
            self.log_error("candidate_scoring", str(e))
            return {
                'symbol': signal.get('symbol', 'UNKNOWN'),
                'final_score': 0.0,
                'recommendation': 'HOLD'
            }
    
    def select_candidate_symbols(self, candidates: List[Dict[str, any]], 
                             max_candidates: int = 5) -> List[Dict[str, any]]:
        """Select top candidates from scored list"""
        try:
            # Filter out HOLD signals
            valid_candidates = [c for c in candidates if c.get('recommendation') != 'HOLD']
            
            # Sort by final score
            valid_candidates.sort(key=lambda x: x.get('final_score', 0.0), reverse=True)
            
            # Return top candidates
            return valid_candidates[:max_candidates]
            
        except Exception as e:
            self.log_error("candidate_selection", str(e))
            return []
    
    def _analyze_ha_signal(self, ha_analysis: Dict[str, List[bool]], index: int = -1) -> Dict[str, any]:
        """Analyze Heikin Ashi signal"""
        try:
            if not ha_analysis or index >= len(ha_analysis.get('bullish', [])):
                return {'signal': 'HOLD', 'confidence': 0.0}
            
            bullish = ha_analysis.get('bullish', [])[index]
            strong_bullish = ha_analysis.get('strong_bullish', [])[index]
            strong_bearish = ha_analysis.get('strong_bearish', [])[index]
            doji = ha_analysis.get('doji', [])[index]
            
            if strong_bullish:
                return {'signal': 'BUY', 'confidence': 0.8}
            elif strong_bearish:
                return {'signal': 'SELL', 'confidence': 0.8}
            elif bullish and not doji:
                return {'signal': 'BUY', 'confidence': 0.6}
            elif not bullish and not doji:
                return {'signal': 'SELL', 'confidence': 0.6}
            else:
                return {'signal': 'HOLD', 'confidence': 0.3}
                
        except Exception as e:
            self.log_error("ha_signal_analysis", str(e))
            return {'signal': 'HOLD', 'confidence': 0.0}
    
    def _analyze_fractal_signal(self, fractals: Dict[str, List[float]], index: int = -1) -> Dict[str, any]:
        """Analyze fractal breakout signal"""
        try:
            if not fractals:
                return {'signal': 'HOLD', 'confidence': 0.0}
            
            high_fractals = fractals.get('high_fractals', [])
            low_fractals = fractals.get('low_fractals', [])
            
            # Check for recent fractal breakouts
            recent_high_fractal = None
            recent_low_fractal = None
            
            for i in range(max(0, index-5), index+1):
                if i < len(high_fractals) and high_fractals[i] is not None:
                    recent_high_fractal = high_fractals[i]
                if i < len(low_fractals) and low_fractals[i] is not None:
                    recent_low_fractal = low_fractals[i]
            
            if recent_high_fractal and recent_low_fractal:
                return {'signal': 'HOLD', 'confidence': 0.3}
            elif recent_high_fractal:
                return {'signal': 'BUY', 'confidence': 0.6}
            elif recent_low_fractal:
                return {'signal': 'SELL', 'confidence': 0.6}
            else:
                return {'signal': 'HOLD', 'confidence': 0.2}
                
        except Exception as e:
            self.log_error("fractal_signal_analysis", str(e))
            return {'signal': 'HOLD', 'confidence': 0.0}
    
    def _analyze_rsi_signal(self, rsi: List[float], index: int = -1) -> Dict[str, any]:
        """Analyze RSI signal"""
        try:
            if not rsi or index >= len(rsi) or rsi[index] is None:
                return {'signal': 'HOLD', 'confidence': 0.0}
            
            current_rsi = rsi[index]
            
            if current_rsi < 30:
                return {'signal': 'BUY', 'confidence': 0.7}
            elif current_rsi > 70:
                return {'signal': 'SELL', 'confidence': 0.7}
            elif 40 <= current_rsi <= 60:
                return {'signal': 'HOLD', 'confidence': 0.5}
            else:
                return {'signal': 'HOLD', 'confidence': 0.3}
                
        except Exception as e:
            self.log_error("rsi_signal_analysis", str(e))
            return {'signal': 'HOLD', 'confidence': 0.0}
    
    def _combine_signals(self, signals: Dict[str, Dict[str, any]], 
                        weights: Dict[str, float]) -> Dict[str, any]:
        """Combine multiple signals with weights"""
        try:
            buy_votes = 0.0
            sell_votes = 0.0
            total_weight = 0.0
            
            for signal_type, signal_data in signals.items():
                weight = weights.get(signal_type, 0.0)
                confidence = signal_data.get('confidence', 0.0)
                signal = signal_data.get('signal', 'HOLD')
                
                if signal == 'BUY':
                    buy_votes += weight * confidence
                elif signal == 'SELL':
                    sell_votes += weight * confidence
                
                total_weight += weight
            
            if total_weight == 0:
                return {'signal': 'HOLD', 'confidence': 0.0, 'reason': 'No valid signals'}
            
            # Normalize votes
            buy_strength = buy_votes / total_weight
            sell_strength = sell_votes / total_weight
            
            # Determine final signal
            if buy_strength > sell_strength and buy_strength > 0.5:
                final_signal = 'BUY'
                confidence = buy_strength
                reason = f'Bullish consensus ({buy_strength:.2f})'
            elif sell_strength > buy_strength and sell_strength > 0.5:
                final_signal = 'SELL'
                confidence = sell_strength
                reason = f'Bearish consensus ({sell_strength:.2f})'
            else:
                final_signal = 'HOLD'
                confidence = max(buy_strength, sell_strength)
                reason = f'No clear consensus (BUY: {buy_strength:.2f}, SELL: {sell_strength:.2f})'
            
            return {
                'signal': final_signal,
                'confidence': confidence,
                'reason': reason,
                'buy_strength': buy_strength,
                'sell_strength': sell_strength
            }
            
        except Exception as e:
            self.log_error("signal_combination", str(e))
            return {'signal': 'HOLD', 'confidence': 0.0, 'reason': f'Error: {str(e)}'}
