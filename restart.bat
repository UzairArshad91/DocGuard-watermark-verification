@echo off
timeout /t 1 /nobreak >nul
taskkill /F /IM python.exe
taskkill /F /IM pythonw.exe
start pythonw login_gui.py