#!/usr/bin/env python3
"""
24-Hour Real Data Downloader for v3.2 Testing
============================================
Downloads actual market data for realistic backtesting.
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add project directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import ccxt
import pandas as pd

class RealDataDownloader:
    """Downloads real market data for v3.2 testing"""
    
    def __init__(self):
        self.exchange = ccxt.binance({
            'sandbox': True,  # Use testnet
            'enableRateLimit': True,
        })
        
        # Symbols to download
        self.symbols = [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT",
            "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT",
            "LINKUSDT", "DOTUSDT", "LTCUSDT", "BCHUSDT",
            "MATICUSDT", "ATOMUSDT", "UNIUSDT", "ETCUSDT"
        ]
        
        # Timeframes to download
        self.timeframes = ['1m', '5m', '15m', '1h']
        
        # Data directory
        self.data_dir = project_root / "real_data"
        self.data_dir.mkdir(exist_ok=True)
        
    def download_klines(self, symbol: str, timeframe: str, limit: int = 1000):
        """Download kline data for a symbol"""
        try:
            print(f"[DOWNLOAD] {symbol} {timeframe}...")
            
            # Calculate start time (24 hours ago)
            since = self.exchange.parse8601((datetime.now() - timedelta(hours=24)).isoformat())
            
            # Download data
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since, limit)
            
            if not ohlcv:
                print(f"[WARNING] No data for {symbol} {timeframe}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
            
        except Exception as e:
            print(f"[ERROR] Failed to download {symbol} {timeframe}: {e}")
            return None
    
    def download_ticker_data(self, symbol: str):
        """Download 24h ticker data"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'priceChangePercent': str(ticker.get('percentage', 0)),
                'priceChange': str(ticker.get('absolute', 0)),
                'high': str(ticker.get('high', 0)),
                'low': str(ticker.get('low', 0)),
                'volume': str(ticker.get('baseVolume', 0)),
                'quoteVolume': str(ticker.get('quoteVolume', 0)),
                'openTime': ticker.get('timestamp', 0),
                'closeTime': ticker.get('datetime', ''),
            }
        except Exception as e:
            print(f"[ERROR] Failed to download ticker for {symbol}: {e}")
            return None
    
    def download_all_data(self):
        """Download all data for testing"""
        print("[DOWNLOAD] Starting 24-hour real data download...")
        print("=" * 60)
        
        # Download klines for all symbols and timeframes
        all_data = {}
        
        for symbol in self.symbols:
            print(f"\n[SYMBOL] {symbol}")
            symbol_data = {}
            
            for timeframe in self.timeframes:
                df = self.download_klines(symbol, timeframe)
                if df is not None:
                    symbol_data[timeframe] = df.to_dict('records')
                    print(f"  {timeframe}: {len(df)} candles")
                else:
                    print(f"  {timeframe}: FAILED")
            
            # Download ticker data
            ticker = self.download_ticker_data(symbol)
            if ticker:
                symbol_data['ticker'] = ticker
                print(f"  ticker: OK")
            
            if symbol_data:
                all_data[symbol] = symbol_data
                
            # Rate limiting
            time.sleep(0.1)
        
        # Save all data
        output_file = self.data_dir / f"real_data_24h_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_file, 'w') as f:
            json.dump(all_data, f, indent=2, default=str)
        
        print(f"\n[SUCCESS] Data saved to {output_file}")
        print(f"[INFO] Total symbols: {len(all_data)}")
        print(f"[INFO] Timeframes: {self.timeframes}")
        
        return output_file
    
    def generate_summary(self, data_file: Path):
        """Generate summary of downloaded data"""
        print(f"\n[SUMMARY] Analyzing {data_file.name}")
        print("=" * 60)
        
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        summary = {
            'download_time': datetime.now().isoformat(),
            'total_symbols': len(data),
            'symbols': {}
        }
        
        for symbol, symbol_data in data.items():
            symbol_summary = {
                'ticker': symbol_data.get('ticker', {}),
                'timeframes': {}
            }
            
            for tf in self.timeframes:
                if tf in symbol_data:
                    candles = symbol_data[tf]
                    symbol_summary['timeframes'][tf] = {
                        'count': len(candles),
                        'start_time': candles[0]['datetime'] if candles else None,
                        'end_time': candles[-1]['datetime'] if candles else None,
                        'price_range': {
                            'min': min(float(c['low']) for c in candles) if candles else None,
                            'max': max(float(c['high']) for c in candles) if candles else None,
                        }
                    }
            
            summary['symbols'][symbol] = symbol_summary
            
            # Print symbol summary
            print(f"{symbol}:")
            if 'ticker' in symbol_summary:
                ticker = symbol_summary['ticker']
                print(f"  Price Change: {ticker.get('priceChangePercent', 'N/A')}%")
            
            for tf, tf_data in symbol_summary['timeframes'].items():
                print(f"  {tf}: {tf_data['count']} candles")
                if tf_data['price_range']['min'] and tf_data['price_range']['max']:
                    price_range = tf_data['price_range']['max'] - tf_data['price_range']['min']
                    print(f"    Range: {price_range:.2f} ({price_range/tf_data['price_range']['min']*100:.2f}%)")
        
        # Save summary
        summary_file = self.data_dir / f"summary_{data_file.stem}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n[SUMMARY] Saved to {summary_file}")
        return summary

def main():
    """Main download function"""
    print("[REAL DATA] 24-Hour Market Data Downloader for v3.2")
    print("=" * 60)
    
    # Check if testnet credentials are available
    if not os.getenv('BINANCE_TESTNET_KEY') or not os.getenv('BINANCE_TESTNET_SECRET'):
        print("[ERROR] Testnet credentials not found!")
        print("Please set environment variables:")
        print("  export BINANCE_TESTNET_KEY=your_key")
        print("  export BINANCE_TESTNET_SECRET=your_secret")
        return
    
    # Initialize downloader
    downloader = RealDataDownloader()
    
    try:
        # Download all data
        data_file = downloader.download_all_data()
        
        if data_file:
            # Generate summary
            downloader.generate_summary(data_file)
            
            print(f"\n[COMPLETE] Real data ready for v3.2 testing!")
            print(f"[NEXT] Use: python test_v3_2_real_data.py")
        
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
