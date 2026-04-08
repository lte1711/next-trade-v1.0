"""
Pending Order Manager - 미체결 주문 관리 전담 모듈
"""

import time
from datetime import datetime


class PendingOrderManager:
    """미체결 주문 상태 추적, 전환 처리, 카운터 관리 전담"""
    
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
        """미체결 주문 상태 새로고침 및 전환 처리"""
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
                
                # 진입 주문이 지연/부분체결 후 FILLED로 바뀐 경우 보호주문 재설치
                if (not trade.get("reduce_only")) and old_status in {"NEW", "PARTIALLY_FILLED"}:
                    print(f"[TRACE] PENDING_TO_FILLED | {symbol} | old={old_status} | new={trade['status']}")
                    self.position_entry_times[symbol] = trade.get("timestamp", datetime.now().isoformat())
                    
                    # 중복 보호주문 방지: 기존 보호주문 먼저 정리 후 재설치
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
                    
                    # 완전청산 판정 직전 포지션 동기화
                    if callable(self.sync_positions):
                        self.sync_positions()
                    
                    # 완전청산 여부 확인
                    remaining_position = self.trading_results["active_positions"].get(symbol)
                    
                    # 완전청산일 때만 상태 초기화 + 보호주문 취소
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
        """실현 손익 추정"""
        try:
            entry_price = self.safe_float_conversion(trade.get("entry_price"), 0.0)
            exit_price = self.safe_float_conversion(trade.get("price"), 0.0)
            quantity = self.safe_float_conversion(trade.get("executed_qty"), 0.0)

            if entry_price > 0 and exit_price > 0 and quantity > 0:
                if trade.get("side") == "BUY":
                    return (exit_price - entry_price) * quantity
                else:
                    return (entry_price - exit_price) * quantity
        except Exception:
            pass
        return 0.0
    
    def safe_float_conversion(self, value, default=0.0):
        """안전한 float 변환"""
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default
    
    def recompute_trade_counters(self):
        """거래 카운터 재계산"""
        try:
            real_orders = self.trading_results.get("real_orders", [])
            pending_trades = [t for t in real_orders if t.get("type") == "PENDING_TRADE"]
            closed_trades = [t for t in real_orders if t.get("type") in {"ACTUAL_TRADE", "FAILED_TRADE"}]
            
            self.trading_results["pending_trades"] = pending_trades
            self.trading_results["closed_trades"] = closed_trades
            self.trading_results["total_trades"] = len(real_orders)
        except Exception:
            pass
