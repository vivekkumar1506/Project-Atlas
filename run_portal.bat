@echo off
title Project Atlas - CI3 Portal
cd /d "%~dp0portal"

set "PORTAL_PORT=%~1"
if "%PORTAL_PORT%"=="" set "PORTAL_PORT=8080"

set "PHP_EXE=%~2"
if "%PHP_EXE%"=="" set "PHP_EXE=C:\xampp\php\php.exe"
if not exist "%PHP_EXE%" (
    if exist "C:\xampp\php\php.exe" set "PHP_EXE=C:\xampp\php\php.exe"
    if exist "C:\php\php.exe" set "PHP_EXE=C:\php\php.exe"
    if not exist "%PHP_EXE%" (
        where php.exe >nul 2>&1
        if not errorlevel 1 set "PHP_EXE=php.exe"
    )
)

echo Starting CodeIgniter 3 Portal on port %PORTAL_PORT%...
echo PHP: "%PHP_EXE%"
"%PHP_EXE%" -S 127.0.0.1:%PORTAL_PORT% -t "%~dp0portal" "%~dp0portal\router.php"

echo.
echo Portal server stopped. Check errors above.
pause
