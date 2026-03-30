@echo off
chcp 65001 >nul
cd /d "C:\next-trade-ver1.0"
set PYTHONPATH=C:\next-trade-ver1.0\src

echo Starting API Server...
start /MIN cmd /c "cd /d C:\next-trade-ver1.0 && set PYTHONPATH=C:\next-trade-ver1.0\src && .venv\Scripts\python.exe -m uvicorn next_trade.api.app:app --host 127.0.0.1 --port 8100"

timeout /t 3 >nul

echo Starting Dashboard Server...
start /MIN cmd /c "cd /d C:\next-trade-ver1.0 && .venv\Scripts\python.exe tools\dashboard\multi5_dashboard_server.py"

timeout /t 3 >nul

echo Starting Engine Wrapper...
start /MIN cmd /c "cd /d C:\next-trade-ver1.0 && .venv\Scripts\python.exe tools\multi5\run_multi5_engine.py --runtime-minutes 1440 --scan-interval-sec 5"

echo All services started in background
pause
