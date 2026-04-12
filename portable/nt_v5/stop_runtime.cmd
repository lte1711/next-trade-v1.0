@echo off
setlocal
cd /d "%~dp0"
python tools\ops\runtime_ops.py stop
endlocal
