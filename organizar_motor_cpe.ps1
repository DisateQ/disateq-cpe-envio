# organizar_motor_cpe.ps1
# ========================
# Organiza Motor CPE v3.0 en estructura profesional
# 
# Autor: Fernando Hernán Tejada (@fhertejada™)

$ErrorActionPreference = "Stop"

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "  Organizador Motor CPE v3.0" -ForegroundColor Cyan
Write-Host "  Estructura de Carpetas Profesional" -ForegroundColor Cyan
Write-Host "================================================================`n" -ForegroundColor Cyan

$BASE = "D:\DisateQ\Motor CPE"

if (-not (Test-Path $BASE)) {
    Write-Host "❌ Error: Directorio base no encontrado: $BASE" -ForegroundColor Red
    exit 1
}

cd $BASE

Write-Host "📁 Creando estructura de carpetas...`n" -ForegroundColor Yellow

# Definir estructura
$estructura = @{
    "src" = "Código fuente del Motor"
    "src\adapters" = "Adaptadores de fuentes de datos"
    "src\adapters\mappings" = "Configuraciones YAML por cliente"
    "config" = "Archivos de configuración"
    "licenses" = "Sistema de licencias"
    "licenses\keys" = "Claves RSA (privada y pública)"
    "licenses\client_licenses" = "Licencias de clientes"
    "docs" = "Documentación"
    "tests" = "Tests unitarios"
    "tools" = "Herramientas auxiliares"
    "logs" = "Logs del Motor"
    "output" = "Archivos de salida (TXT, XML, JSON)"
    "backup" = "Backups automáticos"
    "dist" = "Producto FINAL para distribución (ejecutables, instaladores)"
    "dist\windows" = "Builds para Windows (.exe)"
    "dist\installers" = "Instaladores completos para clientes"
}

# Crear carpetas
foreach ($carpeta in $estructura.Keys) {
    $path = Join-Path $BASE $carpeta
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
        $desc = $estructura[$carpeta]
        Write-Host "   ✅ Creada: $carpeta" -ForegroundColor Green
        Write-Host "      ($desc)" -ForegroundColor Gray
    } else {
        Write-Host "   ⏭️  Ya existe: $carpeta" -ForegroundColor Gray
    }
}

Write-Host "`n📋 Moviendo archivos a sus carpetas...`n" -ForegroundColor Yellow

# Mover archivos a src/
$src_files = @(
    "base_adapter.py",
    "xlsx_adapter.py",
    "dbf_adapter.py",
    "sql_adapter.py",
    "yaml_mapper.py",
    "normalizer.py",
    "sender.py",
    "signer.py"
)

foreach ($file in $src_files) {
    if (Test-Path $file) {
        Move-Item $file "src\adapters\" -Force
        Write-Host "   ✅ $file → src\adapters\" -ForegroundColor Green
    }
}

# Mover sistema de licencias
$license_files = @(
    "validador_licencias.py",
    "generar_claves_disateq.py",
    "crear_licencia_cliente.py",
    "test_licencias.py"
)

foreach ($file in $license_files) {
    if (Test-Path $file) {
        Move-Item $file "licenses\" -Force
        Write-Host "   ✅ $file → licenses\" -ForegroundColor Green
    }
}

# Mover claves RSA
if (Test-Path "disateq_private.pem") {
    Move-Item "disateq_private.pem" "licenses\keys\" -Force
    Write-Host "   ✅ disateq_private.pem → licenses\keys\ ⚠️  SEGURA" -ForegroundColor Green
}

if (Test-Path "disateq_public.pem") {
    Move-Item "disateq_public.pem" "licenses\keys\" -Force
    Write-Host "   ✅ disateq_public.pem → licenses\keys\" -ForegroundColor Green
}

if (Test-Path "disateq_motor.lic") {
    Move-Item "disateq_motor.lic" "licenses\client_licenses\" -Force
    Write-Host "   ✅ disateq_motor.lic → licenses\client_licenses\" -ForegroundColor Green
}

# Mover documentación
$doc_files = @(
    "README.md",
    "README_LICENCIAS.md",
    "ESTADO.md"
)

foreach ($file in $doc_files) {
    if (Test-Path $file) {
        Move-Item $file "docs\" -Force
        Write-Host "   ✅ $file → docs\" -ForegroundColor Green
    }
}

# Mover herramientas
if (Test-Path "source_explorer.py") {
    Move-Item "source_explorer.py" "tools\" -Force
    Write-Host "   ✅ source_explorer.py → tools\" -ForegroundColor Green
}

# main.py se queda en la raíz (punto de entrada)
Write-Host "   ⏭️  main.py permanece en raíz (punto de entrada)" -ForegroundColor Gray

Write-Host "`n📝 Creando archivos de configuración...`n" -ForegroundColor Yellow

# Crear .gitignore
$gitignore = @"
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/

# Licencias y claves (NO subir a Git)
licenses/keys/disateq_private.pem
licenses/client_licenses/*.lic

# Builds y distribución
dist/
build/
*.spec

# Logs
logs/*.log

# Output
output/*.txt
output/*.xml
output/*.json

# Backups
backup/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"@

Set-Content -Path ".gitignore" -Value $gitignore
Write-Host "   ✅ .gitignore creado" -ForegroundColor Green

# Crear README en carpeta raíz
$readme_root = @"
# Motor CPE DisateQ™ v3.0

**Motor de Comprobantes de Pago Electrónicos**

## 🚀 Inicio Rápido

``````powershell
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar licencia (ver licenses/README.md)
cd licenses
python crear_licencia_cliente.py

# 3. Ejecutar Motor
python main.py
``````

## 📁 Estructura del Proyecto

``````
Motor CPE/
├── main.py                 # Punto de entrada principal
├── requirements.txt        # Dependencias Python
├── src/                    # Código fuente
│   └── adapters/          # Adaptadores de fuentes
├── licenses/              # Sistema de licencias RSA
│   ├── keys/             # Claves públicas/privadas
│   └── client_licenses/  # Licencias de clientes
├── config/               # Configuración del Motor
├── docs/                 # Documentación completa
├── tests/                # Tests unitarios
├── tools/                # Herramientas auxiliares
├── logs/                 # Logs de ejecución
├── output/               # Archivos generados
└── backup/               # Backups automáticos
``````

## 📚 Documentación

Ver carpeta `docs/` para documentación completa:
- `README.md` - Documentación general
- `README_LICENCIAS.md` - Sistema de licencias
- `ESTADO.md` - Estado del proyecto

## 📞 Soporte

**DisateQ™**
- Email: soporte@disateq.com
- GitHub: privado

---

© 2026 DisateQ™ | @fhertejada™
"@

Set-Content -Path "README.md" -Value $readme_root
Write-Host "   ✅ README.md creado en raíz" -ForegroundColor Green

# Crear config.yaml de ejemplo
$config_example = @"
# Motor CPE DisateQ™ v3.0 - Configuración

# Modo de operación
modo: legacy  # 'legacy' (TXT → APIFAS) o 'direct' (JSON → SUNAT)

# Fuente de datos
fuente:
  tipo: xlsx  # 'xlsx', 'dbf', 'sql'
  
  # Para Excel (XLSX)
  archivo: "ventas.xlsx"
  
  # Para SQL (descomentar si usas SQL)
  # conexion: "Driver={SQL Server};Server=localhost;Database=ventas;UID=user;PWD=pass"
  # mapping: "src/adapters/mappings/mi_cliente.yaml"

# Envío a SUNAT
envio:
  # Modo legacy (APIFAS)
  legacy:
    url: "https://apifas.disateq.com/produccion_text.php"
    usuario: ""
    token: ""
  
  # Modo direct (futuro)
  direct:
    url: "https://api.disateq.com/v1/cpe"
    certificado: "certificado.pem"
    clave: "clave.pem"

# Logs
logs:
  nivel: INFO  # DEBUG, INFO, WARNING, ERROR
  archivo: "logs/motor_cpe.log"
  max_size_mb: 10

# Backups automáticos
backup:
  habilitado: true
  frecuencia_dias: 7
  carpeta: "backup/"
"@

Set-Content -Path "config\motor_config.yaml" -Value $config_example
Write-Host "   ✅ config/motor_config.yaml creado" -ForegroundColor Green

# Crear README en licenses/
$readme_licenses = @"
# Sistema de Licencias

Ver documentación completa en: `docs/README_LICENCIAS.md`

## Archivos

- `keys/` - Claves RSA (disateq_private.pem, disateq_public.pem)
- `client_licenses/` - Licencias de clientes (.lic)

## Uso Rápido

``````powershell
# Crear licencia para cliente
python crear_licencia_cliente.py

# Validar licencia actual
python validador_licencias.py validate
``````
"@

Set-Content -Path "licenses\README.md" -Value $readme_licenses
Write-Host "   ✅ licenses/README.md creado" -ForegroundColor Green

# Crear README en dist/
$readme_dist = @"
# Carpeta dist/ - Distribución de Producto Final

Esta carpeta contiene los **productos finales listos para distribución** a clientes.

## Compilar Producto

``````powershell
.\compilar_producto_final.ps1
``````

Ver README completo en esta carpeta para más detalles.
"@

Set-Content -Path "dist\README.md" -Value $readme_dist
Write-Host "   ✅ dist/README.md creado" -ForegroundColor Green

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "✅ ESTRUCTURA ORGANIZADA" -ForegroundColor Green
Write-Host "================================================================`n" -ForegroundColor Cyan

Write-Host "📁 Estructura de carpetas creada:`n" -ForegroundColor White

# Mostrar árbol
Write-Host "Motor CPE/" -ForegroundColor Cyan
Write-Host "├── main.py" -ForegroundColor White
Write-Host "├── requirements.txt" -ForegroundColor White
Write-Host "├── README.md" -ForegroundColor White
Write-Host "├── .gitignore" -ForegroundColor White
Write-Host "├── src/" -ForegroundColor Yellow
Write-Host "│   └── adapters/" -ForegroundColor Yellow
Write-Host "├── licenses/" -ForegroundColor Yellow
Write-Host "│   ├── keys/" -ForegroundColor Yellow
Write-Host "│   └── client_licenses/" -ForegroundColor Yellow
Write-Host "├── config/" -ForegroundColor Yellow
Write-Host "├── docs/" -ForegroundColor Yellow
Write-Host "├── tests/" -ForegroundColor Yellow
Write-Host "├── tools/" -ForegroundColor Yellow
Write-Host "├── logs/" -ForegroundColor Yellow
Write-Host "├── output/" -ForegroundColor Yellow
Write-Host "├── backup/" -ForegroundColor Yellow
Write-Host "└── dist/" -ForegroundColor Green
Write-Host "    ├── windows/" -ForegroundColor Green
Write-Host "    └── installers/`n" -ForegroundColor Green

Write-Host "📝 Próximos pasos:`n" -ForegroundColor Yellow
Write-Host "   1. Revisar config/motor_config.yaml" -ForegroundColor White
Write-Host "   2. Actualizar imports en main.py (rutas cambiaron)" -ForegroundColor White
Write-Host "   3. Continuar con integración APIFAS`n" -ForegroundColor White

Write-Host "================================================================`n" -ForegroundColor Cyan
