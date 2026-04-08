"""
Order Executor - 주문 실행 전담 모듈
"""

import requests
import time
import hmac
import hashlib
from datetime import datetime
from decimal import Decimal, ROUND_DOWN, ROUND_UP


class OrderExecutor:
    """주문 실행, 수량 검증, 재시도 로직 전담"""
    
    def __init__(self, api_key, api_secret, base_url, trading_results, symbol_info_getter, 
                 log_error_callback, safe_float_conversion, round_to_step, capital_getter=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.trading_results = trading_results
        self.get_symbol_info = symbol_info_getter
        self.log_error = log_error_callback
        self.safe_float_conversion = safe_float_conversion
        self.round_to_step = round_to_step
        self.get_total_capital = capital_getter
    
    def submit_order(self, strategy_name, symbol, side, quantity, reduce_only=False, metadata=None):
        """주문 실행 및 검증"""
        try:
            metadata = metadata or {}
            metadata.setdefault("market_session", self.get_market_session())
            
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                self.log_error("symbol_info_missing", f"No symbol metadata found for {symbol}")
                return None
            
            filters = symbol_info["filters"]
            min_qty = 0.0
            max_qty = 0.0
            min_notional = 0.0
            qty_precision = 0
            step_size = 0.0
            
            for f in filters:
                if f["filterType"] == "LOT_SIZE":
                    min_qty = float(f["minQty"])
                    max_qty = float(f["maxQty"])
                    if "stepSize" in f:
                        step_size = float(f["stepSize"])
                        step_size_str = format(Decimal(str(step_size)).normalize(), "f")
                        if "." in step_size_str:
                            qty_precision = len(step_size_str.rstrip("0").split('.')[1])
                        else:
                            qty_precision = 0
                    else:
                        qty_precision = 8
                elif f["filterType"] == "MIN_NOTIONAL":
                    min_notional = self.safe_float_conversion(f.get("notional"), min_notional)
                elif f["filterType"] == "NOTIONAL":
                    min_notional = self.safe_float_conversion(f.get("minNotional"), min_notional)
            
            if min_notional <= 0:
                min_notional = 5.0
            
            # reduce_only일 때는 수량 증액 금지
            if not reduce_only:
                if quantity < min_qty:
                    quantity = min_qty
                current_price = self.get_current_price(symbol, 0.0)
                if current_price <= 0:
                    self.log_error("price_lookup_failed", f"Blocked order for {symbol} because price lookup failed")
                    return None
                
                if step_size > 0:
                    quantity = self.round_to_step(quantity, step_size, ROUND_UP)
                else:
                    quantity = round(quantity, qty_precision)
                
                current_notional = quantity * current_price
                if current_notional < min_notional:
                    required_qty = (min_notional * 1.05) / current_price
                    quantity = max(quantity, required_qty, min_qty)
                    if step_size > 0:
                        quantity = self.round_to_step(quantity, step_size, ROUND_UP)
                    else:
                        quantity = round(quantity, qty_precision)
            else:
                # reduce_only는 step_size만 적용하고 수량 증액 금지
                current_price = self.get_current_price(symbol, 0.0)
                if current_price <= 0:
                    self.log_error("price_lookup_failed", f"Blocked order for {symbol} because price lookup failed")
                    return None
                
                if step_size > 0:
                    quantity = self.round_to_step(quantity, step_size, ROUND_DOWN)
                else:
                    quantity = round(quantity, qty_precision)
            
            if quantity > max_qty:
                quantity = max_qty
            if step_size > 0:
                quantity = self.round_to_step(quantity, step_size, ROUND_DOWN)
            else:
                quantity = round(quantity, qty_precision)
            
            # reduce_only 주문은 최종 min_qty/min_notional 검증 건너뛰기
            if not reduce_only:
                if quantity < min_qty:
                    quantity = min_qty
                    if step_size > 0:
                        quantity = self.round_to_step(quantity, step_size, ROUND_UP)
                
                final_notional = quantity * current_price
                if final_notional < min_notional:
                    error_msg = f"{symbol} order quantity validation failed: quantity={quantity}, notional={final_notional:.6f}, min_notional={min_notional:.6f}"
                    self.log_error("min_notional_not_met", error_msg)
                    return None
            
            fallback_capital = 0.0
            if callable(self.get_total_capital):
                fallback_capital = self.safe_float_conversion(self.get_total_capital(), 0.0)
            
            available_balance = self.safe_float_conversion(
                self.trading_results.get("available_balance"),
                fallback_capital
            )
            if (not reduce_only) and available_balance > 0:
                max_affordable_notional = max((available_balance * 0.9), min_notional * 1.05)
                if final_notional > max_affordable_notional:
                    quantity = max_affordable_notional / current_price
                    if step_size > 0:
                        quantity = self.round_to_step(quantity, step_size, ROUND_DOWN)
                    else:
                        quantity = round(quantity, qty_precision)
            
            server_time = self.get_server_time()
            if not server_time:
                self.log_error("server_time_unavailable", f"Failed to get server time for {symbol}")
                return None
            
            timestamp = int(server_time * 1000)
            params = {
                "symbol": symbol,
                "side": side,
                "type": "MARKET",
                "quantity": f"{quantity:.6f}",
                "timestamp": timestamp,
                "recvWindow": 5000
            }
            
            if reduce_only:
                params["reduceOnly"] = "true"
            
            query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            signature = self._create_signature(query_string)
            
            # 주문 제출 및 재시도 로직
            max_retries = 3
            for attempt in range(max_retries):
                url = f"{self.base_url}/fapi/v1/order?{query_string}&signature={signature}"
                headers = {"X-MBX-APIKEY": self.api_key}
                response = requests.post(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    return self._process_order_result(result, strategy_name, symbol, side, quantity, reduce_only, metadata)
                
                # -2019 재시도 로직
                if response.status_code == 400 and '"code":-2019' in response.text:
                    reduced_quantity = quantity * 0.5
                    
                    if step_size > 0:
                        reduced_quantity = self.round_to_step(reduced_quantity, step_size, ROUND_DOWN)
                    else:
                        reduced_quantity = round(reduced_quantity, qty_precision)
                    
                    if reduce_only:
                        # reduce_only는 진입 주문의 min_notional/min_qty 증액 논리를 따르지 않음
                        # 너무 작아져서 0 또는 음수가 되면 중단
                        if reduced_quantity <= 0:
                            break
                        
                        # step rounding 결과가 기존 quantity와 같으면 무한 재시도 방지
                        if reduced_quantity >= quantity:
                            break
                        
                        quantity = reduced_quantity
                        continue
                    
                    # 일반 진입 주문은 기존 min_qty / min_notional 기준 유지
                    if reduced_quantity < min_qty or (reduced_quantity * current_price) < min_notional:
                        break
                    
                    quantity = reduced_quantity
                    continue
                
                self.log_error("order_submission_failed", f"Order failed after {max_retries} attempts: {response.status_code} {response.text}")
                return None
        
        except Exception as e:
            self.log_error("trading_runtime_error", str(e))
            return None
    
    def _process_order_result(self, result, strategy_name, symbol, side, quantity, reduce_only, metadata):
        """주문 결과 처리"""
        try:
            order_id = result.get("orderId", "UNKNOWN")
            status = result.get("status", "UNKNOWN")
            avg_price = self.safe_float_conversion(result.get("avgPrice"), 0.0)
            executed_qty = self.safe_float_conversion(result.get("executedQty"), 0.0)
            
            record_timestamp = datetime.now().isoformat()
            record_type = "ACTUAL_TRADE" if status == "FILLED" else "PENDING_TRADE"
            
            trade_record = {
                "strategy": strategy_name,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": avg_price,
                "status": status,
                "order_id": order_id,
                "executed_qty": executed_qty,
                "timestamp": record_timestamp,
                "type": record_type,
                "market_regime": self.trading_results["market_regime"],
                "strategy_signal": side,
                "position_type": "LONG" if side == "BUY" else "SHORT"
            }
            trade_record.update(metadata)
            if reduce_only:
                trade_record["reduce_only"] = True
                trade_record["entry_price"] = self.safe_float_conversion(
                    metadata.get("entry_price"),
                    trade_record.get("price", 0.0)
                )
            
            # real_orders 리스트 제한으로 메모리 증가 방지
            if len(self.trading_results["real_orders"]) > 500:
                self.trading_results["real_orders"] = self.trading_results["real_orders"][-200:]
            
            self.trading_results["real_orders"].append(trade_record)
            
            if reduce_only and status == "FILLED":
                trade_record["realized_pnl"] = self.estimate_realized_pnl(trade_record)
            
            if reduce_only:
                print(f"[CLOSE] {strategy_name} | {symbol} | {side} | {quantity} | {status}")
            elif status == "FILLED":
                print(f"[FILLED] {strategy_name} | {symbol} | {side} | {quantity}")
            
            return result
        except Exception as e:
            self.log_error("order_result_processing_error", str(e))
            return None
    
    def _create_signature(self, query_string):
        """서명 생성"""
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def get_server_time(self):
        """서버 시간 조회"""
        try:
            response = requests.get(f"{self.base_url}/fapi/v1/time", timeout=5)
            if response.status_code == 200:
                return response.json().get("serverTime")
        except Exception:
            pass
        return None
    
    def get_current_price(self, symbol, default_price=0.0):
        """현재 가격 조회"""
        try:
            current_prices = self.trading_results.get("market_data", {})
            return current_prices.get(symbol, default_price)
        except Exception:
            return default_price
    
    def get_market_session(self):
        """마켓 세션 조회"""
        try:
            server_time = self.get_server_time()
            if not server_time:
                return "UNKNOWN"
            
            dt = datetime.fromtimestamp(server_time / 1000)
            hour = dt.hour
            
            if 0 <= hour < 8:
                return "ASIAN"
            elif 8 <= hour < 16:
                return "EUROPEAN"
            elif 16 <= hour < 24:
                return "AMERICAN"
            else:
                return "UNKNOWN"
        except Exception:
            return "UNKNOWN"
    
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
