"""
Protective Order Manager - Protective Order Management Module
"""

import requests
import time
import hmac
import hashlib
from decimal import Decimal, ROUND_DOWN, ROUND_UP


class ProtectiveOrderManager:
    """Protective order creation, cancellation, and status management"""
    
    def __init__(self, api_key, api_secret, base_url, trading_results, symbol_info_getter, log_error_callback):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.trading_results = trading_results
        self.get_symbol_info = symbol_info_getter
        self.log_error = log_error_callback
        self.managed_stop_prices = {}
    
    def submit_protective_order(self, symbol, side, order_type, stop_price):
        """Submit protective order"""
        try:
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                self.log_error("symbol_info_missing", f"No symbol metadata found for {symbol}")
                return None
            
            price_precision = int(symbol_info.get("pricePrecision", 4))
            tick_size = self._get_tick_size(symbol_info)

            for attempt, buffer_ticks in enumerate((1, 5, 25, 100), start=1):
                server_time = self.get_server_time()
                if not server_time:
                    return None

                # Use server time with buffer to avoid timestamp ahead error.
                timestamp = int(server_time) - 100
                normalized_stop_price = self._normalize_trigger_price(
                    symbol=symbol,
                    side=side,
                    order_type=order_type,
                    stop_price=stop_price,
                    tick_size=tick_size,
                    buffer_ticks=buffer_ticks,
                )
                stop_price_str = f"{float(normalized_stop_price):.{max(0, price_precision)}f}"

                params = {
                    "algoType": "CONDITIONAL",
                    "symbol": symbol,
                    "side": side,
                    "type": order_type,
                    "triggerPrice": stop_price_str,
                    "timeInForce": "GTC",
                    "closePosition": "true",
                    "workingType": "CONTRACT_PRICE",
                    "timestamp": timestamp,
                    "recvWindow": getattr(self, 'recv_window', 5000)
                }

                query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
                signature = hmac.new(
                    self.api_secret.encode('utf-8'),
                    query_string.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()

                url = f"{self.base_url}/fapi/v1/algoOrder?{query_string}&signature={signature}"
                headers = {"X-MBX-APIKEY": self.api_key}
                response = requests.post(url, headers=headers, timeout=10)

                if response.status_code == 200:
                    if attempt > 1:
                        self.trading_results.setdefault("operational_events", []).append({
                            "type": "protective_order_retry_success",
                            "symbol": symbol,
                            "order_type": order_type,
                            "attempt": attempt,
                            "trigger_price": stop_price_str,
                        })
                    return response.json()

                if response.status_code == 400 and '"code":-2021' in response.text and attempt < 4:
                    time.sleep(0.2)
                    continue

                self.log_error(
                    "protective_order_error",
                    f"{symbol} {order_type}: {response.status_code} {response.text}"
                )
                return None
        except Exception as e:
            self.log_error("protective_order_error", f"{symbol} {order_type}: {e}")
        return None

    def _get_tick_size(self, symbol_info):
        """Extract symbol tick size from filters"""
        try:
            for symbol_filter in symbol_info.get("filters", []):
                if symbol_filter.get("filterType") == "PRICE_FILTER":
                    return float(symbol_filter.get("tickSize", 0.0))
        except Exception:
            pass
        return 0.0

    def _normalize_trigger_price(self, symbol, side, order_type, stop_price, tick_size, buffer_ticks=1):
        """Round trigger price to tick size and push it away from current price if needed"""
        normalized = self.safe_float_conversion(stop_price, 0.0)
        current_price = self.safe_float_conversion(
            self.trading_results.get("market_data", {}).get(symbol),
            0.0
        )
        live_current_price = self._get_protective_reference_price(symbol, side, order_type)
        if live_current_price > 0:
            current_price = live_current_price
        if normalized <= 0:
            return stop_price

        if tick_size > 0:
            normalized = self._round_price_to_tick(normalized, tick_size, side, order_type)

        if current_price <= 0 or tick_size <= 0:
            return normalized

        # Only nudge orders that would immediately trigger. The previous 10%
        # current-price buffer widened valid stops too aggressively on tiny
        # contracts, leaving positions exposed well beyond the configured risk.
        buffer_size = tick_size * max(1, int(buffer_ticks or 1))
        min_above = current_price + buffer_size
        max_below = max(current_price - buffer_size, tick_size)

        if order_type == "STOP_MARKET":
            if side == "SELL" and normalized >= current_price:
                normalized = max_below
            elif side == "BUY" and normalized <= current_price:
                normalized = min_above
        elif order_type == "TAKE_PROFIT_MARKET":
            if side == "SELL" and normalized <= current_price:
                normalized = min_above
            elif side == "BUY" and normalized >= current_price:
                normalized = max_below

        if tick_size > 0:
            normalized = self._round_price_to_tick(normalized, tick_size, side, order_type)

        return normalized

    def _get_current_contract_price(self, symbol):
        """Fetch the latest contract price to avoid stale local trigger checks."""
        try:
            response = requests.get(
                f"{self.base_url}/fapi/v1/ticker/price",
                params={"symbol": symbol},
                timeout=5,
            )
            if response.status_code == 200:
                return self.safe_float_conversion(response.json().get("price"), 0.0)
        except Exception:
            pass
        return 0.0

    def _get_protective_reference_price(self, symbol, side, order_type):
        """Return a conservative trigger reference for fast-moving contracts."""
        prices = [self._get_current_contract_price(symbol)]

        try:
            response = requests.get(
                f"{self.base_url}/fapi/v1/ticker/bookTicker",
                params={"symbol": symbol},
                timeout=5,
            )
            if response.status_code == 200:
                payload = response.json()
                prices.extend([
                    self.safe_float_conversion(payload.get("bidPrice"), 0.0),
                    self.safe_float_conversion(payload.get("askPrice"), 0.0),
                ])
        except Exception:
            pass

        prices = [price for price in prices if price > 0]
        if not prices:
            return 0.0

        if order_type == "STOP_MARKET":
            return min(prices) if side == "SELL" else max(prices)
        if order_type == "TAKE_PROFIT_MARKET":
            return max(prices) if side == "SELL" else min(prices)
        return prices[0]

    def _round_price_to_tick(self, price, tick_size, side, order_type):
        """Round price to exchange tick size with direction-aware rounding"""
        price_decimal = Decimal(str(price))
        tick_decimal = Decimal(str(tick_size))
        if tick_decimal <= 0:
            return float(price_decimal)

        if order_type == "STOP_MARKET":
            rounding = ROUND_DOWN if side == "SELL" else ROUND_UP
        else:
            rounding = ROUND_UP if side == "SELL" else ROUND_DOWN

        ticks = (price_decimal / tick_decimal).quantize(Decimal("1"), rounding=rounding)
        normalized = ticks * tick_decimal
        return float(normalized)
    
    def get_open_orders(self, symbol):
        """Get pending orders for specific symbol"""
        try:
            server_time = self.get_server_time()
            if not server_time:
                return []
            
            timestamp = int(server_time) - 100
            params = {
                "algoType": "CONDITIONAL",
                "symbol": symbol,
                "timestamp": timestamp,
                "recvWindow": getattr(self, 'recv_window', 5000)
            }
            
            query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            url = f"{self.base_url}/fapi/v1/openAlgoOrders?{query_string}&signature={signature}"
            headers = {"X-MBX-APIKEY": self.api_key}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            self.log_error("open_orders_error", f"{symbol}: {e}")
            return []
    
    def cancel_order(self, symbol, order_id):
        """Cancel order"""
        try:
            server_time = self.get_server_time()
            if not server_time:
                return False
            
            timestamp = int(server_time) - 100
            params = {
                "algoId": order_id,
                "timestamp": timestamp,
                "recvWindow": getattr(self, 'recv_window', 5000)
            }
            
            query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            url = f"{self.base_url}/fapi/v1/algoOrder?{query_string}&signature={signature}"
            headers = {"X-MBX-APIKEY": self.api_key}
            response = requests.delete(url, headers=headers, timeout=10)
            
            return response.status_code == 200
        except Exception as e:
            self.log_error("cancel_order_error", f"{symbol}/{order_id}: {e}")
            return False
    
    def cancel_symbol_protective_orders(self, symbol):
        """Cancel all protective orders for symbol"""
        open_orders = self.get_open_orders(symbol)
        for order in open_orders:
            order_id = order.get("algoId") or order.get("orderId")
            if order_id:
                self.cancel_order(symbol, order_id)
    
    def place_protective_orders(self, strategy_name, symbol, entry_side, entry_price):
        """Install protective orders"""
        strategy = self.trading_results.get("strategies", {}).get(strategy_name, {})
        stop_loss_pct = self.safe_float_conversion(strategy.get("stop_loss_pct"), 0.02)
        take_profit_pct = self.safe_float_conversion(strategy.get("take_profit_pct"), 0.0)
        
        exit_side = "SELL" if entry_side == "BUY" else "BUY"
        if entry_side == "BUY":
            stop_price = entry_price * (1 - stop_loss_pct)
            take_price = entry_price * (1 + take_profit_pct) if take_profit_pct and take_profit_pct > 0 else None
        else:
            stop_price = entry_price * (1 + stop_loss_pct)
            take_price = entry_price * (1 - take_profit_pct) if take_profit_pct and take_profit_pct > 0 else None
        
        # Cancel existing protective orders
        self.cancel_symbol_protective_orders(symbol)
        
        # Install STOP order
        print(f"[TRACE] PROTECTIVE_ORDER_SUBMIT | {symbol} | STOP_MARKET | price={stop_price}")
        stop_result = self.submit_protective_order(symbol, exit_side, "STOP_MARKET", stop_price)
        if stop_result:
            self.managed_stop_prices[symbol] = stop_price
            self.trading_results.setdefault("managed_stop_prices", {})[symbol] = stop_price
        
        # Install TAKE_PROFIT order
        if take_price is not None:
            print(f"[TRACE] PROTECTIVE_ORDER_SUBMIT | {symbol} | TAKE_PROFIT_MARKET | price={take_price}")
            self.submit_protective_order(symbol, exit_side, "TAKE_PROFIT_MARKET", take_price)
    
    def update_stop_loss(self, symbol, new_stop_price, amount):
        """Cancel existing STOP_MARKET protective order and reinstall new stop loss"""
        try:
            exit_side = "SELL" if amount > 0 else "BUY"

            open_orders = self.get_open_orders(symbol)
            for order in open_orders:
                order_type = order.get("orderType") or order.get("type")
                if order_type == "STOP_MARKET":
                    order_id = order.get("algoId") or order.get("orderId")
                    if order_id:
                        self.cancel_order(symbol, order_id)

            result = self.submit_protective_order(
                symbol=symbol,
                side=exit_side,
                order_type="STOP_MARKET",
                stop_price=new_stop_price
            )

            if result:
                self.managed_stop_prices[symbol] = new_stop_price
                self.trading_results.setdefault("managed_stop_prices", {})[symbol] = new_stop_price
                return True
            return False

        except Exception as e:
            self.log_error("update_stop_loss_error", f"{symbol}: {e}")
            return False
    
    def get_server_time(self):
        """Get server time"""
        try:
            response = requests.get(f"{self.base_url}/fapi/v1/time", timeout=5)
            if response.status_code == 200:
                return response.json().get("serverTime")
        except Exception:
            pass
        return None
    
    def safe_float_conversion(self, value, default=0.0):
        """Safe float conversion"""
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default
