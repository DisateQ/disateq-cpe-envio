@echo off
title CPE DisateQ - Reiniciar
color 1F

echo.
echo  ===================================================
echo    CPE DisateQ (tm)  -  Reiniciar servicio
echo  ===================================================
echo.

set DIR=D:\FFEESUNAT\CPE DisateQ
set EXE=%DIR%\cpe_disateq.exe

if not exist "%EXE%" (
    echo  [ERROR] No se encontro el ejecutable en %EXE%
    echo  Ejecute INSTALAR.bat primero.
    pause & exit /b 1
)

:: Detener si esta corriendo
taskkill /f /im cpe_disateq.exe >nul 2>&1
timeout /t 2 /nobreak >nul

:: Reactivar tarea programada
schtasks /change /tn "CPE_DisateQ" /enable >nul 2>&1
echo  [OK] Tarea programada reactivada.

:: Abrir aplicacion
start "" "%EXE%"
echo  [OK] CPE DisateQ iniciado.
echo.
timeout /t 2 /nobreak >nul
