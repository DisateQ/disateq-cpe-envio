@echo off
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

:: Crear carpetas
if not exist "%DIR%"           mkdir "%DIR%"
if not exist "%DIR%\enviados"  mkdir "%DIR%\enviados"
if not exist "%DIR%\errores"   mkdir "%DIR%\errores"

:: Copiar ejecutable
copy /y "%~dp0cpe_disateq.exe" "%DIR%\cpe_disateq.exe" >nul

:: Tarea programada cada 5 minutos
schtasks /delete /tn "CPE_DisateQ" /f >nul 2>&1
schtasks /create /tn "CPE_DisateQ" /tr "\"%DIR%\cpe_disateq.exe\" --once" /sc MINUTE /mo 5 /ru SYSTEM /rl HIGHEST /f >nul

:: Acceso directo en escritorio publico
powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell;$s=$ws.CreateShortcut('%PUBLIC%\Desktop\CPE DisateQ.lnk');$s.TargetPath='%DIR%\cpe_disateq.exe';$s.WorkingDirectory='%DIR%';$s.Description='CPE DisateQ';$s.Save()" >nul 2>&1

echo  [OK] Instalacion completada en: %DIR%
echo.
echo  Abriendo CPE DisateQ para configurar...
echo.
timeout /t 2 /nobreak >nul
start "" "%DIR%\cpe_disateq.exe"
