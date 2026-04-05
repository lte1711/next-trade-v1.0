@echo off
setlocal
cd /d "%~dp0"
start http://127.0.0.1:8787
merged_partial_v2_v1.exe --dashboard --dashboard-port 8787
