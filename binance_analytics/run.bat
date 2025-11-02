@echo off
REM Binance Live Quant Analytics - Quick Start Script for Windows

echo Starting Binance Live Quant Analytics...
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed. Please install Python 3.9+
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Create data directory
if not exist "data" mkdir data

REM Start backend
echo Starting backend on port 8000...
start "Backend" python backend/main.py

timeout /t 3 /nobreak

REM Start frontend
echo Starting frontend on port 8501...
streamlit run frontend/app.py

pause
