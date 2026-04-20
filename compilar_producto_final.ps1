# compilar_producto_final.ps1
# ==============================
# Compila Motor CPE v3.0 a ejecutable Windows
# Genera instalador completo para clientes
# 
# Autor: Fernando Hernán Tejada (@fhertejada™)

$ErrorActionPreference = "Stop"

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "  Compilador Producto Final" -ForegroundColor Cyan
Write-Host "  Motor CPE DisateQ™ v3.0" -ForegroundColor Cyan
Write-Host "================================================================`n" -ForegroundColor Cyan

$BASE = "D:\DATA\_DEV_\repos\disateq-cpe-envio"
$DIST = "$BASE\dist"
$VERSION = "3.0.0"
$BUILD_DATE = Get-Date -Format "yyyy-MM-dd"

cd $BASE

Write-Host "📋 Verificando requisitos...`n" -ForegroundColor Yellow

# Verificar PyInstaller
$pyinstaller = python -m pip show pyinstaller 2>$null

if (-not $pyinstaller) {
    Write-Host "⚠️  PyInstaller no encontrado. Instalando..." -ForegroundColor Yellow
    pip install pyinstaller
    Write-Host "   ✅ PyInstaller instalado`n" -ForegroundColor Green
} else {
    Write-Host "   ✅ PyInstaller disponible`n" -ForegroundColor Green
}

# Limpiar builds anteriores
Write-Host "🧹 Limpiando builds anteriores..." -ForegroundColor Yellow

if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
if (Test-Path "dist\windows\MotorCPE_v$VERSION.exe") { 
    Remove-Item "dist\windows\MotorCPE_v$VERSION.exe" -Force 
}

Write-Host "   ✅ Limpieza completada`n" -ForegroundColor Green

# Compilar con PyInstaller
Write-Host "⚙️  Compilando Motor CPE a ejecutable Windows...`n" -ForegroundColor Yellow

$spec_content = @"
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'cryptography',
        'cryptography.hazmat.primitives',
        'cryptography.hazmat.backends',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MotorCPE_DisateQ_v$VERSION',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
"@

Set-Content -Path "motor_cpe.spec" -Value $spec_content

# Ejecutar PyInstaller
pyinstaller motor_cpe.spec --clean

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Error en compilación" -ForegroundColor Red
    exit 1
}

Write-Host "`n   ✅ Compilación exitosa`n" -ForegroundColor Green

# Mover ejecutable a dist/windows/
Write-Host "📦 Organizando archivos de distribución..." -ForegroundColor Yellow

if (-not (Test-Path "$DIST\windows")) {
    New-Item -ItemType Directory -Path "$DIST\windows" -Force | Out-Null
}

Move-Item "dist\MotorCPE_DisateQ_v$VERSION.exe" "$DIST\windows\" -Force
Write-Host "   ✅ Ejecutable movido a dist/windows/`n" -ForegroundColor Green

# Crear paquete instalador completo
Write-Host "📦 Creando paquete instalador para cliente...`n" -ForegroundColor Yellow

$INSTALLER_DIR = "$DIST\installers\MotorCPE_v$VERSION`_$BUILD_DATE"

if (Test-Path $INSTALLER_DIR) {
    Remove-Item $INSTALLER_DIR -Recurse -Force
}

New-Item -ItemType Directory -Path $INSTALLER_DIR -Force | Out-Null

# Copiar ejecutable
Copy-Item "$DIST\windows\MotorCPE_DisateQ_v$VERSION.exe" $INSTALLER_DIR -Force
Write-Host "   ✅ Ejecutable copiado" -ForegroundColor Green

# Copiar clave pública (NO la privada)
Copy-Item "licenses\keys\disateq_public.pem" $INSTALLER_DIR -Force
Write-Host "   ✅ Clave pública incluida" -ForegroundColor Green

# Crear estructura de carpetas vacías
$carpetas_cliente = @("config", "logs", "output", "backup")
foreach ($carpeta in $carpetas_cliente) {
    New-Item -ItemType Directory -Path "$INSTALLER_DIR\$carpeta" -Force | Out-Null
}
Write-Host "   ✅ Carpetas de trabajo creadas" -ForegroundColor Green

# Copiar configuración de ejemplo
Copy-Item "config\motor_config.yaml" "$INSTALLER_DIR\config\motor_config.ejemplo.yaml" -Force
Write-Host "   ✅ Configuración de ejemplo incluida" -ForegroundColor Green

# Crear README para cliente
$readme_cliente = @"
# Motor CPE DisateQ™ v$VERSION

**Instalación del Cliente**

## 📦 Contenido del Paquete

- MotorCPE_DisateQ_v$VERSION.exe  ← Ejecutable principal
- disateq_public.pem              ← Clave pública (requerida)
- config/                         ← Configuración
- logs/                           ← Logs automáticos
- output/                         ← Archivos generados
- backup/                         ← Backups
- INSTALAR.bat                    ← Script de instalación automática

## 🚀 Instalación Automática (Recomendado)

1. **Ejecutar como Administrador**: INSTALAR.bat

   Esto instalará:
   - PROGRAMAS en: C:\Program Files\DisateQ\Motor CPE\
   - DATOS en: D:\FFEESUNAT\CPE DisateQ\

## 🔧 Instalación Manual (Alternativa)

1. **Crear carpetas**:
   ```
   C:\Program Files\DisateQ\Motor CPE\     ← Ejecutable + clave pública
   D:\FFEESUNAT\CPE DisateQ\               ← Configuración + datos
   ```

2. **Copiar archivos**:
   - MotorCPE_DisateQ_v$VERSION.exe → C:\Program Files\DisateQ\Motor CPE\
   - disateq_public.pem → C:\Program Files\DisateQ\Motor CPE\
   - Carpetas config/, logs/, output/, backup/ → D:\FFEESUNAT\CPE DisateQ\

## 🔐 Activación de Licencia

3. **Solicitar licencia** a DisateQ™:
   - Email: soporte@disateq.com
   - WhatsApp: +51 999 999 999
   - Proporcionar: Nombre empresa + RUC

4. **Colocar licencia** recibida (disateq_motor.lic):
   ```
   C:\Program Files\DisateQ\Motor CPE\disateq_motor.lic
   ```

## ⚙️ Configuración

5. **Editar configuración**:
   ```
   D:\FFEESUNAT\CPE DisateQ\config\motor_config.yaml
   ```

   Configurar según su sistema origen (Excel, DBF, SQL)

## ▶️ Ejecución

**Desde línea de comandos**:
```cmd
cd "C:\Program Files\DisateQ\Motor CPE"
MotorCPE_DisateQ_v$VERSION.exe
```

**Crear acceso directo** (opcional):
- Botón derecho en MotorCPE_DisateQ_v$VERSION.exe
- Enviar a → Escritorio (crear acceso directo)

## 📁 Estructura de Carpetas

```
C:\Program Files\DisateQ\Motor CPE\
├── MotorCPE_DisateQ_v$VERSION.exe    ← Programa
├── disateq_public.pem                ← Clave pública
└── disateq_motor.lic                 ← Licencia (después de activar)

D:\FFEESUNAT\CPE DisateQ\
├── config\
│   └── motor_config.yaml             ← Configuración
├── logs\                             ← Logs automáticos
├── output\                           ← TXT/XML/JSON generados
└── backup\                           ← Backups automáticos
```

## 📞 Soporte Técnico

**DisateQ™**
- Email: soporte@disateq.com
- WhatsApp: +51 999 999 999
- Web: www.disateq.com

---

© 2026 DisateQ™ | Motor CPE v$VERSION
Build: $BUILD_DATE
"@

Set-Content -Path "$INSTALLER_DIR\README.txt" -Value $readme_cliente -Encoding UTF8
Write-Host "   ✅ README para cliente creado" -ForegroundColor Green

# Crear script de instalación automática
$install_script = @"
@echo off
echo ================================================================
echo   Motor CPE DisateQ v$VERSION - Instalador
echo ================================================================
echo.

REM Rutas de instalacion
set PROGRAM_DIR=C:\Program Files\DisateQ\Motor CPE
set DATA_DIR=D:\FFEESUNAT\CPE DisateQ

echo Instalando Motor CPE...
echo   Programas: %PROGRAM_DIR%
echo   Datos:     %DATA_DIR%
echo.

REM Crear carpeta de programas
if not exist "%PROGRAM_DIR%" (
    mkdir "%PROGRAM_DIR%"
)

REM Crear carpeta de datos
if not exist "%DATA_DIR%" (
    mkdir "%DATA_DIR%"
)

echo Copiando archivos de programa...
copy /Y "MotorCPE_DisateQ_v$VERSION.exe" "%PROGRAM_DIR%\"
copy /Y "disateq_public.pem" "%PROGRAM_DIR%\"

echo Copiando archivos de datos...
xcopy /E /I /Y config "%DATA_DIR%\config\"
xcopy /E /I /Y logs "%DATA_DIR%\logs\"
xcopy /E /I /Y output "%DATA_DIR%\output\"
xcopy /E /I /Y backup "%DATA_DIR%\backup\"

copy /Y "README.txt" "%DATA_DIR%\"

echo.
echo ================================================================
echo   Instalacion Completada
echo ================================================================
echo.
echo PROGRAMAS instalados en: %PROGRAM_DIR%
echo DATOS instalados en:     %DATA_DIR%
echo.
echo Proximos pasos:
echo   1. Solicitar licencia a DisateQ (soporte@disateq.com)
echo   2. Colocar disateq_motor.lic en: %PROGRAM_DIR%
echo   3. Configurar %DATA_DIR%\config\motor_config.yaml
echo   4. Crear acceso directo al escritorio (opcional)
echo.
echo Para ejecutar:
echo   "%PROGRAM_DIR%\MotorCPE_DisateQ_v$VERSION.exe"
echo.
pause
"@

Set-Content -Path "$INSTALLER_DIR\INSTALAR.bat" -Value $install_script
Write-Host "   ✅ Script de instalación creado`n" -ForegroundColor Green

# Comprimir todo en ZIP
Write-Host "📦 Comprimiendo instalador..." -ForegroundColor Yellow

$ZIP_FILE = "$DIST\installers\MotorCPE_v$VERSION`_Instalador_$BUILD_DATE.zip"

if (Test-Path $ZIP_FILE) {
    Remove-Item $ZIP_FILE -Force
}

Compress-Archive -Path "$INSTALLER_DIR\*" -DestinationPath $ZIP_FILE

Write-Host "   ✅ Instalador comprimido`n" -ForegroundColor Green

# Limpiar archivos temporales
Remove-Item "motor_cpe.spec" -Force -ErrorAction SilentlyContinue
Remove-Item "build" -Recurse -Force -ErrorAction SilentlyContinue

# Resumen
$exe_size = (Get-Item "$DIST\windows\MotorCPE_DisateQ_v$VERSION.exe").Length / 1MB
$zip_size = (Get-Item $ZIP_FILE).Length / 1MB

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "✅ PRODUCTO FINAL GENERADO" -ForegroundColor Green
Write-Host "================================================================`n" -ForegroundColor Cyan

Write-Host "📦 Ejecutable Windows:" -ForegroundColor White
Write-Host "   $DIST\windows\MotorCPE_DisateQ_v$VERSION.exe" -ForegroundColor Gray
Write-Host "   Tamaño: $([math]::Round($exe_size, 2)) MB`n" -ForegroundColor Gray

Write-Host "📦 Instalador Completo (ZIP):" -ForegroundColor White
Write-Host "   $ZIP_FILE" -ForegroundColor Gray
Write-Host "   Tamaño: $([math]::Round($zip_size, 2)) MB`n" -ForegroundColor Gray

Write-Host "📋 Contenido del instalador:" -ForegroundColor Yellow
Write-Host "   - Ejecutable Motor CPE v$VERSION" -ForegroundColor White
Write-Host "   - Clave pública DisateQ" -ForegroundColor White
Write-Host "   - Configuración de ejemplo" -ForegroundColor White
Write-Host "   - README para cliente" -ForegroundColor White
Write-Host "   - Script de instalación (INSTALAR.bat)" -ForegroundColor White
Write-Host "   - Carpetas de trabajo (config, logs, output, backup)`n" -ForegroundColor White

Write-Host "📤 Para distribuir a clientes:" -ForegroundColor Yellow
Write-Host "   1. Enviar: $ZIP_FILE" -ForegroundColor White
Write-Host "   2. Cliente ejecuta: INSTALAR.bat" -ForegroundColor White
Write-Host "   3. DisateQ genera licencia: crear_licencia_cliente.py" -ForegroundColor White
Write-Host "   4. Enviar disateq_motor.lic al cliente`n" -ForegroundColor White

Write-Host "================================================================`n" -ForegroundColor Cyan
