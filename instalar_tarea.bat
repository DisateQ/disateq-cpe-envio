@echo off
title Instalando Tarea Programada FFEE Farmacia...
echo ============================================
echo   FFEE Farmacia - Instalador Tarea Programada
echo   Desarrollado por @fhertejada - DisateQ
echo ============================================
echo.

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Este script debe ejecutarse como Administrador.
    echo Haga clic derecho y seleccione "Ejecutar como administrador".
    pause
    exit /b 1
)

set INSTALL_DIR=D:\FFEESUNAT\CPE DisateQ
set EXE_PATH=%INSTALL_DIR%\cpe_disateq.exe

if not exist "%EXE_PATH%" (
    echo [ERROR] No se encontro el ejecutable en:
    echo         %EXE_PATH%
    echo.
    echo Compile primero con compilar.bat o copie el exe a esa carpeta.
    pause
    exit /b 1
)

schtasks /delete /tn "CPE_DisateQ" /f >nul 2>&1

schtasks /create ^
    /tn "CPE_DisateQ" ^
    /tr "\"%EXE_PATH%\" --once" ^
    /sc MINUTE ^
    /mo 5 ^
    /ru SYSTEM ^
    /f

if %errorlevel% neq 0 (
    echo [ERROR] No se pudo crear la tarea programada.
    pause
    exit /b 1
)

echo.
echo ============================================
echo [OK] Tarea programada instalada:
echo      Nombre:     CPE_DisateQ
echo      Ejecucion:  cada 5 minutos
echo      Ejecutable: %EXE_PATH%
echo ============================================
echo.
pause
