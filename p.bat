@echo off
cls
echo Matando procesos Python existentes...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1
echo Procesos Python terminados.
echo.
echo Iniciando servidor...
rem cd /d c:\www\insta
python server.py
pause
