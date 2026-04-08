"""
Position Manager - Active position management and profit/loss control
"""

from typing import List, Dict, Optional, Any, Tuple
from decimal import Decimal
import json
from datetime import datetime

class PositionManager:
    """Active position management and profit/loss control"""
    
    def __init__(self, trading_results: Dict[str, Any], 
                 order_executor, protective_order_manager,
                 log_error_callback=None):
        self.trading_results = trading_results
        self.order_executor = order_executor
        self.protective_order_manager = protective_order_manager
        self.log_error = log_error_callback or self._default_log_error
        self._position_states = {}
    
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
    
    def get_position_management_state(self, symbol: str) -> Dict[str, Any]:
        """Get current position management state for symbol"""
        try:
            active_positions = self.trading_results.get("active_positions", {})
            position = active_positions.get(symbol, {})
            
            if not position:
                return {}
            
            # Calculate position metrics
            current_price = position.get("current_price", 0.0)
            entry_price = position.get("entry_price", 0.0)
            amount = position.get("amount", 0.0)
            
            if entry_price > 0 and current_price > 0:
                if amount > 0:  # Long position
                    unrealized_pnl = (current_price - entry_price) * amount
                    pnl_pct = (current_price - entry_price) / entry_price
                else:  # Short position
                    unrealized_pnl = (entry_price - current_price) * abs(amount)
                    pnl_pct = (entry_price - current_price) / entry_price
            else:
                unrealized_pnl = 0.0
                pnl_pct = 0.0
            
            # Get position state
            state = self._position_states.get(symbol, {})
            
            return {
                'symbol': symbol,
                'amount': amount,
                'entry_price': entry_price,
                'current_price': current_price,
                'unrealized_pnl': unrealized_pnl,
                'pnl_pct': pnl_pct,
                'entry_time': position.get("entry_time"),
                'hold_seconds': self._get_position_hold_seconds(symbol),
                'partial_take_profit_state': state.get('partial_take_profit_state', {}),
                'stop_loss_adjusted': state.get('stop_loss_adjusted', False),
                'trailing_active': state.get('trailing_active', False)
            }
            
        except Exception as e:
            self.log_error("position_state_get", str(e))
            return {}
    
    def clear_position_management_state(self, symbol: str):
        """Clear position management state for symbol"""
        try:
            if symbol in self._position_states:
                del self._position_states[symbol]
            
            # Clear from trading results
            partial_tp_state = self.trading_results.get("partial_take_profit_state", {})
            if symbol in partial_tp_state:
                del partial_tp_state[symbol]
                
        except Exception as e:
            self.log_error("position_state_clear", str(e))
    
    def get_position_profit_pct(self, symbol: str) -> float:
        """Get position profit percentage"""
        try:
            state = self.get_position_management_state(symbol)
            return state.get('pnl_pct', 0.0)
        except Exception as e:
            self.log_error("profit_pct_calc", str(e))
            return 0.0
    
    def get_position_entry_mode(self, symbol: str) -> str:
        """Get position entry mode"""
        try:
            position = self.trading_results.get("active_positions", {}).get(symbol, {})
            return position.get("entry_mode", "UNKNOWN")
        except Exception as e:
            self.log_error("entry_mode_get", str(e))
            return "UNKNOWN"
    
    def get_position_hold_seconds(self, symbol: str) -> int:
        """Get how long position has been held in seconds"""
        return self._get_position_hold_seconds(symbol)
    
    def _get_position_hold_seconds(self, symbol: str) -> int:
        """Internal calculation of position hold time"""
        try:
            position = self.trading_results.get("active_positions", {}).get(symbol, {})
            entry_time = position.get("entry_time")
            
            if entry_time:
                current_time = int(datetime.now().timestamp() * 1000)
                hold_seconds = (current_time - entry_time) // 1000
                return max(0, hold_seconds)
            
            return 0
            
        except Exception as e:
            self.log_error("hold_time_calc", str(e))
            return 0
    
    def should_force_close_for_max_hold(self, symbol: str, max_hold_minutes: int = 30) -> bool:
        """Check if position should be closed due to maximum hold time"""
        try:
            hold_seconds = self.get_position_hold_seconds(symbol)
            max_hold_seconds = max_hold_minutes * 60
            
            return hold_seconds >= max_hold_seconds
            
        except Exception as e:
            self.log_error("max_hold_check", str(e))
            return False
    
    def should_force_close_for_funding(self, symbol: str, funding_rate: float = 0.0) -> bool:
        """Check if position should be closed due to unfavorable funding rate"""
        try:
            if funding_rate == 0.0:
                return False
            
            position = self.trading_results.get("active_positions", {}).get(symbol, {})
            amount = position.get("amount", 0.0)
            
            # For long positions, negative funding is bad
            # For short positions, positive funding is bad
            if amount > 0 and funding_rate < -0.001:  # -0.1% threshold
                return True
            elif amount < 0 and funding_rate > 0.001:  # 0.1% threshold
                return True
            
            return False
            
        except Exception as e:
            self.log_error("funding_close_check", str(e))
            return False
    
    def tighten_symbol_stop(self, symbol: str, new_stop_pct: float):
        """Tighten stop loss for symbol"""
        try:
            position = self.trading_results.get("active_positions", {}).get(symbol, {})
            if not position:
                return False
            
            current_price = position.get("current_price", 0.0)
            amount = position.get("amount", 0.0)
            
            if amount > 0:  # Long position
                new_stop_price = current_price * (1 - new_stop_pct)
            else:  # Short position
                new_stop_price = current_price * (1 + new_stop_pct)
            
            # Update protective order
            success = self.protective_order_manager.update_stop_loss(
                symbol, new_stop_price, amount
            )
            
            if success:
                state = self._position_states.setdefault(symbol, {})
                state['stop_loss_adjusted'] = True
                state['last_adjustment_time'] = int(datetime.now().timestamp() * 1000)
            
            return success
            
        except Exception as e:
            self.log_error("stop_tighten", str(e))
            return False
    
    def close_partial_position(self, symbol: str, close_fraction: float,
                        reason: str = "partial_profit_take") -> bool:
        """Close partial position"""
        try:
            position = self.trading_results.get("active_positions", {}).get(symbol, {})
            if not position:
                return False

            current_amount = position.get("amount", 0.0)
            if current_amount == 0.0:
                return False

            close_amount = abs(current_amount) * close_fraction
            order_side = "SELL" if current_amount > 0 else "BUY"
            strategy_name = position.get("strategy", "position_management")

            order_result = self.order_executor.submit_order(
                strategy_name=strategy_name,
                symbol=symbol,
                side=order_side,
                quantity=close_amount,
                reduce_only=True,
                metadata={
                    "exit_reason": reason,
                    "entry_price": position.get("entry_price", 0.0)
                }
            )

            if order_result and order_result.get("status") in {"FILLED", "NEW", "PARTIALLY_FILLED"}:
                state = self._position_states.setdefault(symbol, {})
                partial_tp = state.setdefault('partial_take_profit_state', {})
                partial_tp['last_partial_close'] = {
                    'timestamp': int(datetime.now().timestamp() * 1000),
                    'fraction': close_fraction,
                    'amount': close_amount,
                    'reason': reason
                }

                print(f"[INFO] Partial position closed for {symbol}: {close_fraction:.1%} ({reason})")
                return True

            return False

        except Exception as e:
            self.log_error("partial_close", str(e))
            return False
    
    def manage_profit_targets(self, symbol: str, strategy_config: Dict[str, Any]):
        """Manage profit targets and partial exits"""
        try:
            state = self.get_position_management_state(symbol)
            if not state:
                return
            
            pnl_pct = state.get('pnl_pct', 0.0)
            partial_tp_state = state.get('partial_take_profit_state', {})
            
            # Get strategy configuration
            risk_config = strategy_config.get('risk_config', {})
            take_profit_pct = risk_config.get('take_profit_pct', 0.04)
            
            # Partial profit taking levels
            partial_levels = [0.5, 1.0, 1.5]  # 50%, 100%, 150% of target
            
            for i, level in enumerate(partial_levels):
                target_pct = take_profit_pct * level
                close_fraction = 0.25 + (i * 0.25)  # 25%, 50%, 75%
                
                # Check if this level has been hit
                if pnl_pct >= target_pct:
                    level_key = f"level_{i+1}"
                    if not partial_tp_state.get(level_key):
                        # Execute partial close
                        if self.close_partial_position(symbol, close_fraction, f"partial_tp_level_{i+1}"):
                            partial_tp_state[level_key] = {
                                'timestamp': int(datetime.now().timestamp() * 1000),
                                'pnl_pct': pnl_pct,
                                'close_fraction': close_fraction
                            }
                            
                            # Update state
                            self._position_states[symbol]['partial_take_profit_state'] = partial_tp_state
            
        except Exception as e:
            self.log_error("profit_target_manage", str(e))
    
    def should_exit_position_ma(self, symbol: str, ma_analysis: Dict[str, List[float]], 
                              current_price: float, index: int = -1) -> bool:
        """Check if position should be closed based on MA crossover"""
        try:
            if not ma_analysis or index >= len(ma_analysis.get('fast_ma', [])):
                return False
            
            fast_ma = ma_analysis['fast_ma'][index]
            slow_ma = ma_analysis['slow_ma'][index]
            fast_above_slow = ma_analysis.get('fast_above_slow', [])[index] if index < len(ma_analysis.get('fast_above_slow', [])) else False
            
            if fast_ma is None or slow_ma is None:
                return False
            
            position = self.trading_results.get("active_positions", {}).get(symbol, {})
            amount = position.get("amount", 0.0)
            
            if amount > 0:  # Long position - exit when fast crosses below slow
                return not fast_above_slow and current_price < slow_ma
            else:  # Short position - exit when fast crosses above slow
                return fast_above_slow and current_price > slow_ma
            
        except Exception as e:
            self.log_error("ma_exit_check", str(e))
            return False
    
    def should_exit_position_ema21_trailing(self, symbol: str, ema21: List[float], 
                                          current_price: float, index: int = -1) -> bool:
        """Check if position should be closed based on EMA21 trailing"""
        try:
            if not ema21 or index >= len(ema21) or ema21[index] is None:
                return False
            
            current_ema21 = ema21[index]
            
            position = self.trading_results.get("active_positions", {}).get(symbol, {})
            amount = position.get("amount", 0.0)
            
            if amount > 0:  # Long position - trail EMA21, exit when price closes below
                return current_price < current_ema21
            else:  # Short position - trail EMA21, exit when price closes above
                return current_price > current_ema21
            
        except Exception as e:
            self.log_error("ema_trailing_exit", str(e))
            return False
    
    def close_position(self, symbol: str, reason: str = "manual_close") -> bool:
        """Close entire position"""
        try:
            position = self.trading_results.get("active_positions", {}).get(symbol, {})
            if not position:
                return False

            current_amount = position.get("amount", 0.0)
            if current_amount == 0.0:
                return False

            order_side = "SELL" if current_amount > 0 else "BUY"
            strategy_name = position.get("strategy", "position_management")

            order_result = self.order_executor.submit_order(
                strategy_name=strategy_name,
                symbol=symbol,
                side=order_side,
                quantity=abs(current_amount),
                reduce_only=True,
                metadata={
                    "exit_reason": reason,
                    "entry_price": position.get("entry_price", 0.0)
                }
            )

            if order_result and order_result.get("status") in {"FILLED", "NEW", "PARTIALLY_FILLED"}:
                self.clear_position_management_state(symbol)

                if symbol in self.trading_results.get("active_positions", {}):
                    del self.trading_results["active_positions"][symbol]

                print(f"[INFO] Position closed for {symbol}: {reason}")
                return True

            return False

        except Exception as e:
            self.log_error("position_close", str(e))
            return False
    
    def manage_open_positions(self, market_data: Dict[str, Any], 
                           indicators: Dict[str, Any],
                           strategy_config: Dict[str, Any]):
        """Manage all open positions"""
        try:
            active_positions = self.trading_results.get("active_positions", {})
            
            for symbol in list(active_positions.keys()):
                position = active_positions[symbol]
                if not position or position.get("amount", 0.0) == 0.0:
                    continue
                
                # Update current price
                symbol_data = market_data.get(symbol, {})
                current_price = symbol_data.get("prices", {}).get("current", 0.0)
                if current_price > 0:
                    position["current_price"] = current_price
                
                # Get position state
                state = self.get_position_management_state(symbol)
                
                # Check various exit conditions
                
                # 3. Profit targets management
                symbol_strategy_config = strategy_config.get(symbol, {}) if isinstance(strategy_config, dict) else {}
                if symbol_strategy_config:
                    self.manage_profit_targets(symbol, symbol_strategy_config)
                
                # 4. EMA21 trailing exit
                ema_data = indicators.get(symbol, {}).get('ema_data', {})
                ema21 = ema_data.get('ema21', [])
                if self.should_exit_position_ema21_trailing(symbol, ema21, current_price):
                    self.close_position(symbol, "ema21_trailing")
                    continue
                
                # 5. Stop loss management (handled by protective orders)
                # This is mainly for emergency stop loss adjustments
                
        except Exception as e:
            self.log_error("positions_manage", str(e))
    
    def get_position_summary(self) -> Dict[str, Any]:
        """Get summary of all positions"""
        try:
            active_positions = self.trading_results.get("active_positions", {})
            
            summary = {
                'total_positions': len(active_positions),
                'long_positions': 0,
                'short_positions': 0,
                'total_unrealized_pnl': 0.0,
                'positions': []
            }
            
            for symbol, position in active_positions.items():
                amount = position.get("amount", 0.0)
                if amount > 0:
                    summary['long_positions'] += 1
                elif amount < 0:
                    summary['short_positions'] += 1
                
                state = self.get_position_management_state(symbol)
                summary['total_unrealized_pnl'] += state.get('unrealized_pnl', 0.0)
                
                summary['positions'].append({
                    'symbol': symbol,
                    'amount': amount,
                    'entry_price': position.get('entry_price', 0.0),
                    'current_price': position.get('current_price', 0.0),
                    'unrealized_pnl': state.get('unrealized_pnl', 0.0),
                    'pnl_pct': state.get('pnl_pct', 0.0),
                    'hold_seconds': state.get('hold_seconds', 0)
                })
            
            return summary
            
        except Exception as e:
            self.log_error("position_summary", str(e))
            return {}
