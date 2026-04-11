"""
aplicar_cambios.py
Aplica los cambios del Punto 4 en monitor.py y config.py
Ejecutar desde: D:\DATA\_Proyectos_\disateq\disateq-cpe-envio
"""
from pathlib import Path
import shutil

BASE = Path(__file__).parent

CAMBIOS = [
    {
        "archivo": "src/monitor.py",
        "desc":    "monitor.py — timer boletas 5min → 30min",
        "buscar":  "INTERVALO_BOLETA   = 300   # 5 min entre ciclos automaticos de boletas",
        "poner":   "INTERVALO_BOLETA   = 1800  # 30 min entre ciclos automaticos de boletas",
    },
    {
        "archivo": "src/monitor.py",
        "desc":    "monitor.py — emitir monto y tipo_doc en evento enviado",
        "buscar":  (
            '        self._emit({"tipo": "evento", "estado": "enviado",\n'
            '                    "nombre": nombre, "cpe_tipo": cpe_tipo, "msg": msg})'
        ),
        "poner": (
            '        monto_enviado = float(comp["totales"]["total"])\n'
            '        tipo_doc_env  = comp.get("tipo_doc", "03")\n'
            '        self._emit({"tipo": "evento", "estado": "enviado",\n'
            '                    "nombre": nombre, "cpe_tipo": cpe_tipo, "msg": msg,\n'
            '                    "monto": monto_enviado, "tipo_doc": tipo_doc_env})'
        ),
    },
]

print("\n=== Aplicando cambios Punto 4 ===\n")

for c in CAMBIOS:
    ruta = BASE / c["archivo"]
    if not ruta.exists():
        print(f"[!] No encontrado: {ruta}")
        continue

    contenido = ruta.read_text(encoding="utf-8")

    if c["buscar"] not in contenido:
        print(f"[~] Ya aplicado o no encontrado: {c['desc']}")
        continue

    # Backup
    shutil.copy(ruta, str(ruta) + ".bak2")
    contenido = contenido.replace(c["buscar"], c["poner"], 1)
    ruta.write_text(contenido, encoding="utf-8")
    print(f"[OK] {c['desc']}")

print("\n=== Listo ===\n")
