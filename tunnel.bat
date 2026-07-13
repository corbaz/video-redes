@echo off
cls
echo ============================================
echo   Video-Redes: App + Tunel (backend casa)
echo ============================================
echo.
cd /d c:\www\video-redes
echo Levantando la app local...
start "Video-Redes App" cmd /c ".venv\Scripts\activate.bat && python src/server.py"
echo Esperando a que la app arranque...
timeout /t 5 >nul
echo Abriendo tunel y registrandolo en Railway...
start "Video-Redes Tunnel" cmd /c ".venv\Scripts\activate.bat && python -u home_tunnel.py"
echo.
echo Listo. Se abrieron 2 ventanas: "Video-Redes App" y "Video-Redes Tunnel".
echo   - Para apagar todo:  tunnel-off.bat
echo   - Para chequear:     tunnel-status.bat
echo.
echo (Podes cerrar esta ventana; las otras dos siguen corriendo.)
timeout /t 6 >nul
