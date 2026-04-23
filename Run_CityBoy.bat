@echo off
title City Boy Universal Booster Launcher
color 0b

:: ─────────────────────────────────────────
:: Check if already running as Administrator
:: ─────────────────────────────────────────
net session >nul 2>&1
if %errorlevel% NEQ 0 (
    echo Requesting Administrator privileges to apply system optimizations...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"

echo ==============================================
echo       CITY BOY UNIVERSAL BOOSTER
echo       Running with Administrator Privileges
echo ==============================================
echo.
echo Verifying system dependencies...
pip install customtkinter psutil >nul 2>&1
echo Dependencies confirmed. Launching application...
echo.
python main.py
pause
