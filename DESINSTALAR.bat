@echo off
title CPE DisateQ - Desinstalacion
color 4F

echo.
echo  ===================================================
echo    CPE DisateQ (tm)  -  Desinstalacion
echo  ===================================================
echo.

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo  Se necesitan permisos de Administrador.
    echo  Haga clic derecho ^> Ejecutar como administrador
    pause & exit /b 1
)

set /p CONFIRMAR= Confirma la desinstalacion? (S/N): 
if /i not "%CONFIRMAR%"=="S" (
    echo  Operacion cancelada.
    pause & exit /b 0
)

:: Detener proceso
echo  Deteniendo proceso...
taskkill /f /im cpe_disateq.exe >nul 2>&1
timeout /t 2 /nobreak >nul

:: Eliminar tarea programada
schtasks /delete /tn "CPE_DisateQ" /f >nul 2>&1
echo  [OK] Tarea programada eliminada.

:: Eliminar acceso directo del escritorio
set SHORTCUT=%PUBLIC%\Desktop\CPE DisateQ.lnk
if exist "%SHORTCUT%" del /f /q "%SHORTCUT%"
echo  [OK] Acceso directo eliminado.

:: Preguntar si eliminar datos
set /p DATOS= Eliminar carpeta de datos D:\FFEESUNAT\CPE DisateQ? (S/N): 
if /i "%DATOS%"=="S" (
    rmdir /s /q "D:\FFEESUNAT\CPE DisateQ" >nul 2>&1
    echo  [OK] Carpeta de datos eliminada.
) else (
    echo  [INFO] Carpeta de datos conservada en D:\FFEESUNAT\CPE DisateQ
)

echo.
echo  [OK] Desinstalacion completada.
echo.
pause
