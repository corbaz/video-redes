@echo off
cls
echo Deteniendo tunel y app local...
taskkill /f /im cloudflared.exe >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq Video-Redes App*" >nul 2>&1
echo.
echo Listo. Tunel y app detenidos.
echo (Si la ventana del tunel sigue abierta, cerrala con Ctrl+C.)
echo.
pause
