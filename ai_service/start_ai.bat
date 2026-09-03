@echo off
echo ========================================
echo EmoLink AI Service - Quick Start
echo ========================================
echo.

cd /d "%~dp0"
echo Current directory: %CD%
echo.

echo Step 1: Installing Python dependencies...
echo.
py -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install dependencies.
    echo Try running: py -m pip install fastapi uvicorn google-generativeai pydantic python-dotenv PyMySQL
    pause
    exit /b 1
)
echo.
echo Step 2: Dependencies installed successfully!
echo.

echo Step 3: Starting AI Service on port 8001...
echo.
echo Open your browser and go to: http://127.0.0.1:8001/docs
echo for the API documentation.
echo.
py -m uvicorn main:app --reload --port 8001 --host 127.0.0.1
