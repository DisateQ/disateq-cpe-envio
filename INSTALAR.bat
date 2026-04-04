@echo off
setlocal enabledelayedexpansion
title CPE DisateQ - Instalacion
color 1F

echo.
echo  ===================================================
echo    CPE DisateQ (tm)  -  Instalacion
echo    DisateQ  .  @fhertejada (tm)
echo  ===================================================
echo.

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo  Se necesitan permisos de Administrador.
    echo  Haga clic derecho ^> Ejecutar como administrador
    echo.
    pause & exit /b 1
)

if not exist "%~dp0cpe_disateq.exe" (
    echo  [ERROR] No se encontro cpe_disateq.exe en esta carpeta.
    pause & exit /b 1
)

set DIR=D:\FFEESUNAT\CPE DisateQ
set EXE=%DIR%\cpe_disateq.exe
set ICO=%DIR%\cpe_disateq.ico

:: Detener proceso si esta corriendo
echo  Deteniendo proceso anterior si existe...
taskkill /f /im cpe_disateq.exe >nul 2>&1
timeout /t 2 /nobreak >nul

:: Crear carpetas
if not exist "%DIR%"           mkdir "%DIR%"
if not exist "%DIR%\enviados"  mkdir "%DIR%\enviados"
if not exist "%DIR%\errores"   mkdir "%DIR%\errores"

:: Copiar ejecutable e icono
copy /y "%~dp0cpe_disateq.exe" "%EXE%" >nul
if exist "%~dp0cpe_disateq.ico" copy /y "%~dp0cpe_disateq.ico" "%ICO%" >nul

:: Tarea programada
schtasks /delete /tn "CPE_DisateQ" /f >nul 2>&1
schtasks /create /tn "CPE_DisateQ" /tr "\"%EXE%\" --once" /sc MINUTE /mo 5 /ru SYSTEM /rl HIGHEST /f >nul

:: Acceso directo en escritorio publico con icono personalizado
set SHORTCUT=%PUBLIC%\Desktop\CPE DisateQ.lnk
if exist "%ICO%" (
    powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell;$s=$ws.CreateShortcut('%SHORTCUT%');$s.TargetPath='%EXE%';$s.WorkingDirectory='%DIR%';$s.IconLocation='%ICO%';$s.Description='CPE DisateQ - Envio de Facturacion Electronica';$s.Save()" >nul 2>&1
) else (
    powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell;$s=$ws.CreateShortcut('%SHORTCUT%');$s.TargetPath='%EXE%';$s.WorkingDirectory='%DIR%';$s.Description='CPE DisateQ - Envio de Facturacion Electronica';$s.Save()" >nul 2>&1
)

echo  [OK] Instalacion completada en: %DIR%
echo.
echo  Abriendo CPE DisateQ...
timeout /t 1 /nobreak >nul
start "" "%EXE%"
