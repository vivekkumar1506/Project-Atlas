@echo off
setlocal EnableDelayedExpansion
title Project Atlas - Prototype Launcher

cd /d "%~dp0"

echo ======================================================================
echo           PROJECT ATLAS - LOCAL PROTOTYPE LAUNCHER
echo ======================================================================
echo.

:: -------------------------------------------------------------------
:: 1. Verify Configuration (.env)
:: -------------------------------------------------------------------
echo [1/5] Checking configuration files...
if not exist ".env" (
    if exist ".env.example" (
        echo [WARN] .env file not found.
        echo        Creating .env from .env.example with default local configuration...
        copy ".env.example" ".env" >nul
        echo [OK]   .env created. If your MySQL credentials differ, please edit .env.
    ) else (
        echo [ERROR] Neither .env nor .env.example was found in "%~dp0".
        echo         Please restore .env.example and rerun start.bat.
        echo.
        pause
        exit /b 1
    )
) else (
    echo [OK]   .env configuration file detected.
)

:: -------------------------------------------------------------------
:: 2. Detect Python Virtual Environment & Runtime
:: -------------------------------------------------------------------
echo.
echo [2/5] Detecting Python virtual environment...
set "PYTHON_EXE="

if exist "%~dp0backend\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0backend\.venv\Scripts\python.exe"
) else if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
) else (
    where python.exe >nul 2>&1
    if not errorlevel 1 (
        for /f "delims=" %%I in ('where python.exe') do (
            if not defined PYTHON_EXE set "PYTHON_EXE=%%I"
        )
    )
)

if not defined PYTHON_EXE (
    echo [ERROR] Python runtime was not found!
    echo.
    echo Please install Python 3.11+ and create the virtual environment:
    echo   1. uv venv backend\.venv
    echo      or: python -m venv backend\.venv
    echo   2. backend\.venv\Scripts\pip install -r backend\requirements.txt
    echo.
    pause
    exit /b 1
)

echo [OK]   Using Python runtime: !PYTHON_EXE!

:: -------------------------------------------------------------------
:: 3. Verify Python Dependencies
:: -------------------------------------------------------------------
echo.
echo [3/5] Verifying required backend dependencies...
"!PYTHON_EXE!" -c "import fastapi, uvicorn, pydantic, sqlalchemy, pymysql" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Required Python packages are missing.
    echo.
    echo Please install dependencies using:
    echo   "!PYTHON_EXE!" -m pip install -r backend\requirements.txt
    echo.
    pause
    exit /b 1
)
echo [OK]   Core Python dependencies verified.

:: -------------------------------------------------------------------
:: 4. Detect Port Configuration
:: -------------------------------------------------------------------
set "FASTAPI_PORT=8000"
set "PORTAL_PORT=8080"

for /f "tokens=1,2" %%A in ('"!PYTHON_EXE!" -c "from backend.app.config import get_settings; s=get_settings(); print(s.app_port, 8080)" 2^>nul') do (
    set "FASTAPI_PORT=%%A"
    set "PORTAL_PORT=%%B"
)

:: -------------------------------------------------------------------
:: 5. Detect PHP Runtime (for CI3 Portal)
:: -------------------------------------------------------------------
echo.
echo [4/5] Detecting PHP runtime for CodeIgniter 3 portal...
set "PHP_EXE="

where php.exe >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%I in ('where php.exe') do (
        if not defined PHP_EXE set "PHP_EXE=%%I"
    )
)

if not defined PHP_EXE (
    if exist "C:\xampp\php\php.exe" set "PHP_EXE=C:\xampp\php\php.exe"
    if exist "C:\php\php.exe" set "PHP_EXE=C:\php\php.exe"
    if exist "C:\Program Files\PHP\php.exe" set "PHP_EXE=C:\Program Files\PHP\php.exe"
    if exist "C:\tools\php\php.exe" set "PHP_EXE=C:\tools\php\php.exe"
    if exist "C:\laragon\bin\php\php.exe" set "PHP_EXE=C:\laragon\bin\php\php.exe"
)

:: -------------------------------------------------------------------
:: 6. Launch Services (Prevent Duplicates & Keep Terminals Open)
:: -------------------------------------------------------------------
echo.
echo [5/5] Checking service statuses and launching servers...

:: Check if FastAPI backend is already running
set "FASTAPI_RUNNING=0"
"!PYTHON_EXE!" -c "import socket, sys; s=socket.socket(); res=s.connect_ex(('127.0.0.1', int('!FASTAPI_PORT!'))); s.close(); sys.exit(0 if res==0 else 1)" >nul 2>&1
if not errorlevel 1 (
    set "FASTAPI_RUNNING=1"
    echo [INFO] FastAPI AI backend is ALREADY RUNNING on port !FASTAPI_PORT!. Skipping launch.
) else (
    echo [INFO] Launching FastAPI AI backend on port !FASTAPI_PORT! in separate window...
    start "Project Atlas - FastAPI Backend" cmd.exe /k call "%~dp0run_backend.bat" !FASTAPI_PORT! "!PYTHON_EXE!"
)

:: Check if CI3 Portal is already running
set "PORTAL_RUNNING=0"
"!PYTHON_EXE!" -c "import socket, sys; s=socket.socket(); res=s.connect_ex(('127.0.0.1', int('!PORTAL_PORT!'))); s.close(); sys.exit(0 if res==0 else 1)" >nul 2>&1
if not errorlevel 1 (
    set "PORTAL_RUNNING=1"
    echo [INFO] CodeIgniter 3 Portal is ALREADY RUNNING on port !PORTAL_PORT!. Skipping launch.
) else (
    if defined PHP_EXE (
        echo [OK]   PHP CLI detected: !PHP_EXE!
        echo [INFO] Launching CodeIgniter 3 Portal on port !PORTAL_PORT! in separate window...
        start "Project Atlas - CI3 Portal" cmd.exe /k call "%~dp0run_portal.bat" !PORTAL_PORT! "!PHP_EXE!"
    ) else (
        echo [WARN] PHP CLI was not found on system PATH or standard folders.
        echo        The FastAPI AI Backend was launched, but the PHP portal UI could not start.
        echo.
        echo        To run the CodeIgniter 3 Portal UI:
        echo          1. Install PHP or XAMPP
        echo          2. Add PHP to your system PATH
        echo          3. Rerun start.bat or start manually: cd portal ^&^& php -S 0.0.0.0:!PORTAL_PORT!
    )
)

echo.
echo ======================================================================
echo             PROJECT ATLAS SERVICES READY / RUNNING
echo ======================================================================
echo.
echo   [1] CodeIgniter 3 Portal UI:
echo       http://localhost:!PORTAL_PORT!/
echo.
echo   [2] FastAPI AI Backend Docs:
echo       http://localhost:!FASTAPI_PORT!/docs
echo.
echo   [3] Health Check Endpoint:
echo       http://localhost:!FASTAPI_PORT!/health
echo.
echo ----------------------------------------------------------------------
echo   * Opening CodeIgniter 3 Portal in your default web browser...
echo   * Server consoles are kept open in separate terminal windows.
echo   * Check those windows if you encounter any runtime or database errors.
echo   * To stop all running Atlas services, run stop.bat or close windows.
echo ======================================================================
echo.

:: Automatically open browser after 2 seconds
timeout /t 2 >nul 2>&1
start http://localhost:!PORTAL_PORT!/

pause
