#!/usr/bin/env python3
"""
Sample Real Data Generator for v3.2 Testing
=============================================
Generates realistic sample data when API access is not available.
"""

import json
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

class SampleDataGenerator:
    """Generates realistic sample market data for testing"""
    
    def __init__(self):
        self.symbols = [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT",
            "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT",
            "LINKUSDT", "DOTUSDT", "LTCUSDT", "BCHUSDT",
            "MATICUSDT", "ATOMUSDT", "UNIUSDT", "ETCUSDT"
        ]
        
        # Base prices for each symbol
        self.base_prices = {
            "BTCUSDT": 50000.0,
            "ETHUSDT": 3000.0,
            "BNBUSDT": 600.0,
            "SOLUSDT": 150.0,
            "XRPUSDT": 0.5,
            "ADAUSDT": 0.4,
            "DOGEUSDT": 0.08,
            "AVAXUSDT": 35.0,
            "LINKUSDT": 15.0,
            "DOTUSDT": 7.0,
            "LTCUSDT": 70.0,
            "BCHUSDT": 250.0,
            "MATICUSDT": 0.9,
            "ATOMUSDT": 10.0,
            "UNIUSDT": 8.0,
            "ETCUSDT": 3.0
        }
        
        # Different market patterns for different symbols
        self.patterns = {
            "BTCUSDT": "trending_up",      # Strong uptrend
            "ETHUSDT": "volatile",         # High volatility
            "BNBUSDT": "sideways",         # Sideways market
            "SOLUSDT": "trending_down",    # Downtrend
            "XRPUSDT": "mean_reverting",   # Mean reversion
            "ADAUSDT": "breakout",         # Breakout pattern
            "DOGEUSDT": "chaotic",         # Random walk
            "AVAXUSDT": "trending_up",
            "LINKUSDT": "sideways",
            "DOTUSDT": "volatile",
            "LTCUSDT": "mean_reverting",
            "BCHUSDT": "breakout",
            "MATICUSDT": "trending_down",
            "ATOMUSDT": "sideways",
            "UNIUSDT": "volatile",
            "ETCUSDT": "chaotic"
        }
        
        self.data_dir = Path(__file__).parent / "real_data"
        self.data_dir.mkdir(exist_ok=True)
    
    def generate_price_pattern(self, base_price: float, pattern: str, minutes: int):
        """Generate price data based on pattern"""
        prices = []
        current_price = base_price
        
        for i in range(minutes):
            if pattern == "trending_up":
                # Gradual uptrend with noise
                trend = 0.0002 * (i / minutes)  # Gradual increase
                noise = random.gauss(0, 0.001)
                change = trend + noise
                
            elif pattern == "trending_down":
                # Gradual downtrend with noise
                trend = -0.0002 * (i / minutes)  # Gradual decrease
                noise = random.gauss(0, 0.001)
                change = trend + noise
                
            elif pattern == "sideways":
                # Oscillating around base price
                oscillation = 0.001 * math.sin(i * 0.1)
                noise = random.gauss(0, 0.0005)
                change = oscillation + noise
                
            elif pattern == "volatile":
                # High volatility with random movements
                change = random.gauss(0, 0.003)
                # Occasional spikes
                if random.random() < 0.05:
                    change *= 3
                    
            elif pattern == "mean_reverting":
                # Tendency to return to mean
                deviation = (current_price - base_price) / base_price
                correction = -deviation * 0.1
                noise = random.gauss(0, 0.0008)
                change = correction + noise
                
            elif pattern == "breakout":
                # Extended sideways then breakout
                if i < minutes * 0.7:
                    change = random.gauss(0, 0.0003)  # Tight range
                else:
                    change = 0.002 * (1 if random.random() > 0.5 else -1)  # Breakout
                    
            elif pattern == "chaotic":
                # Pure random walk
                change = random.gauss(0, 0.002)
                
            else:
                change = random.gauss(0, 0.001)
            
            # Apply change
            current_price *= (1 + change)
            prices.append(current_price)
        
        return prices
    
    def generate_ohlcv(self, prices: list, volume_base: float = 1000000):
        """Convert prices to OHLCV format"""
        ohlcv = []
        
        for i, price in enumerate(prices):
            # Generate realistic OHLC
            high = price * (1 + abs(random.gauss(0, 0.001)))
            low = price * (1 - abs(random.gauss(0, 0.001)))
            
            # Ensure high >= price >= low
            high = max(high, price)
            low = min(low, price)
            
            # Generate volume
            volume = volume_base * (1 + random.gauss(0, 0.3))
            
            # Timestamp (1-minute intervals starting from 24 hours ago)
            timestamp = datetime.now() - timedelta(hours=24) + timedelta(minutes=i)
            
            ohlcv.append({
                'open': price,
                'high': high,
                'low': low,
                'close': price,
                'volume': volume,
                'datetime': timestamp.isoformat(),
                'timestamp': int(timestamp.timestamp() * 1000)
            })
        
        return ohlcv
    
    def generate_ticker_data(self, prices: list):
        """Generate 24h ticker data from prices"""
        if not prices:
            return {}
        
        start_price = prices[0]
        end_price = prices[-1]
        high_price = max(prices)
        low_price = min(prices)
        
        price_change = end_price - start_price
        price_change_percent = (price_change / start_price) * 100
        
        # Generate volume data
        volume = random.uniform(1000000, 10000000)
        quote_volume = volume * sum(prices) / len(prices)
        
        return {
            'symbol': 'SYMBOL',
            'priceChange': str(price_change),
            'priceChangePercent': str(price_change_percent),
            'high': str(high_price),
            'low': str(low_price),
            'volume': str(volume),
            'quoteVolume': str(quote_volume),
            'openTime': int((datetime.now() - timedelta(hours=24)).timestamp() * 1000),
            'closeTime': int(datetime.now().timestamp() * 1000)
        }
    
    def generate_all_data(self):
        """Generate complete dataset for all symbols and timeframes"""
        print("[GENERATOR] Creating sample real data for v3.2 testing...")
        print("=" * 60)
        
        all_data = {}
        
        # Generate 24 hours of data (1440 minutes)
        total_minutes = 24 * 60
        
        for symbol in self.symbols:
            print(f"[SYMBOL] {symbol}...")
            
            pattern = self.patterns.get(symbol, "sideways")
            base_price = self.base_prices[symbol]
            
            symbol_data = {}
            
            # Generate minute data
            minute_prices = self.generate_price_pattern(base_price, pattern, total_minutes)
            symbol_data['1m'] = self.generate_ohlcv(minute_prices)
            
            # Generate 5-minute data (aggregate)
            five_minute_prices = [minute_prices[i] for i in range(0, len(minute_prices), 5)]
            symbol_data['5m'] = self.generate_ohlcv(five_minute_prices, volume_base=5000000)
            
            # Generate 15-minute data (aggregate)
            fifteen_minute_prices = [minute_prices[i] for i in range(0, len(minute_prices), 15)]
            symbol_data['15m'] = self.generate_ohlcv(fifteen_minute_prices, volume_base=15000000)
            
            # Generate 1-hour data (aggregate)
            hourly_prices = [minute_prices[i] for i in range(0, len(minute_prices), 60)]
            symbol_data['1h'] = self.generate_ohlcv(hourly_prices, volume_base=60000000)
            
            # Generate ticker data
            ticker = self.generate_ticker_data(minute_prices)
            ticker['symbol'] = symbol
            symbol_data['ticker'] = ticker
            
            all_data[symbol] = symbol_data
            
            print(f"  Pattern: {pattern}")
            print(f"  1m candles: {len(symbol_data['1m'])}")
            print(f"  Price change: {ticker['priceChangePercent']}%")
        
        # Save data
        output_file = self.data_dir / f"real_data_24h_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_file, 'w') as f:
            json.dump(all_data, f, indent=2, default=str)
        
        print(f"\n[SUCCESS] Sample data saved to {output_file}")
        print(f"[INFO] Generated data for {len(all_data)} symbols")
        print(f"[INFO] Timeframes: 1m, 5m, 15m, 1h")
        print(f"[INFO] Patterns: {set(self.patterns.values())}")
        
        # Generate summary
        self.generate_summary(output_file)
        
        return output_file
    
    def generate_summary(self, data_file: Path):
        """Generate summary of generated data"""
        print(f"\n[SUMMARY] Analyzing {data_file.name}")
        print("=" * 60)
        
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        summary = {
            'generation_time': datetime.now().isoformat(),
            'total_symbols': len(data),
            'patterns_used': {},
            'price_changes': {}
        }
        
        for symbol, symbol_data in data.items():
            pattern = self.patterns.get(symbol, 'unknown')
            summary['patterns_used'][pattern] = summary['patterns_used'].get(pattern, 0) + 1
            
            if 'ticker' in symbol_data:
                price_change = float(symbol_data['ticker']['priceChangePercent'])
                summary['price_changes'][symbol] = price_change
        
        # Print summary
        print("Patterns distribution:")
        for pattern, count in summary['patterns_used'].items():
            print(f"  {pattern}: {count} symbols")
        
        print("\nPrice changes:")
        for symbol, change in summary['price_changes'].items():
            print(f"  {symbol}: {change:+.2f}%")
        
        # Save summary
        summary_file = self.data_dir / f"summary_{data_file.stem}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n[SUMMARY] Saved to {summary_file}")

def main():
    """Main generation function"""
    print("[SAMPLE DATA] Realistic Market Data Generator for v3.2")
    print("=" * 60)
    
    generator = SampleDataGenerator()
    
    try:
        data_file = generator.generate_all_data()
        
        print(f"\n[COMPLETE] Sample data ready for v3.2 testing!")
        print(f"[NEXT] Use: python test_v3_2_real_data.py")
        print(f"[INFO] This data contains diverse market patterns:")
        print(f"  - Trending markets (up/down)")
        print(f"  - Sideways markets")
        print(f"  - Volatile markets")
        print(f"  - Mean reversion patterns")
        print(f"  - Breakout patterns")
        print(f"  - Chaotic movements")
        
    except Exception as e:
        print(f"[ERROR] Generation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
