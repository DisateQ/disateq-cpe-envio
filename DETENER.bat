@echo off
title CPE DisateQ - Detener
color 0E

echo.
echo  ===================================================
echo    CPE DisateQ (tm)  -  Detener servicio
echo  ===================================================
echo.

:: Detener proceso GUI
taskkill /f /im cpe_disateq.exe >nul 2>&1
if %errorlevel%==0 (
    echo  [OK] Proceso cpe_disateq.exe detenido.
) else (
    echo  [INFO] El proceso no estaba en ejecucion.
)

:: Deshabilitar tarea programada (sin eliminarla)
schtasks /change /tn "CPE_DisateQ" /disable >nul 2>&1
echo  [OK] Tarea programada deshabilitada.
echo.
echo  CPE DisateQ detenido. Para reactivar ejecute INSTALAR.bat
echo.
pause
