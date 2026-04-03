"""
report.py
=========
Generación de reportes de correlativos y control de envíos.
"""

import logging
import re

_RE_CPE = re.compile(r'^\d{11}-0[12]-[A-Z]\d{3}-\d+\.txt$', re.IGNORECASE)
from datetime import date
from pathlib import Path
from collections import defaultdict

log = logging.getLogger(__name__)


def _extraer_correlativo(nombre: str) -> tuple:
    n = Path(nombre).stem
    if n.upper().startswith("A-"):
        n = n[2:]
    partes = n.split("-")
    if len(partes) >= 4:
        try:
            return partes[2], int(partes[3])
        except ValueError:
            pass
    return None, None


def _detectar_gaps(numeros: list) -> list:
    if not numeros:
        return []
    ordenados = sorted(numeros)
    gaps = []
    for i in range(len(ordenados) - 1):
        for faltante in range(ordenados[i] + 1, ordenados[i + 1]):
            gaps.append(faltante)
            if len(gaps) >= 50:
                return gaps
    return gaps


def generar_reporte(carpeta: Path, fecha: date = None) -> Path:
    if fecha is None:
        fecha = date.today()

    enviados = [f for f in (carpeta / "enviados").glob("*.txt") if _RE_CPE.match(f.name)] if (carpeta / "enviados").exists() else []
    errores  = [f for f in (carpeta / "errores").glob("*.txt")  if _RE_CPE.match(f.name)] if (carpeta / "errores").exists() else []

    series = defaultdict(list)
    for archivo in enviados:
        serie, numero = _extraer_correlativo(archivo.name)
        if serie and numero:
            series[serie].append(numero)

    lineas = []
    lineas.append("=" * 58)
    lineas.append(f"  REPORTE DE CORRELATIVOS — {fecha.strftime('%d/%m/%Y')}")
    lineas.append(f"  CPE DisateQ™ — Powered by DisateQ™")
    lineas.append("=" * 58)
    lineas.append("")

    if not series:
        lineas.append("  Sin comprobantes enviados registrados.")
    else:
        for serie in sorted(series.keys()):
            numeros = sorted(series[serie])
            gaps = _detectar_gaps(numeros)
            rango = f"{numeros[0]} al {numeros[-1]}"
            estado = "OK" if not gaps else f"ALERTA — faltan: {', '.join(str(g) for g in gaps[:10])}"
            lineas.append(f"  {serie}: {rango}  |  {estado}")

    lineas.append("")
    lineas.append(f"  Archivos en errores: {len(errores)}")
    for e in errores:
        lineas.append(f"    — {e.name}")
    lineas.append("")
    lineas.append("=" * 58)

    rpt = carpeta / f"reporte_{fecha.strftime('%Y%m%d')}.txt"
    rpt.write_text("\n".join(lineas), encoding="utf-8")
    log.info(f"Reporte generado: {rpt}")
    return rpt
