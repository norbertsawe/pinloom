@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1" %*
if errorlevel 1 exit /b %errorlevel%
if /I not "%~1"=="-NoPath" set "PATH=%LOCALAPPDATA%\Pinloom\bin;%PATH%"
exit /b 0
