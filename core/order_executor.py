"""
Order Executor - Order Execution Module
"""

import requests
import time
import hmac
import hashlib
from datetime import datetime
from decimal import Decimal, ROUND_DOWN, ROUND_UP


class OrderExecutor:
    """Order execution, quantity validation, and retry logic"""
    
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
        """Execute and validate order"""
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
            
            # Prevent quantity increase for reduce_only orders
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

            if not reduce_only:
                percent_price_check = self._validate_market_order_preflight(symbol, side, symbol_info)
                if not percent_price_check["allowed"]:
                    self.log_error("order_preflight_blocked", percent_price_check["reason"])
                    return {
                        "status": "BLOCKED",
                        "reason": percent_price_check["reason"],
                    }
            
            server_time = self.get_server_time()
            if not server_time:
                self.log_error("server_time_unavailable", f"Failed to get server time for {symbol}")
                return None
            
            # Add small buffer to avoid timestamp ahead of server time
            local_time = int(time.time() * 1000)
            server_time_ms = int(server_time)
            time_offset = server_time_ms - local_time
            
            # Use server time with small adjustment to avoid being ahead
            timestamp = server_time_ms - 100  # Subtract 100ms buffer
            params = {
                "symbol": symbol,
                "side": side,
                "type": "MARKET",
                "quantity": f"{quantity:.6f}",
                "timestamp": timestamp,
                "recvWindow": getattr(self, 'recv_window', 5000)
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

    def _validate_market_order_preflight(self, symbol, side, symbol_info):
        """Block market orders likely to fail exchange-side price filters."""
        try:
            current_price = self.get_current_price(symbol, 0.0)
            min_trade_price = 0.00001
            if current_price > 0 and current_price < min_trade_price:
                return {
                    "allowed": False,
                    "reason": f"{symbol} current price {current_price:.10f} below preflight floor {min_trade_price:.5f}"
                }

            percent_filter = None
            for symbol_filter in symbol_info.get("filters", []):
                if symbol_filter.get("filterType") == "PERCENT_PRICE":
                    percent_filter = symbol_filter
                    break

            if not percent_filter:
                return {"allowed": True}

            mark_price = self._get_mark_price(symbol)
            book_price = self._get_book_ticker_price(symbol, side)
            if mark_price <= 0 or book_price <= 0:
                return {"allowed": True}

            multiplier_up = self.safe_float_conversion(percent_filter.get("multiplierUp"), 0.0)
            multiplier_down = self.safe_float_conversion(percent_filter.get("multiplierDown"), 0.0)
            if multiplier_up <= 0 or multiplier_down <= 0:
                return {"allowed": True}

            upper_bound = mark_price * multiplier_up
            lower_bound = mark_price * multiplier_down
            if book_price > upper_bound or book_price < lower_bound:
                return {
                    "allowed": False,
                    "reason": (
                        f"{symbol} market order preflight blocked: "
                        f"book_price={book_price:.10f}, mark_price={mark_price:.10f}, "
                        f"allowed_range=[{lower_bound:.10f}, {upper_bound:.10f}]"
                    ),
                }

            return {"allowed": True}
        except Exception as e:
            self.log_error("order_preflight_error", f"{symbol}: {e}")
            return {"allowed": True}

    def _get_mark_price(self, symbol):
        """Fetch mark price for a symbol."""
        try:
            response = requests.get(
                f"{self.base_url}/fapi/v1/premiumIndex",
                params={"symbol": symbol},
                timeout=5,
            )
            if response.status_code == 200:
                return self.safe_float_conversion(response.json().get("markPrice"), 0.0)
        except Exception:
            pass
        return 0.0

    def _get_book_ticker_price(self, symbol, side):
        """Fetch best executable book price for a side."""
        try:
            response = requests.get(
                f"{self.base_url}/fapi/v1/ticker/bookTicker",
                params={"symbol": symbol},
                timeout=5,
            )
            if response.status_code != 200:
                return 0.0
            payload = response.json()
            if side == "BUY":
                return self.safe_float_conversion(payload.get("askPrice"), 0.0)
            return self.safe_float_conversion(payload.get("bidPrice"), 0.0)
        except Exception:
            pass
        return 0.0
    
    def _process_order_result(self, result, strategy_name, symbol, side, quantity, reduce_only, metadata):
        """Process order result"""
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
                self._record_realized_pnl_event(trade_record)
            
            if reduce_only:
                print(f"[CLOSE] {strategy_name} | {symbol} | {side} | {quantity} | {status}")
            elif status == "FILLED":
                print(f"[FILLED] {strategy_name} | {symbol} | {side} | {quantity}")
            
            return result
        except Exception as e:
            self.log_error("order_result_processing_error", str(e))
            return None

    def reconcile_pending_reduce_only_fills(self):
        """Refresh reduce-only close orders that were initially returned as pending."""
        summary = {
            "checked": 0,
            "filled": 0,
            "terminal": 0,
            "errors": [],
            "updated_orders": [],
        }
        try:
            for trade_record in self.trading_results.get("real_orders", []):
                if not trade_record.get("reduce_only"):
                    continue
                if trade_record.get("realized_pnl") is not None:
                    continue
                if trade_record.get("status") not in {"NEW", "PARTIALLY_FILLED"}:
                    continue

                symbol = trade_record.get("symbol")
                order_id = trade_record.get("order_id")
                if not symbol or not order_id or order_id == "UNKNOWN":
                    continue

                summary["checked"] += 1
                exchange_order = self.get_order_status(symbol, order_id)
                if not exchange_order:
                    continue

                exchange_status = exchange_order.get("status")
                if exchange_status == "FILLED":
                    self._apply_filled_reconciliation(trade_record, exchange_order)
                    self._record_realized_pnl_event(trade_record)
                    summary["filled"] += 1
                    summary["updated_orders"].append({
                        "symbol": symbol,
                        "order_id": order_id,
                        "status": exchange_status,
                        "realized_pnl": trade_record.get("realized_pnl"),
                    })
                elif exchange_status in {"CANCELED", "EXPIRED", "REJECTED"}:
                    trade_record["status"] = exchange_status
                    trade_record["type"] = "TERMINAL_TRADE"
                    trade_record["exchange_update_time"] = exchange_order.get("updateTime")
                    summary["terminal"] += 1
                    summary["updated_orders"].append({
                        "symbol": symbol,
                        "order_id": order_id,
                        "status": exchange_status,
                    })

            if summary["checked"] or summary["filled"] or summary["terminal"]:
                self.trading_results.setdefault("operational_events", []).append({
                    "timestamp": datetime.now().isoformat(),
                    "type": "reduce_only_fill_reconciliation",
                    "summary": summary,
                })
            return summary
        except Exception as e:
            self.log_error("reduce_only_fill_reconciliation", str(e))
            summary["errors"].append(str(e))
            return summary

    def _apply_filled_reconciliation(self, trade_record, exchange_order):
        """Update a local close-order record from the exchange FILLED status."""
        trade_record["status"] = "FILLED"
        trade_record["type"] = "ACTUAL_TRADE"
        trade_record["price"] = self.safe_float_conversion(
            exchange_order.get("avgPrice"),
            trade_record.get("price", 0.0)
        )
        trade_record["executed_qty"] = self.safe_float_conversion(
            exchange_order.get("executedQty"),
            trade_record.get("executed_qty", 0.0)
        )
        trade_record["exchange_update_time"] = exchange_order.get("updateTime")
        trade_record["realized_pnl"] = self.estimate_realized_pnl(trade_record)

    def _record_realized_pnl_event(self, trade_record):
        """Persist realized PnL events for audit and adaptive ranking."""
        try:
            order_id = trade_record.get("order_id")
            if not order_id or order_id == "UNKNOWN":
                return

            journal = self.trading_results.setdefault("realized_pnl_journal", [])
            if any(entry.get("order_id") == order_id for entry in journal):
                return

            realized_pnl = self.safe_float_conversion(trade_record.get("realized_pnl"), 0.0)
            symbol = trade_record.get("symbol")
            strategy = trade_record.get("strategy") or "unknown"
            journal.append({
                "timestamp": trade_record.get("timestamp"),
                "order_id": order_id,
                "symbol": symbol,
                "strategy": strategy,
                "side": trade_record.get("side"),
                "entry_price": self.safe_float_conversion(trade_record.get("entry_price"), 0.0),
                "exit_price": self.safe_float_conversion(trade_record.get("price"), 0.0),
                "executed_qty": self.safe_float_conversion(trade_record.get("executed_qty"), 0.0),
                "realized_pnl": realized_pnl,
                "exit_reason": trade_record.get("exit_reason"),
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
            symbol_stats["last_updated"] = trade_record.get("timestamp")
        except Exception as e:
            self.log_error("realized_pnl_event_record", str(e))
    
    def _create_signature(self, query_string):
        """Create signature"""
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def get_server_time(self):
        """Get server time"""
        try:
            response = requests.get(f"{self.base_url}/fapi/v1/time", timeout=5)
            if response.status_code == 200:
                return response.json().get("serverTime")
        except Exception:
            pass
        return None

    def cancel_order(self, symbol, order_id):
        """Cancel a standard futures order"""
        try:
            server_time = self.get_server_time()
            if not server_time:
                self.log_error("server_time_unavailable", f"Failed to cancel {symbol}/{order_id}")
                return False

            timestamp = int(server_time) - 100
            params = {
                "symbol": symbol,
                "orderId": order_id,
                "timestamp": timestamp,
                "recvWindow": getattr(self, "recv_window", 5000)
            }

            query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            signature = self._create_signature(query_string)
            url = f"{self.base_url}/fapi/v1/order?{query_string}&signature={signature}"
            headers = {"X-MBX-APIKEY": self.api_key}
            response = requests.delete(url, headers=headers, timeout=10)

            if response.status_code == 200:
                return True

            self.log_error(
                "cancel_order_failed",
                f"{symbol}/{order_id}: {response.status_code} {response.text}"
            )
            return False
        except Exception as e:
            self.log_error("cancel_order_error", f"{symbol}/{order_id}: {e}")
            return False

    def get_order_status(self, symbol, order_id):
        """Fetch a standard futures order status."""
        try:
            server_time = self.get_server_time()
            if not server_time:
                self.log_error("server_time_unavailable", f"Failed to query {symbol}/{order_id}")
                return None

            timestamp = int(server_time) - 100
            params = {
                "symbol": symbol,
                "orderId": order_id,
                "timestamp": timestamp,
                "recvWindow": getattr(self, "recv_window", 5000)
            }

            query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            signature = self._create_signature(query_string)
            url = f"{self.base_url}/fapi/v1/order?{query_string}&signature={signature}"
            headers = {"X-MBX-APIKEY": self.api_key}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                return response.json()

            self.log_error(
                "order_status_query_failed",
                f"{symbol}/{order_id}: {response.status_code} {response.text}"
            )
            return None
        except Exception as e:
            self.log_error("order_status_query_error", f"{symbol}/{order_id}: {e}")
            return None
    
    def get_current_price(self, symbol, default_price=0.0):
        """Get current price"""
        try:
            current_prices = self.trading_results.get("market_data", {})
            current_price = self.safe_float_conversion(current_prices.get(symbol), 0.0)
            if current_price > 0:
                return current_price

            response = requests.get(
                f"{self.base_url}/fapi/v1/ticker/price",
                params={"symbol": symbol},
                timeout=5,
            )
            if response.status_code == 200:
                live_price = self.safe_float_conversion(response.json().get("price"), default_price)
                if live_price > 0:
                    return live_price
        except Exception:
            pass
        return default_price
    
    def get_market_session(self):
        """Get market session"""
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
                exit_side = trade.get("side")
                if exit_side == "SELL":
                    return (exit_price - entry_price) * quantity
                if exit_side == "BUY":
                    return (entry_price - exit_price) * quantity
        except Exception:
            pass
        return 0.0
