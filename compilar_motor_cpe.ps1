# compilar_motor_cpe.ps1
# =====================
# Script de compilación Motor CPE v3.0
# Genera ejecutable standalone con PyInstaller
#
# Uso: .\compilar_motor_cpe.ps1
#
# Autor: Fernando Miguel Tejada Quevedo
# Empresa: DisateQ™
# Fecha: Abril 2026

#Requires -Version 5.1

# Configuración
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

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
    param($Text)
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] " -NoNewline -ForegroundColor Gray
    Write-Host "→ " -NoNewline -ForegroundColor Cyan
    Write-Host $Text -ForegroundColor White
}

function Write-Success {
    param($Text)
    Write-Host "✓ " -NoNewline -ForegroundColor Green
    Write-Host $Text -ForegroundColor White
}

function Write-Error-Custom {
    param($Text)
    Write-Host "✗ " -NoNewline -ForegroundColor Red
    Write-Host $Text -ForegroundColor Red
}

# Banner
Clear-Host
Write-Header "COMPILADOR MOTOR CPE v3.0 — DisateQ™"

# Variables
$REPO_ROOT = "D:\DATA\_DEV_\repos\disateq-cpe-envio"
$SRC_DIR = Join-Path $REPO_ROOT "src"
$DIST_DIR = Join-Path $REPO_ROOT "dist"
$BUILD_DIR = Join-Path $REPO_ROOT "build"
$OUTPUT_DIR = Join-Path $REPO_ROOT "instaladores"
$VERSION = "3.0.1"

Write-Step "Directorio raíz: $REPO_ROOT"
Write-Step "Versión: $VERSION"
Write-Host ""

# Verificar que estamos en el directorio correcto
if (-not (Test-Path $REPO_ROOT)) {
    Write-Error-Custom "No se encuentra el repositorio en: $REPO_ROOT"
    Write-Host ""
    Write-Host "Verifica la ruta y vuelve a ejecutar." -ForegroundColor Yellow
    exit 1
}

# Cambiar al directorio del repositorio
Set-Location $REPO_ROOT

# Paso 1: Verificar Python
Write-Header "PASO 1: Verificación de Requisitos"

Write-Step "Verificando Python..."
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python encontrado: $pythonVersion"
} catch {
    Write-Error-Custom "Python no encontrado"
    Write-Host ""
    Write-Host "Instala Python 3.10+ desde https://python.org" -ForegroundColor Yellow
    exit 1
}

# Paso 2: Verificar/Instalar PyInstaller
Write-Step "Verificando PyInstaller..."
$pyinstallerInstalled = python -c "import PyInstaller" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "   PyInstaller no encontrado, instalando..." -ForegroundColor Yellow
    pip install pyinstaller --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Success "PyInstaller instalado correctamente"
    } else {
        Write-Error-Custom "Error al instalar PyInstaller"
        exit 1
    }
} else {
    Write-Success "PyInstaller encontrado"
}

# Paso 3: Verificar dependencias
Write-Step "Verificando dependencias..."
if (Test-Path (Join-Path $REPO_ROOT "requirements.txt")) {
    Write-Host "   Instalando/actualizando dependencias..." -ForegroundColor Gray
    pip install -r requirements.txt --quiet
    Write-Success "Dependencias instaladas"
} else {
    Write-Error-Custom "requirements.txt no encontrado"
    exit 1
}

Write-Host ""

# Paso 4: Limpiar builds anteriores
Write-Header "PASO 2: Limpieza"

Write-Step "Eliminando builds anteriores..."
if (Test-Path $DIST_DIR) {
    Remove-Item -Path $DIST_DIR -Recurse -Force
    Write-Success "Carpeta dist/ eliminada"
}
if (Test-Path $BUILD_DIR) {
    Remove-Item -Path $BUILD_DIR -Recurse -Force
    Write-Success "Carpeta build/ eliminada"
}

Write-Host ""

# Paso 5: Crear script principal si no existe
Write-Header "PASO 3: Preparación"

$MAIN_SCRIPT = Join-Path $SRC_DIR "main.py"
if (-not (Test-Path $MAIN_SCRIPT)) {
    Write-Step "Creando script principal main.py..."
    
    $mainContent = @"
"""
main.py
=======
Punto de entrada principal — Motor CPE DisateQ™ v3.0

Ejecutable compilado para deployment en clientes.
"""

import sys
import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path

def main():
    """Función principal del Motor CPE."""
    
    # Crear ventana principal
    root = tk.Tk()
    root.title("Motor CPE DisateQ™ v$VERSION")
    root.geometry("500x300")
    root.resizable(False, False)
    
    # Frame principal
    frame = tk.Frame(root, padx=20, pady=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    # Logo/Título
    titulo = tk.Label(
        frame,
        text="Motor CPE DisateQ™",
        font=("Arial", 18, "bold"),
        fg="#2c3e50"
    )
    titulo.pack(pady=10)
    
    version = tk.Label(
        frame,
        text="Versión $VERSION",
        font=("Arial", 10),
        fg="#7f8c8d"
    )
    version.pack()
    
    # Separador
    separator = tk.Frame(frame, height=2, bg="#bdc3c7")
    separator.pack(fill=tk.X, pady=20)
    
    # Mensaje
    mensaje = tk.Label(
        frame,
        text="Motor de Comprobantes de Pago Electrónicos\nEnvío automático a SUNAT vía APIFAS",
        font=("Arial", 10),
        justify=tk.CENTER,
        fg="#34495e"
    )
    mensaje.pack(pady=10)
    
    # Botones
    btn_frame = tk.Frame(frame)
    btn_frame.pack(pady=20)
    
    def configurar():
        messagebox.showinfo(
            "Configuración",
            "Próximamente: Wizard de configuración\n\n"
            "Por ahora, edita manualmente:\n"
            "C:\\DisateQ\\Motor CPE\\config\\cliente.yaml"
        )
    
    def enviar():
        messagebox.showinfo(
            "Envío Manual",
            "Próximamente: Envío manual de comprobantes pendientes"
        )
    
    def salir():
        root.quit()
    
    tk.Button(
        btn_frame,
        text="⚙️ Configurar",
        command=configurar,
        width=15,
        height=2,
        font=("Arial", 10)
    ).pack(side=tk.LEFT, padx=5)
    
    tk.Button(
        btn_frame,
        text="📤 Enviar Pendientes",
        command=enviar,
        width=15,
        height=2,
        font=("Arial", 10)
    ).pack(side=tk.LEFT, padx=5)
    
    tk.Button(
        btn_frame,
        text="❌ Salir",
        command=salir,
        width=15,
        height=2,
        font=("Arial", 10)
    ).pack(side=tk.LEFT, padx=5)
    
    # Footer
    footer = tk.Label(
        frame,
        text="DisateQ™ — Soluciones Empresariales",
        font=("Arial", 8),
        fg="#95a5a6"
    )
    footer.pack(side=tk.BOTTOM, pady=10)
    
    # Ejecutar
    root.mainloop()

if __name__ == "__main__":
    main()
"@
    
    $mainContent | Out-File -FilePath $MAIN_SCRIPT -Encoding UTF8
    Write-Success "main.py creado"
} else {
    Write-Success "main.py ya existe"
}

Write-Host ""

# Paso 6: Compilar con PyInstaller
Write-Header "PASO 4: Compilación"

Write-Step "Compilando Motor CPE con PyInstaller..."
Write-Host "   (Esto puede tomar 1-2 minutos...)" -ForegroundColor Gray
Write-Host ""

$pyinstallerArgs = @(
    "--name=Motor_CPE_v$VERSION",
    "--onefile",
    "--windowed",
    "--icon=NONE",
    "--clean",
    "--noconfirm",
    $MAIN_SCRIPT
)

$compileOutput = pyinstaller $pyinstallerArgs 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Success "Compilación exitosa"
} else {
    Write-Error-Custom "Error en compilación"
    Write-Host ""
    Write-Host $compileOutput -ForegroundColor Red
    exit 1
}

Write-Host ""

# Paso 7: Verificar ejecutable
Write-Header "PASO 5: Verificación"

$exePath = Join-Path $DIST_DIR "Motor_CPE_v$VERSION.exe"
if (Test-Path $exePath) {
    $exeSize = [math]::Round((Get-Item $exePath).Length / 1MB, 2)
    Write-Success "Ejecutable generado: Motor_CPE_v$VERSION.exe"
    Write-Host "   Tamaño: $exeSize MB" -ForegroundColor Gray
    Write-Host "   Ubicación: $exePath" -ForegroundColor Gray
} else {
    Write-Error-Custom "No se encontró el ejecutable"
    exit 1
}

Write-Host ""

# Paso 8: Crear carpeta de instaladores
Write-Header "PASO 6: Empaquetado"

Write-Step "Creando estructura de instaladores..."
if (-not (Test-Path $OUTPUT_DIR)) {
    New-Item -Path $OUTPUT_DIR -ItemType Directory | Out-Null
}

$installerPackage = Join-Path $OUTPUT_DIR "Motor_CPE_v$VERSION"
if (Test-Path $installerPackage) {
    Remove-Item -Path $installerPackage -Recurse -Force
}
New-Item -Path $installerPackage -ItemType Directory | Out-Null

# Copiar ejecutable
Copy-Item -Path $exePath -Destination $installerPackage
Write-Success "Ejecutable copiado"

# Crear estructura de carpetas
$configDir = Join-Path $installerPackage "config"
$logsDir = Join-Path $installerPackage "logs"
$docsDir = Join-Path $installerPackage "docs"

New-Item -Path $configDir -ItemType Directory | Out-Null
New-Item -Path $logsDir -ItemType Directory | Out-Null
New-Item -Path $docsDir -ItemType Directory | Out-Null

Write-Success "Carpetas creadas"

# Crear YAML de ejemplo
$exampleYaml = @"
# Configuración Motor CPE v$VERSION
# Edita este archivo según tu sistema

cliente:
  nombre: "Mi Empresa S.A.C."
  ruc: "20123456789"

source:
  type: excel  # excel, dbf, sql
  path: "C:/Sistema/ventas.xlsx"

envio:
  modo: legacy
  url: "https://apifas.disateq.com/produccion_text.php"

# Para más información: docs/CONFIGURACION.md
"@

$exampleYaml | Out-File -FilePath (Join-Path $configDir "ejemplo.yaml") -Encoding UTF8
Write-Success "Archivo de ejemplo creado"

# Crear README
$readmeContent = @"
# MOTOR CPE DisateQ™ v$VERSION

## INSTALACIÓN

1. Copia la carpeta completa a: C:\DisateQ\Motor CPE\
2. Edita: config\cliente.yaml con tus datos
3. Ejecuta: Motor_CPE_v$VERSION.exe

## CONFIGURACIÓN

Edita config\cliente.yaml:
- Cambia 'nombre' y 'ruc' por los de tu empresa
- En 'source.path' indica dónde están tus ventas
- Guarda y cierra

## SOPORTE

Email: soporte@disateq.com
Web: https://disateq.com

---
DisateQ™ — Motor CPE v$VERSION
Compilado: $(Get-Date -Format 'yyyy-MM-dd HH:mm')
"@

$readmeContent | Out-File -FilePath (Join-Path $installerPackage "README.txt") -Encoding UTF8
Write-Success "README.txt creado"

Write-Host ""

# Paso 9: Crear ZIP distribuible
Write-Step "Comprimiendo package..."
$zipPath = Join-Path $OUTPUT_DIR "Motor_CPE_v$VERSION.zip"
if (Test-Path $zipPath) {
    Remove-Item -Path $zipPath -Force
}

Compress-Archive -Path "$installerPackage\*" -DestinationPath $zipPath -CompressionLevel Optimal
$zipSize = [math]::Round((Get-Item $zipPath).Length / 1MB, 2)
Write-Success "ZIP creado: Motor_CPE_v$VERSION.zip ($zipSize MB)"

Write-Host ""

# Resumen final
Write-Header "✅ COMPILACIÓN COMPLETADA"

Write-Host "ARCHIVOS GENERADOS:" -ForegroundColor White
Write-Host ""
Write-Host "  📁 Carpeta instalador:" -ForegroundColor Cyan
Write-Host "     $installerPackage" -ForegroundColor Gray
Write-Host ""
Write-Host "  📦 ZIP distribuible:" -ForegroundColor Cyan
Write-Host "     $zipPath" -ForegroundColor Gray
Write-Host "     Tamaño: $zipSize MB" -ForegroundColor Gray
Write-Host ""
Write-Host "PRÓXIMOS PASOS:" -ForegroundColor White
Write-Host ""
Write-Host "  1. Probar ejecutable localmente" -ForegroundColor Yellow
Write-Host "  2. Enviar ZIP a técnicos de campo" -ForegroundColor Yellow
Write-Host "  3. Documentar instalación en clientes" -ForegroundColor Yellow
Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

# Abrir carpeta de instaladores
Write-Host "¿Abrir carpeta de instaladores? (S/N): " -NoNewline -ForegroundColor Cyan
$response = Read-Host
if ($response -eq "S" -or $response -eq "s") {
    explorer $OUTPUT_DIR
}

Write-Host ""
Write-Host "✓ Proceso completado exitosamente" -ForegroundColor Green
Write-Host ""
