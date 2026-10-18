@echo off
title Project Atlas - FastAPI Backend
cd /d "%~dp0"

set "FASTAPI_PORT=%~1"
if "%FASTAPI_PORT%"=="" set "FASTAPI_PORT=8000"

set "PYTHON_EXE=%~2"
if "%PYTHON_EXE%"=="" set "PYTHON_EXE=%~dp0backend\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    where python.exe >nul 2>&1
    if not errorlevel 1 set "PYTHON_EXE=python.exe"
)

echo Starting FastAPI backend on port %FASTAPI_PORT%...
echo Python: "%PYTHON_EXE%"
"%PYTHON_EXE%" -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port %FASTAPI_PORT%

echo.
echo FastAPI backend stopped. Check any errors above.
pause
