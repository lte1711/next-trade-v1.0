"""
Trade Orchestrator - Main trading execution orchestration
"""

from typing import List, Dict, Optional, Any, Tuple
import json
import logging
from datetime import datetime
from core.position_manager import PositionManager
from core.account_service import AccountService
from core.partial_take_profit_manager import PartialTakeProfitManager

class TradeOrchestrator:
    """Main trading execution orchestration"""
    
    def __init__(self, trading_results: Dict[str, Any],
                 market_data_service, indicator_service, market_regime_service,
                 signal_engine, strategy_registry, allocation_service,
                 position_manager: PositionManager, order_executor, account_service: AccountService,
                 protective_order_manager, partial_take_profit_manager: PartialTakeProfitManager,
                 log_error_callback=None):
        self.trading_results = trading_results
        self.market_data_service = market_data_service
        self.indicator_service = indicator_service
        self.market_regime_service = market_regime_service
        self.signal_engine = signal_engine
        self.strategy_registry = strategy_registry
        self.allocation_service = allocation_service
        self.position_manager = position_manager
        self.order_executor = order_executor
        self.account_service = account_service
        self.protective_order_manager = protective_order_manager
        self.partial_take_profit_manager = partial_take_profit_manager
        self.log_error = log_error_callback or self._default_log_error
        self.logger = logging.getLogger(__name__)
    
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
    
    def _check_duplicate_entry(self, symbol: str, strategy_name: str) -> bool:
        """Check if there's already a pending or active entry for this symbol"""
        try:
            # Check active positions
            active_positions = self.trading_results.get('active_positions', {})
            if symbol in active_positions:
                self.logger.warning(f"Duplicate entry prevented: {symbol} already in active positions")
                return True
            
            # Check pending trades
            pending_trades = self.trading_results.get('pending_trades', [])
            for trade in pending_trades:
                if trade.get('symbol') == symbol:
                    self.logger.warning(f"Duplicate entry prevented: {symbol} already in pending trades")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking duplicate entry: {e}")
            return False
    
    def execute_strategy_trade(self, symbol: str, strategy_name: str,
                            market_data: Dict[str, Any], indicators: Dict[str, Any],
                            regime: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute a strategy trade for a symbol"""
        try:
            # Check for duplicate entry
            if self._check_duplicate_entry(symbol, strategy_name):
                return {
                    'success': False,
                    'skipped': True,
                    'reason': f'Duplicate entry prevented: {symbol} already has active or pending trade'
                }
            
            # Get strategy configuration
            strategy_config = self.strategy_registry.get_strategy_profile(strategy_name)
            if not strategy_config:
                return {'success': False, 'reason': f'Strategy {strategy_name} not found'}
            
            # Generate trading signal
            signal = self.signal_engine.generate_strategy_signal(
                market_data, indicators, regime, strategy_config
            )
            
            if signal.get('signal') == 'HOLD':
                return {'success': False, 'reason': 'No trading signal'}

            entry_cross_gate = self._evaluate_entry_cross_gate(signal, market_data)
            if not entry_cross_gate.get('passed', False):
                return {
                    'success': False,
                    'skipped': True,
                    'reason': f"5m MA5/MA15 cross + MA60 gate blocked: {entry_cross_gate.get('reason')}",
                    'entry_cross_gate': entry_cross_gate
                }
            signal['entry_cross_gate'] = entry_cross_gate
            
            # Check entry filters
            confidence = signal.get('confidence', 0.0)
            min_confidence = strategy_config.get('entry_filters', {}).get('min_confidence', 0.6)
            
            if confidence < min_confidence:
                return {'success': False, 'reason': f'Confidence {confidence:.2f} below threshold {min_confidence}'}
            
            # Check if we can open new positions
            max_positions = self._get_current_position_limit(strategy_config)
            if not self.account_service.can_open_new_positions(self.trading_results, max_positions):
                return {
                    'success': False,
                    'skipped': True,
                    'reason': f'Cannot open new positions (dynamic limit {max_positions} or balance)'
                }
            
            # Calculate position size
            strategy_capital = self.allocation_service.get_strategy_capital(strategy_name)
            if strategy_capital <= 0:
                return {'success': False, 'reason': f'No capital allocated for strategy {strategy_name}'}
            
            current_price = market_data.get('prices', {}).get('current', 0.0)
            volatility = regime.get('volatility_level', 0.0)
            atr = indicators.get('atr', [0])[-1] if indicators.get('atr') else 0.0
            allocation_context = {
                'signal_side': signal.get('signal'),
                'market_regime': regime.get('regime', 'UNKNOWN'),
                'trend_strength': regime.get('trend_strength', 0.0),
                'volume_ratio': indicators.get('volume_ratio', 1.0),
                'multi_timeframe_direction': indicators.get('multi_timeframe_market', {}).get('direction', 'UNKNOWN'),
                'multi_timeframe_score': indicators.get('multi_timeframe_market', {}).get('score', 0.0),
                'symbol_performance': self.trading_results.get('symbol_performance', {}).get(symbol, {}),
                'active_position_count': len(self.trading_results.get('active_positions', {}) or {}),
                'max_open_positions': max_positions
            }
            
            position_sizing = self.allocation_service.calculate_position_size(
                symbol, current_price, strategy_capital, confidence,
                volatility, atr, strategy_config, allocation_context
            )
            
            position_size = position_sizing.get('position_size', 0.0)
            if position_size <= 0:
                return {'success': False, 'reason': 'Invalid position size calculated'}
            
            # Determine order side
            signal_type = signal.get('signal')
            if signal_type == 'BUY':
                order_side = 'BUY'
            elif signal_type == 'SELL':
                order_side = 'SELL'
            else:
                return {'success': False, 'reason': f'Invalid signal type: {signal_type}'}
            
            # Submit order
            trade_metadata = {
                'strategy': strategy_name,
                'signal_confidence': confidence,
                'signal_reason': signal.get('reason', ''),
                'stop_loss_pct': position_sizing.get('stop_loss_pct'),
                'take_profit_pct': position_sizing.get('take_profit_pct'),
                'atr': atr,
                'volatility': volatility,
                'allocation_context': position_sizing.get('allocation_context', {}),
                'position_amount_usdt': position_sizing.get('position_amount_usdt'),
                'risk_amount_usdt': position_sizing.get('risk_amount_usdt')
            }
            
            order_result = self.order_executor.submit_order(
                strategy_name=strategy_name,
                symbol=symbol,
                side=order_side,
                quantity=position_size,
                reduce_only=False,
                metadata=trade_metadata
            )
            
            if order_result and order_result.get("status") in {"FILLED", "NEW", "PARTIALLY_FILLED"}:
                # Update position management
                filled_price = self.safe_float_conversion(order_result.get("avgPrice"), current_price)
                if filled_price <= 0:
                    filled_price = current_price
                
                position_info = {
                    'symbol': symbol,
                    'amount': position_size if order_side == 'BUY' else -position_size,
                    'entry_price': filled_price,
                    'current_price': current_price,
                    'entry_time': int(datetime.now().timestamp() * 1000),
                    'strategy': strategy_name,
                    'signal_confidence': confidence,
                    'stop_loss_pct': position_sizing.get('stop_loss_pct'),
                    'take_profit_pct': position_sizing.get('take_profit_pct'),
                    'allocation_context': position_sizing.get('allocation_context', {}),
                    'position_amount_usdt': position_sizing.get('position_amount_usdt'),
                    'risk_amount_usdt': position_sizing.get('risk_amount_usdt')
                }
                
                # Add to active positions
                self.trading_results.setdefault('active_positions', {})[symbol] = position_info
                self.trading_results.setdefault('position_state_journal', {})[symbol] = {
                    'strategy': strategy_name,
                    'entry_time': position_info.get('entry_time'),
                    'signal_confidence': confidence,
                    'stop_loss_pct': position_sizing.get('stop_loss_pct'),
                    'take_profit_pct': position_sizing.get('take_profit_pct'),
                    'allocation_context': position_sizing.get('allocation_context', {}),
                    'position_amount_usdt': position_sizing.get('position_amount_usdt'),
                    'risk_amount_usdt': position_sizing.get('risk_amount_usdt'),
                    'entry_price': filled_price,
                    'side': 'LONG' if order_side == 'BUY' else 'SHORT'
                }
                self.trading_results.setdefault('position_entry_times', {})[symbol] = position_info.get('entry_time')
                
                # Place protective orders
                self._place_protective_orders(symbol, position_info, strategy_config)
                
                # Record allocation decision
                self.allocation_service.record_capital_allocation_decision(
                    strategy_name, symbol, position_sizing.get('position_amount_usdt', 0.0),
                    position_sizing.get('allocation_fraction', 0.0), confidence,
                    signal.get('reason', 'Strategy signal')
                )
                
                return {
                    'success': True,
                    'symbol': symbol,
                    'side': order_side,
                    'quantity': position_size,
                    'price': filled_price,
                    'strategy': strategy_name,
                    'confidence': confidence,
                    'reason': signal.get('reason', 'Strategy execution')
                }
            else:
                if not order_result:
                    return {'success': False, 'reason': 'Order failed'}
                if order_result.get("status") == "BLOCKED":
                    return {
                        'success': False,
                        'skipped': True,
                        'reason': order_result.get('reason', 'Order preflight blocked')
                    }
                
                return {
                    'success': False,
                    'reason': f"Unexpected order status: {order_result.get('status', 'UNKNOWN')}"
                }
                
        except Exception as e:
            self.log_error("strategy_trade_execute", str(e))
            return {'success': False, 'reason': f'Exception: {str(e)}'}
    
    def _place_protective_orders(self, symbol: str, position_info: Dict[str, Any],
                               strategy_config: Dict[str, Any]):
        """Place protective orders for a position using V2 Merged methodology"""
        try:
            entry_price = position_info.get('entry_price', 0.0)
            amount = position_info.get('amount', 0.0)
            strategy_name = strategy_config.get('name', 'unknown')
            
            # Get V2 Merged risk config
            risk_config = strategy_config.get('risk_config', {})
            stop_loss_pct = risk_config.get('stop_loss_pct', 0.02)
            take_profit_pct = risk_config.get('take_profit_pct', 0.04)
            
            # V2 Merged: Apply session multipliers
            session_multipliers = risk_config.get('session_multipliers', {})
            current_session = self._get_market_session()
            session_multiplier = session_multipliers.get(current_session, {'stop': 1.0, 'take': 1.0})
            
            # Apply session-based adjustments
            adjusted_stop_loss_pct = stop_loss_pct * session_multiplier.get('stop', 1.0)
            adjusted_take_profit_pct = take_profit_pct * session_multiplier.get('take', 1.0)
            
            # V2 Merged: Check for fast entry tight stop
            entry_mode = position_info.get('entry_mode', 'NORMAL')
            fast_tight_stop_loss_pct = risk_config.get('fast_tight_stop_loss_pct', 0.003)
            if entry_mode in {'FAST_LONG', 'FAST_SHORT'} and fast_tight_stop_loss_pct > 0:
                adjusted_stop_loss_pct = min(adjusted_stop_loss_pct, fast_tight_stop_loss_pct)
            
            if entry_price <= 0:
                return
            
            if amount > 0:  # Long position
                stop_loss_price = entry_price * (1 - adjusted_stop_loss_pct)
                take_profit_price = entry_price * (1 + adjusted_take_profit_pct)
            else:  # Short position
                stop_loss_price = entry_price * (1 + adjusted_stop_loss_pct)
                take_profit_price = entry_price * (1 - adjusted_take_profit_pct)
            
            # Cancel existing protective orders
            self.protective_order_manager.cancel_symbol_protective_orders(symbol)
            
            # Place stop loss order
            print(f"[TRACE] PROTECTIVE_ORDER_SUBMIT | {symbol} | STOP_MARKET | price={stop_loss_price}")
            self.protective_order_manager.submit_protective_order(
                symbol=symbol,
                side='SELL' if amount > 0 else 'BUY',
                order_type='STOP_MARKET',
                stop_price=stop_loss_price
            )
            
            # Place take profit order
            if take_profit_price is not None:
                print(f"[TRACE] PROTECTIVE_ORDER_SUBMIT | {symbol} | TAKE_PROFIT_MARKET | price={take_profit_price}")
                self.protective_order_manager.submit_protective_order(
                    symbol=symbol,
                    side='SELL' if amount > 0 else 'BUY',
                    order_type='TAKE_PROFIT_MARKET',
                    stop_price=take_profit_price
                )
            
        except Exception as e:
            self.log_error("protective_orders_place", str(e))
    
    def _get_market_session(self):
        """V2 Merged: Get current market session for time-based adjustments"""
        try:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            hour = now.hour
            
            # V2 Merged session definitions
            if 9 <= hour < 12:  # US morning peak
                return 'US_PEAK'
            elif 13 <= hour < 16:  # US afternoon
                return 'US_PEAK'
            elif 7 <= hour < 10:  # European morning
                return 'EU_PEAK'
            elif 0 <= hour < 3:  # Asian evening
                return 'ASIA_PEAK'
            elif 3 <= hour < 6:  # Dead zone
                return 'DEAD_ZONE'
            else:
                return 'NORMAL'
                
        except Exception as e:
            self.log_error("market_session_detection", str(e))
            return 'NORMAL'
    
    def emit_signal_diagnostic(self, symbol: str, strategy_name: str, signal: Dict[str, Any],
                            market_data: Dict[str, Any], indicators: Dict[str, Any],
                            regime: Dict[str, Any]):
        """Emit detailed signal diagnostic information"""
        try:
            klines_1h = market_data.get('klines', {}).get('1h', [])
            latest_volume = klines_1h[-1].get('volume', 0.0) if klines_1h else 0.0
            current_price = indicators.get('price', market_data.get('prices', {}).get('current', 0.0))
            sma_10 = indicators.get('sma_10', 0.0)
            price_vs_sma_pct = 0.0
            if current_price > 0 and sma_10 > 0:
                price_vs_sma_pct = ((current_price - sma_10) / sma_10) * 100.0

            diagnostic = {
                'timestamp': int(datetime.now().timestamp() * 1000),
                'symbol': symbol,
                'strategy': strategy_name,
                'signal': signal.get('signal', 'HOLD'),
                'confidence': signal.get('confidence', 0.0),
                'reason': signal.get('reason', ''),
                'base_interval': indicators.get('base_interval', '1h'),
                'current_price': current_price,
                'sma_10': sma_10,
                'price_vs_sma_pct': price_vs_sma_pct,
                'market_regime': regime.get('regime', 'UNKNOWN'),
                'trend_strength': regime.get('trend_strength', 0.0),
                'volatility': regime.get('volatility_level', 0.0),
                'volume': indicators.get('volume', latest_volume),
                'volume_ratio': indicators.get('volume_ratio', 1.0),
                'multi_timeframe_market': indicators.get('multi_timeframe_market', {}),
                'thresholds': {
                    'buy_trigger_pct': 0.1,
                    'sell_trigger_pct': -0.1,
                    'min_confidence': self.signal_engine.minimal_thresholds.get('min_confidence', 0.1)
                }
            }

            ma_analysis = indicators.get('ma_analysis', {})
            if ma_analysis:
                diagnostic['ma_alignment'] = {
                    'fast_above_slow': ma_analysis.get('fast_above_slow', [])[-1] if ma_analysis.get('fast_above_slow') else False,
                    'ma_trend': ma_analysis.get('ma_trend', [])[-1] if ma_analysis.get('ma_trend') else False
                }

            ema_data = indicators.get('ema_data', {}) or {}
            ema12 = ema_data.get('ema12', []) or []
            ema26 = ema_data.get('ema26', []) or []
            ema21 = ema_data.get('ema21', []) or []
            if ema12 and ema26:
                ema12_now = ema12[-1]
                ema26_now = ema26[-1]
                ema_spread_pct = ((ema12_now - ema26_now) / ema26_now) * 100.0 if ema26_now else 0.0
                diagnostic['ema_alignment'] = {
                    'ema12': ema12_now,
                    'ema26': ema26_now,
                    'ema21': ema21[-1] if ema21 else 0.0,
                    'ema12_above_ema26': ema12_now > ema26_now,
                    'ema_spread_pct': ema_spread_pct
                }

            if 'buy_strength' in signal and 'sell_strength' in signal:
                diagnostic['signal_breakdown'] = {
                    'buy_strength': signal.get('buy_strength', 0.0),
                    'sell_strength': signal.get('sell_strength', 0.0)
                }

            print(f"[SIGNAL_DIAGNOSTIC] {json.dumps(diagnostic, indent=2)}")
            return diagnostic

        except Exception as e:
            self.log_error("signal_diagnostic", str(e))
            return None
    
    def build_signal_diagnostic_summary(self, all_diagnostics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build summary of all signal diagnostics"""
        try:
            if not all_diagnostics:
                return {}
            
            summary = {
                'total_signals': len(all_diagnostics),
                'buy_signals': 0,
                'sell_signals': 0,
                'hold_signals': 0,
                'high_confidence_signals': 0,
                'average_confidence': 0.0,
                'regime_distribution': {},
                'top_candidates': [],
                'hold_reasons': {},
                'closest_to_entry': []
            }
            
            total_confidence = 0.0
            top_signal_candidates = []
            proximity_candidates = []
            seen_top_candidates = set()
            seen_proximity_candidates = set()
            
            for diagnostic in all_diagnostics:
                signal = diagnostic.get('signal', 'HOLD')
                confidence = diagnostic.get('confidence', 0.0)
                
                # Count signals
                if signal == 'BUY':
                    summary['buy_signals'] += 1
                elif signal == 'SELL':
                    summary['sell_signals'] += 1
                else:
                    summary['hold_signals'] += 1
                
                # Count high confidence signals
                if confidence >= 0.7:
                    summary['high_confidence_signals'] += 1
                
                total_confidence += confidence
                reason = diagnostic.get('reason', 'Unknown reason')
                if signal == 'HOLD':
                    summary['hold_reasons'][reason] = summary['hold_reasons'].get(reason, 0) + 1
                
                # Count regime distribution
                regime = diagnostic.get('market_regime', 'UNKNOWN')
                summary['regime_distribution'][regime] = summary['regime_distribution'].get(regime, 0) + 1
                
                # Collect candidates for top signals
                if signal != 'HOLD' and confidence >= 0.6:
                    candidate_key = (diagnostic.get('symbol'), signal)
                    if candidate_key not in seen_top_candidates:
                        top_signal_candidates.append({
                            'symbol': diagnostic.get('symbol'),
                            'signal': signal,
                            'confidence': confidence,
                            'reason': diagnostic.get('reason', ''),
                            'market_regime': diagnostic.get('market_regime'),
                            'trend_strength': diagnostic.get('trend_strength', 0.0),
                            'volume_ratio': diagnostic.get('volume_ratio', 1.0)
                        })
                        seen_top_candidates.add(candidate_key)

                distance_to_entry = abs(abs(diagnostic.get('price_vs_sma_pct', 0.0)) - 0.1)
                proximity_key = (diagnostic.get('symbol'), signal)
                if proximity_key not in seen_proximity_candidates:
                    proximity_candidates.append({
                        'symbol': diagnostic.get('symbol'),
                        'signal': signal,
                        'confidence': confidence,
                        'reason': diagnostic.get('reason', ''),
                        'price_vs_sma_pct': diagnostic.get('price_vs_sma_pct', 0.0),
                        'distance_to_entry_pct': distance_to_entry,
                        'market_regime': diagnostic.get('market_regime'),
                        'trend_strength': diagnostic.get('trend_strength', 0.0),
                        'volume_ratio': diagnostic.get('volume_ratio', 1.0)
                    })
                    seen_proximity_candidates.add(proximity_key)
            
            # Calculate averages
            if len(all_diagnostics) > 0:
                summary['average_confidence'] = total_confidence / len(all_diagnostics)
            
            # Sort and select top candidates
            top_signal_candidates.sort(key=lambda x: x['confidence'], reverse=True)
            summary['top_candidates'] = top_signal_candidates[:5]
            closest_candidates = sorted(
                proximity_candidates,
                key=lambda x: x.get('distance_to_entry_pct', float('inf'))
            )
            summary['closest_to_entry'] = closest_candidates[:5]
            
            return summary
            
        except Exception as e:
            self.log_error("diagnostic_summary", str(e))
            return {}

    def _get_symbol_performance_bias(self, symbol: str) -> Dict[str, Any]:
        """Build a lightweight performance bias for candidate ranking."""
        stats = self.trading_results.get('symbol_performance', {}).get(symbol, {}) or {}
        trade_count = int(stats.get('trade_count', 0) or 0)
        win_count = int(stats.get('win_count', 0) or 0)
        net_realized_pnl = self.safe_float_conversion(stats.get('net_realized_pnl'), 0.0)
        last_realized_pnl = self.safe_float_conversion(stats.get('last_realized_pnl'), 0.0)
        win_rate = (win_count / trade_count) if trade_count > 0 else 0.0

        penalty = 0.0
        bonus = 0.0
        if trade_count > 0:
            if net_realized_pnl < 0:
                penalty += min(abs(net_realized_pnl) / 5.0, 0.2)
            if win_rate < 0.5:
                penalty += min((0.5 - win_rate) * 0.2, 0.1)
            if last_realized_pnl > 0:
                bonus += min(last_realized_pnl / 5.0, 0.05)

        return {
            'trade_count': trade_count,
            'win_rate': round(win_rate, 4),
            'net_realized_pnl': round(net_realized_pnl, 8),
            'last_realized_pnl': round(last_realized_pnl, 8),
            'penalty': round(penalty, 6),
            'bonus': round(bonus, 6),
        }

    def _evaluate_symbol_quality(self, symbol: str, indicators: Dict[str, Any],
                                 regime: Dict[str, Any]) -> Dict[str, Any]:
        """Filter symbols that have too little usable movement for new entries."""
        try:
            price_vs_sma_pct = self.safe_float_conversion(indicators.get('price_vs_sma_pct'), 0.0)
            volume_ratio = self.safe_float_conversion(indicators.get('volume_ratio'), 1.0)
            trend_strength = self.safe_float_conversion(regime.get('trend_strength'), 0.0)
            volatility = self.safe_float_conversion(regime.get('volatility_level'), 0.0)
            market_regime = regime.get('regime', 'UNKNOWN')
            mtf = indicators.get('multi_timeframe_market', {}) or {}
            performance_gate = self._get_symbol_loss_gate(symbol)

            reasons = []
            critical_reasons = []
            if abs(price_vs_sma_pct) < 0.12:
                reasons.append('flat_price_vs_sma')
            if volume_ratio < 0.30:
                reasons.append('thin_recent_volume')
                if volume_ratio < 0.05:
                    critical_reasons.append('critically_thin_recent_volume')
            if trend_strength < 10.0:
                reasons.append('weak_trend_strength')
            if volatility < 0.002:
                reasons.append('very_low_volatility')
            if market_regime == 'UNKNOWN':
                reasons.append('unknown_market_regime')
                critical_reasons.append('unknown_market_regime')
            if performance_gate.get('blocked'):
                reasons.append(performance_gate.get('reason', 'loss_gate_blocked'))
                critical_reasons.append(performance_gate.get('reason', 'loss_gate_blocked'))

            eligible_for_new_entry = len(reasons) == 0 and not critical_reasons
            eligible_for_hold = len(reasons) == 0 and not critical_reasons
            return {
                'eligible_for_new_entry': eligible_for_new_entry,
                'eligible_for_hold': eligible_for_hold,
                'reason': ','.join(reasons) if reasons else 'quality_ok',
                'critical_reason': ','.join(critical_reasons) if critical_reasons else '',
                'price_vs_sma_pct': round(price_vs_sma_pct, 6),
                'volume_ratio': round(volume_ratio, 6),
                'trend_strength': round(trend_strength, 6),
                'volatility': round(volatility, 8),
                'market_regime': market_regime,
                'multi_timeframe_direction': mtf.get('direction', 'UNKNOWN'),
                'multi_timeframe_score': mtf.get('score', 0.0),
                'multi_timeframe_alignment': mtf.get('alignment', 0.0),
                'performance_gate': performance_gate
            }
        except Exception as e:
            self.log_error("symbol_quality_filter", str(e))
            return {
                'eligible_for_new_entry': False,
                'reason': f'quality_filter_error:{str(e)}'
            }

    def _get_symbol_loss_gate(self, symbol: str) -> Dict[str, Any]:
        """Block new entries for symbols with repeated realized losses."""
        stats = self.trading_results.get('symbol_performance', {}).get(symbol, {}) or {}
        trade_count = int(stats.get('trade_count', 0) or 0)
        win_count = int(stats.get('win_count', 0) or 0)
        loss_count = int(stats.get('loss_count', 0) or 0)
        net_realized_pnl = self.safe_float_conversion(stats.get('net_realized_pnl'), 0.0)
        last_realized_pnl = self.safe_float_conversion(stats.get('last_realized_pnl'), 0.0)
        win_rate = (win_count / trade_count) if trade_count > 0 else 1.0

        blocked = False
        reason = 'performance_ok'
        if trade_count >= 2 and net_realized_pnl <= -1.0:
            blocked = True
            reason = 'realized_loss_cooldown'
        elif trade_count >= 3 and win_rate < 0.35 and net_realized_pnl < 0:
            blocked = True
            reason = 'low_win_rate_cooldown'
        elif loss_count >= 2 and last_realized_pnl <= -1.0:
            blocked = True
            reason = 'recent_large_loss_cooldown'

        return {
            'blocked': blocked,
            'reason': reason,
            'trade_count': trade_count,
            'win_rate': round(win_rate, 4),
            'net_realized_pnl': round(net_realized_pnl, 8),
            'last_realized_pnl': round(last_realized_pnl, 8),
            'loss_count': loss_count,
        }

    def _select_indicator_interval(self, regime: Dict[str, Any]) -> str:
        """Use 30m only for ranging markets; keep 1h for trend/high-volatility regimes."""
        if regime.get('regime') == 'RANGING':
            return '30m'
        return '1h'
    
    def run_trading_cycle(self, symbols: List[str], active_strategies: List[str]) -> Dict[str, Any]:
        """Run a complete trading cycle"""
        try:
            cycle_results = {
                'start_time': int(datetime.now().timestamp() * 1000),
                'symbols_analyzed': len(symbols),
                'strategies_active': len(active_strategies),
                'signals_generated': 0,
                'trades_executed': 0,
                'errors': [],
                'skips': [],
                'low_quality_symbols': [],
                'diagnostics': [],
                'replacement_evaluation': {
                    'enabled': True,
                    'evaluated': False,
                    'candidates': [],
                    'actions': []
                }
            }
            
            # 1. Sync account and positions
            if not self.account_service.periodic_sync(self.trading_results):
                cycle_results['errors'].append('Account sync failed')
            
            # 2. Update market data and apply V2 Merged symbol selection
            market_data = self.market_data_service.update_market_data(symbols)
            
            # V2 Merged: Apply strategy-specific symbol selection
            strategy_symbols = {}
            for strategy_name in active_strategies:
                # Convert symbols to proper format for strategy registry
                symbol_list = []
                for symbol_data in symbols:
                    if isinstance(symbol_data, dict):
                        symbol_list.append(symbol_data.get('symbol', ''))
                    elif isinstance(symbol_data, str):
                        symbol_list.append(symbol_data)
                    else:
                        symbol_list.append(str(symbol_data))
                
                # Get strategy-specific symbols
                preferred_symbols = self.strategy_registry.select_preferred_symbols(
                    strategy_name,
                    symbol_list,
                    max_symbols=min(25, len(symbol_list))
                )
                strategy_symbols[strategy_name] = preferred_symbols
                
                print(f"[INFO] {strategy_name}: Selected {len(preferred_symbols)} symbols: {preferred_symbols[:3]}...")
            if not market_data:
                cycle_results['errors'].append('Market data update failed')
                return cycle_results
            
            # Store flat market data for OrderExecutor
            self.trading_results["market_data"] = {
                symbol: data.get("prices", {}).get("current", 0.0)
                for symbol, data in market_data.items()
            }
            
            # 3. Analyze market regime
            regime_data = {}
            for symbol in symbols:
                symbol_data = market_data.get(symbol, {})
                prices = [k['close'] for k in symbol_data.get('klines', {}).get('1h', [])]
                volumes = [k['volume'] for k in symbol_data.get('klines', {}).get('1h', [])]
                
                if prices:
                    regime = self.market_regime_service.analyze_market_regime(prices, volumes)
                    regime_data[symbol] = regime

            dynamic_limit = self._calculate_dynamic_position_limit(regime_data)
            self.trading_results['dynamic_position_limit'] = dynamic_limit
            cycle_results['dynamic_position_limit'] = dynamic_limit
            print(
                f"[DYNAMIC_POSITION_LIMIT] limit={dynamic_limit.get('limit')} "
                f"base={dynamic_limit.get('base_limit')} reason={dynamic_limit.get('reason')}"
            )
            
            # 4. Generate and evaluate signals
            all_diagnostics = []
            trade_candidates = []
            skipped_candidate_symbols = set()
            
            # V2 Merged: Use strategy-specific symbols for signal generation
            for strategy_name in active_strategies:
                strategy_specific_symbols = strategy_symbols.get(strategy_name, symbols)
                
                for symbol in strategy_specific_symbols:
                    symbol_data = market_data.get(symbol, {})
                    if not symbol_data:
                        continue
                
                    # Calculate indicators
                    base_interval = self._select_indicator_interval(regime_data.get(symbol, {}))
                    indicators = self._calculate_symbol_indicators(symbol_data, base_interval)
                    if not indicators:
                        continue

                    symbol_quality = self._evaluate_symbol_quality(
                        symbol,
                        indicators,
                        regime_data.get(symbol, {})
                    )
                    if not symbol_quality.get('eligible_for_new_entry', True):
                        low_quality_record = {
                            'symbol': symbol,
                            'strategy': strategy_name,
                            **symbol_quality
                        }
                        cycle_results['low_quality_symbols'].append(low_quality_record)
                        if symbol not in (self.trading_results.get('active_positions', {}) or {}):
                            cycle_results['skips'].append(
                                f"Candidate skipped for {symbol}: low quality symbol filter ({symbol_quality.get('reason')})"
                            )
                            continue
                    
                    # Generate signal for this strategy
                    signal = self.signal_engine.generate_strategy_signal(
                        symbol_data, indicators, regime_data.get(symbol, {}), 
                        self.strategy_registry.get_strategy_profile(strategy_name)
                    )
                    
                    cycle_results['signals_generated'] += 1
                    
                    # Emit diagnostic
                    diagnostic = self.emit_signal_diagnostic(
                        symbol,
                        strategy_name,
                        signal,
                        symbol_data,
                        indicators,
                        regime_data.get(symbol, {})
                    )
                    if diagnostic:
                        all_diagnostics.append(diagnostic)
                    
                    # Collect trade candidates
                    if signal.get('signal') != 'HOLD':
                        active_positions = self.trading_results.get('active_positions', {})
                        pending_symbols = {
                            trade.get('symbol')
                            for trade in self.trading_results.get('pending_trades', [])
                            if trade.get('symbol')
                        }
                        if symbol in active_positions or symbol in pending_symbols:
                            skip_key = (symbol, 'open_or_pending')
                            if skip_key not in skipped_candidate_symbols:
                                cycle_results['skips'].append(
                                    f"Candidate skipped for {symbol}: already active or pending"
                                )
                                skipped_candidate_symbols.add(skip_key)
                            continue

                        entry_cross_gate = self._evaluate_entry_cross_gate(signal, symbol_data)
                        if not entry_cross_gate.get('passed', False):
                            skip_key = (symbol, 'entry_cross_gate')
                            if skip_key not in skipped_candidate_symbols:
                                cycle_results['skips'].append(
                                    f"Candidate skipped for {symbol}: 5m MA5/MA15 cross + MA60 gate ({entry_cross_gate.get('reason')})"
                                )
                                skipped_candidate_symbols.add(skip_key)
                            continue
                        signal['entry_cross_gate'] = entry_cross_gate

                        trade_candidates.append({
                            'symbol': symbol,
                            'strategy': strategy_name,
                            'signal': signal,
                            'market_data': symbol_data,
                            'indicators': indicators,
                            'regime': regime_data.get(symbol, {})
                        })
            
            # 5. Score and select candidates
            scored_candidates = []
            for candidate in trade_candidates:
                base_score = self.signal_engine.score_trade_candidate(
                    candidate['signal'], candidate['market_data'], 
                    self.strategy_registry.get_strategy_profile(candidate['strategy']).get('risk_config', {})
                )
                performance_bias = self._get_symbol_performance_bias(candidate['symbol'])
                scored_candidates.append({
                    **candidate,
                    'score': {
                        **base_score,
                        'performance_bias': performance_bias,
                        'final_score': round(
                            self.safe_float_conversion(base_score.get('final_score'), 0.0)
                            - performance_bias.get('penalty', 0.0)
                            + performance_bias.get('bonus', 0.0),
                            6
                        )
                    }
                })
            
            # Sort by score and select top candidates
            scored_candidates.sort(key=lambda x: x['score'].get('final_score', 0.0), reverse=True)
            replacement_evaluation = self._evaluate_replacement_candidates(scored_candidates)
            cycle_results['replacement_evaluation'] = replacement_evaluation

            if replacement_evaluation.get('should_replace'):
                action = replacement_evaluation.get('selected_replacement', {})
                close_symbol = action.get('close_symbol')
                replacement_symbol = action.get('replacement_symbol')
                if close_symbol and replacement_symbol:
                    if self.position_manager.close_position(close_symbol, "candidate_rotation_replacement"):
                        cycle_results['replacement_evaluation']['actions'].append({
                            'action': 'closed_for_replacement',
                            'closed_symbol': close_symbol,
                            'replacement_symbol': replacement_symbol,
                            'score_gap': action.get('score_gap')
                        })
                        print(
                            f"[REPLACEMENT_EXECUTED] closed={close_symbol} "
                            f"replacement_candidate={replacement_symbol} score_gap={action.get('score_gap')}"
                        )
                    else:
                        cycle_results['replacement_evaluation']['actions'].append({
                            'action': 'close_failed',
                            'closed_symbol': close_symbol,
                            'replacement_symbol': replacement_symbol
                        })

            top_candidates = scored_candidates[:3]  # Top 3 candidates
            
            # 6. Execute trades
            for candidate in top_candidates:
                result = self.execute_strategy_trade(
                    candidate['symbol'], candidate['strategy'],
                    candidate['market_data'], candidate['indicators'],
                    candidate['regime']
                )
                
                if result.get('success'):
                    cycle_results['trades_executed'] += 1
                    print(f"[TRADE_EXECUTED] {result}")
                elif result.get('skipped'):
                    cycle_results['skips'].append(
                        f"Trade skipped for {candidate['symbol']}: {result.get('reason')}"
                    )
                else:
                    cycle_results['errors'].append(f"Trade failed for {candidate['symbol']}: {result.get('reason')}")
            
            # 7. Manage existing positions
            position_indicators = {}
            position_strategy_config = {}
            
            for symbol, position in self.trading_results.get("active_positions", {}).items():
                base_interval = self._select_indicator_interval(regime_data.get(symbol, {}))
                position_indicators[symbol] = self._calculate_symbol_indicators(
                    market_data.get(symbol, {}),
                    base_interval
                )
                strategy_name = position.get("strategy")
                if strategy_name:
                    position_strategy_config[symbol] = self.strategy_registry.get_strategy_profile(strategy_name) or {}
            
            self.position_manager.manage_open_positions(
                market_data,
                position_indicators,
                position_strategy_config
            )
            
            # 8. Build diagnostic summary
            cycle_results['diagnostics'] = all_diagnostics[-20:]
            cycle_results['diagnostic_summary'] = self.build_signal_diagnostic_summary(all_diagnostics)
            cycle_results['end_time'] = int(datetime.now().timestamp() * 1000)
            cycle_results['duration_ms'] = cycle_results['end_time'] - cycle_results['start_time']
            
            return cycle_results
            
        except Exception as e:
            self.log_error("trading_cycle", str(e))
            return {
                'start_time': int(datetime.now().timestamp() * 1000),
                'errors': [f'Trading cycle exception: {str(e)}']
            }

    def _score_active_position_for_replacement(self, symbol: str, position: Dict[str, Any]) -> Dict[str, Any]:
        """Score an active position so new candidates can be compared against it."""
        try:
            entry_price = self.safe_float_conversion(position.get('entry_price'), 0.0)
            current_price = self.safe_float_conversion(position.get('current_price'), 0.0)
            amount = self.safe_float_conversion(position.get('amount'), 0.0)
            journal = self.trading_results.get('position_state_journal', {}).get(symbol, {}) or {}
            confidence = self.safe_float_conversion(
                position.get('signal_confidence', journal.get('signal_confidence')),
                0.0
            )
            allocation_context = (
                position.get('allocation_context')
                or journal.get('allocation_context')
                or {}
            )
            trend_strength = self.safe_float_conversion(allocation_context.get('trend_strength'), 0.0)
            volume_ratio = self.safe_float_conversion(allocation_context.get('volume_ratio'), 1.0)
            performance = self.trading_results.get('symbol_performance', {}).get(symbol, {}) or {}
            win_rate = 0.0
            trade_count = int(performance.get('trade_count', 0) or 0)
            if trade_count > 0:
                win_rate = int(performance.get('win_count', 0) or 0) / trade_count

            pnl_pct = 0.0
            if entry_price > 0 and current_price > 0:
                if amount > 0:
                    pnl_pct = (current_price - entry_price) / entry_price
                elif amount < 0:
                    pnl_pct = (entry_price - current_price) / entry_price

            pnl_score = max(min(pnl_pct * 4.0, 0.25), -0.35)
            trend_score = min(trend_strength / 200.0, 0.18)
            volume_score = min(max(volume_ratio - 0.5, 0.0) * 0.08, 0.12)
            performance_score = min(win_rate * 0.08, 0.08)
            final_score = round(confidence + pnl_score + trend_score + volume_score + performance_score, 6)
            hold_seconds = self.position_manager.get_position_hold_seconds(symbol, position)
            replaceable = hold_seconds >= 600 or pnl_pct <= -0.004

            return {
                'symbol': symbol,
                'score': final_score,
                'pnl_pct': round(pnl_pct, 6),
                'confidence': round(confidence, 6),
                'trend_strength': round(trend_strength, 6),
                'volume_ratio': round(volume_ratio, 6),
                'win_rate': round(win_rate, 4),
                'hold_seconds': hold_seconds,
                'replaceable': replaceable,
                'side': 'LONG' if amount > 0 else 'SHORT' if amount < 0 else 'FLAT'
            }
        except Exception as e:
            self.log_error("active_position_replacement_score", str(e))
            return {'symbol': symbol, 'score': 0.0, 'error': str(e)}

    def _evaluate_replacement_candidates(self, scored_candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare pending entry candidates with active positions and choose safe rotations."""
        try:
            active_positions = self.trading_results.get('active_positions', {}) or {}
            max_positions = self._get_current_position_limit()
            for strategy_name in self.trading_results.get('strategies', {}).keys():
                strategy_config = self.strategy_registry.get_strategy_profile(strategy_name) or {}
                max_positions = max(
                    max_positions,
                    int(strategy_config.get('risk_config', {}).get('max_open_positions', max_positions) or max_positions)
                )
            dynamic_limit = self.trading_results.get('dynamic_position_limit', {}) or {}
            if dynamic_limit.get('limit'):
                max_positions = int(dynamic_limit.get('limit'))

            active_scores = [
                self._score_active_position_for_replacement(symbol, position)
                for symbol, position in active_positions.items()
            ]
            active_scores.sort(key=lambda item: item.get('score', 0.0))

            candidate_snapshots = []
            for candidate in scored_candidates[:10]:
                candidate_snapshots.append({
                    'symbol': candidate.get('symbol'),
                    'strategy': candidate.get('strategy'),
                    'signal': candidate.get('signal', {}).get('signal'),
                    'score': candidate.get('score', {}).get('final_score', 0.0),
                    'confidence': candidate.get('signal', {}).get('confidence', 0.0),
                    'reason': candidate.get('signal', {}).get('reason', '')
                })

            evaluation = {
                'enabled': True,
                'evaluated': True,
                'active_count': len(active_positions),
                'max_positions': max_positions,
                'candidate_count': len(scored_candidates),
                'top_candidates': candidate_snapshots[:5],
                'weakest_positions': active_scores[:5],
                'should_replace': False,
                'selected_replacement': None,
                'actions': []
            }

            replaceable_active_scores = [
                position_score
                for position_score in active_scores
                if position_score.get('replaceable')
            ]

            if not scored_candidates or not active_scores:
                evaluation['reason'] = 'missing_candidates_or_active_positions'
                return evaluation
            if not replaceable_active_scores:
                evaluation['reason'] = 'no_replaceable_active_positions'
                return evaluation

            best_candidate = scored_candidates[0]
            weakest_position = replaceable_active_scores[0]
            best_score = self.safe_float_conversion(best_candidate.get('score', {}).get('final_score'), 0.0)
            weakest_score = self.safe_float_conversion(weakest_position.get('score'), 0.0)
            score_gap = round(best_score - weakest_score, 6)
            weak_pnl_pct = self.safe_float_conversion(weakest_position.get('pnl_pct'), 0.0)

            at_or_over_limit = len(active_positions) >= max(1, max_positions - 1)
            weak_position = weakest_score < 0.80 or weak_pnl_pct <= -0.004
            strong_candidate = best_score >= 1.10
            enough_gap = score_gap >= 0.35

            evaluation['selected_replacement'] = {
                'close_symbol': weakest_position.get('symbol'),
                'replacement_symbol': best_candidate.get('symbol'),
                'candidate_score': best_score,
                'weakest_position_score': weakest_score,
                'score_gap': score_gap,
                'weak_position_pnl_pct': weak_pnl_pct,
                'at_or_over_limit': at_or_over_limit,
                'strong_candidate': strong_candidate,
                'weak_position': weak_position,
                'enough_gap': enough_gap,
                'thresholds': {
                    'weak_score_below': 0.80,
                    'weak_pnl_pct_at_or_below': -0.004,
                    'strong_candidate_score_at_or_above': 1.10,
                    'score_gap_at_or_above': 0.35,
                    'replaceable_hold_seconds': 600,
                    'near_limit_buffer': 1
                }
            }

            if at_or_over_limit and strong_candidate and weak_position and enough_gap:
                evaluation['should_replace'] = True
                evaluation['reason'] = 'safe_replacement_conditions_met'
            else:
                evaluation['reason'] = 'replacement_conditions_not_met'

            return evaluation
        except Exception as e:
            self.log_error("replacement_evaluation", str(e))
            return {
                'enabled': True,
                'evaluated': False,
                'error': str(e),
                'candidates': [],
                'actions': []
            }

    def _get_current_position_limit(self, strategy_config: Optional[Dict[str, Any]] = None) -> int:
        """Return the active dynamic limit, falling back to strategy risk config."""
        dynamic_limit = self.trading_results.get('dynamic_position_limit', {}) or {}
        if dynamic_limit.get('limit'):
            return max(1, int(dynamic_limit.get('limit')))

        if strategy_config:
            return max(1, int(strategy_config.get('risk_config', {}).get('max_open_positions', 10) or 10))
        return 10

    def _calculate_dynamic_position_limit(self, regime_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Adapt max open positions to current market quality with hard safety bounds."""
        try:
            base_limit = 10
            for strategy_name in self.trading_results.get('strategies', {}).keys():
                strategy_config = self.strategy_registry.get_strategy_profile(strategy_name) or {}
                base_limit = max(
                    base_limit,
                    int(strategy_config.get('risk_config', {}).get('max_open_positions', base_limit) or base_limit)
                )

            regimes = [item for item in regime_data.values() if item]
            total = max(len(regimes), 1)
            bull_bear_count = sum(1 for item in regimes if item.get('regime') in {'BULL_TREND', 'BEAR_TREND'})
            high_vol_count = sum(1 for item in regimes if item.get('regime') == 'HIGH_VOLATILITY')
            ranging_count = sum(1 for item in regimes if item.get('regime') == 'RANGING')
            avg_trend = sum(self.safe_float_conversion(item.get('trend_strength'), 0.0) for item in regimes) / total
            avg_volatility = sum(self.safe_float_conversion(item.get('volatility_level'), 0.0) for item in regimes) / total
            available_balance = self.safe_float_conversion(self.trading_results.get('available_balance'), 0.0)

            limit = base_limit
            reasons = []
            trend_ratio = bull_bear_count / total
            high_vol_ratio = high_vol_count / total
            ranging_ratio = ranging_count / total

            if trend_ratio >= 0.45 and avg_trend >= 18.0 and high_vol_ratio < 0.35:
                limit += 2
                reasons.append('broad_trend_quality')
            if trend_ratio >= 0.60 and avg_trend >= 24.0 and high_vol_ratio < 0.25:
                limit += 1
                reasons.append('strong_trend_breadth')
            if ranging_ratio >= 0.55:
                limit -= 1
                reasons.append('ranging_market_cap')
            if high_vol_ratio >= 0.35 or avg_volatility >= 0.04:
                limit -= 2
                reasons.append('high_volatility_risk_cap')
            if available_balance < 1000.0:
                limit = min(limit, 8)
                reasons.append('low_balance_cap')
            elif available_balance >= 5000.0 and high_vol_ratio < 0.30:
                limit += 1
                reasons.append('sufficient_balance_buffer')

            min_limit = 6
            max_limit = 14
            limit = max(min_limit, min(max_limit, limit))

            return {
                'limit': limit,
                'base_limit': base_limit,
                'min_limit': min_limit,
                'max_limit': max_limit,
                'reason': ','.join(reasons) if reasons else 'base_limit',
                'trend_ratio': round(trend_ratio, 6),
                'high_vol_ratio': round(high_vol_ratio, 6),
                'ranging_ratio': round(ranging_ratio, 6),
                'avg_trend_strength': round(avg_trend, 6),
                'avg_volatility': round(avg_volatility, 8),
                'available_balance': round(available_balance, 8),
                'updated_at': datetime.now().isoformat()
            }
        except Exception as e:
            self.log_error("dynamic_position_limit", str(e))
            return {
                'limit': 10,
                'base_limit': 10,
                'min_limit': 6,
                'max_limit': 14,
                'reason': f'fallback:{str(e)}',
                'updated_at': datetime.now().isoformat()
            }
    
    def _calculate_symbol_indicators(self, symbol_data: Dict[str, Any],
                                     base_interval: str = '1h') -> Dict[str, Any]:
        """Calculate all indicators for a symbol"""
        try:
            indicators = {}
            
            # Get price data from different timeframes
            klines = symbol_data.get('klines', {}).get(base_interval, [])
            if not klines and base_interval != '1h':
                base_interval = '1h'
                klines = symbol_data.get('klines', {}).get('1h', [])
            
            if not klines:
                return {}
            
            # Extract price series
            closes = [k['close'] for k in klines]
            highs = [k['high'] for k in klines]
            lows = [k['low'] for k in klines]
            opens = [k['open'] for k in klines]
            latest_price = symbol_data.get('prices', {}).get('current', closes[-1] if closes else 0.0)
            latest_volume = klines[-1].get('volume', 0.0) if klines else 0.0
            recent_volumes = [k.get('volume', 0.0) for k in klines[-20:]]
            avg_volume = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0.0

            indicators['base_interval'] = base_interval
            indicators['price'] = latest_price
            indicators['volume'] = latest_volume
            indicators['volume_sma_20'] = avg_volume
            indicators['volume_ratio'] = (latest_volume / avg_volume) if avg_volume > 0 else 1.0
            indicators['sma_10'] = sum(closes[-10:]) / min(len(closes), 10)
            if indicators['sma_10'] > 0:
                indicators['price_vs_sma_pct'] = ((latest_price - indicators['sma_10']) / indicators['sma_10']) * 100.0
            indicators['multi_timeframe_market'] = self._evaluate_multi_timeframe_market(symbol_data)

            # Calculate indicators
            ma_analysis = self.market_regime_service.analyze_timeframe_ma(closes)
            if ma_analysis:
                indicators['ma_analysis'] = ma_analysis
            
            # EMA calculations
            ema_12 = self.indicator_service.calculate_ema(closes, 12)
            ema_26 = self.indicator_service.calculate_ema(closes, 26)
            ema_21 = self.indicator_service.calculate_ema(closes, 21)
            
            indicators['ema_data'] = {
                'ema12': ema_12,
                'ema26': ema_26,
                'ema21': ema_21
            }
            
            # Heikin Ashi
            ha_candles = self.indicator_service.calculate_heikin_ashi(opens, highs, lows, closes)
            if ha_candles:
                ha_analysis = self.indicator_service.analyze_heikin_ashi(ha_candles)
                indicators['ha_analysis'] = ha_analysis
            
            # Fractals
            high_fractals, low_fractals = self.indicator_service.calculate_recent_fractals(highs, lows)
            indicators['fractals'] = {
                'high_fractals': high_fractals,
                'low_fractals': low_fractals
            }
            
            # RSI
            rsi = self.indicator_service.calculate_rsi(closes)
            indicators['rsi'] = rsi
            
            # ATR
            atr = self.indicator_service.calculate_atr(highs, lows, closes)
            indicators['atr'] = atr
            
            return indicators
            
        except Exception as e:
            self.log_error("indicators_calculate", str(e))
            return {}

    def _evaluate_entry_cross_gate(self, signal: Dict[str, Any],
                                   symbol_data: Dict[str, Any]) -> Dict[str, Any]:
        """Require a 5m MA5/MA15 cross with MA60 reference-line confirmation before new entries."""
        try:
            signal_type = signal.get('signal')
            if signal_type not in {'BUY', 'SELL'}:
                return {'passed': True, 'reason': 'not_entry_signal'}

            ma_cross = self._evaluate_5m_ma5_ma15_cross_with_ma60(symbol_data)
            target_cross = 'golden_cross' if signal_type == 'BUY' else 'dead_cross'
            target_bias = 'above_ma60' if signal_type == 'BUY' else 'below_ma60'
            passed = (
                ma_cross.get('cross') == target_cross
                and ma_cross.get('ma60_filter') == target_bias
            )

            return {
                'passed': passed,
                'required_cross': target_cross,
                'required_ma60_filter': target_bias,
                'signal': signal_type,
                'ma_cross': ma_cross,
                'reason': 'passed' if passed else (
                    f"requires 5m MA5/MA15 {target_cross} and price {target_bias}; "
                    f"actual_cross={ma_cross.get('cross')}, "
                    f"actual_ma60_filter={ma_cross.get('ma60_filter')}"
                )
            }
        except Exception as e:
            self.log_error("entry_cross_gate_eval", str(e))
            return {
                'passed': False,
                'reason': f'entry_cross_gate_error:{str(e)}'
            }

    def _evaluate_5m_ma5_ma15_cross_with_ma60(self, symbol_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect the latest 5m MA5/MA15 cross and confirm price against the 5m MA60 reference line."""
        try:
            klines_5m = symbol_data.get('klines', {}).get('5m', [])
            closes = [
                self.safe_float_conversion(k.get('close'), 0.0)
                for k in klines_5m
                if self.safe_float_conversion(k.get('close'), 0.0) > 0.0
            ]
            if len(closes) < 61:
                return {
                    'cross': 'insufficient_data',
                    'ma60_filter': 'insufficient_data',
                    'timeframe': '5m',
                    'bars': len(closes),
                    'ma_periods': {'fast': 5, 'slow': 15, 'trend_line': 60}
                }

            ma_5 = self.indicator_service.calculate_sma(closes, 5)
            ma_15 = self.indicator_service.calculate_sma(closes, 15)
            ma_60 = self.indicator_service.calculate_sma(closes, 60)
            if len(ma_5) < 2 or len(ma_15) < 2 or len(ma_60) < 2:
                return {
                    'cross': 'insufficient_ma',
                    'ma60_filter': 'insufficient_ma',
                    'timeframe': '5m',
                    'bars': len(closes),
                    'ma_periods': {'fast': 5, 'slow': 15, 'trend_line': 60}
                }

            prev_ma_5 = ma_5[-2]
            prev_ma_15 = ma_15[-2]
            curr_ma_5 = ma_5[-1]
            curr_ma_15 = ma_15[-1]
            prev_ma_60 = ma_60[-2]
            curr_ma_60 = ma_60[-1]
            current_price = closes[-1]
            if None in {prev_ma_5, prev_ma_15, curr_ma_5, curr_ma_15, prev_ma_60, curr_ma_60}:
                return {
                    'cross': 'insufficient_ma',
                    'ma60_filter': 'insufficient_ma',
                    'timeframe': '5m',
                    'bars': len(closes),
                    'ma_periods': {'fast': 5, 'slow': 15, 'trend_line': 60}
                }

            prev_spread = prev_ma_5 - prev_ma_15
            curr_spread = curr_ma_5 - curr_ma_15
            cross = 'none'
            if prev_spread <= 0.0 and curr_spread > 0.0:
                cross = 'golden_cross'
            elif prev_spread >= 0.0 and curr_spread < 0.0:
                cross = 'dead_cross'

            ma60_filter = 'neutral_ma60'
            if current_price > curr_ma_60:
                ma60_filter = 'above_ma60'
            elif current_price < curr_ma_60:
                ma60_filter = 'below_ma60'
            ma60_slope = curr_ma_60 - prev_ma_60

            return {
                'cross': cross,
                'ma60_filter': ma60_filter,
                'timeframe': '5m',
                'bars': len(closes),
                'prev_spread': round(prev_spread, 12),
                'curr_spread': round(curr_spread, 12),
                'prev_ma5': round(prev_ma_5, 12),
                'prev_ma15': round(prev_ma_15, 12),
                'curr_ma5': round(curr_ma_5, 12),
                'curr_ma15': round(curr_ma_15, 12),
                'prev_ma60': round(prev_ma_60, 12),
                'curr_ma60': round(curr_ma_60, 12),
                'ma60_slope': round(ma60_slope, 12),
                'current_price': round(current_price, 12),
                'comparison_mode': '5m_sma5_vs_sma15_with_sma60_reference_line',
                'ma_periods': {'fast': 5, 'slow': 15, 'trend_line': 60}
            }
        except Exception as e:
            self.log_error("5m_ma5_ma15_cross_eval", str(e))
            return {
                'cross': 'error',
                'ma60_filter': 'error',
                'reason': str(e)
            }

    def _evaluate_5m_15m_ema_line_cross(self, symbol_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect whether the 5m EMA12 line just crossed the 15m EMA12 line."""
        try:
            klines_5m = symbol_data.get('klines', {}).get('5m', [])
            klines_15m = symbol_data.get('klines', {}).get('15m', [])
            closes_5m = [
                self.safe_float_conversion(k.get('close'), 0.0)
                for k in klines_5m
                if self.safe_float_conversion(k.get('close'), 0.0) > 0.0
            ]
            closes_15m = [
                self.safe_float_conversion(k.get('close'), 0.0)
                for k in klines_15m
                if self.safe_float_conversion(k.get('close'), 0.0) > 0.0
            ]
            if len(closes_5m) < 30 or len(closes_15m) < 27:
                return {
                    'cross': 'insufficient_data',
                    'ema_period': 12,
                    '5m_bars': len(closes_5m),
                    '15m_bars': len(closes_15m)
                }

            ema_5m = self.indicator_service.calculate_ema(closes_5m, 12)
            ema_15m = self.indicator_service.calculate_ema(closes_15m, 12)
            if len(ema_5m) < 2 or len(ema_15m) < 2:
                return {
                    'cross': 'insufficient_ema',
                    'ema_period': 12,
                    '5m_bars': len(closes_5m),
                    '15m_bars': len(closes_15m)
                }

            # Fast mode: compare the previous 5m EMA with the previous 15m EMA to reduce entry lag.
            prev_5m = ema_5m[-2]
            prev_15m = ema_15m[-2]
            curr_5m = ema_5m[-1]
            curr_15m = ema_15m[-1]
            if None in {prev_5m, prev_15m, curr_5m, curr_15m}:
                return {
                    'cross': 'insufficient_ema',
                    'ema_period': 12,
                    '5m_bars': len(closes_5m),
                    '15m_bars': len(closes_15m)
                }

            prev_spread = prev_5m - prev_15m
            curr_spread = curr_5m - curr_15m
            cross = 'none'
            if prev_spread <= 0.0 and curr_spread > 0.0:
                cross = 'golden_cross'
            elif prev_spread >= 0.0 and curr_spread < 0.0:
                cross = 'dead_cross'

            return {
                'cross': cross,
                'ema_period': 12,
                'prev_spread': round(prev_spread, 12),
                'curr_spread': round(curr_spread, 12),
                'prev_5m_ema12': round(prev_5m, 12),
                'prev_15m_ema12': round(prev_15m, 12),
                'curr_5m_ema12': round(curr_5m, 12),
                'curr_15m_ema12': round(curr_15m, 12),
                'comparison_mode': 'fast_prev_5m_vs_prev_15m',
                '5m_bars': len(closes_5m),
                '15m_bars': len(closes_15m)
            }
        except Exception as e:
            self.log_error("5m_15m_ema_line_cross_eval", str(e))
            return {
                'cross': 'error',
                'reason': str(e)
            }

    def _evaluate_timeframe_ema_cross(self, symbol_data: Dict[str, Any],
                                      timeframe: str) -> Dict[str, Any]:
        """Detect the latest-candle EMA12/EMA26 cross for a single timeframe."""
        try:
            klines = symbol_data.get('klines', {}).get(timeframe, [])
            closes = [
                self.safe_float_conversion(k.get('close'), 0.0)
                for k in klines
                if self.safe_float_conversion(k.get('close'), 0.0) > 0.0
            ]
            if len(closes) < 27:
                return {
                    'cross': 'insufficient_data',
                    'timeframe': timeframe,
                    'bars': len(closes)
                }

            ema_12 = self.indicator_service.calculate_ema(closes, 12)
            ema_26 = self.indicator_service.calculate_ema(closes, 26)
            if len(ema_12) < 2 or len(ema_26) < 2:
                return {
                    'cross': 'insufficient_ema',
                    'timeframe': timeframe,
                    'bars': len(closes)
                }

            prev_ema_12 = ema_12[-2]
            prev_ema_26 = ema_26[-2]
            curr_ema_12 = ema_12[-1]
            curr_ema_26 = ema_26[-1]
            if None in {prev_ema_12, prev_ema_26, curr_ema_12, curr_ema_26}:
                return {
                    'cross': 'insufficient_ema',
                    'timeframe': timeframe,
                    'bars': len(closes)
                }

            prev_spread = prev_ema_12 - prev_ema_26
            curr_spread = curr_ema_12 - curr_ema_26
            cross = 'none'
            if prev_spread <= 0.0 and curr_spread > 0.0:
                cross = 'golden_cross'
            elif prev_spread >= 0.0 and curr_spread < 0.0:
                cross = 'dead_cross'

            return {
                'cross': cross,
                'timeframe': timeframe,
                'bars': len(closes),
                'prev_spread': round(prev_spread, 12),
                'curr_spread': round(curr_spread, 12),
                'ema12': round(curr_ema_12, 12),
                'ema26': round(curr_ema_26, 12)
            }
        except Exception as e:
            self.log_error("timeframe_ema_cross_eval", f"{timeframe}: {str(e)}")
            return {
                'cross': 'error',
                'timeframe': timeframe,
                'reason': str(e)
            }

    def _evaluate_multi_timeframe_market(self, symbol_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate 5m/15m/30m/1h alignment and momentum for entry quality."""
        try:
            timeframe_weights = {
                '5m': 0.15,
                '15m': 0.25,
                '30m': 0.25,
                '1h': 0.35,
            }
            frames = {}
            weighted_score = 0.0
            total_weight = 0.0
            bullish_count = 0
            bearish_count = 0

            for timeframe, weight in timeframe_weights.items():
                klines = symbol_data.get('klines', {}).get(timeframe, [])
                if len(klines) < 20:
                    continue

                closes = [k.get('close', 0.0) for k in klines if k.get('close', 0.0) > 0]
                volumes = [k.get('volume', 0.0) for k in klines if k.get('volume', 0.0) >= 0]
                if len(closes) < 20:
                    continue

                current_price = closes[-1]
                sma_10 = sum(closes[-10:]) / 10
                sma_20 = sum(closes[-20:]) / 20
                momentum = (current_price - closes[-5]) / closes[-5] if closes[-5] > 0 else 0.0
                price_vs_sma20 = (current_price - sma_20) / sma_20 if sma_20 > 0 else 0.0
                recent_volumes = volumes[-20:] if len(volumes) >= 20 else volumes
                avg_volume = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0.0
                volume_ratio = (volumes[-1] / avg_volume) if avg_volume > 0 and volumes else 1.0

                raw_score = 0.0
                raw_score += max(min(price_vs_sma20 * 8.0, 0.4), -0.4)
                raw_score += max(min(momentum * 12.0, 0.35), -0.35)
                if current_price > sma_10 > sma_20:
                    raw_score += 0.2
                elif current_price < sma_10 < sma_20:
                    raw_score -= 0.2
                raw_score += min(max(volume_ratio - 1.0, 0.0) * 0.05, 0.08)
                score = round(max(min(raw_score, 1.0), -1.0), 6)

                direction = 'BULLISH' if score > 0.12 else 'BEARISH' if score < -0.12 else 'NEUTRAL'
                if direction == 'BULLISH':
                    bullish_count += 1
                elif direction == 'BEARISH':
                    bearish_count += 1

                frames[timeframe] = {
                    'direction': direction,
                    'score': score,
                    'price_vs_sma20_pct': round(price_vs_sma20 * 100.0, 6),
                    'momentum_5bar_pct': round(momentum * 100.0, 6),
                    'volume_ratio': round(volume_ratio, 6)
                }
                weighted_score += score * weight
                total_weight += weight

            if total_weight <= 0:
                return {
                    'direction': 'UNKNOWN',
                    'score': 0.0,
                    'alignment': 0.0,
                    'frames': frames
                }

            final_score = round(weighted_score / total_weight, 6)
            direction = 'BULLISH' if final_score > 0.12 else 'BEARISH' if final_score < -0.12 else 'NEUTRAL'
            aligned_count = max(bullish_count, bearish_count)
            alignment = round(aligned_count / max(len(frames), 1), 6)

            return {
                'direction': direction,
                'score': final_score,
                'alignment': alignment,
                'frames': frames
            }
        except Exception as e:
            self.log_error("multi_timeframe_market_eval", str(e))
            return {
                'direction': 'UNKNOWN',
                'score': 0.0,
                'alignment': 0.0,
                'frames': {}
            }
