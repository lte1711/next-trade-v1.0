@echo off
cd /d C:\next-trade-ver1.0
set PYTHONPATH=C:\next-trade-ver1.0\src
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
  if not "%%~A"=="" if not "%%~A:~0,1%%"=="#" set "%%~A=%%~B"
)
"C:\next-trade-ver1.0\.venv\Scripts\python.exe" -m uvicorn next_trade.api.app:app --host 127.0.0.1 --port 8100
