# deploy_motor_cpe.ps1
# ====================
# Script de deployment Motor CPE v3.0
# Para técnicos en campo - instalación en cliente
#
# Uso: .\deploy_motor_cpe.ps1
#
# Autor: Fernando Miguel Tejada Quevedo
# Empresa: DisateQ™
# Fecha: Abril 2026

#Requires -Version 5.1
#Requires -RunAsAdministrator

# Configuración
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

function Write-Step {
    param($Step, $Text)
    Write-Host "[$Step] " -NoNewline -ForegroundColor Yellow
    Write-Host $Text -ForegroundColor White
}

function Write-Success {
    param($Text)
    Write-Host "    ✓ " -NoNewline -ForegroundColor Green
    Write-Host $Text -ForegroundColor White
}

function Write-Info {
    param($Text)
    Write-Host "    ℹ " -NoNewline -ForegroundColor Cyan
    Write-Host $Text -ForegroundColor Gray
}

function Write-Error-Custom {
    param($Text)
    Write-Host "    ✗ " -NoNewline -ForegroundColor Red
    Write-Host $Text -ForegroundColor Red
}

function Write-Warning-Custom {
    param($Text)
    Write-Host "    ⚠ " -NoNewline -ForegroundColor Yellow
    Write-Host $Text -ForegroundColor Yellow
}

# Banner
Clear-Host
Write-Header "DEPLOYMENT MOTOR CPE v3.0 — DisateQ™"
Write-Host "Script de instalación para técnicos de campo" -ForegroundColor Gray
Write-Host ""

# Variables
$INSTALL_DIR = "D:\DisateQ\Motor CPE"
$VERSION = "3.0.1"

# Verificar permisos de administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Error-Custom "Este script requiere permisos de Administrador"
    Write-Host ""
    Write-Host "Click derecho → 'Ejecutar como Administrador'" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

# PASO 1: Información del Cliente
Write-Header "PASO 1: Información del Cliente"

Write-Host "Ingrese los datos del cliente:" -ForegroundColor Cyan
Write-Host ""

$clienteNombre = Read-Host "Nombre de la empresa"
$clienteRUC = Read-Host "RUC"

Write-Host ""
Write-Success "Datos registrados:"
Write-Info "Empresa: $clienteNombre"
Write-Info "RUC: $clienteRUC"
Write-Host ""

# Validar RUC (11 dígitos)
if ($clienteRUC -notmatch '^\d{11}$') {
    Write-Warning-Custom "RUC debe tener 11 dígitos"
    Write-Host ""
    $continuar = Read-Host "¿Continuar de todas formas? (S/N)"
    if ($continuar -ne "S" -and $continuar -ne "s") {
        exit 0
    }
}

# PASO 2: Ubicación del package
Write-Header "PASO 2: Ubicación del Package"

Write-Host "Seleccione la carpeta con Motor_CPE_v$VERSION.zip" -ForegroundColor Cyan
Write-Host ""

Add-Type -AssemblyName System.Windows.Forms
$folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
$folderBrowser.Description = "Selecciona carpeta con el ZIP del Motor CPE"
$folderBrowser.RootFolder = [System.Environment+SpecialFolder]::MyComputer

if ($folderBrowser.ShowDialog() -eq "OK") {
    $sourceFolder = $folderBrowser.SelectedPath
    Write-Success "Carpeta seleccionada: $sourceFolder"
} else {
    Write-Error-Custom "No se seleccionó carpeta"
    exit 1
}

# Buscar ZIP
$zipPath = Join-Path $sourceFolder "Motor_CPE_v$VERSION.zip"
if (-not (Test-Path $zipPath)) {
    Write-Error-Custom "No se encontró: Motor_CPE_v$VERSION.zip"
    Write-Info "Buscado en: $zipPath"
    Write-Host ""
    pause
    exit 1
}

Write-Success "ZIP encontrado"
Write-Host ""

# PASO 3: Instalación
Write-Header "PASO 3: Instalación"

Write-Step "3.1" "Creando directorio de instalación..."
if (-not (Test-Path $INSTALL_DIR)) {
    New-Item -Path $INSTALL_DIR -ItemType Directory -Force | Out-Null
    Write-Success "Directorio creado: $INSTALL_DIR"
} else {
    Write-Warning-Custom "El directorio ya existe"
    $sobrescribir = Read-Host "    ¿Sobrescribir? (S/N)"
    if ($sobrescribir -eq "S" -or $sobrescribir -eq "s") {
        Remove-Item -Path $INSTALL_DIR -Recurse -Force
        New-Item -Path $INSTALL_DIR -ItemType Directory -Force | Out-Null
        Write-Success "Directorio recreado"
    } else {
        Write-Error-Custom "Instalación cancelada"
        exit 0
    }
}
Write-Host ""

Write-Step "3.2" "Extrayendo archivos..."
try {
    Expand-Archive -Path $zipPath -DestinationPath $INSTALL_DIR -Force
    Write-Success "Archivos extraídos"
} catch {
    Write-Error-Custom "Error al extraer: $_"
    exit 1
}
Write-Host ""

# PASO 4: Configuración
Write-Header "PASO 4: Configuración Inicial"

Write-Step "4.1" "Detectando fuente de datos..."
Write-Host ""
Write-Host "    ¿Dónde están los datos de ventas del cliente?" -ForegroundColor Cyan
Write-Host ""
Write-Host "    1. Excel (.xlsx)" -ForegroundColor White
Write-Host "    2. FoxPro (.dbf)" -ForegroundColor White
Write-Host "    3. SQL Server" -ForegroundColor White
Write-Host "    4. Otro (configurar manualmente)" -ForegroundColor White
Write-Host ""

$tipoFuente = Read-Host "    Seleccione opción (1-4)"

$sourceType = ""
$sourcePath = ""

switch ($tipoFuente) {
    "1" {
        $sourceType = "excel"
        Write-Host ""
        Write-Host "    Seleccione el archivo Excel con las ventas" -ForegroundColor Cyan
        $fileBrowser = New-Object System.Windows.Forms.OpenFileDialog
        $fileBrowser.Filter = "Archivos Excel (*.xlsx)|*.xlsx"
        $fileBrowser.Title = "Seleccionar archivo de ventas"
        if ($fileBrowser.ShowDialog() -eq "OK") {
            $sourcePath = $fileBrowser.FileName
            Write-Success "Archivo: $sourcePath"
        }
    }
    "2" {
        $sourceType = "dbf"
        Write-Host ""
        Write-Host "    Seleccione el archivo DBF con las ventas" -ForegroundColor Cyan
        $fileBrowser = New-Object System.Windows.Forms.OpenFileDialog
        $fileBrowser.Filter = "Archivos DBF (*.dbf)|*.dbf"
        $fileBrowser.Title = "Seleccionar archivo de ventas"
        if ($fileBrowser.ShowDialog() -eq "OK") {
            $sourcePath = $fileBrowser.FileName
            Write-Success "Archivo: $sourcePath"
        }
    }
    "3" {
        $sourceType = "sql"
        Write-Host ""
        $sqlServer = Read-Host "    Servidor SQL"
        $sqlDB = Read-Host "    Base de datos"
        $sourcePath = "Server=$sqlServer;Database=$sqlDB"
        Write-Success "Conexión: $sourcePath"
    }
    "4" {
        Write-Warning-Custom "Configuración manual requerida"
        Write-Info "Editar: $INSTALL_DIR\config\cliente.yaml"
        $sourceType = "manual"
    }
}

Write-Host ""

# Crear YAML de configuración
if ($sourceType -ne "manual") {
    Write-Step "4.2" "Generando archivo de configuración..."
    
    $configPath = Join-Path $INSTALL_DIR "config\cliente.yaml"
    
    # Escapar backslashes para YAML
    $sourcePathEscaped = $sourcePath -replace '\\', '/'
    
    $yamlContent = @"
# Configuración Motor CPE v$VERSION
# Cliente: $clienteNombre
# Generado: $(Get-Date -Format 'yyyy-MM-dd HH:mm')

cliente:
  nombre: "$clienteNombre"
  ruc: "$clienteRUC"

source:
  type: $sourceType
  path: "$sourcePathEscaped"

envio:
  modo: legacy
  url: "https://apifas.disateq.com/produccion_text.php"

# IMPORTANTE: Validar mapeo de campos en:
# docs/CONFIGURACION.md
"@
    
    $yamlContent | Out-File -FilePath $configPath -Encoding UTF8
    Write-Success "Configuración guardada"
    Write-Info "Archivo: $configPath"
}

Write-Host ""

# PASO 5: Crear accesos directos
Write-Header "PASO 5: Accesos Directos"

Write-Step "5.1" "Creando acceso directo en Escritorio..."

$desktopPath = [Environment]::GetFolderPath("Desktop")
$exePath = Join-Path $INSTALL_DIR "Motor_CPE_v$VERSION.exe"

$WshShell = New-Object -ComObject WScript.Shell
$shortcut = $WshShell.CreateShortcut("$desktopPath\Motor CPE.lnk")
$shortcut.TargetPath = $exePath
$shortcut.WorkingDirectory = $INSTALL_DIR
$shortcut.Description = "Motor CPE DisateQ™ v$VERSION"
$shortcut.Save()

Write-Success "Acceso directo creado en Escritorio"
Write-Host ""

# PASO 6: Test de conexión
Write-Header "PASO 6: Test de Conexión (Opcional)"

Write-Host "¿Ejecutar test de conexión a la fuente de datos? (S/N): " -NoNewline -ForegroundColor Cyan
$runTest = Read-Host

if ($runTest -eq "S" -or $runTest -eq "s") {
    Write-Host ""
    Write-Step "6.1" "Probando acceso a datos..."
    
    if ($sourceType -eq "excel" -or $sourceType -eq "dbf") {
        if (Test-Path $sourcePath) {
            Write-Success "Archivo accesible: $sourcePath"
        } else {
            Write-Error-Custom "No se puede acceder al archivo"
            Write-Warning-Custom "Verificar permisos y ruta"
        }
    } elseif ($sourceType -eq "sql") {
        Write-Info "Test SQL requiere credenciales - omitido"
    }
} else {
    Write-Info "Test omitido"
}

Write-Host ""

# RESUMEN FINAL
Write-Header "✅ INSTALACIÓN COMPLETADA"

Write-Host "RESUMEN:" -ForegroundColor White
Write-Host ""
Write-Host "  Cliente:        $clienteNombre" -ForegroundColor Gray
Write-Host "  RUC:            $clienteRUC" -ForegroundColor Gray
Write-Host "  Tipo fuente:    $sourceType" -ForegroundColor Gray
if ($sourcePath) {
    Write-Host "  Ruta datos:     $sourcePath" -ForegroundColor Gray
}
Write-Host "  Instalado en:   $INSTALL_DIR" -ForegroundColor Gray
Write-Host ""
Write-Host "PRÓXIMOS PASOS:" -ForegroundColor White
Write-Host ""
Write-Host "  1. Ejecutar 'Motor CPE' desde el escritorio" -ForegroundColor Yellow
Write-Host "  2. Verificar lectura de datos" -ForegroundColor Yellow
Write-Host "  3. Configurar mapeo de campos (si es necesario)" -ForegroundColor Yellow
Write-Host "  4. Ejecutar envío de prueba" -ForegroundColor Yellow
Write-Host ""
Write-Host "ARCHIVOS IMPORTANTES:" -ForegroundColor White
Write-Host ""
Write-Host "  Config:   $INSTALL_DIR\config\cliente.yaml" -ForegroundColor Cyan
Write-Host "  Logs:     $INSTALL_DIR\logs\" -ForegroundColor Cyan
Write-Host "  Docs:     $INSTALL_DIR\docs\" -ForegroundColor Cyan
Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

# Guardar log de instalación
$logPath = Join-Path $INSTALL_DIR "logs\instalacion_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
$logContent = @"
INSTALACIÓN MOTOR CPE v$VERSION
================================
Fecha: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Técnico: $env:USERNAME
Equipo: $env:COMPUTERNAME

Cliente: $clienteNombre
RUC: $clienteRUC
Tipo fuente: $sourceType
Ruta: $sourcePath

Instalado en: $INSTALL_DIR
Estado: COMPLETADO
"@

$logContent | Out-File -FilePath $logPath -Encoding UTF8

Write-Host "📄 Log de instalación guardado en:" -ForegroundColor Cyan
Write-Host "   $logPath" -ForegroundColor Gray
Write-Host ""

# Abrir carpeta de instalación
Write-Host "¿Abrir carpeta de instalación? (S/N): " -NoNewline -ForegroundColor Cyan
$openFolder = Read-Host
if ($openFolder -eq "S" -or $openFolder -eq "s") {
    explorer $INSTALL_DIR
}

Write-Host ""
Write-Host "✓ Deployment completado exitosamente" -ForegroundColor Green
Write-Host ""
Write-Host "Para soporte: soporte@disateq.com" -ForegroundColor Gray
Write-Host ""

pause
