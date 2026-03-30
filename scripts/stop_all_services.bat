@echo off
REM NEXT-TRADE 모든 서비스 중지 스크립트

echo Stopping all NEXT-TRADE services...
echo.

REM 모든 Python 프로세스 중지
taskkill /f /im python.exe

REM 잠시 대기
timeout /t 3 /nobreak >nul

echo.
echo All NEXT-TRADE services stopped!
echo.

pause
