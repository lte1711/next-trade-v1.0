"""
Market Data Service - Binance Futures API for market data retrieval
"""

import requests
import time
import json
from datetime import datetime
from decimal import Decimal

class MarketDataService:
    """Binance Futures market data retrieval and caching"""
    
    def __init__(self, base_url, api_key=None, api_secret=None, log_error_callback=None):
        self.base_url = base_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.log_error = log_error_callback or self._default_log_error
        self._symbol_cache = {}
        self._price_cache = {}
        self._cache_timeout = 60  # 60 seconds cache
    
    def _default_log_error(self, error_type, message):
        """Default error logging"""
        print(f"[ERROR] {error_type}: {message}")
    
    def get_klines(self, symbol, interval, limit=500):
        """Get kline data for symbol"""
        try:
            url = f"{self.base_url}/fapi/v1/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                klines = response.json()
                # Convert to structured format
                processed_klines = []
                for kline in klines:
                    processed_klines.append({
                        'timestamp': int(kline[0]),
                        'open': float(kline[1]),
                        'high': float(kline[2]),
                        'low': float(kline[3]),
                        'close': float(kline[4]),
                        'volume': float(kline[5]),
                        'close_time': int(kline[6]),
                        'quote_volume': float(kline[7]),
                        'count': int(kline[8])
                    })
                return processed_klines
            else:
                self.log_error("klines_fetch", f"Failed to fetch klines: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_error("klines_exception", str(e))
            return None
    
    def get_current_prices(self, symbols):
        """Get current prices for multiple symbols"""
        try:
            if not symbols:
                return {}
            
            # Check cache first
            current_time = time.time()
            cached_prices = {}
            symbols_to_fetch = []
            
            for symbol in symbols:
                cache_key = f"price_{symbol}"
                if cache_key in self._price_cache:
                    cached_data = self._price_cache[cache_key]
                    if current_time - cached_data['timestamp'] < self._cache_timeout:
                        cached_prices[symbol] = cached_data['price']
                    else:
                        symbols_to_fetch.append(symbol)
                else:
                    symbols_to_fetch.append(symbol)
            
            if not symbols_to_fetch:
                return cached_prices
            
            # Fetch missing prices
            url = f"{self.base_url}/fapi/v1/ticker/price"
            if len(symbols_to_fetch) == 1:
                params = {'symbol': symbols_to_fetch[0]}
            else:
                params = {'symbols': json.dumps(symbols_to_fetch)}
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    for item in data:
                        symbol = item.get('symbol')
                        price = float(item.get('price', 0))
                        if symbol and price > 0:
                            cached_prices[symbol] = price
                            self._price_cache[f"price_{symbol}"] = {
                                'price': price,
                                'timestamp': current_time
                            }
                else:
                    symbol = data.get('symbol')
                    price = float(data.get('price', 0))
                    if symbol and price > 0:
                        cached_prices[symbol] = price
                        self._price_cache[f"price_{symbol}"] = {
                            'price': price,
                            'timestamp': current_time
                        }
                
                return cached_prices
            else:
                self.log_error("prices_fetch", f"Failed to fetch prices: {response.status_code}")
                return cached_prices
                
        except Exception as e:
            self.log_error("prices_exception", str(e))
            return {}
    
    def get_current_price(self, symbol):
        """Get current price for single symbol"""
        prices = self.get_current_prices([symbol])
        return prices.get(symbol, 0.0)
    
    def update_market_data(self, symbols, intervals=['1m', '5m', '15m', '1h']):
        """Update market data for symbols across multiple timeframes"""
        try:
            market_data = {}
            
            for symbol in symbols:
                symbol_data = {'prices': {}, 'klines': {}}
                
                # Get current price
                current_price = self.get_current_price(symbol)
                symbol_data['prices']['current'] = current_price
                
                # Get klines for each interval
                for interval in intervals:
                    klines = self.get_klines(symbol, interval)
                    if klines:
                        symbol_data['klines'][interval] = klines
                
                market_data[symbol] = symbol_data
            
            return market_data
            
        except Exception as e:
            self.log_error("market_data_update", str(e))
            return {}
    
    def refresh_symbol_universe(self):
        """Refresh available symbols from exchange"""
        try:
            url = f"{self.base_url}/fapi/v1/exchangeInfo"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                exchange_info = response.json()
                symbols = []
                
                for symbol_info in exchange_info['symbols']:
                    if symbol_info['status'] == 'TRADING':
                        symbols.append({
                            'symbol': symbol_info['symbol'],
                            'base_asset': symbol_info['baseAsset'],
                            'quote_asset': symbol_info['quoteAsset'],
                            'price_precision': symbol_info['pricePrecision'],
                            'quantity_precision': symbol_info['quantityPrecision'],
                            'tick_size': float(symbol_info['filters'][0]['tickSize']),
                            'step_size': float(symbol_info['filters'][1]['stepSize'])
                        })
                
                self._symbol_cache = {
                    'symbols': symbols,
                    'timestamp': time.time()
                }
                
                return symbols
            else:
                self.log_error("symbol_universe", f"Failed to fetch symbols: {response.status_code}")
                return []
                
        except Exception as e:
            self.log_error("symbol_universe_exception", str(e))
            return []
    
    def get_symbol_info(self, symbol):
        """Get symbol information from cache or fetch if needed"""
        try:
            # Check cache first
            if 'symbols' in self._symbol_cache:
                for symbol_info in self._symbol_cache['symbols']:
                    if symbol_info['symbol'] == symbol:
                        return symbol_info
            
            # If not in cache, refresh universe
            self.refresh_symbol_universe()
            
            # Try again
            if 'symbols' in self._symbol_cache:
                for symbol_info in self._symbol_cache['symbols']:
                    if symbol_info['symbol'] == symbol:
                        return symbol_info
            
            return None
            
        except Exception as e:
            self.log_error("symbol_info", str(e))
            return None
