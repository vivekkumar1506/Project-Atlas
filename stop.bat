@echo off
setlocal EnableDelayedExpansion
title Project Atlas - Service Stopper

cd /d "%~dp0"

echo ======================================================================
echo           PROJECT ATLAS - STOP RUNNING SERVICES
echo ======================================================================
echo.

set "STOPPED=0"

:: -------------------------------------------------------------------
:: 1. Detect Configured Ports
:: -------------------------------------------------------------------
set "FASTAPI_PORT=8000"
set "PORTAL_PORT=8080"

set "PYTHON_EXE="
if exist "backend\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0backend\.venv\Scripts\python.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
)

if defined PYTHON_EXE (
    for /f "tokens=1,2" %%A in ('"!PYTHON_EXE!" -c "from backend.app.config import get_settings; s=get_settings(); print(s.app_port, 8080)" 2^>nul') do (
        set "FASTAPI_PORT=%%A"
        set "PORTAL_PORT=%%B"
    )
)

:: -------------------------------------------------------------------
:: 2. Stop FastAPI Backend Process
:: -------------------------------------------------------------------
echo [1/2] Checking FastAPI backend on port %FASTAPI_PORT%...
for /f "tokens=5" %%P in ('netstat -aon 2^>nul ^| findstr /r ":%FASTAPI_PORT% .*LISTENING"') do (
    if not "%%P"=="0" (
        echo [INFO] Stopping process PID %%P listening on port %FASTAPI_PORT%...
        taskkill /F /PID %%P >nul 2>&1
        set "STOPPED=1"
    )
)

:: -------------------------------------------------------------------
:: 3. Stop CodeIgniter 3 Portal Process
:: -------------------------------------------------------------------
echo [2/2] Checking CodeIgniter 3 portal on port %PORTAL_PORT%...
for /f "tokens=5" %%P in ('netstat -aon 2^>nul ^| findstr /r ":%PORTAL_PORT% .*LISTENING"') do (
    if not "%%P"=="0" (
        echo [INFO] Stopping process PID %%P listening on port %PORTAL_PORT%...
        taskkill /F /PID %%P >nul 2>&1
        set "STOPPED=1"
    )
)

echo.
if "!STOPPED!"=="1" (
    echo [OK] Project Atlas services have been successfully stopped.
) else (
    echo [INFO] No active Project Atlas services were found on ports %FASTAPI_PORT% or %PORTAL_PORT%.
)
echo.
pause
