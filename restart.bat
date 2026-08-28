@echo off
timeout /t 1 /nobreak >nul
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
cd /d "%~dp0"
start "DocGuard" ".venv\Scripts\pythonw.exe" "login_gui.py"