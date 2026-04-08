#!/usr/bin/env python3
"""
Rewrite Market Data Service - Completely rewrite the market data service to fix issues
"""

def rewrite_market_data_service():
    """Rewrite the market data service to fix all issues"""
    print('=' * 60)
    print('REWRITE MARKET DATA SERVICE')
    print('=' * 60)
    
    # Read the current file
    with open('core/market_data_service.py', 'r') as f:
        content = f.read()
    
    # Create a new, clean version of the update_market_data method
    new_service_content = '''import requests
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
            
            # Handle both dict and string inputs
            processed_symbols = []
            for symbol in symbols:
                if isinstance(symbol, dict):
                    symbol_name = symbol.get('symbol', str(symbol))
                    processed_symbols.append(symbol_name)
                elif isinstance(symbol, str):
                    processed_symbols.append(symbol)
                else:
                    processed_symbols.append(str(symbol))
            
            # Remove duplicates
            processed_symbols = list(set(processed_symbols))
            
            for symbol in processed_symbols:
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
                
                for symbol_info in exchange_info['symbols']:
                    if (symbol_info['status'] == 'TRADING' and 
                        symbol_info['contractType'] == 'PERPETUAL' and
                        symbol_info['quoteAsset'] == 'USDT'):
                        
                        # Get 24hr ticker data for volume and price
                        ticker_url = f"{self.base_url}/fapi/v1/ticker/24hr"
                        ticker_params = {'symbol': symbol_info['symbol']}
                        ticker_response = requests.get(ticker_url, params=ticker_params, timeout=5)
                        
                        if ticker_response.status_code == 200:
                            ticker_data = ticker_response.json()
                            
                            symbols.append({
                                'symbol': symbol_info['symbol'],
                                'base_asset': symbol_info['baseAsset'],
                                'quote_asset': symbol_info['quoteAsset'],
                                'status': symbol_info['status'],
                                'contract_type': symbol_info['contractType'],
                                'volume': float(ticker_data.get('volume', 0)),
                                'volatility': 0.0,  # Will be calculated later
                                'price': float(ticker_data.get('lastPrice', 0))
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
'''
    
    # Write the new service
    with open('core/market_data_service.py', 'w') as f:
        f.write(new_service_content)
    
    print('[SUCCESS] Market data service completely rewritten')
    
    # Test the new service
    print('\n[TEST] Testing the new market data service:')
    
    try:
        from core.market_data_service import MarketDataService
        mds = MarketDataService('https://demo-fapi.binance.com')
        
        # Test get_available_symbols
        symbols = mds.get_available_symbols()
        print(f'  - Available symbols: {len(symbols)}')
        
        if symbols:
            print(f'    First symbol: {symbols[0]}')
        
        # Test get_current_prices
        test_symbols = ['BTCUSDT', 'ETHUSDT', 'DOGEUSDT']
        prices = mds.get_current_prices(test_symbols)
        print(f'  - Current prices: {len(prices)}')
        
        for symbol, price in prices.items():
            print(f'    {symbol}: {price}')
        
        # Test update_market_data with string symbols
        market_data = mds.update_market_data(test_symbols)
        print(f'  - Market data update: {len(market_data)} symbols')
        
        for symbol in test_symbols:
            if symbol in market_data:
                symbol_data = market_data[symbol]
                prices = symbol_data.get('prices', {})
                current_price = prices.get('current', 0)
                print(f'    {symbol}: {current_price}')
        
        print('[SUCCESS] New market data service tested successfully')
        
    except Exception as e:
        print(f'[ERROR] Test failed: {e}')
        import traceback
        traceback.print_exc()
    
    print('=' * 60)
    print('[RESULT] Market data service rewrite complete')
    print('=' * 60)

if __name__ == "__main__":
    rewrite_market_data_service()
