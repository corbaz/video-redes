@echo off
cls
cd /d c:\www\video-redes
call .venv\Scripts\activate.bat
python tunnel_status.py
echo.
pause
