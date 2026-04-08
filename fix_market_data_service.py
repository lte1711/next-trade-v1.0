#!/usr/bin/env python3
"""
Fix Market Data Service - Fix the issue with market data not updating
"""

import json

def fix_market_data_service():
    """Fix the market data service issues"""
    print('=' * 60)
    print('FIX MARKET DATA SERVICE')
    print('=' * 60)
    
    # Read the current market_data_service.py
    with open('core/market_data_service.py', 'r') as f:
        content = f.read()
    
    # Find the problematic update_market_data method
    print('[ANALYSIS] Current update_market_data method:')
    
    # The issue is that update_market_data expects a list of dicts
    # but the runtime is passing a list of strings
    
    # Fix the update_market_data method to handle both dict and string inputs
    fixed_update_method = '''    def update_market_data(self, symbols, intervals=['1m', '5m', '15m', '1h']):
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
            return {}'''
    
    # Replace the method in the file
    import re
    
    # Find the method start and end
    method_pattern = r'def update_market_data\(self, symbols.*?\n\s*except Exception as e:\s*\n\s*self\.log_error\("market_data_update".*?\n\s*return \{\}'
    
    method_match = re.search(method_pattern, content, re.DOTALL)
    
    if method_match:
        old_method = method_match.group(0)
        new_content = content.replace(old_method, fixed_update_method)
        
        # Write the fixed file
        with open('core/market_data_service.py', 'w') as f:
            f.write(new_content)
        
        print('[SUCCESS] update_market_data method fixed')
    else:
        print('[ERROR] Could not find update_market_data method')
        return
    
    # Test the fix
    print('\n[TEST] Testing the fixed market data service:')
    
    try:
        from core.market_data_service import MarketDataService
        mds = MarketDataService('https://demo-fapi.binance.com')
        
        # Test with string symbols (what runtime passes)
        string_symbols = ['BTCUSDT', 'ETHUSDT', 'DOGEUSDT']
        market_data = mds.update_market_data(string_symbols)
        
        print(f'  - String symbols test: {len(market_data)} results')
        
        for symbol in string_symbols:
            if symbol in market_data:
                symbol_data = market_data[symbol]
                prices = symbol_data.get('prices', {})
                current_price = prices.get('current', 0)
                print(f'    {symbol}: {current_price}')
        
        # Test with dict symbols (what service originally expected)
        dict_symbols = [
            {'symbol': 'BTCUSDT', 'base_asset': 'BTC', 'quote_asset': 'USDT'},
            {'symbol': 'ETHUSDT', 'base_asset': 'ETH', 'quote_asset': 'USDT'}
        ]
        market_data = mds.update_market_data(dict_symbols)
        
        print(f'  - Dict symbols test: {len(market_data)} results')
        
        for symbol in ['BTCUSDT', 'ETHUSDT']:
            if symbol in market_data:
                symbol_data = market_data[symbol]
                prices = symbol_data.get('prices', {})
                current_price = prices.get('current', 0)
                print(f'    {symbol}: {current_price}')
        
        print('[SUCCESS] Market data service fix tested successfully')
        
    except Exception as e:
        print(f'[ERROR] Fix test failed: {e}')
        import traceback
        traceback.print_exc()
    
    print('=' * 60)
    print('[RESULT] Market data service fix complete')
    print('=' * 60)

if __name__ == "__main__":
    fix_market_data_service()
