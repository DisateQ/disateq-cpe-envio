# compilar_generador.ps1
# =======================
# Compila generador_licencias.py a .exe
#
# Uso: .\compilar_generador.ps1
#
# Autor: Fernando Miguel Tejada Quevedo
# Empresa: DisateQ™
# Fecha: Abril 2026

#Requires -Version 5.1

$ErrorActionPreference = "Stop"

# Colores
function Write-Header {
    param($Text)
    Write-Host ""
    Write-Host "=" -NoNewline -ForegroundColor Cyan
    Write-Host ("=" * 68) -ForegroundColor Cyan
    Write-Host " $Text" -ForegroundColor White
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host ""
}

function Write-Success {
    param($Text)
    Write-Host "✓ " -NoNewline -ForegroundColor Green
    Write-Host $Text -ForegroundColor White
}

function Write-Info {
    param($Text)
    Write-Host "ℹ " -NoNewline -ForegroundColor Cyan
    Write-Host $Text -ForegroundColor Gray
}

# Banner
Clear-Host
Write-Header "COMPILADOR — Generador de Licencias DisateQ™"

# Verificar archivos necesarios
Write-Host "Verificando archivos..." -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path "generador_licencias.py")) {
    Write-Host "✗ generador_licencias.py no encontrado" -ForegroundColor Red
    exit 1
}
Write-Success "generador_licencias.py encontrado"

# Verificar Python
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python: $pythonVersion"
} catch {
    Write-Host "✗ Python no encontrado" -ForegroundColor Red
    exit 1
}

# Verificar/Instalar dependencias
Write-Host ""
Write-Host "Verificando dependencias..." -ForegroundColor Cyan
Write-Host ""

# cryptography
$cryptoInstalled = python -c "import cryptography" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Info "Instalando cryptography..."
    pip install cryptography --quiet
    Write-Success "cryptography instalado"
} else {
    Write-Success "cryptography OK"
}

# PyInstaller
$pyinstallerInstalled = python -c "import PyInstaller" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Info "Instalando PyInstaller..."
    pip install pyinstaller --quiet
    Write-Success "PyInstaller instalado"
} else {
    Write-Success "PyInstaller OK"
}

Write-Host ""

# Limpiar builds anteriores
Write-Header "Limpieza"

if (Test-Path "dist") {
    Remove-Item -Path "dist" -Recurse -Force
    Write-Success "dist/ eliminado"
}
if (Test-Path "build") {
    Remove-Item -Path "build" -Recurse -Force
    Write-Success "build/ eliminado"
}

Write-Host ""

# Compilar
Write-Header "Compilación"

Write-Host "Compilando generador_licencias.py..." -ForegroundColor Cyan
Write-Host "(Esto puede tomar 1-2 minutos...)" -ForegroundColor Gray
Write-Host ""

$pyinstallerArgs = @(
    "--name=Generador_Licencias_DisateQ",
    "--onefile",
    "--windowed",
    "--icon=NONE",
    "--clean",
    "--noconfirm",
    "generador_licencias.py"
)

$output = pyinstaller $pyinstallerArgs 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Success "Compilación exitosa"
} else {
    Write-Host "✗ Error en compilación" -ForegroundColor Red
    Write-Host $output -ForegroundColor Red
    exit 1
}

Write-Host ""

# Verificar ejecutable
Write-Header "Verificación"

$exePath = "dist\Generador_Licencias_DisateQ.exe"
if (Test-Path $exePath) {
    $exeSize = [math]::Round((Get-Item $exePath).Length / 1MB, 2)
    Write-Success "Ejecutable generado"
    Write-Info "Tamaño: $exeSize MB"
    Write-Info "Ubicación: $exePath"
} else {
    Write-Host "✗ Ejecutable no encontrado" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Crear package para técnicos
Write-Header "Empaquetado"

$packageDir = "Package_Generador_Licencias"
if (Test-Path $packageDir) {
    Remove-Item -Path $packageDir -Recurse -Force
}
New-Item -Path $packageDir -ItemType Directory | Out-Null

# Copiar ejecutable
Copy-Item -Path $exePath -Destination $packageDir
Write-Success "Ejecutable copiado"

# Copiar clave privada (si existe)
if (Test-Path "firma_disateq.key") {
    Copy-Item -Path "firma_disateq.key" -Destination $packageDir
    Write-Success "firma_disateq.key copiado"
} else {
    Write-Host "⚠ " -NoNewline -ForegroundColor Yellow
    Write-Host "firma_disateq.key no encontrado (generar con generar_claves_rsa.ps1)" -ForegroundColor Yellow
}

# Crear README
$readmeContent = @"
GENERADOR DE LICENCIAS DisateQ™
================================

CONTENIDO:
- Generador_Licencias_DisateQ.exe
- firma_disateq.key (clave privada - CONFIDENCIAL)

USO:
1. Doble click en Generador_Licencias_DisateQ.exe
2. Ingresar password del técnico
3. Click en "Cargar Clave Privada"
4. Completar datos del cliente
5. Click en "Generar Licencia"
6. Guardar archivo licencia_XXXXXXXXXX.lic
7. Copiar a: C:\DisateQ\Motor CPE\licencia.lic

IMPORTANTE:
- Proteger firma_disateq.key
- No compartir password
- Registrar licencias generadas

SOPORTE:
soporte@disateq.com

---
DisateQ™ — Sistema de Licencias v3.0
Compilado: $(Get-Date -Format 'yyyy-MM-dd HH:mm')
"@

$readmeContent | Out-File -FilePath "$packageDir\README.txt" -Encoding UTF8
Write-Success "README.txt creado"

Write-Host ""

# Crear ZIP
Write-Host "Comprimiendo package..." -ForegroundColor Cyan
$zipPath = "Package_Generador_Licencias.zip"
if (Test-Path $zipPath) {
    Remove-Item -Path $zipPath -Force
}

Compress-Archive -Path "$packageDir\*" -DestinationPath $zipPath -CompressionLevel Optimal
$zipSize = [math]::Round((Get-Item $zipPath).Length / 1MB, 2)
Write-Success "ZIP creado: $zipPath ($zipSize MB)"

Write-Host ""

# Resumen
Write-Header "✅ COMPILACIÓN COMPLETADA"

Write-Host "ARCHIVOS GENERADOS:" -ForegroundColor White
Write-Host ""
Write-Host "  📂 Carpeta:" -ForegroundColor Cyan
Write-Host "     $packageDir\" -ForegroundColor Gray
Write-Host ""
Write-Host "  📦 ZIP:" -ForegroundColor Cyan
Write-Host "     $zipPath" -ForegroundColor Gray
Write-Host "     Tamaño: $zipSize MB" -ForegroundColor Gray
Write-Host ""
Write-Host "DISTRIBUCIÓN:" -ForegroundColor White
Write-Host ""
Write-Host "  1. Copiar $zipPath a USB de técnicos" -ForegroundColor Yellow
Write-Host "  2. Técnico extrae ZIP" -ForegroundColor Yellow
Write-Host "  3. Ejecuta Generador_Licencias_DisateQ.exe" -ForegroundColor Yellow
Write-Host ""
Write-Host "SEGURIDAD:" -ForegroundColor White
Write-Host ""
Write-Host "  ⚠️  firma_disateq.key es CONFIDENCIAL" -ForegroundColor Red
Write-Host "     - Solo para técnicos autorizados" -ForegroundColor Gray
Write-Host "     - Protegido con password" -ForegroundColor Gray
Write-Host "     - No compartir públicamente" -ForegroundColor Gray
Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

# Abrir carpeta
Write-Host "¿Abrir carpeta del package? (S/N): " -NoNewline -ForegroundColor Cyan
$response = Read-Host
if ($response -eq "S" -or $response -eq "s") {
    explorer $packageDir
}

Write-Host ""
Write-Host "✓ Proceso completado" -ForegroundColor Green
Write-Host ""
