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
        """Generate a strategy-specific signal."""
        try:
            current_price = indicators.get('price', 0)
            volume = indicators.get('volume', 0)
            sma_10 = indicators.get('sma_10', 0)
            volume_ratio = float(indicators.get('volume_ratio', 1.0) or 1.0)
            trend_strength = float(regime.get('trend_strength', 0.0) or 0.0)
            volatility_level = float(regime.get('volatility_level', 0.0) or 0.0)
            market_regime = regime.get('regime', 'UNKNOWN')
            strategy_name = strategy_config.get('name', 'ma_trend_follow')

            signal = 'HOLD'
            confidence = 0.0
            reason = 'No signal conditions met'

            if strategy_name == 'ema_crossover':
                signal, confidence, reason = self._generate_ema_crossover_signal(
                    current_price,
                    indicators,
                    volume_ratio,
                    trend_strength,
                    volatility_level,
                    market_regime
                )
            elif current_price > 0 and sma_10 > 0:
                price_vs_sma = (current_price - sma_10) / sma_10

                if price_vs_sma > 0.001:  # 0.1% above SMA
                    signal = 'BUY'
                    confidence = self._calculate_dynamic_confidence(
                        signal, price_vs_sma, volume_ratio, trend_strength, volatility_level, market_regime
                    )
                    reason = f'MA trend: price {price_vs_sma*100:.2f}% above SMA10'
                elif price_vs_sma < -0.001:  # 0.1% below SMA
                    signal = 'SELL'
                    confidence = self._calculate_dynamic_confidence(
                        signal, price_vs_sma, volume_ratio, trend_strength, volatility_level, market_regime
                    )
                    reason = f'MA trend: price {price_vs_sma*100:.2f}% below SMA10'
            else:
                missing_inputs = []
                if current_price <= 0:
                    missing_inputs.append('price')
                if sma_10 <= 0:
                    missing_inputs.append('sma_10')
                reason = f"Missing baseline inputs: {', '.join(missing_inputs)}"

            if volume > 0 and signal != 'HOLD':
                reason += ' and volume present'

            if signal != 'HOLD':
                mtf_adjustment = self._multi_timeframe_alignment_adjustment(
                    signal,
                    indicators.get('multi_timeframe_market', {}) or {}
                )
                confidence = round(max(0.0, min(confidence + mtf_adjustment, 0.95)), 4)
                if mtf_adjustment:
                    reason += f' | MTF adjustment {mtf_adjustment:+.2f}'

            if confidence >= self.minimal_thresholds['min_confidence']:
                return {
                    'signal': signal,
                    'confidence': confidence,
                    'reason': reason,
                    'timestamp': datetime.now().isoformat(),
                    'indicators': indicators,
                    'regime': regime,
                    'strategy_model': strategy_name,
                    'buy_strength': confidence if signal == 'BUY' else 0.0,
                    'sell_strength': confidence if signal == 'SELL' else 0.0,
                    'volume_ratio': round(volume_ratio, 4),
                    'market_alignment': self._market_alignment_score(signal, market_regime),
                    'multi_timeframe_adjustment': mtf_adjustment if signal != 'HOLD' else 0.0,
                    'volatility_penalty': self._volatility_penalty(volatility_level)
                }
            else:
                return {
                    'signal': 'HOLD',
                    'confidence': 0.0,
                    'reason': reason if reason else 'Confidence below minimal threshold',
                    'timestamp': datetime.now().isoformat(),
                    'strategy_model': strategy_name,
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

    def _generate_ema_crossover_signal(self, current_price: float, indicators: Dict[str, Any],
                                       volume_ratio: float, trend_strength: float,
                                       volatility_level: float, market_regime: str):
        """Generate EMA12/EMA26 crossover or aligned-continuation signals."""
        ema_data = indicators.get('ema_data', {}) or {}
        ema12 = ema_data.get('ema12', []) or []
        ema26 = ema_data.get('ema26', []) or []
        ema21 = ema_data.get('ema21', []) or []
        if len(ema12) < 2 or len(ema26) < 2:
            return 'HOLD', 0.0, 'EMA crossover: missing EMA12/EMA26 history'

        ema12_now = float(ema12[-1] or 0.0)
        ema26_now = float(ema26[-1] or 0.0)
        ema12_prev = float(ema12[-2] or 0.0)
        ema26_prev = float(ema26[-2] or 0.0)
        ema21_now = float(ema21[-1] or 0.0) if ema21 else 0.0
        if current_price <= 0 or ema12_now <= 0 or ema26_now <= 0 or ema12_prev <= 0 or ema26_prev <= 0:
            return 'HOLD', 0.0, 'EMA crossover: missing usable price or EMA values'

        spread = (ema12_now - ema26_now) / ema26_now
        prev_spread = (ema12_prev - ema26_prev) / ema26_prev
        min_spread = 0.0005  # 0.05%; avoids tiny/noisy EMA separation.
        price_above_ema21 = ema21_now <= 0 or current_price >= ema21_now
        price_below_ema21 = ema21_now <= 0 or current_price <= ema21_now

        if spread > min_spread and price_above_ema21:
            crossed = prev_spread <= 0
            confidence = self._calculate_dynamic_confidence(
                'BUY', spread, volume_ratio, trend_strength, volatility_level, market_regime
            )
            mode = 'bullish cross' if crossed else 'bullish alignment'
            return 'BUY', confidence, f'EMA crossover: {mode}, EMA12 {spread*100:.2f}% above EMA26'

        if spread < -min_spread and price_below_ema21:
            crossed = prev_spread >= 0
            confidence = self._calculate_dynamic_confidence(
                'SELL', spread, volume_ratio, trend_strength, volatility_level, market_regime
            )
            mode = 'bearish cross' if crossed else 'bearish alignment'
            return 'SELL', confidence, f'EMA crossover: {mode}, EMA12 {abs(spread)*100:.2f}% below EMA26'

        return 'HOLD', 0.0, f'EMA crossover: spread {spread*100:.3f}% below trigger or price not aligned with EMA21'

    def _calculate_dynamic_confidence(self, signal: str, price_vs_sma: float,
                                      volume_ratio: float, trend_strength: float,
                                      volatility_level: float, market_regime: str) -> float:
        """Calculate confidence from market quality instead of a fixed value."""
        deviation_score = min(abs(price_vs_sma) * 20.0, 0.22)
        volume_score = min(max(volume_ratio - 1.0, 0.0) * 0.08, 0.12)
        trend_score = min(trend_strength / 100.0, 0.18)
        alignment_score = self._market_alignment_score(signal, market_regime)
        volatility_penalty = self._volatility_penalty(volatility_level)

        confidence = 0.42 + deviation_score + volume_score + trend_score + alignment_score - volatility_penalty
        return round(max(0.0, min(confidence, 0.95)), 4)

    def _market_alignment_score(self, signal: str, market_regime: str) -> float:
        """Reward signals that align with the classified market regime."""
        if signal == 'BUY' and market_regime == 'BULL_TREND':
            return 0.12
        if signal == 'SELL' and market_regime == 'BEAR_TREND':
            return 0.12
        if signal in {'BUY', 'SELL'} and market_regime == 'RANGING':
            return 0.02
        if signal == 'BUY' and market_regime == 'BEAR_TREND':
            return -0.08
        if signal == 'SELL' and market_regime == 'BULL_TREND':
            return -0.08
        return 0.0

    def _multi_timeframe_alignment_adjustment(self, signal: str, mtf: Dict[str, Any]) -> float:
        """Adjust confidence using 5m/15m/30m/1h directional agreement."""
        direction = mtf.get('direction', 'UNKNOWN')
        score = float(mtf.get('score', 0.0) or 0.0)
        alignment = float(mtf.get('alignment', 0.0) or 0.0)
        if direction == 'UNKNOWN':
            return 0.0

        if signal == 'BUY':
            if direction == 'BULLISH':
                return round(min(0.08 + abs(score) * 0.04 + alignment * 0.04, 0.14), 4)
            if direction == 'BEARISH':
                return round(-min(0.10 + abs(score) * 0.05, 0.16), 4)
        if signal == 'SELL':
            if direction == 'BEARISH':
                return round(min(0.08 + abs(score) * 0.04 + alignment * 0.04, 0.14), 4)
            if direction == 'BULLISH':
                return round(-min(0.10 + abs(score) * 0.05, 0.16), 4)
        return 0.0

    def _volatility_penalty(self, volatility_level: float) -> float:
        """Penalize very noisy symbols while allowing normal crypto volatility."""
        if volatility_level <= 0.02:
            return 0.0
        return min((volatility_level - 0.02) * 2.0, 0.12)
    
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

    def score_trade_candidate(self, signal: Dict[str, Any],
                            market_data: Dict[str, Any],
                            risk_config: Dict[str, Any]) -> Dict[str, Any]:
        """Score a trade candidate for ranking within the cycle"""
        try:
            confidence = float(signal.get('confidence', 0.0) or 0.0)
            signal_type = signal.get('signal', 'HOLD')
            indicators = signal.get('indicators', {}) or {}
            regime = signal.get('regime', {}) or {}
            current_price = indicators.get('price') or market_data.get('prices', {}).get('current', 0.0)
            sma_10 = indicators.get('sma_10', 0.0)
            volume_ratio = float(indicators.get('volume_ratio', 1.0) or 1.0)
            trend_strength = float(regime.get('trend_strength', 0.0) or 0.0)
            volatility_level = float(regime.get('volatility_level', 0.0) or 0.0)
            price_vs_sma = 0.0
            if current_price and sma_10:
                price_vs_sma = abs((current_price - sma_10) / sma_10)

            direction_bonus = 0.1 if signal_type in {'BUY', 'SELL'} else 0.0
            deviation_score = min(price_vs_sma * 100.0, 0.3)
            volume_score = min(max(volume_ratio - 1.0, 0.0) * 0.05, 0.1)
            regime_score = min(trend_strength / 150.0, 0.18)
            volatility_penalty = min(max(volatility_level - 0.02, 0.0) * 1.5, 0.12)
            mtf = indicators.get('multi_timeframe_market', {}) or {}
            mtf_adjustment = self._multi_timeframe_alignment_adjustment(signal_type, mtf)
            risk_bonus = 0.05 if risk_config else 0.0
            final_score = round(
                confidence + direction_bonus + deviation_score + volume_score + regime_score + risk_bonus + mtf_adjustment - volatility_penalty,
                6
            )

            return {
                'final_score': final_score,
                'confidence_score': confidence,
                'deviation_score': deviation_score,
                'volume_score': volume_score,
                'regime_score': regime_score,
                'volatility_penalty': volatility_penalty,
                'multi_timeframe_adjustment': mtf_adjustment,
                'direction_bonus': direction_bonus,
                'risk_bonus': risk_bonus,
                'signal': signal_type
            }
        except Exception as e:
            self.logger.error(f"Trade candidate scoring error: {e}")
            return {
                'final_score': 0.0,
                'confidence_score': 0.0,
                'deviation_score': 0.0,
                'direction_bonus': 0.0,
                'risk_bonus': 0.0,
                'signal': signal.get('signal', 'HOLD') if isinstance(signal, dict) else 'HOLD',
                'error': str(e)
            }
    
    def get_signal_statistics(self) -> Dict[str, Any]:
        """Get signal generation statistics"""
        return {
            'minimal_thresholds': self.minimal_thresholds,
            'engine_type': 'DYNAMIC_MARKET_QUALITY_SCORING',
            'timestamp': datetime.now().isoformat()
        }
