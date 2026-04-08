"""
Trade Orchestrator - Main trading execution orchestration
"""

from typing import List, Dict, Optional, Any, Tuple
from decimal import Decimal
import json
from datetime import datetime

class TradeOrchestrator:
    """Main trading execution orchestration"""
    
    def __init__(self, trading_results: Dict[str, Any],
                 market_data_service, indicator_service, market_regime_service,
                 signal_engine, strategy_registry, allocation_service,
                 position_manager, order_executor, account_service,
                 protective_order_manager,
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
    
    def execute_strategy_trade(self, symbol: str, strategy_name: str,
                            market_data: Dict[str, Any], indicators: Dict[str, Any],
                            regime: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute a strategy trade for a symbol"""
        try:
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
            
            # Check entry filters
            confidence = signal.get('confidence', 0.0)
            min_confidence = strategy_config.get('entry_filters', {}).get('min_confidence', 0.6)
            
            if confidence < min_confidence:
                return {'success': False, 'reason': f'Confidence {confidence:.2f} below threshold {min_confidence}'}
            
            # Check if we can open new positions
            if not self.account_service.can_open_new_positions(self.trading_results):
                return {'success': False, 'reason': 'Cannot open new positions (limit or balance)'}
            
            # Calculate position size
            strategy_capital = self.allocation_service.get_strategy_capital(strategy_name)
            if strategy_capital <= 0:
                return {'success': False, 'reason': f'No capital allocated for strategy {strategy_name}'}
            
            current_price = market_data.get('current_price', 0.0)
            volatility = market_data.get('volatility', 0.0)
            atr = indicators.get('atr', [0])[-1] if indicators.get('atr') else 0.0
            
            position_sizing = self.allocation_service.calculate_position_size(
                symbol, current_price, strategy_capital, confidence,
                volatility, atr, strategy_config
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
                'volatility': volatility
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
                    'take_profit_pct': position_sizing.get('take_profit_pct')
                }
                
                # Add to active positions
                self.trading_results.setdefault('active_positions', {})[symbol] = position_info
                
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
                
                return {
                    'success': False,
                    'reason': f"Unexpected order status: {order_result.get('status', 'UNKNOWN')}"
                }
                
        except Exception as e:
            self.log_error("strategy_trade_execute", str(e))
            return {'success': False, 'reason': f'Exception: {str(e)}'}
    
    def _place_protective_orders(self, symbol: str, position_info: Dict[str, Any],
                               strategy_config: Dict[str, Any]):
        """Place protective orders for a position"""
        try:
            current_price = position_info.get('current_price', 0.0)
            amount = position_info.get('amount', 0.0)
            stop_loss_pct = position_info.get('stop_loss_pct', 0.02)
            take_profit_pct = position_info.get('take_profit_pct', 0.04)
            
            if amount > 0:  # Long position
                stop_loss_price = current_price * (1 - stop_loss_pct)
                take_profit_price = current_price * (1 + take_profit_pct)
            else:  # Short position
                stop_loss_price = current_price * (1 + stop_loss_pct)
                take_profit_price = current_price * (1 - take_profit_pct)
            
            # Place stop loss order
            self.protective_order_manager.submit_protective_order(
                symbol=symbol,
                side='SELL' if amount > 0 else 'BUY',
                order_type='STOP_MARKET',
                stop_price=stop_loss_price
            )
            
            # Place take profit order
            self.protective_order_manager.submit_protective_order(
                symbol=symbol,
                side='SELL' if amount > 0 else 'BUY',
                order_type='TAKE_PROFIT_MARKET',
                stop_price=take_profit_price
            )
            
        except Exception as e:
            self.log_error("protective_orders_place", str(e))
    
    def emit_signal_diagnostic(self, symbol: str, signal: Dict[str, Any],
                            market_data: Dict[str, Any], indicators: Dict[str, Any]):
        """Emit detailed signal diagnostic information"""
        try:
            diagnostic = {
                'timestamp': int(datetime.now().timestamp() * 1000),
                'symbol': symbol,
                'signal': signal.get('signal', 'HOLD'),
                'confidence': signal.get('confidence', 0.0),
                'reason': signal.get('reason', ''),
                'current_price': market_data.get('current_price', 0.0),
                'market_regime': market_data.get('regime', 'UNKNOWN'),
                'trend_strength': market_data.get('trend_strength', 0.0),
                'volatility': market_data.get('volatility', 0.0),
                'volume': market_data.get('volume', 0.0)
            }
            
            # Add indicator details
            ma_analysis = indicators.get('ma_analysis', {})
            if ma_analysis:
                diagnostic['ma_alignment'] = {
                    'fast_above_slow': ma_analysis.get('fast_above_slow', [])[-1] if ma_analysis.get('fast_above_slow') else False,
                    'ma_trend': ma_analysis.get('ma_trend', [])[-1] if ma_analysis.get('ma_trend') else False
                }
            
            # Add signal breakdown
            if 'buy_strength' in signal and 'sell_strength' in signal:
                diagnostic['signal_breakdown'] = {
                    'buy_strength': signal.get('buy_strength', 0.0),
                    'sell_strength': signal.get('sell_strength', 0.0)
                }
            
            print(f"[SIGNAL_DIAGNOSTIC] {json.dumps(diagnostic, indent=2)}")
            
        except Exception as e:
            self.log_error("signal_diagnostic", str(e))
    
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
                'top_candidates': []
            }
            
            total_confidence = 0.0
            candidates = []
            
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
                
                # Count regime distribution
                regime = diagnostic.get('market_regime', 'UNKNOWN')
                summary['regime_distribution'][regime] = summary['regime_distribution'].get(regime, 0) + 1
                
                # Collect candidates for top signals
                if signal != 'HOLD' and confidence >= 0.6:
                    candidates.append({
                        'symbol': diagnostic.get('symbol'),
                        'signal': signal,
                        'confidence': confidence,
                        'reason': diagnostic.get('reason', '')
                    })
            
            # Calculate averages
            if len(all_diagnostics) > 0:
                summary['average_confidence'] = total_confidence / len(all_diagnostics)
            
            # Sort and select top candidates
            candidates.sort(key=lambda x: x['confidence'], reverse=True)
            summary['top_candidates'] = candidates[:5]  # Top 5 candidates
            
            return summary
            
        except Exception as e:
            self.log_error("diagnostic_summary", str(e))
            return {}
    
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
                'diagnostics': []
            }
            
            # 1. Sync account and positions
            if not self.account_service.periodic_sync(self.trading_results):
                cycle_results['errors'].append('Account sync failed')
            
            # 2. Update market data
            market_data = self.market_data_service.update_market_data(symbols)
            if not market_data:
                cycle_results['errors'].append('Market data update failed')
                return cycle_results
            
            # 3. Analyze market regime
            regime_data = {}
            for symbol in symbols:
                symbol_data = market_data.get(symbol, {})
                prices = [k['close'] for k in symbol_data.get('klines', {}).get('1h', [])]
                volumes = [k['volume'] for k in symbol_data.get('klines', {}).get('1h', [])]
                
                if prices:
                    regime = self.market_regime_service.analyze_market_regime(prices, volumes)
                    regime_data[symbol] = regime
            
            # 4. Generate and evaluate signals
            all_diagnostics = []
            trade_candidates = []
            
            for symbol in symbols:
                symbol_data = market_data.get(symbol, {})
                if not symbol_data:
                    continue
                
                # Calculate indicators
                indicators = self._calculate_symbol_indicators(symbol_data)
                if not indicators:
                    continue
                
                # Generate signals for each strategy
                for strategy_name in active_strategies:
                    signal = self.signal_engine.generate_strategy_signal(
                        symbol_data, indicators, regime_data.get(symbol, {}), 
                        self.strategy_registry.get_strategy_profile(strategy_name)
                    )
                    
                    cycle_results['signals_generated'] += 1
                    
                    # Emit diagnostic
                    self.emit_signal_diagnostic(symbol, signal, symbol_data, indicators)
                    all_diagnostics.append({
                        'symbol': symbol,
                        'strategy': strategy_name,
                        'signal': signal
                    })
                    
                    # Collect trade candidates
                    if signal.get('signal') != 'HOLD':
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
                score = self.signal_engine.score_trade_candidate(
                    candidate['signal'], candidate['market_data'], 
                    self.strategy_registry.get_strategy_profile(candidate['strategy']).get('risk_config', {})
                )
                scored_candidates.append({
                    **candidate,
                    'score': score
                })
            
            # Sort by score and select top candidates
            scored_candidates.sort(key=lambda x: x['score'].get('final_score', 0.0), reverse=True)
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
                else:
                    cycle_results['errors'].append(f"Trade failed for {candidate['symbol']}: {result.get('reason')}")
            
            # 7. Manage existing positions
            position_indicators = {}
            position_strategy_config = {}
            
            for symbol, position in self.trading_results.get("active_positions", {}).items():
                position_indicators[symbol] = self._calculate_symbol_indicators(market_data.get(symbol, {}))
                strategy_name = position.get("strategy")
                if strategy_name:
                    position_strategy_config[symbol] = self.strategy_registry.get_strategy_profile(strategy_name) or {}
            
            self.position_manager.manage_open_positions(
                market_data,
                position_indicators,
                position_strategy_config
            )
            
            # 8. Build diagnostic summary
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
    
    def _calculate_symbol_indicators(self, symbol_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate all indicators for a symbol"""
        try:
            indicators = {}
            
            # Get price data from different timeframes
            klines_5m = symbol_data.get('klines', {}).get('5m', [])
            klines_15m = symbol_data.get('klines', {}).get('15m', [])
            klines_1h = symbol_data.get('klines', {}).get('1h', [])
            
            if not klines_1h:
                return {}
            
            # Extract price series
            closes_1h = [k['close'] for k in klines_1h]
            highs_1h = [k['high'] for k in klines_1h]
            lows_1h = [k['low'] for k in klines_1h]
            opens_1h = [k['open'] for k in klines_1h]
            
            # Calculate indicators
            ma_analysis = self.market_regime_service.analyze_timeframe_ma(closes_1h)
            if ma_analysis:
                indicators['ma_analysis'] = ma_analysis
            
            # EMA calculations
            ema_12 = self.indicator_service.calculate_ema(closes_1h, 12)
            ema_26 = self.indicator_service.calculate_ema(closes_1h, 26)
            ema_21 = self.indicator_service.calculate_ema(closes_1h, 21)
            
            indicators['ema_data'] = {
                'ema12': ema_12,
                'ema26': ema_26,
                'ema21': ema_21
            }
            
            # Heikin Ashi
            ha_candles = self.indicator_service.calculate_heikin_ashi(opens_1h, highs_1h, lows_1h, closes_1h)
            if ha_candles:
                ha_analysis = self.indicator_service.analyze_heikin_ashi(ha_candles)
                indicators['ha_analysis'] = ha_analysis
            
            # Fractals
            high_fractals, low_fractals = self.indicator_service.calculate_recent_fractals(highs_1h, lows_1h)
            indicators['fractals'] = {
                'high_fractals': high_fractals,
                'low_fractals': low_fractals
            }
            
            # RSI
            rsi = self.indicator_service.calculate_rsi(closes_1h)
            indicators['rsi'] = rsi
            
            # ATR
            atr = self.indicator_service.calculate_atr(highs_1h, lows_1h, closes_1h)
            indicators['atr'] = atr
            
            return indicators
            
        except Exception as e:
            self.log_error("indicators_calculate", str(e))
            return {}
