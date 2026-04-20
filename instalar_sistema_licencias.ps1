# instalar_sistema_licencias.ps1
# ================================
# Instala sistema de licencias RSA en Motor CPE DisateQ v3.0
# 
# Autor: Fernando Hernán Tejada (@fhertejada™)

$ErrorActionPreference = "Stop"

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "  Instalación Sistema de Licencias RSA" -ForegroundColor Cyan
Write-Host "  Motor CPE DisateQ™ v3.0" -ForegroundColor Cyan
Write-Host "================================================================`n" -ForegroundColor Cyan

# Rutas
$REPO = "D:\DATA\_DEV_\repos\disateq-cpe-envio"
$MOTOR = "D:\DisateQ\Motor CPE"

Write-Host "📁 Verificando directorios..." -ForegroundColor Yellow

if (-not (Test-Path $REPO)) {
    Write-Host "❌ Error: Repositorio no encontrado: $REPO" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $MOTOR)) {
    Write-Host "❌ Error: Motor CPE no encontrado: $MOTOR" -ForegroundColor Red
    exit 1
}

Write-Host "   ✅ Repositorio: $REPO" -ForegroundColor Green
Write-Host "   ✅ Motor CPE: $MOTOR`n" -ForegroundColor Green

# 1. Instalar dependencias
Write-Host "📦 Instalando dependencia: cryptography..." -ForegroundColor Yellow

pip install cryptography==42.0.5

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error instalando cryptography" -ForegroundColor Red
    exit 1
}

Write-Host "   ✅ cryptography instalado correctamente`n" -ForegroundColor Green

# 2. Copiar archivos al Motor
Write-Host "📋 Copiando archivos al Motor CPE..." -ForegroundColor Yellow

$archivos = @(
    "validador_licencias.py",
    "main.py",
    "generar_claves_disateq.py",
    "crear_licencia_cliente.py",
    "test_licencias.py",
    "README_LICENCIAS.md"
)

foreach ($archivo in $archivos) {
    $origen = Join-Path $REPO $archivo
    $destino = Join-Path $MOTOR $archivo
    
    if (Test-Path $origen) {
        Copy-Item $origen $destino -Force
        Write-Host "   ✅ $archivo" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  No encontrado: $archivo (continuando...)" -ForegroundColor Yellow
    }
}

Write-Host ""

# 3. Actualizar requirements.txt
Write-Host "📝 Actualizando requirements.txt..." -ForegroundColor Yellow

$reqFile = Join-Path $MOTOR "requirements.txt"

# Copiar requirements.txt del repo si no existe en Motor
if (-not (Test-Path $reqFile)) {
    $reqOrigen = Join-Path $REPO "requirements.txt"
    if (Test-Path $reqOrigen) {
        Copy-Item $reqOrigen $reqFile -Force
        Write-Host "   ✅ requirements.txt copiado desde repositorio" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Creando requirements.txt nuevo" -ForegroundColor Yellow
        Set-Content $reqFile "# Motor CPE DisateQ™ v3.0 — Dependencias`n"
    }
}

$reqContent = Get-Content $reqFile -Raw

if ($reqContent -notmatch "cryptography") {
    Add-Content $reqFile "`n# Sistema de licencias offline`ncryptography==42.0.5    # RSA-2048 para validación de licencias"
    Write-Host "   ✅ cryptography agregado a requirements.txt`n" -ForegroundColor Green
} else {
    Write-Host "   ✅ cryptography ya está en requirements.txt`n" -ForegroundColor Green
}

# 4. Ejecutar tests
Write-Host "🧪 Ejecutando tests del sistema de licencias..." -ForegroundColor Yellow

Push-Location $MOTOR

python test_licencias.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n   ✅ Tests pasaron correctamente`n" -ForegroundColor Green
} else {
    Write-Host "`n   ❌ Tests fallaron`n" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location

# 5. Resumen
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "✅ INSTALACIÓN COMPLETADA" -ForegroundColor Green
Write-Host "================================================================`n" -ForegroundColor Cyan

Write-Host "📁 Archivos instalados en: $MOTOR`n" -ForegroundColor White

Write-Host "📝 Próximos pasos:`n" -ForegroundColor Yellow
Write-Host "   1. Generar claves RSA DisateQ (una sola vez):" -ForegroundColor White
Write-Host "      cd `"$MOTOR`"" -ForegroundColor Gray
Write-Host "      python generar_claves_disateq.py`n" -ForegroundColor Gray

Write-Host "   2. Crear licencia de prueba:" -ForegroundColor White
Write-Host "      python crear_licencia_cliente.py`n" -ForegroundColor Gray

Write-Host "   3. Probar Motor con licencias:" -ForegroundColor White
Write-Host "      python main.py`n" -ForegroundColor Gray

Write-Host "   4. Compilar a .exe (cuando esté listo):" -ForegroundColor White
Write-Host "      pip install pyinstaller" -ForegroundColor Gray
Write-Host "      pyinstaller --onefile --name MotorCPE_v3.0 main.py`n" -ForegroundColor Gray

Write-Host "================================================================`n" -ForegroundColor Cyan
