# Merged Partial V2

This folder is a self-contained merge workspace.

The original project and the test project remain untouched.
Everything needed for the merged partial integration now lives inside this folder.

## Intent

This workspace follows the previously selected "Option 2: partial extraction integration":

- keep only the useful strategy logic from the test project
- rebuild the required exchange bridge locally inside the merge folder
- avoid importing the original `next_trade` package at runtime

## Included Components

### Exchange layer

- `src/merged_partial_v2/exchange/public_read_client.py`
  - public ticker and kline access
- `src/merged_partial_v2/exchange/private_read_client.py`
  - private account and position reads
- `src/merged_partial_v2/exchange/execution_client.py`
  - order submission bridge
- `src/merged_partial_v2/exchange/local_binance_bridge.py`
  - copied and simplified local bridge for Binance futures testnet access

### Strategy layer

- `src/merged_partial_v2/services/market_scoring_service.py`
  - extracted market scoring logic from the modular test strategy
- `src/merged_partial_v2/services/symbol_selection_service.py`
  - extracted regime and symbol selection logic

### Orchestration layer

- `src/merged_partial_v2/simulation/strategy_engine.py`
  - combines extracted strategy logic and local exchange clients
- `src/merged_partial_v2/main.py`
  - builds a merged market/account snapshot
- `run_merged_partial_v2.py`
  - launcher

## Local Config

The merge folder includes its own config file:

- `config.json`

Current defaults:

- exchange base: `https://demo-fapi.binance.com`
- API key env: `BINANCE_TESTNET_KEY_PLACEHOLDER`
- API secret env: `BINANCE_TESTNET_SECRET_PLACEHOLDER`

## Run

From the repository root:

```powershell
python .\merged_partial_v2\run_merged_partial_v2.py
```

## Output

The launcher writes:

- `merged_partial_v2/merged_snapshot.json`

## Notes

- Public market snapshot building works without the original package.
- Private account and order functions require valid Binance testnet credentials in environment variables.
- This is still a merge staging workspace, not a production engine.
