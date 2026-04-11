# aplicar_cambios.ps1
# Aplica los cambios del Punto 4 en monitor.py y config.py
# Ejecutar desde: D:\DATA\_Proyectos_\disateq\disateq-cpe-envio

$ErrorActionPreference = "Stop"
$base = $PSScriptRoot
if (-not $base) { $base = Get-Location }

function Aplicar {
    param($archivo, $buscar, $reemplazar, $descripcion)
    $ruta = Join-Path $base $archivo
    if (-not (Test-Path $ruta)) {
        Write-Host "[!] No encontrado: $ruta" -ForegroundColor Red
        return
    }
    $contenido = Get-Content $ruta -Raw -Encoding UTF8
    if ($contenido -notlike "*$buscar*") {
        Write-Host "[!] Texto no encontrado en $archivo — puede ya estar aplicado: $descripcion" -ForegroundColor Yellow
        return
    }
    # Backup
    Copy-Item $ruta "$ruta.bak2" -Force
    $contenido = $contenido.Replace($buscar, $reemplazar)
    Set-Content $ruta $contenido -Encoding UTF8 -NoNewline
    Write-Host "[OK] $descripcion" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Aplicando cambios Punto 4 ===" -ForegroundColor Cyan
Write-Host ""

# 1 — monitor.py: timer 30 min
Aplicar `
    "src\monitor.py" `
    "INTERVALO_BOLETA   = 300   # 5 min entre ciclos automaticos de boletas" `
    "INTERVALO_BOLETA   = 1800  # 30 min entre ciclos automaticos de boletas" `
    "monitor.py — timer boletas 300s → 1800s"

# 2 — monitor.py: emitir monto y tipo_doc en evento enviado
Aplicar `
    "src\monitor.py" `
    '        self._emit({"tipo": "evento", "estado": "enviado",
                    "nombre": nombre, "cpe_tipo": cpe_tipo, "msg": msg})' `
    '        monto_enviado = float(comp["totales"]["total"])
        tipo_doc_env  = comp.get("tipo_doc", "03")
        self._emit({"tipo": "evento", "estado": "enviado",
                    "nombre": nombre, "cpe_tipo": cpe_tipo, "msg": msg,
                    "monto": monto_enviado, "tipo_doc": tipo_doc_env})' `
    "monitor.py — emitir monto y tipo_doc en evento enviado"

# 3 — config.py: INTERVALO_BOLETA (si existe ahi tambien)
Aplicar `
    "src\config.py" `
    "INTERVALO_BOLETA   = 300   # 5 min" `
    "INTERVALO_BOLETA   = 1800  # 30 min" `
    "config.py — INTERVALO_BOLETA 300 → 1800"

Write-Host ""
Write-Host "=== Listo. Verificando archivos modificados ===" -ForegroundColor Cyan
Get-ChildItem src\monitor.py, src\config.py | Select-Object Name, LastWriteTime, Length
Write-Host ""
