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
            server_time = self.get_server_time()
            if not server_time:
                return None
            
            # Use server time with buffer to avoid timestamp ahead error
            server_time_ms = int(server_time)
            timestamp = server_time_ms - 100  # Subtract 100ms buffer
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                self.log_error("symbol_info_missing", f"No symbol metadata found for {symbol}")
                return None
            
            price_precision = int(symbol_info.get("pricePrecision", 4))
            stop_price_str = f"{float(stop_price):.{max(0, price_precision)}f}"
            
            params = {
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": "0",
                "price": "0",
                "stopPrice": stop_price_str,
                "timeInForce": "GTC",
                "reduceOnly": "true",
                "closePosition": "true",
                "timestamp": timestamp,
                "recvWindow": getattr(self, 'recv_window', 5000)
            }
            
            query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            url = f"{self.base_url}/fapi/v1/order?{query_string}&signature={signature}"
            headers = {"X-MBX-APIKEY": self.api_key}
            response = requests.post(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            self.log_error("protective_order_error", f"{symbol} {order_type}: {response.status_code} {response.text}")
        except Exception as e:
            self.log_error("protective_order_error", f"{symbol} {order_type}: {e}")
        return None
    
    def get_open_orders(self, symbol):
        """Get pending orders for specific symbol"""
        try:
            server_time = self.get_server_time()
            if not server_time:
                return []
            
            timestamp = int(server_time) - 100
            params = {
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
            
            url = f"{self.base_url}/fapi/v1/openOrders?{query_string}&signature={signature}"
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
                "symbol": symbol,
                "orderId": order_id,
                "timestamp": timestamp,
                "recvWindow": getattr(self, 'recv_window', 5000)
            }
            
            query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            url = f"{self.base_url}/fapi/v1/order?{query_string}&signature={signature}"
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
            order_id = order.get("orderId")
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
                if order.get("type") == "STOP_MARKET":
                    order_id = order.get("orderId")
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
