@echo off
cls
echo ============================================
echo   Generando APK de Redes Downloader
echo ============================================
echo.
cd /d c:\www\video-redes\mobile\android
call gradlew.bat assembleDebug
if errorlevel 1 (
    echo.
    echo [X] Fallo el build. Revisa el error de arriba.
    pause
    exit /b 1
)
copy /y app\build\outputs\apk\debug\app-debug.apk ..\RedesDownloader-debug.apk >nul
echo.
echo [OK] APK generado en: mobile\RedesDownloader-debug.apk
echo Pasalo al celular e instalalo (permitir "origenes desconocidos").
echo.
pause
