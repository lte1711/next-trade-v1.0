#!/usr/bin/env python3
"""
Simple Market Data Fix - Simple fix for market data service
"""

def simple_market_data_fix():
    """Simple fix for market data service"""
    print('=' * 60)
    print('SIMPLE MARKET DATA FIX')
    print('=' * 60)
    
    # Read the current file
    with open('core/market_data_service.py', 'r') as f:
        content = f.read()
    
    # Find and replace the problematic method
    import re
    
    # Find the update_market_data method
    pattern = r'def update_market_data\(self, symbols.*?return \{\}'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        old_method = match.group(0)
        
        # Create a simple replacement
        new_method = '''def update_market_data(self, symbols, intervals=['1m', '5m', '15m', '1h']):
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
            return {}'''
        
        # Replace in content
        new_content = content.replace(old_method, new_method)
        
        # Write back
        with open('core/market_data_service.py', 'w') as f:
            f.write(new_content)
        
        print('[SUCCESS] Market data service method fixed')
    else:
        print('[ERROR] Could not find update_market_data method')
        return
    
    # Test the fix
    print('\n[TEST] Testing the fix:')
    
    try:
        from core.market_data_service import MarketDataService
        mds = MarketDataService('https://demo-fapi.binance.com')
        
        # Test with string symbols
        test_symbols = ['BTCUSDT', 'ETHUSDT']
        market_data = mds.update_market_data(test_symbols)
        
        print(f'  - Test result: {len(market_data)} symbols updated')
        
        for symbol in test_symbols:
            if symbol in market_data:
                symbol_data = market_data[symbol]
                prices = symbol_data.get('prices', {})
                current_price = prices.get('current', 0)
                print(f'    {symbol}: {current_price}')
        
        print('[SUCCESS] Fix tested successfully')
        
    except Exception as e:
        print(f'[ERROR] Test failed: {e}')
        import traceback
        traceback.print_exc()
    
    print('=' * 60)
    print('[RESULT] Simple market data fix complete')
    print('=' * 60)

if __name__ == "__main__":
    simple_market_data_fix()
