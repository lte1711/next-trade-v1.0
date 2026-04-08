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
                return {}
            
            # Base allocation (equal weight initially)
            base_allocation = total_capital / len(active_strategies)
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
                             strategy_config: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate optimal position size"""
        try:
            # Calculate allocation fraction
            allocation_fraction = self.calculate_allocation_fraction(
                'current_strategy', signal_confidence, strategy_capital, strategy_config
            )
            
            # Calculate position amount in USDT
            position_amount_usdt = strategy_capital * allocation_fraction
            
            # Apply volatility multiplier
            volatility_multiplier = self.calculate_volatility_size_multiplier(
                symbol, volatility, strategy_config
            )
            position_amount_usdt *= volatility_multiplier
            
            # Calculate position size in base currency
            position_size = position_amount_usdt / current_price
            
            # Calculate stop loss
            stop_loss_pct = self.estimate_stop_loss_pct(
                symbol, current_price, atr, volatility, strategy_config
            )
            
            # Risk amount
            risk_amount_usdt = position_amount_usdt * stop_loss_pct
            
            # Ensure position doesn't exceed strategy limits
            max_position_usdt = strategy_config.get('risk_config', {}).get('max_position_size_usdt', 1000.0)
            if position_amount_usdt > max_position_usdt:
                position_amount_usdt = max_position_usdt
                position_size = position_amount_usdt / current_price
                risk_amount_usdt = position_amount_usdt * stop_loss_pct
            
            return {
                'position_size': position_size,
                'position_amount_usdt': position_amount_usdt,
                'allocation_fraction': allocation_fraction,
                'stop_loss_pct': stop_loss_pct,
                'risk_amount_usdt': risk_amount_usdt,
                'volatility_multiplier': volatility_multiplier,
                'take_profit_pct': strategy_config.get('risk_config', {}).get('take_profit_pct', 0.04)
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
        return self._strategy_capital.get(strategy_name, 0.0)
    
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
