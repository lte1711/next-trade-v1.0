"""
V2 Merged Partial Take Profit Manager
Handles partial take profit logic for position management
"""

from datetime import datetime
from typing import Dict, Any, Optional


class PartialTakeProfitManager:
    """V2 Merged style partial take profit management"""
    
    def __init__(self, trading_results=None, log_error_callback=None):
        self.trading_results = trading_results if isinstance(trading_results, dict) else {}
        self.log_error = log_error_callback or self._default_log_error
        self.partial_take_profit_state = self.trading_results.setdefault("partial_take_profit_state", {})
        self.managed_stop_prices = self.trading_results.setdefault("managed_stop_prices", {})
    
    def _default_log_error(self, error_type, message):
        """Default error logging"""
        print(f"[ERROR] {error_type}: {message}")
    
    def get_position_management_state(self, symbol):
        """Return mutable management state for an active symbol."""
        state = self.partial_take_profit_state.get(symbol)
        if state is None:
            state = {
                "tp1_done": False,
                "tp2_done": False,
                "fast_tp1_done": False,
                "fast_tp2_done": False,
                "last_partial_close_at": None,
            }
            self.partial_take_profit_state[symbol] = state
        return state
    
    def clear_position_management_state(self, symbol):
        """Clear partial take-profit and stop-tracking state for a symbol."""
        self.partial_take_profit_state.pop(symbol, None)
        self.managed_stop_prices.pop(symbol, None)
    
    def get_position_profit_pct(self, position, entry_price):
        """Calculate position profit percentage"""
        try:
            if not position or entry_price <= 0:
                return 0.0
            
            current_price = position.get('markPrice', 0.0)
            if current_price <= 0:
                return 0.0
            
            position_side = position.get('positionSide', 'BOTH')
            position_amt = position.get('positionAmt', 0.0)
            
            if position_amt > 0:  # Long
                profit_pct = (current_price - entry_price) / entry_price
            else:  # Short
                profit_pct = (entry_price - current_price) / entry_price
            
            return profit_pct
            
        except Exception as e:
            self.log_error("profit_calculation", str(e))
            return 0.0
    
    def check_partial_take_profit(self, symbol, position, entry_price, 
                                 strategy_config, entry_mode='NORMAL'):
        """Check and execute partial take profit logic"""
        try:
            if not position or entry_price <= 0:
                return False
            
            profit_pct = self.get_position_profit_pct(position, entry_price)
            if profit_pct <= 0:
                return False
            
            state = self.get_position_management_state(symbol)
            risk_config = strategy_config.get('risk_config', {})
            
            # V2 Merged partial take profit thresholds
            partial_tp1_pct = risk_config.get('partial_tp1_pct', 0.005)  # 0.5%
            partial_tp2_pct = risk_config.get('partial_tp2_pct', 0.011)  # 1.1%
            fast_tp1_pct = risk_config.get('fast_tp1_pct', 0.004)       # 0.4%
            fast_tp2_pct = risk_config.get('fast_tp2_pct', 0.009)       # 0.9%
            fast_tp1_close_ratio = risk_config.get('fast_tp1_close_ratio', 0.45)
            
            is_fast_entry = entry_mode in {'FAST_LONG', 'FAST_SHORT'}
            
            # Check and execute partial take profits
            executed = False
            
            if is_fast_entry:
                # Fast entry partial take profits
                if (not state.get("fast_tp1_done")) and profit_pct >= fast_tp1_pct:
                    executed = self._execute_partial_close(
                        symbol, position, fast_tp1_close_ratio, "FAST_TP1"
                    )
                    if executed:
                        state["fast_tp1_done"] = True
                        state["last_partial_close_at"] = datetime.now()
                
                elif (not state.get("fast_tp2_done")) and profit_pct >= fast_tp2_pct:
                    executed = self._execute_partial_close(
                        symbol, position, 1.0, "FAST_TP2"
                    )
                    if executed:
                        state["fast_tp2_done"] = True
                        state["last_partial_close_at"] = datetime.now()
            else:
                # Normal partial take profits
                if (not state.get("tp1_done")) and profit_pct >= partial_tp1_pct:
                    executed = self._execute_partial_close(
                        symbol, position, 0.45, "TP1"
                    )
                    if executed:
                        state["tp1_done"] = True
                        state["last_partial_close_at"] = datetime.now()
                
                elif (not state.get("tp2_done")) and profit_pct >= partial_tp2_pct:
                    executed = self._execute_partial_close(
                        symbol, position, 1.0, "TP2"
                    )
                    if executed:
                        state["tp2_done"] = True
                        state["last_partial_close_at"] = datetime.now()
            
            return executed
            
        except Exception as e:
            self.log_error("partial_take_profit_check", str(e))
            return False
    
    def _execute_partial_close(self, symbol, position, close_ratio, reason):
        """Execute partial position close"""
        try:
            position_amt = position.get('positionAmt', 0.0)
            if position_amt == 0:
                return False
            
            # Calculate close amount
            close_amount = abs(position_amt) * close_ratio
            
            # Determine order side
            if position_amt > 0:  # Long position
                order_side = 'SELL'
            else:  # Short position
                order_side = 'BUY'
            
            print(f"[PARTIAL_CLOSE] {symbol} | {reason} | {order_side} | {close_amount} | ratio={close_ratio}")
            
            # Here you would submit the actual order
            # For now, just log the action
            return True
            
        except Exception as e:
            self.log_error("partial_close_execute", str(e))
            return False
    
    def update_trailing_stop(self, symbol, position, entry_price, trail_pct=0.01):
        """Update trailing stop loss"""
        try:
            if not position or entry_price <= 0:
                return False
            
            profit_pct = self.get_position_profit_pct(position, entry_price)
            if profit_pct <= 0.02:  # Only trail if profitable by 2%
                return False
            
            current_price = position.get('markPrice', 0.0)
            position_amt = position.get('positionAmt', 0.0)
            
            if position_amt > 0:  # Long
                new_stop_price = current_price * (1 - trail_pct)
                old_stop_price = self.managed_stop_prices.get(symbol, 0)
                
                if new_stop_price > old_stop_price:
                    self.managed_stop_prices[symbol] = new_stop_price
                    print(f"[TRAILING_STOP] {symbol} | LONG | {new_stop_price}")
                    return True
            else:  # Short
                new_stop_price = current_price * (1 + trail_pct)
                old_stop_price = self.managed_stop_prices.get(symbol, 0)
                
                if new_stop_price < old_stop_price or old_stop_price == 0:
                    self.managed_stop_prices[symbol] = new_stop_price
                    print(f"[TRAILING_STOP] {symbol} | SHORT | {new_stop_price}")
                    return True
            
            return False
            
        except Exception as e:
            self.log_error("trailing_stop_update", str(e))
            return False
