# setup_licencias_completo.ps1
# ================================
# Setup completo de licencias - Todo en uno
# Motor CPE DisateQ™ v3.0

$ErrorActionPreference = "Stop"

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "  Setup Completo Sistema de Licencias" -ForegroundColor Cyan
Write-Host "  Motor CPE DisateQ™ v3.0" -ForegroundColor Cyan
Write-Host "================================================================`n" -ForegroundColor Cyan

$DIR = "D:\DisateQ\Motor CPE"

if (-not (Test-Path $DIR)) {
    Write-Host "❌ Error: Directorio no encontrado: $DIR" -ForegroundColor Red
    exit 1
}

cd $DIR

Write-Host "📁 Directorio de trabajo: $DIR`n" -ForegroundColor Yellow

# PASO 1: Verificar archivos necesarios
Write-Host "📋 Verificando archivos necesarios..." -ForegroundColor Yellow

$archivos_requeridos = @(
    "validador_licencias.py",
    "main.py"
)

$faltantes = @()
foreach ($archivo in $archivos_requeridos) {
    if (-not (Test-Path $archivo)) {
        $faltantes += $archivo
    }
}

if ($faltantes.Count -gt 0) {
    Write-Host "❌ Archivos faltantes:" -ForegroundColor Red
    foreach ($archivo in $faltantes) {
        Write-Host "   - $archivo" -ForegroundColor Red
    }
    Write-Host "`nPor favor ejecute primero: .\instalar_sistema_licencias.ps1`n" -ForegroundColor Yellow
    exit 1
}

Write-Host "   ✅ Archivos OK`n" -ForegroundColor Green

# PASO 2: Generar claves RSA
Write-Host "🔐 PASO 1: Generando claves RSA DisateQ..." -ForegroundColor Yellow

if ((Test-Path "disateq_private.pem") -and (Test-Path "disateq_public.pem")) {
    Write-Host "   ⚠️  Las claves ya existen. ¿Regenerar? Esto invalidará todas las licencias existentes." -ForegroundColor Yellow
    $respuesta = Read-Host "   Continuar (s/n)"
    if ($respuesta -ne "s") {
        Write-Host "   ⏭️  Saltando generación de claves`n" -ForegroundColor Gray
    } else {
        Remove-Item "disateq_private.pem", "disateq_public.pem" -Force
        python -c "from validador_licencias import LicenseGenerator; from pathlib import Path; LicenseGenerator.generate_keypair(Path.cwd())"
        Write-Host "   ✅ Claves regeneradas`n" -ForegroundColor Green
    }
} else {
    python -c "from validador_licencias import LicenseGenerator; from pathlib import Path; LicenseGenerator.generate_keypair(Path.cwd())"
    Write-Host "   ✅ Claves generadas`n" -ForegroundColor Green
}

# PASO 3: Crear licencia de prueba
Write-Host "📝 PASO 2: Creando licencia de prueba..." -ForegroundColor Yellow

$codigo = @"
from validador_licencias import LicenseGenerator
from pathlib import Path

LicenseGenerator.create_license(
    client_name='DisateQ™ - Licencia de Prueba',
    client_ruc='20123456789',
    expiry_days=365,
    max_docs_month=999999,
    private_key_path=Path('disateq_private.pem'),
    output_path=Path('disateq_motor.lic')
)
"@

python -c $codigo

Write-Host "   ✅ Licencia creada`n" -ForegroundColor Green

# PASO 4: Validar licencia
Write-Host "✅ PASO 3: Validando licencia..." -ForegroundColor Yellow

python -c "from validador_licencias import LicenseValidator; v = LicenseValidator(); valida, msg, datos = v.validate(); print(f'\n{msg}\n' if valida else f'\n❌ {msg}\n')"

# PASO 5: Probar Motor
Write-Host "🚀 PASO 4: Probando Motor CPE con licencias..." -ForegroundColor Yellow

python main.py

# Resumen final
Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "✅ SETUP COMPLETADO" -ForegroundColor Green
Write-Host "================================================================`n" -ForegroundColor Cyan

Write-Host "📁 Archivos generados en: $DIR`n" -ForegroundColor White

Write-Host "Archivos clave:" -ForegroundColor Yellow
Write-Host "   ✅ disateq_private.pem (MANTENER SEGURA)" -ForegroundColor Green
Write-Host "   ✅ disateq_public.pem (distribuir)" -ForegroundColor Green
Write-Host "   ✅ disateq_motor.lic (licencia prueba)`n" -ForegroundColor Green

Write-Host "📝 Próximos pasos:" -ForegroundColor Yellow
Write-Host "   1. Crear licencias para clientes:" -ForegroundColor White
Write-Host "      python crear_licencia_cliente.py`n" -ForegroundColor Gray

Write-Host "   2. Integrar adaptadores y lógica de envío a SUNAT" -ForegroundColor White
Write-Host "      (próxima sesión)`n" -ForegroundColor Gray

Write-Host "================================================================`n" -ForegroundColor Cyan
