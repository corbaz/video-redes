@echo off
cls
echo Deteniendo tunel y app local...

REM 1) Matar home_tunnel por su PID (asi no relanza cloudflared con la auto-reparacion)
if exist ".tunnel_pid" (
    set /p TPID=<.tunnel_pid
    taskkill /f /pid %TPID% >nul 2>&1
    del /q ".tunnel_pid" >nul 2>&1
)

REM 2) Matar las ventanas por titulo (y sus hijos con /t)
taskkill /f /t /fi "WINDOWTITLE eq Video-Redes Tunnel*" >nul 2>&1
taskkill /f /t /fi "WINDOWTITLE eq Video-Redes App*" >nul 2>&1

REM 3) Matar cloudflared (despues de home_tunnel, para que no lo resucite)
taskkill /f /im cloudflared.exe >nul 2>&1

REM 4) Limpiar el estado
del /q ".tunnel_url" >nul 2>&1

echo.
echo Listo. Tunel y app detenidos.
echo (Corre tunnel-status.bat para confirmar que quedo apagado.)
echo.
pause
