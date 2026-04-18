@echo off
setlocal
title CPE DisateQ - Compilador
color 1F

echo.
echo  =======================================================
echo    CPE DisateQ (tm)  -  Compilador
echo    Desarrollado por @fhertejada  .  DisateQ
echo  =======================================================
echo.

cd /d %~dp0

:: ── Buscar Python ─────────────────────────────────────────
set PYTHON=
for %%p in (
    "%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "C:\Program Files\Python313\python.exe"
    "C:\Program Files\Python312\python.exe"
    "C:\Program Files\Python311\python.exe"
    "C:\Program Files\PyManager\python.exe"
) do (
    if exist %%p (
        set PYTHON=%%p
        goto :found
    )
)
python --version >nul 2>&1
if %errorlevel%==0 ( set PYTHON=python & goto :found )

echo  [ERROR] Python no encontrado. Instale Python 3.10 o superior.
echo  Descargue desde https://www.python.org/downloads/
pause & exit /b 1

:found
echo  [OK] Python: %PYTHON%
echo.

:: ── Instalar dependencias ─────────────────────────────────
echo  Instalando dependencias...
%PYTHON% -m pip install pyinstaller requests dbfread --quiet --upgrade
if %errorlevel% neq 0 (
    echo  [ERROR] Fallo al instalar dependencias.
    pause & exit /b 1
)
echo  [OK] Dependencias listas
echo.

:: ── Limpiar build anterior ────────────────────────────────
echo  Limpiando build anterior...
if exist dist\cpe_disateq.exe del /f /q dist\cpe_disateq.exe
if exist build rmdir /s /q build
if exist cpe_disateq.spec del /q cpe_disateq.spec

:: ── Compilar ──────────────────────────────────────────────
echo  Compilando...
%PYTHON% -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name cpe_disateq ^
    --icon src\cpe_disateq.ico ^
    --paths src ^
    --add-data "src;src" ^
    src\main.py

if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Fallo en la compilacion.
    pause & exit /b 1
)

if not exist "dist\cpe_disateq.exe" (
    echo  [ERROR] No se genero el ejecutable.
    pause & exit /b 1
)

echo.
echo  [OK] Ejecutable generado: dist\cpe_disateq.exe
echo.

:: ── Armar paquete de instalacion ──────────────────────────
echo  Armando paquete de instalacion para clientes...
set PKG_DIR=%~dp0dist\CPE_DisateQ_Instalador
if exist "%PKG_DIR%" rmdir /s /q "%PKG_DIR%"
mkdir "%PKG_DIR%"

copy /y "dist\cpe_disateq.exe"   "%PKG_DIR%\cpe_disateq.exe"   >nul
copy /y "INSTALAR.bat"           "%PKG_DIR%\INSTALAR.bat"       >nul
copy /y "DETENER.bat"            "%PKG_DIR%\DETENER.bat"         >nul
copy /y "DESINSTALAR.bat"        "%PKG_DIR%\DESINSTALAR.bat"     >nul
if exist "src\cpe_disateq.ico" copy /y "src\cpe_disateq.ico" "%PKG_DIR%\cpe_disateq.ico" >nul

:: Comprimir con PowerShell
powershell -NoProfile -Command ^
  "Compress-Archive -Path '%PKG_DIR%\*' -DestinationPath '%~dp0dist\CPE_DisateQ_Instalador.zip' -Force"

if exist "%~dp0dist\CPE_DisateQ_Instalador.zip" (
    echo  [OK] Paquete listo: dist\CPE_DisateQ_Instalador.zip
) else (
    echo  [AVISO] No se pudo crear el zip ^(PowerShell no disponible^)
    echo          Copie manualmente: dist\CPE_DisateQ_Instalador\
)

echo.
echo  =======================================================
echo   COMPILACION EXITOSA
echo  =======================================================
echo   Ejecutable : dist\cpe_disateq.exe
echo   Instalador : dist\CPE_DisateQ_Instalador.zip
echo  =======================================================
echo.
pause
