@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1"
set ERR=%ERRORLEVEL%
if not "%ERR%"=="0" exit /b %ERR%
echo.
pause
