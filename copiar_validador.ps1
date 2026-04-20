# copiar_validador.ps1
# ======================
# Copia validador_licencias.py al repositorio

$ErrorActionPreference = "Stop"

Write-Host "`n Copiando validador_licencias.py..." -ForegroundColor Yellow

$REPO = "D:\DATA\_DEV_\repos\disateq-cpe-envio"
$DOWNLOADS = "$env:USERPROFILE\Downloads"

# Buscar archivo en descargas
$archivo = Get-ChildItem "$DOWNLOADS\validador_licencias.py" -ErrorAction SilentlyContinue

if (-not $archivo) {
    Write-Host " ❌ No encontrado en: $DOWNLOADS" -ForegroundColor Red
    Write-Host "`n Buscando en Desktop..." -ForegroundColor Yellow
    
    $DESKTOP = "$env:USERPROFILE\Desktop"
    $archivo = Get-ChildItem "$DESKTOP\validador_licencias.py" -ErrorAction SilentlyContinue
    
    if (-not $archivo) {
        Write-Host " ❌ No encontrado en: $DESKTOP" -ForegroundColor Red
        Write-Host "`n Por favor, descarga validador_licencias.py y colócalo en Descargas o Escritorio`n" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host " ✅ Encontrado: $($archivo.FullName)" -ForegroundColor Green

# Copiar al repositorio
$destino = "$REPO\licenses\validador_licencias.py"

Copy-Item $archivo.FullName $destino -Force

Write-Host " ✅ Copiado a: $destino`n" -ForegroundColor Green

Write-Host " Probando Motor CPE...`n" -ForegroundColor Yellow

cd $REPO
python main.py

Write-Host "`n ✅ Listo!`n" -ForegroundColor Green
