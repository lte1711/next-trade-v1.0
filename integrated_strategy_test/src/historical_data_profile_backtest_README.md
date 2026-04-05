# Historical Data Profile Backtest

This runner reuses the promoted `v3_candidate_cs_more_entries` profile against external daily-bar data.

## Supported Input Formats

### JSON

Either:

1. A list of day records already shaped like the simulator:

```json
[
  {
    "date": "2025-04-02",
    "timestamp": "2025-04-02",
    "synthetic_regime": "UNKNOWN",
    "symbols": {
      "BTCUSDT": {
        "price": 65000.0,
        "change": 1.25,
        "volatility": 3.8,
        "volume": 12345,
        "quote_volume": 91000000.0,
        "high": 66000.0,
        "low": 64000.0,
        "change_history": [0.5, 1.0, 1.25],
        "quote_volume_history": [80000000, 85000000, 91000000]
      }
    }
  }
]
```

2. A flat list of rows:

```json
[
  {
    "date": "2025-04-02",
    "symbol": "BTCUSDT",
    "price": 65000.0,
    "change": 1.25,
    "volatility": 3.8,
    "quote_volume": 91000000.0,
    "high": 66000.0,
    "low": 64000.0
  }
]
```

### CSV

Required headers:

```text
date,symbol,price,change,volatility,quote_volume,high,low
```

Example:

```csv
date,symbol,price,change,volatility,quote_volume,high,low
2025-04-02,BTCUSDT,65000.0,1.25,3.8,91000000.0,66000.0,64000.0
2025-04-02,ETHUSDT,3500.0,0.95,4.2,70000000.0,3560.0,3450.0
```

## Run

```powershell
python .\integrated_strategy_test\src\historical_data_profile_backtest.py .\path\to\your_history.csv
```

Optional output path:

```powershell
python .\integrated_strategy_test\src\historical_data_profile_backtest.py .\path\to\your_history.json --output .\custom_results.json
```
