# generar_claves_rsa.ps1
# ======================
# Genera par de claves RSA para sistema de licencias DisateQ™
#
# Uso: .\generar_claves_rsa.ps1
#
# Genera:
#   - firma_disateq.key (privada - para técnicos)
#   - firma_disateq.pub (pública - para Motor CPE)
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
Write-Header "GENERADOR DE CLAVES RSA — Sistema Licencias DisateQ™"

# Verificar Python
Write-Host "Verificando requisitos..." -ForegroundColor Cyan
Write-Host ""

try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python encontrado: $pythonVersion"
} catch {
    Write-Host "✗ Python no encontrado" -ForegroundColor Red
    Write-Host ""
    Write-Host "Instala Python 3.10+ desde https://python.org" -ForegroundColor Yellow
    exit 1
}

# Instalar cryptography si no existe
Write-Host ""
Write-Host "Verificando biblioteca cryptography..." -ForegroundColor Cyan
$cryptoInstalled = python -c "import cryptography" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "   Instalando cryptography..." -ForegroundColor Yellow
    pip install cryptography --quiet
    Write-Success "cryptography instalado"
} else {
    Write-Success "cryptography encontrado"
}

Write-Host ""
Write-Header "Generación de Claves"

# Crear script Python temporal
$pythonScript = @"
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import getpass
import os

print('Generando par de claves RSA 2048 bits...')
print()

# Generar clave privada
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)

print('✓ Clave privada generada')

# Generar clave pública
public_key = private_key.public_key()
print('✓ Clave pública generada')
print()

# Solicitar password para encriptar clave privada
print('═' * 70)
print(' IMPORTANTE: Password para proteger clave privada')
print('═' * 70)
print()
print('Este password lo usarán los técnicos en el generador de licencias.')
print('Debe ser seguro pero fácil de compartir con técnicos autorizados.')
print()

password = getpass.getpass('Ingrese password: ')
password_confirm = getpass.getpass('Confirme password: ')

if password != password_confirm:
    print()
    print('✗ Los passwords no coinciden')
    exit(1)

if len(password) < 8:
    print()
    print('✗ Password debe tener al menos 8 caracteres')
    exit(1)

print()
print('✓ Password configurado')
print()

# Serializar clave privada (encriptada)
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.BestAvailableEncryption(password.encode())
)

# Serializar clave pública
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# Guardar archivos
with open('firma_disateq.key', 'wb') as f:
    f.write(private_pem)

with open('firma_disateq.pub', 'wb') as f:
    f.write(public_pem)

print('Archivos guardados:')
print()
print('  ✓ firma_disateq.key  (Clave privada - CONFIDENCIAL)')
print('  ✓ firma_disateq.pub  (Clave pública - Incluir en Motor CPE)')
print()

# Mostrar contenido
print('═' * 70)
print(' CLAVE PÚBLICA (Incluir en Motor CPE):')
print('═' * 70)
print()
print(public_pem.decode())

print('═' * 70)
print(' CLAVE PRIVADA (Solo para técnicos - PROTEGIDA):')
print('═' * 70)
print()
print(private_pem.decode()[:200] + '...')
print()
print('(Contenido completo en: firma_disateq.key)')
print()
"@

# Ejecutar script Python
$pythonScript | python -

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Header "✅ CLAVES GENERADAS EXITOSAMENTE"
    
    Write-Host "ARCHIVOS CREADOS:" -ForegroundColor White
    Write-Host ""
    
    if (Test-Path "firma_disateq.key") {
        $keySize = [math]::Round((Get-Item "firma_disateq.key").Length / 1KB, 2)
        Write-Host "  🔐 firma_disateq.key" -ForegroundColor Red
        Write-Host "     Tamaño: $keySize KB" -ForegroundColor Gray
        Write-Host "     Uso: Técnicos (generador de licencias)" -ForegroundColor Gray
        Write-Host "     CONFIDENCIAL - Proteger con password" -ForegroundColor Red
    }
    
    Write-Host ""
    
    if (Test-Path "firma_disateq.pub") {
        $pubSize = [math]::Round((Get-Item "firma_disateq.pub").Length / 1KB, 2)
        Write-Host "  🔓 firma_disateq.pub" -ForegroundColor Green
        Write-Host "     Tamaño: $pubSize KB" -ForegroundColor Gray
        Write-Host "     Uso: Motor CPE (validación)" -ForegroundColor Gray
        Write-Host "     Público - Incluir en compilación" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "PRÓXIMOS PASOS:" -ForegroundColor White
    Write-Host ""
    Write-Host "  1. Copiar firma_disateq.key a USB de técnicos" -ForegroundColor Yellow
    Write-Host "  2. Guardar backup seguro de firma_disateq.key" -ForegroundColor Yellow
    Write-Host "  3. Incluir firma_disateq.pub en Motor CPE" -ForegroundColor Yellow
    Write-Host "  4. Compartir password con técnicos autorizados" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "SEGURIDAD:" -ForegroundColor White
    Write-Host ""
    Write-Host "  ⚠️  SI PIERDES firma_disateq.key:" -ForegroundColor Red
    Write-Host "     - No podrás generar más licencias" -ForegroundColor Gray
    Write-Host "     - Licencias existentes seguirán funcionando" -ForegroundColor Gray
    Write-Host "     - Deberás regenerar claves" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  ⚠️  SI SE FILTRA firma_disateq.key:" -ForegroundColor Red
    Write-Host "     - Cualquiera con el password puede generar licencias" -ForegroundColor Gray
    Write-Host "     - Deberás regenerar claves inmediatamente" -ForegroundColor Gray
    Write-Host "     - Actualizar Motor CPE en todos los clientes" -ForegroundColor Gray
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host ""
    
    # Crear backup
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupDir = "backup_claves_$timestamp"
    
    Write-Host "¿Crear backup automático de las claves? (S/N): " -NoNewline -ForegroundColor Cyan
    $createBackup = Read-Host
    
    if ($createBackup -eq "S" -or $createBackup -eq "s") {
        New-Item -Path $backupDir -ItemType Directory | Out-Null
        Copy-Item "firma_disateq.key" -Destination "$backupDir\"
        Copy-Item "firma_disateq.pub" -Destination "$backupDir\"
        
        $readmeBackup = @"
BACKUP CLAVES DISATEQ™
======================
Fecha: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Usuario: $env:USERNAME
Equipo: $env:COMPUTERNAME

CONTENIDO:
- firma_disateq.key (Privada - CONFIDENCIAL)
- firma_disateq.pub (Pública)

IMPORTANTE:
- Guardar en ubicación segura
- No compartir clave privada
- Backup regular recomendado

DisateQ™ — Sistema de Licencias v3.0
"@
        $readmeBackup | Out-File -FilePath "$backupDir\README.txt" -Encoding UTF8
        
        Write-Host ""
        Write-Success "Backup creado en: $backupDir"
        Write-Host ""
        Write-Host "  Mueve esta carpeta a ubicación segura" -ForegroundColor Yellow
        Write-Host "  (Ejemplo: unidad de red, nube encriptada, caja fuerte)" -ForegroundColor Gray
    }
    
} else {
    Write-Host ""
    Write-Host "✗ Error al generar claves" -ForegroundColor Red
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "✓ Proceso completado" -ForegroundColor Green
Write-Host ""
