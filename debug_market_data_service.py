#!/usr/bin/env python3
"""
Debug Market Data Service - Debug why market data service is failing
"""

import json
import requests
from datetime import datetime

def debug_market_data_service():
    """Debug market data service issues"""
    print('=' * 60)
    print('MARKET DATA SERVICE DEBUG')
    print('=' * 60)
    
    # Test the specific failing method
    print('[DEBUG] Testing market data service methods:')
    
    try:
        from core.market_data_service import MarketDataService
        
        # Initialize service
        mds = MarketDataService('https://demo-fapi.binance.com')
        print(f'  - Service initialized: OK')
        
        # Test get_available_symbols
        print(f'\n  - Testing get_available_symbols():')
        symbols = mds.get_available_symbols()
        print(f'    Result: {len(symbols)} symbols')
        
        if symbols:
            print(f'    First symbol type: {type(symbols[0])}')
            print(f'    First symbol: {symbols[0]}')
        
        # Test get_prices method directly
        print(f'\n  - Testing get_prices() method:')
        try:
            test_symbols = ['BTCUSDT', 'ETHUSDT', 'DOGEUSDT']
            prices = mds.get_prices(test_symbols)
            print(f'    Result: {len(prices)} prices')
            
            for symbol, price in prices.items():
                print(f'      {symbol}: {price}')
                
        except Exception as e:
            print(f'    ERROR: {e}')
            import traceback
            traceback.print_exc()
        
        # Test update_market_data with different input formats
        print(f'\n  - Testing update_market_data() with different inputs:')
        
        # Test 1: String symbols
        try:
            string_symbols = ['BTCUSDT', 'ETHUSDT', 'DOGEUSDT']
            market_data = mds.update_market_data(string_symbols)
            print(f'    String symbols: {len(market_data)} results')
        except Exception as e:
            print(f'    String symbols ERROR: {e}')
        
        # Test 2: Dict symbols (what the service expects)
        try:
            # Create dict symbols like the service expects
            dict_symbols = [
                {'symbol': 'BTCUSDT', 'base_asset': 'BTC', 'quote_asset': 'USDT'},
                {'symbol': 'ETHUSDT', 'base_asset': 'ETH', 'quote_asset': 'USDT'},
                {'symbol': 'DOGEUSDT', 'base_asset': 'DOGE', 'quote_asset': 'USDT'}
            ]
            market_data = mds.update_market_data(dict_symbols)
            print(f'    Dict symbols: {len(market_data)} results')
            
            # Check the structure of returned data
            if market_data:
                first_symbol = list(market_data.keys())[0]
                first_data = market_data[first_symbol]
                print(f'    First symbol: {first_symbol}')
                print(f'    Data structure: {list(first_data.keys())}')
                
                # Check prices
                prices = first_data.get('prices', {})
                if prices:
                    print(f'    Prices: {prices}')
                else:
                    print(f'    No prices found')
                    
        except Exception as e:
            print(f'    Dict symbols ERROR: {e}')
            import traceback
            traceback.print_exc()
        
        # Test 3: Mixed symbols
        try:
            mixed_symbols = ['BTCUSDT', {'symbol': 'ETHUSDT'}, 'DOGEUSDT']
            market_data = mds.update_market_data(mixed_symbols)
            print(f'    Mixed symbols: {len(market_data)} results')
        except Exception as e:
            print(f'    Mixed symbols ERROR: {e}')
        
    except Exception as e:
        print(f'  - Service initialization ERROR: {e}')
        import traceback
        traceback.print_exc()
    
    # Check the actual implementation
    print(f'\n[IMPLEMENTATION] Check update_market_data implementation:')
    
    try:
        import inspect
        from core.market_data_service import MarketDataService
        
        # Get the source code of update_market_data
        source = inspect.getsource(MarketDataService.update_market_data)
        print(f'  - update_market_data source:')
        print(f'    {source[:500]}...')
        
        # Get the source code of get_prices
        prices_source = inspect.getsource(MarketDataService.get_prices)
        print(f'\n  - get_prices source:')
        print(f'    {prices_source[:500]}...')
        
    except Exception as e:
        print(f'  - Implementation check ERROR: {e}')
    
    # Test API endpoints directly
    print(f'\n[API ENDPOINTS] Test direct API calls:')
    
    base_url = 'https://demo-fapi.binance.com'
    
    # Test prices endpoint
    try:
        response = requests.get(f'{base_url}/fapi/v1/ticker/price', timeout=5)
        if response.status_code == 200:
            prices = response.json()
            print(f'  - All prices endpoint: OK ({len(prices)} prices)')
            
            # Find our symbols
            test_symbols = ['BTCUSDT', 'ETHUSDT', 'DOGEUSDT']
            found_prices = {}
            
            for price_data in prices:
                symbol = price_data['symbol']
                if symbol in test_symbols:
                    found_prices[symbol] = price_data['price']
            
            print(f'  - Found prices for our symbols: {len(found_prices)}')
            for symbol, price in found_prices.items():
                print(f'    {symbol}: {price}')
                
        else:
            print(f'  - All prices endpoint: FAILED ({response.status_code})')
            
    except Exception as e:
        print(f'  - All prices endpoint ERROR: {e}')
    
    # Test individual price endpoint
    try:
        response = requests.get(f'{base_url}/fapi/v1/ticker/price?symbol=BTCUSDT', timeout=5)
        if response.status_code == 200:
            price_data = response.json()
            print(f'  - Individual price endpoint: OK')
            print(f'    BTCUSDT: {price_data.get('price', 'N/A')}')
        else:
            print(f'  - Individual price endpoint: FAILED ({response.status_code})')
            
    except Exception as e:
        print(f'  - Individual price endpoint ERROR: {e}')
    
    # Check what the runtime is actually passing to the service
    print(f'\n[RUNTIME INTEGRATION] Check what main_runtime passes:')
    
    # Read main_runtime.py to see how it calls market_data_service
    try:
        with open('main_runtime.py', 'r') as f:
            content = f.read()
        
        # Find the line that calls update_market_data
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'update_market_data' in line:
                print(f'  - Line {i+1}: {line.strip()}')
                
                # Show surrounding context
                start = max(0, i-3)
                end = min(len(lines), i+4)
                print(f'  - Context:')
                for j in range(start, end):
                    marker = '>>>' if j == i else '   '
                    print(f'    {marker} {j+1:3d}: {lines[j]}')
                break
        
    except Exception as e:
        print(f'  - Runtime integration check ERROR: {e}')
    
    print('=' * 60)
    print('[RESULT] Market data service debug complete')
    print('=' * 60)

if __name__ == "__main__":
    debug_market_data_service()
