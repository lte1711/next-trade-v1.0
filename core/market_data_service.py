import requests
import json
import time
import logging
from typing import Dict, List, Optional, Any

class MarketDataService:
    """Service for fetching and managing market data from Binance Futures"""
    
    def __init__(self, base_url: str = "https://demo-fapi.binance.com"):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        self._price_cache = {}
        self._cache_timeout = 5  # 5 seconds cache timeout
        self._symbols_cache = None
        self._symbols_cache_time = 0
        self._symbols_cache_timeout = 300  # 5 minutes cache for symbols
        self._min_symbol_price = 0.00001
    
    def log_error(self, error_type: str, message: str):
        """Log error message"""
        self.logger.error(f"[{error_type}] {message}")
    
    def get_klines(self, symbol: str, interval: str, limit: int = 500) -> Optional[List[Dict]]:
        """Get kline data for a symbol"""
        try:
            url = f"{self.base_url}/fapi/v1/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                klines = response.json()
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
    
    def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
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
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for single symbol"""
        prices = self.get_current_prices([symbol])
        return prices.get(symbol, 0.0)
    
    def update_market_data(self, symbols, intervals=['1m', '5m', '15m', '1h']):
        """Update market data for symbols across multiple timeframes"""
        try:
            market_data = {}
            
            # Convert symbols to strings
            symbol_strings = []
            for symbol in symbols:
                if isinstance(symbol, dict):
                    symbol_strings.append(symbol.get('symbol', str(symbol)))
                elif isinstance(symbol, str):
                    symbol_strings.append(symbol)
                else:
                    symbol_strings.append(str(symbol))
            
            # Remove duplicates
            symbol_strings = list(set(symbol_strings))
            
            for symbol in symbol_strings:
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
    
    def get_available_symbols(self) -> List[Dict]:
        """Get available symbols from exchange"""
        try:
            current_time = time.time()
            
            # Check cache first
            if (self._symbols_cache and 
                current_time - self._symbols_cache_time < self._symbols_cache_timeout):
                return self._symbols_cache
            
            url = f"{self.base_url}/fapi/v1/exchangeInfo"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                exchange_info = response.json()
                symbols = []
                ticker_url = f"{self.base_url}/fapi/v1/ticker/24hr"
                ticker_response = requests.get(ticker_url, timeout=10)
                if ticker_response.status_code != 200:
                    self.log_error("symbols_fetch", f"Failed to fetch 24hr tickers: {ticker_response.status_code}")
                    return []

                ticker_lookup = {
                    item.get('symbol'): item
                    for item in ticker_response.json()
                    if isinstance(item, dict) and item.get('symbol')
                }
                
                for symbol_info in exchange_info['symbols']:
                    if (symbol_info['status'] == 'TRADING' and 
                        symbol_info['contractType'] == 'PERPETUAL' and
                        symbol_info['quoteAsset'] == 'USDT'):
                        ticker_data = ticker_lookup.get(symbol_info['symbol'])
                        if not ticker_data:
                            continue

                        last_price = float(ticker_data.get('lastPrice', 0))
                        if last_price < self._min_symbol_price:
                            continue

                        symbols.append({
                            'symbol': symbol_info['symbol'],
                            'base_asset': symbol_info['baseAsset'],
                            'quote_asset': symbol_info['quoteAsset'],
                            'status': symbol_info['status'],
                            'contract_type': symbol_info['contractType'],
                            'volume': float(ticker_data.get('volume', 0)),
                            'volatility': 0.0,  # Will be calculated later
                            'price': last_price
                        })
                
                # Sort by volume and limit to top 50
                symbols.sort(key=lambda x: x['volume'], reverse=True)
                symbols = symbols[:50]
                
                # Calculate volatility (simplified)
                for symbol in symbols:
                    # Get recent klines for volatility calculation
                    klines = self.get_klines(symbol['symbol'], '1m', 20)
                    if klines and len(klines) >= 2:
                        prices = [k['close'] for k in klines]
                        if len(prices) > 1:
                            returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
                            if returns:
                                avg_return = sum(returns) / len(returns)
                                variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
                                symbol['volatility'] = (variance ** 0.5) * 100  # Convert to percentage
                
                # Cache the results
                self._symbols_cache = symbols
                self._symbols_cache_time = current_time
                
                return symbols
            else:
                self.log_error("symbols_fetch", f"Failed to fetch symbols: {response.status_code}")
                return []
                
        except Exception as e:
            self.log_error("symbols_exception", str(e))
            return []
    
    def rank_symbols_by_liquidity(self, symbols: List[str]) -> List[Dict]:
        """Rank symbols by liquidity (volume * price)"""
        try:
            ranked_symbols = []
            
            for symbol in symbols:
                # Get current price
                price = self.get_current_price(symbol)
                
                # Get 24hr volume
                volume = 0
                try:
                    url = f"{self.base_url}/fapi/v1/ticker/24hr"
                    params = {'symbol': symbol}
                    response = requests.get(url, params=params, timeout=5)
                    
                    if response.status_code == 200:
                        ticker_data = response.json()
                        volume = float(ticker_data.get('volume', 0))
                except:
                    pass
                
                # Calculate liquidity score
                liquidity = volume * price
                
                # Get volatility
                volatility = 0
                try:
                    klines = self.get_klines(symbol, '1m', 20)
                    if klines and len(klines) >= 2:
                        prices = [k['close'] for k in klines]
                        if len(prices) > 1:
                            returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
                            if returns:
                                avg_return = sum(returns) / len(returns)
                                variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
                                volatility = (variance ** 0.5) * 100
                except:
                    pass
                
                ranked_symbols.append({
                    'symbol': symbol,
                    'volume': volume,
                    'volatility': volatility,
                    'price': price
                })
            
            # Sort by liquidity
            ranked_symbols.sort(key=lambda x: x['volume'], reverse=True)
            
            return ranked_symbols
            
        except Exception as e:
            self.log_error("ranking_error", str(e))
            return []
