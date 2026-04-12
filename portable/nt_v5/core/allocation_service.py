"""
Allocation Service - Position sizing and capital allocation
"""

from typing import List, Dict, Optional, Any, Tuple
from decimal import Decimal
import json

class AllocationService:
    """Position sizing and capital allocation service"""
    
    def __init__(self, log_error_callback=None):
        self.log_error = log_error_callback or self._default_log_error
        self._strategy_capital = {}
        self._allocation_history = []
        
        # V2 Merged risk parameters
        self.v2_risk_settings = {
            'ma_trend_follow': {'risk_per_trade': 0.015, 'leverage': 12.0},
            'ema_crossover': {'risk_per_trade': 0.012, 'leverage': 8.0},
            'fractal_breakout': {'risk_per_trade': 0.010, 'leverage': 10.0}
        }
    
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
    
    def get_dynamic_capital_per_strategy(self, total_capital: float, 
                                       active_strategies: List[str],
                                       performance_data: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """Calculate dynamic capital allocation per strategy"""
        try:
            if not active_strategies:
                # Default strategies if none provided
                active_strategies = ['ma_trend_follow', 'ema_crossover']
            
            # V2 Merged style: Use symbol count for more granular allocation
            symbol_count = 30  # V2 Merged typical symbol count
            strategy_count = len(active_strategies)
            
            # Base allocation per symbol (V2 Merged style)
            capital_per_symbol = total_capital / symbol_count
            
            # Allocate capital to strategies based on symbol allocation
            base_allocation = capital_per_symbol * (symbol_count / strategy_count)
            allocations = {strategy: base_allocation for strategy in active_strategies}
            
            # Adjust based on performance
            for strategy in active_strategies:
                performance = performance_data.get(strategy, {})
                
                # Performance factors
                win_rate = performance.get('win_rate', 0.5)
                profit_factor = performance.get('profit_factor', 1.0)
                max_drawdown = performance.get('max_drawdown', 0.1)
                
                # Calculate performance multiplier
                performance_multiplier = 1.0
                
                # Win rate adjustment
                if win_rate > 0.6:
                    performance_multiplier *= 1.2
                elif win_rate < 0.4:
                    performance_multiplier *= 0.8
                
                # Profit factor adjustment
                if profit_factor > 1.5:
                    performance_multiplier *= 1.1
                elif profit_factor < 1.0:
                    performance_multiplier *= 0.9
                
                # Drawdown penalty
                if max_drawdown > 0.15:  # 15% drawdown threshold
                    performance_multiplier *= 0.9
                elif max_drawdown > 0.25:  # 25% drawdown threshold
                    performance_multiplier *= 0.7
                
                # Apply performance adjustment
                allocations[strategy] *= performance_multiplier
            
            # Normalize to ensure total doesn't exceed available capital
            total_allocated = sum(allocations.values())
            if total_allocated > total_capital:
                normalization_factor = total_capital / total_allocated
                for strategy in allocations:
                    allocations[strategy] *= normalization_factor
            
            return allocations
            
        except Exception as e:
            self.log_error("dynamic_capital_allocation", str(e))
            return {strategy: total_capital / len(active_strategies) for strategy in active_strategies}
    
    def refresh_strategy_capital_allocations(self, total_capital: float,
                                           active_strategies: List[str],
                                           performance_data: Dict[str, Dict[str, float]]):
        """Refresh and store strategy capital allocations"""
        try:
            allocations = self.get_dynamic_capital_per_strategy(total_capital, active_strategies, performance_data)
            self._strategy_capital = allocations
            
            # Record allocation history
            self._allocation_history.append({
                'timestamp': self._get_current_timestamp(),
                'total_capital': total_capital,
                'allocations': allocations.copy()
            })
            
            # Keep only last 100 allocation records
            if len(self._allocation_history) > 100:
                self._allocation_history = self._allocation_history[-100:]
            
        except Exception as e:
            self.log_error("capital_allocation_refresh", str(e))
    
    def estimate_stop_loss_pct(self, symbol: str, current_price: float,
                             atr: float, volatility: float,
                             strategy_config: Dict[str, Any]) -> float:
        """Estimate optimal stop loss percentage"""
        try:
            base_stop_loss = strategy_config.get('risk_config', {}).get('stop_loss_pct', 0.02)
            
            # ATR-based adjustment
            if atr > 0 and current_price > 0:
                atr_pct = atr / current_price
                # Use 2x ATR as stop loss, but respect strategy limits
                atr_stop_loss = min(atr_pct * 2, base_stop_loss * 2)
                base_stop_loss = max(base_stop_loss, atr_stop_loss * 0.5)
            
            # Volatility adjustment
            if volatility > 0.05:  # High volatility
                base_stop_loss *= 1.5  # Wider stops
            elif volatility < 0.02:  # Low volatility
                base_stop_loss *= 0.8  # Tighter stops
            
            # Ensure reasonable bounds
            base_stop_loss = max(0.005, min(0.05, base_stop_loss))  # 0.5% to 5%
            
            return base_stop_loss
            
        except Exception as e:
            self.log_error("stop_loss_estimation", str(e))
            return 0.02  # Default 2%
    
    def calculate_volatility_size_multiplier(self, symbol: str, volatility: float,
                                          strategy_config: Dict[str, Any]) -> float:
        """Calculate position size multiplier based on volatility"""
        try:
            base_multiplier = 1.0
            
            # Volatility adjustment
            if volatility > 0.06:  # Very high volatility
                base_multiplier = 0.5  # Reduce position size significantly
            elif volatility > 0.04:  # High volatility
                base_multiplier = 0.7
            elif volatility > 0.02:  # Normal volatility
                base_multiplier = 1.0
            else:  # Low volatility
                base_multiplier = 1.2  # Can increase position size
            
            # Strategy-specific adjustments
            strategy_type = strategy_config.get('type', 'unknown')
            if strategy_type == 'breakout':
                base_multiplier *= 1.1  # Breakout strategies can handle more volatility
            elif strategy_type == 'trend_following':
                base_multiplier *= 0.9  # Trend following prefers stable trends
            
            return base_multiplier
            
        except Exception as e:
            self.log_error("volatility_multiplier", str(e))
            return 1.0
    
    def calculate_allocation_fraction(self, strategy_name: str, 
                                    signal_confidence: float,
                                    available_capital: float,
                                    strategy_config: Dict[str, Any]) -> float:
        """Calculate fraction of strategy capital to allocate to this trade"""
        try:
            # Base allocation fraction
            max_position_size = strategy_config.get('risk_config', {}).get('max_position_size_usdt', 1000.0)
            base_fraction = min(max_position_size / available_capital, 0.2)  # Max 20% of strategy capital
            
            # Confidence adjustment
            confidence_multiplier = 0.5 + (signal_confidence * 0.5)  # 0.5 to 1.0 range
            base_fraction *= confidence_multiplier
            
            # Strategy type adjustment
            strategy_type = strategy_config.get('type', 'unknown')
            if strategy_type == 'breakout':
                base_fraction *= 0.8  # Breakout strategies use smaller positions
            elif strategy_type == 'trend_following':
                base_fraction *= 1.1  # Trend following can use larger positions
            
            # Ensure reasonable bounds
            base_fraction = max(0.05, min(0.3, base_fraction))  # 5% to 30% of strategy capital
            
            return base_fraction
            
        except Exception as e:
            self.log_error("allocation_fraction", str(e))
            return 0.1  # Default 10%
    
    def record_capital_allocation_decision(self, strategy_name: str,
                                        symbol: str,
                                        allocation_amount: float,
                                        allocation_fraction: float,
                                        signal_confidence: float,
                                        reason: str):
        """Record capital allocation decision for analysis"""
        try:
            decision = {
                'timestamp': self._get_current_timestamp(),
                'strategy': strategy_name,
                'symbol': symbol,
                'allocation_amount': allocation_amount,
                'allocation_fraction': allocation_fraction,
                'signal_confidence': signal_confidence,
                'reason': reason
            }
            
            self._allocation_history.append(decision)
            
            # Keep only last 1000 records
            if len(self._allocation_history) > 1000:
                self._allocation_history = self._allocation_history[-1000:]
            
        except Exception as e:
            self.log_error("allocation_recording", str(e))
    
    def calculate_position_size(self, symbol: str, current_price: float,
                             strategy_capital: float, signal_confidence: float,
                             volatility: float, atr: float,
                             strategy_config: Dict[str, Any],
                             allocation_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculate optimal position size using signal, market, and symbol quality."""
        try:
            allocation_context = allocation_context or {}
            # Get strategy name for V2 risk settings
            strategy_name = strategy_config.get('name', 'unknown')
            
            # Get V2 Merged risk settings
            v2_risk = self.v2_risk_settings.get(strategy_name, {'risk_per_trade': 0.015, 'leverage': 1.0})
            
            # V2 Merged style calculation
            risk_per_trade = v2_risk['risk_per_trade']
            leverage = v2_risk['leverage']
            
            # Base position size (V2 Merged style)
            base_position_usdt = strategy_capital * risk_per_trade
            
            # Apply confidence multiplier
            confidence_multiplier = min(max(signal_confidence, 0.35), 1.0)

            # Market quality multiplier
            market_regime = allocation_context.get('market_regime', 'UNKNOWN')
            signal_side = allocation_context.get('signal_side', 'HOLD')
            trend_strength = self.safe_float_conversion(allocation_context.get('trend_strength'), 0.0)
            volume_ratio = self.safe_float_conversion(allocation_context.get('volume_ratio'), 1.0)
            active_position_count = int(allocation_context.get('active_position_count', 0) or 0)
            max_open_positions = max(1, int(allocation_context.get('max_open_positions', 10) or 10))

            regime_multiplier = 1.0
            if signal_side == 'BUY' and market_regime == 'BULL_TREND':
                regime_multiplier = 1.15
            elif signal_side == 'SELL' and market_regime == 'BEAR_TREND':
                regime_multiplier = 1.15
            elif signal_side == 'BUY' and market_regime == 'BEAR_TREND':
                regime_multiplier = 0.75
            elif signal_side == 'SELL' and market_regime == 'BULL_TREND':
                regime_multiplier = 0.75
            elif market_regime == 'HIGH_VOLATILITY':
                regime_multiplier = 0.8

            trend_multiplier = 0.9 + min(trend_strength / 100.0, 0.25)
            volume_multiplier = min(max(0.85 + (volume_ratio * 0.12), 0.75), 1.25)
            exposure_multiplier = max(0.65, 1.0 - max(active_position_count - 5, 0) * 0.04)

            # Symbol performance multiplier
            performance = allocation_context.get('symbol_performance', {}) or {}
            trade_count = int(performance.get('trade_count', 0) or 0)
            win_count = int(performance.get('win_count', 0) or 0)
            net_realized_pnl = self.safe_float_conversion(performance.get('net_realized_pnl'), 0.0)
            last_realized_pnl = self.safe_float_conversion(performance.get('last_realized_pnl'), 0.0)
            win_rate = (win_count / trade_count) if trade_count > 0 else 0.5

            performance_multiplier = 1.0
            if trade_count >= 2:
                if net_realized_pnl < 0:
                    performance_multiplier -= min(abs(net_realized_pnl) / 10.0, 0.25)
                if win_rate < 0.4:
                    performance_multiplier -= 0.1
                if net_realized_pnl > 0 and win_rate >= 0.5:
                    performance_multiplier += min(net_realized_pnl / 20.0, 0.15)
            if last_realized_pnl > 0:
                performance_multiplier += min(last_realized_pnl / 20.0, 0.05)
            elif last_realized_pnl < 0:
                performance_multiplier -= min(abs(last_realized_pnl) / 20.0, 0.05)
            performance_multiplier = min(max(performance_multiplier, 0.55), 1.2)

            quality_multiplier = (
                confidence_multiplier
                * regime_multiplier
                * trend_multiplier
                * volume_multiplier
                * exposure_multiplier
                * performance_multiplier
            )
            quality_multiplier = min(max(quality_multiplier, 0.25), 1.5)
            position_amount_usdt = base_position_usdt * quality_multiplier
            
            # Apply volatility scaling (V2 Merged style)
            if volatility > 0.03:  # High volatility penalty
                position_amount_usdt *= 0.75
            elif volatility < 0.01:  # Low volatility bonus
                position_amount_usdt *= 1.15

            risk_config = strategy_config.get('risk_config', {}) or {}
            max_position_size_usdt = self.safe_float_conversion(risk_config.get('max_position_size_usdt'), 0.0)
            if max_position_size_usdt <= 0:
                legacy_max_position_size = self.safe_float_conversion(risk_config.get('max_position_size'), 0.0)
                # Legacy configs may store a fraction such as 0.02 rather than a USDT cap.
                max_position_size_usdt = legacy_max_position_size if legacy_max_position_size > 1.0 else 0.0
            if max_position_size_usdt > 0:
                position_amount_usdt = min(position_amount_usdt, max_position_size_usdt)

            # Apply leverage effect after all allocation adjustments.
            leveraged_position_usdt = position_amount_usdt * leverage
            
            # Calculate position size in base currency
            position_size = position_amount_usdt / current_price
            
            # Tighten stops when recent evidence shows losses are too large.
            stop_loss_pct = risk_per_trade * 2
            stop_profile = 'base'
            if trade_count >= 2 and (net_realized_pnl < 0 or win_rate < 0.4):
                stop_loss_pct = min(stop_loss_pct, 0.012)
                stop_profile = 'loss_control'
            elif volatility > 0.03 or market_regime == 'HIGH_VOLATILITY':
                stop_loss_pct = min(stop_loss_pct, 0.015)
                stop_profile = 'high_volatility_control'
            elif market_regime == 'RANGING':
                stop_loss_pct = min(stop_loss_pct, 0.018)
                stop_profile = 'ranging_control'
            
            # Risk amount
            risk_amount_usdt = position_amount_usdt * risk_per_trade
            
            return {
                'position_size': position_size,
                'position_amount_usdt': position_amount_usdt,
                'leveraged_amount_usdt': leveraged_position_usdt,
                'allocation_fraction': position_amount_usdt / strategy_capital,
                'stop_loss_pct': stop_loss_pct,
                'risk_amount_usdt': risk_amount_usdt,
                'volatility_multiplier': 0.75 if volatility > 0.03 else (1.15 if volatility < 0.01 else 1.0),
                'take_profit_pct': risk_per_trade * 3,
                'leverage': leverage,
                'risk_per_trade': risk_per_trade,
                'stop_profile': stop_profile,
                'allocation_context': {
                    'confidence_multiplier': round(confidence_multiplier, 6),
                    'regime_multiplier': round(regime_multiplier, 6),
                    'trend_multiplier': round(trend_multiplier, 6),
                    'volume_multiplier': round(volume_multiplier, 6),
                    'exposure_multiplier': round(exposure_multiplier, 6),
                    'performance_multiplier': round(performance_multiplier, 6),
                    'quality_multiplier': round(quality_multiplier, 6),
                    'stop_profile': stop_profile,
                    'market_regime': market_regime,
                    'signal_side': signal_side,
                    'trend_strength': trend_strength,
                    'volume_ratio': volume_ratio,
                    'active_position_count': active_position_count,
                    'max_open_positions': max_open_positions,
                    'symbol_performance': performance
                }
            }
            
        except Exception as e:
            self.log_error("position_sizing", str(e))
            return {
                'position_size': 0.0,
                'position_amount_usdt': 0.0,
                'allocation_fraction': 0.0,
                'stop_loss_pct': 0.02,
                'risk_amount_usdt': 0.0,
                'volatility_multiplier': 1.0,
                'take_profit_pct': 0.04
            }
    
    def get_strategy_capital(self, strategy_name: str) -> float:
        """Get allocated capital for a specific strategy"""
        capital = self._strategy_capital.get(strategy_name, 0.0)
        
        # Fallback: if no capital allocated, provide default allocation
        if capital <= 0 and len(self._strategy_capital) == 0:
            # Provide minimum capital for trading
            return 1000.0  # Default $1000 per strategy
        
        return capital
    
    def get_allocation_summary(self) -> Dict[str, Any]:
        """Get summary of current allocations"""
        try:
            total_allocated = sum(self._strategy_capital.values())
            
            return {
                'total_strategies': len(self._strategy_capital),
                'total_allocated_capital': total_allocated,
                'strategy_allocations': self._strategy_capital.copy(),
                'allocation_count': len(self._allocation_history),
                'last_allocation_time': self._allocation_history[-1]['timestamp'] if self._allocation_history else None
            }
            
        except Exception as e:
            self.log_error("allocation_summary", str(e))
            return {}
    
    def _get_current_timestamp(self) -> int:
        """Get current timestamp"""
        import time
        return int(time.time() * 1000)
