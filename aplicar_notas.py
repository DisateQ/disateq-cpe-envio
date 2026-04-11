"""
aplicar_notas.py
Aplica soporte completo notas credito/debito — Punto 7
Ejecutar desde: D:\DATA\_Proyectos_\disateq\disateq-cpe-envio
"""
from pathlib import Path
import shutil

BASE = Path(__file__).parent

CAMBIOS = [
    {
        "archivo": "src/txt_validator.py",
        "desc":    "txt_validator.py — agregar tipo 3 (NC/ND) como valido",
        "buscar":  (
            '    if tipo and tipo not in ("1", "2"):\n'
            '        return [f"Tipo de comprobante invalido: \'{tipo}\' — esperado 1 (factura) o 2 (boleta)"]'
        ),
        "poner": (
            '    if tipo and tipo not in ("1", "2", "3"):\n'
            '        return [f"Tipo de comprobante invalido: \'{tipo}\' — esperado 1 (factura), 2 (boleta) o 3 (nota credito/debito)"]'
        ),
    },
    {
        "archivo": "src/monitor.py",
        "desc":    "monitor.py — detectar NOTA en cpe_tipo para log y GUI",
        "buscar":  (
            '        cpe_tipo  = "FACTURA" if tipo == "F" else "BOLETA"'
        ),
        "poner": (
            '        tipo_upper = tipo.upper()\n'
            '        if tipo_upper in ("N", "NC") or serie_fmt.upper().startswith(("FC", "NC", "BC")):\n'
            '            cpe_tipo = "NOTA CREDITO"\n'
            '        elif tipo_upper in ("D", "ND") or serie_fmt.upper().startswith(("FD", "ND", "BD")):\n'
            '            cpe_tipo = "NOTA DEBITO"\n'
            '        elif tipo_upper == "F" or serie_fmt.upper().startswith("F"):\n'
            '            cpe_tipo = "FACTURA"\n'
            '        else:\n'
            '            cpe_tipo = "BOLETA"'
        ),
    },
]

print("\n=== Aplicando Punto 7 — Notas credito/debito ===\n")

for c in CAMBIOS:
    ruta = BASE / c["archivo"]
    if not ruta.exists():
        print(f"[!] No encontrado: {ruta}")
        continue

    contenido = ruta.read_text(encoding="utf-8")

    if c["buscar"] not in contenido:
        print(f"[~] Ya aplicado o no encontrado: {c['desc']}")
        continue

    shutil.copy(ruta, str(ruta) + ".bak3")
    contenido = contenido.replace(c["buscar"], c["poner"], 1)
    ruta.write_text(contenido, encoding="utf-8")
    print(f"[OK] {c['desc']}")

print("\n=== Listo ===\n")
