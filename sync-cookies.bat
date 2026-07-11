@echo off
cls
echo ============================================
echo   Sincronizar cookies con Railway
echo ============================================
echo.
echo Se abrira un navegador. Logueate normal en la red,
echo y la cookie se sube sola a Railway al terminar.
echo.
set /p PLATFORM="Red (instagram / facebook): "
call .venv\Scripts\activate.bat
python push_cookies.py %PLATFORM%
echo.
pause
