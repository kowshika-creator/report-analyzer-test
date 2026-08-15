@echo off
TITLE AXON Server Launcher
COLOR 0B

echo =======================================================================
echo                 AXON - LAB INSIGHT DECODED LAUNCHER
echo =======================================================================
echo.

:: 1. Validate Python Installation
echo [1/4] Verifying Python installation...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Python was not found in your system PATH.
    echo Please install Python 3.10+ from https://www.python.org/
    echo.
) else (
    echo [SUCCESS] Python is available.
    
    :: Initialize and Seed Backend
    echo [2/4] Initializing FastAPI Backend and Seeding SQLite Database...
    cd backend
    if not exist venv (
        echo Creating virtual environment venv...
        python -m venv venv
    )
    
    echo Activating virtual environment...
    call venv\Scripts\activate
    
    echo Installing backend dependencies...
    pip install -r requirements.txt
    
    echo Recreating and Seeding clinical database...
    python init_db.py
    
    echo Starting FastAPI server in a new window...
    start "FastAPI Backend Server" cmd /k "venv\Scripts\activate && uvicorn main:app --reload --port 8000"
    cd ..
)

:: 2. Validate Node/NPM Installation
echo.
echo [3/4] Verifying Node.js and NPM installation...
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Node.js and NPM were not found in your system PATH.
    echo Please install Node.js LTS version from https://nodejs.org/
    echo.
) else (
    echo [SUCCESS] Node.js and NPM are available.
    
    :: Initialize Frontend
    echo [4/4] Initializing Next.js Frontend...
    cd frontend
    echo Installing node packages with npm install...
    call npm install
    
    echo Starting Next.js Dev Server in a new window...
    start "Next.js Frontend Dashboard" cmd /k "npm run dev"
    cd ..
    
    echo.
    echo =======================================================================
    echo [SUCCESS] Next.js is launching on: http://localhost:3000
    echo [SUCCESS] FastAPI is launching on: http://127.0.0.1:8000
    echo =======================================================================
    echo.
    echo Opening dashboard in your default browser...
    timeout /t 5 >nul
    start http://localhost:3000
)

echo.
echo Press any key to exit this launcher...
pause >nul
