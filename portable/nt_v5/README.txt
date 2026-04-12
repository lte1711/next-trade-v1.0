NT V5 standalone runtime bundle

Folder purpose:
- This folder contains the minimum files required to run the current Binance demo-futures runtime independently.

Included:
- main_runtime.py
- api_config.py
- config.json
- api_credentials.json
- core\*.py required by main_runtime.py
- tools\ops\runtime_ops.py
- runtime\ and logs\ working folders

How to run:
1. Open Command Prompt in this folder.
2. Install dependencies if needed:
   python -m pip install -r requirements.txt
3. Start runtime:
   start_runtime.cmd
4. Check status:
   status_runtime.cmd
5. Stop runtime:
   stop_runtime.cmd

Notes:
- This bundle is configured for Binance demo futures endpoint only.
- Runtime status file is written to runtime\main_runtime_testnet_status.json
- Runtime logs are written to logs\main_runtime_testnet.log
