@echo off
cls
echo ============================================
echo   Video-Redes: App + Tunel + Backend casa
echo ============================================
echo.
echo Levantando la app en tu PC (IP residencial)...
cd /d c:\www\video-redes
start "Video-Redes App" cmd /c ".venv\Scripts\activate.bat && python src/server.py"
echo Esperando a que la app arranque...
timeout /t 5 >nul
echo.
echo Abriendo tunel y avisandole la URL a Railway...
echo (deja esta ventana abierta. Para cortar: cerrala)
echo.
call .venv\Scripts\activate.bat
python home_tunnel.py
pause
