"""
Pending Order Manager - Pending Order Management Module
"""

import time
from datetime import datetime


class PendingOrderManager:
    """Pending order status tracking, conversion processing, and counter management"""
    
    def __init__(self, trading_results, get_order_status_callback, log_error_callback, 
                 position_entry_times, protective_order_manager, clear_position_state_callback, sync_positions_callback=None):
        self.trading_results = trading_results
        self.get_order_status = get_order_status_callback
        self.log_error = log_error_callback
        self.position_entry_times = position_entry_times
        self.protective_order_manager = protective_order_manager
        self.clear_position_management_state = clear_position_state_callback
        self.sync_positions = sync_positions_callback
    
    def refresh_pending_orders(self):
        """Refresh pending order status and handle conversions"""
        for trade in self.trading_results.get("real_orders", []):
            if trade.get("status") not in {"NEW", "PARTIALLY_FILLED"}:
                continue
            
            order_id = trade.get("order_id")
            symbol = trade.get("symbol")
            if not order_id or order_id == "UNKNOWN" or not symbol:
                continue
            
            old_status = trade.get("status")
            refreshed_status = self.get_order_status(symbol, order_id)
            if not refreshed_status:
                continue
            
            trade["status"] = refreshed_status.get("status", trade.get("status"))
            trade["executed_qty"] = self.safe_float_conversion(
                refreshed_status.get("executedQty"),
                trade.get("executed_qty", 0.0)
            )
            
            refreshed_price = self.safe_float_conversion(
                refreshed_status.get("avgPrice"),
                trade.get("price", 0.0)
            )
            if refreshed_price > 0:
                trade["price"] = refreshed_price
            
            if trade["status"] in {"NEW", "PARTIALLY_FILLED"}:
                trade["type"] = "PENDING_TRADE"
            
            elif trade["status"] == "FILLED":
                trade["type"] = "ACTUAL_TRADE"
                
                # Reinstall protective orders when entry order changes from delayed/partial fill to FILLED
                if (not trade.get("reduce_only")) and old_status in {"NEW", "PARTIALLY_FILLED"}:
                    print(f"[TRACE] PENDING_TO_FILLED | {symbol} | old={old_status} | new={trade['status']}")
                    self.position_entry_times[symbol] = trade.get("timestamp", datetime.now().isoformat())

                    active_position = self.trading_results.get("active_positions", {}).get(symbol)
                    if not active_position or abs(active_position.get("amount", 0.0)) == 0:
                        print(f"[TRACE] SKIP_PROTECTIVE_REINSTALL_NO_POSITION | {symbol}")
                        continue
                    
                    # Prevent duplicate protective orders: cancel existing orders first, then reinstall
                    self.protective_order_manager.cancel_symbol_protective_orders(symbol)
                    self.protective_order_manager.place_protective_orders(
                        trade.get("strategy"),
                        symbol,
                        trade.get("side"),
                        trade.get("price"),
                    )
            else:
                trade["type"] = "FAILED_TRADE"
            
            if trade.get("reduce_only"):
                if trade["status"] == "FILLED":
                    trade["realized_pnl"] = self.estimate_realized_pnl(trade)
                    self._record_realized_pnl_event(trade)
                    
                    # Synchronize positions just before determining full exit
                    if callable(self.sync_positions):
                        self.sync_positions()
                    
                    # Check for full exit
                    remaining_position = self.trading_results["active_positions"].get(symbol)
                    
                    # Only initialize state and cancel protective orders on full exit
                    if not remaining_position or abs(remaining_position.get("amount", 0.0)) == 0:
                        print(f"[TRACE] FULL_EXIT_CONFIRMED | {symbol}")
                        self.trading_results["recently_closed_symbols"][symbol] = datetime.now().isoformat()
                        self.position_entry_times.pop(symbol, None)
                        self.clear_position_management_state(symbol)
                        self.protective_order_manager.cancel_symbol_protective_orders(symbol)
                    else:
                        print(f"[TRACE] PARTIAL_EXIT_CONFIRMED | {symbol} | remaining={remaining_position.get('amount', 0.0)}")
        
        self.recompute_trade_counters()
    
    def estimate_realized_pnl(self, trade):
        """Estimate realized profit/loss"""
        try:
            entry_price = self.safe_float_conversion(trade.get("entry_price"), 0.0)
            exit_price = self.safe_float_conversion(trade.get("price"), 0.0)
            quantity = self.safe_float_conversion(trade.get("executed_qty"), 0.0)

            if entry_price > 0 and exit_price > 0 and quantity > 0:
                exit_side = trade.get("side")
                if exit_side == "SELL":
                    return (exit_price - entry_price) * quantity
                if exit_side == "BUY":
                    return (entry_price - exit_price) * quantity
        except Exception:
            pass
        return 0.0
    
    def safe_float_conversion(self, value, default=0.0):
        """Safe float conversion"""
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default

    def _record_realized_pnl_event(self, trade):
        """Persist realized PnL events for audit and adaptive ranking."""
        try:
            order_id = trade.get("order_id")
            if not order_id or order_id == "UNKNOWN":
                return

            journal = self.trading_results.setdefault("realized_pnl_journal", [])
            if any(entry.get("order_id") == order_id for entry in journal):
                return

            realized_pnl = self.safe_float_conversion(trade.get("realized_pnl"), 0.0)
            symbol = trade.get("symbol")
            strategy = trade.get("strategy") or "unknown"
            journal.append({
                "timestamp": trade.get("timestamp"),
                "order_id": order_id,
                "symbol": symbol,
                "strategy": strategy,
                "side": trade.get("side"),
                "entry_price": self.safe_float_conversion(trade.get("entry_price"), 0.0),
                "exit_price": self.safe_float_conversion(trade.get("price"), 0.0),
                "executed_qty": self.safe_float_conversion(trade.get("executed_qty"), 0.0),
                "realized_pnl": realized_pnl,
                "exit_reason": trade.get("exit_reason"),
            })
            if len(journal) > 500:
                self.trading_results["realized_pnl_journal"] = journal[-250:]

            performance_map = self.trading_results.setdefault("symbol_performance", {})
            symbol_stats = performance_map.setdefault(symbol, {
                "trade_count": 0,
                "win_count": 0,
                "loss_count": 0,
                "net_realized_pnl": 0.0,
                "last_realized_pnl": 0.0,
                "last_strategy": strategy,
                "last_updated": None,
            })
            symbol_stats["trade_count"] += 1
            if realized_pnl > 0:
                symbol_stats["win_count"] += 1
            elif realized_pnl < 0:
                symbol_stats["loss_count"] += 1
            symbol_stats["net_realized_pnl"] = round(
                self.safe_float_conversion(symbol_stats.get("net_realized_pnl"), 0.0) + realized_pnl,
                8,
            )
            symbol_stats["last_realized_pnl"] = realized_pnl
            symbol_stats["last_strategy"] = strategy
            symbol_stats["last_updated"] = trade.get("timestamp")
        except Exception:
            pass
    
    def recompute_trade_counters(self):
        """Recalculate trade counters"""
        try:
            real_orders = self.trading_results.get("real_orders", [])
            pending_trades = [t for t in real_orders if t.get("type") == "PENDING_TRADE"]
            closed_trades = [t for t in real_orders if t.get("type") in {"ACTUAL_TRADE", "FAILED_TRADE"}]
            
            self.trading_results["pending_trades"] = pending_trades
            self.trading_results["closed_trades"] = closed_trades
            self.trading_results["total_trades"] = len(real_orders)
        except Exception:
            pass
