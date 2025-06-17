@echo off
echo 🚀 Starting logs_querier service...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is required but not installed. Please install Python.
    pause
    exit /b 1
)

echo ✅ Python found
for /f "tokens=*" %%i in ('python --version') do echo %%i

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo ❌ requirements.txt not found. Please ensure you're in the correct directory.
    pause
    exit /b 1
)

REM Install dependencies
echo ℹ️ Installing/updating dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed successfully

REM Check for environment file
if not exist ".env" (
    if exist "env_example.txt" (
        echo ⚠️ .env file not found. Creating from template...
        copy env_example.txt .env
        echo ℹ️ Please edit .env with your Datadog credentials:
        echo   DD_API_KEY=your_actual_api_key
        echo   DD_APP_KEY=your_actual_app_key (optional)
        echo   DD_SITE=datadoghq.com (or your region)
        echo.
        pause
    ) else (
        echo ⚠️ .env file not found and no template available.
        echo ℹ️ You can set environment variables manually:
        echo   set DD_API_KEY=your_actual_api_key
        echo.
    )
)

REM Check if the main script exists
if not exist "logs_querier.py" (
    echo ❌ logs_querier.py not found. Please ensure you're in the correct directory.
    pause
    exit /b 1
)

echo ✅ All checks passed!
echo.

REM Warning about periodic logging
echo ⚠️ PERIODIC LOGGING IS ENABLED BY DEFAULT
echo ℹ️ The service will automatically log status updates every 30 seconds to:
echo   /var/log/logs_querier/logs_querier.log (or ./logs_querier.log as fallback)
echo.
echo ℹ️ This is designed for Datadog agent pickup and monitoring.
echo ℹ️ To disable periodic logging, set in your .env file:
echo   ENABLE_PERIODIC_LOGGING=false
echo.
echo ℹ️ To change log interval (default 30s), set:
echo   LOG_INTERVAL_SECONDS=60
echo.

echo ℹ️ Starting logs_querier service on http://localhost:5000
echo ℹ️ Available endpoints:
echo   GET  /health
echo   POST /logs/search
echo   POST /logs/search/timerange
echo.
echo ℹ️ You can test the service with:
echo   python cli.py health
echo   python cli.py quick-search --service your-service
echo   python cli.py logs
echo.
echo ℹ️ Press Ctrl+C to stop the service
echo.

REM Start the service
python logs_querier.py 