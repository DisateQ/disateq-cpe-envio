"""
status_dia.py
=============
Genera reporte de status del dia — CPE DisateQ.

Muestra y graba en status/ el detalle de envios del dia:
  serie, correlativo, fecha/hora envio, total, items, resultado.

Principio S: responsabilidad unica — generar status. No envia ni lee DBF.
"""

import json
import logging
from datetime import datetime, date
from pathlib import Path
from collections import defaultdict

log = logging.getLogger(__name__)

STATUS_DIR = "status"


def _ruta_status(salida: str) -> Path:
    p = Path(salida) / STATUS_DIR
    p.mkdir(exist_ok=True)
    return p


def _leer_enviados_hoy(salida: str) -> list:
    """
    Lee los TXT de la carpeta enviados/ y extrae metadata.
    Solo los del dia de hoy por fecha de modificacion.
    """
    carpeta = Path(salida) / "enviados"
    if not carpeta.exists():
        return []

    hoy = date.today()
    registros = []

    for f in sorted(carpeta.glob("*.txt")):
        # Filtrar solo los de hoy
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        if mtime.date() != hoy:
            continue

        # Parsear nombre: RUC-02-SERIE-NUMERO.txt
        partes = f.stem.split("-")
        if len(partes) < 4:
            continue
        try:
            ruc    = partes[0]
            serie  = partes[2]
            numero = int(partes[3])
        except (ValueError, IndexError):
            continue

        # Leer totales del TXT
        totales = _extraer_totales(f)

        registros.append({
            "archivo":   f.name,
            "ruc":       ruc,
            "serie":     serie,
            "numero":    numero,
            "hora":      mtime.strftime("%H:%M:%S"),
            "total":     totales.get("total", 0.0),
            "gravada":   totales.get("gravada", 0.0),
            "igv":       totales.get("igv", 0.0),
            "exonerada": totales.get("exonerada", 0.0),
            "items":     totales.get("items", 0),
        })

    return registros


def _extraer_totales(ruta_txt: Path) -> dict:
    """Extrae campos de totales del TXT."""
    try:
        contenido = ruta_txt.read_text(encoding="latin-1")
        campos = {}
        items_count = 0
        for linea in contenido.split("\n"):
            linea = linea.strip()
            if linea.startswith("item|"):
                items_count += 1
                continue
            if "|" in linea:
                p = linea.split("|")
                if len(p) >= 2:
                    campos[p[0].strip()] = p[1].strip()

        return {
            "total":     float(campos.get("total",           "0") or "0"),
            "gravada":   float(campos.get("total_gravada",   "0") or "0"),
            "igv":       float(campos.get("total_igv",       "0") or "0"),
            "exonerada": float(campos.get("total_exonerada", "0") or "0"),
            "items":     items_count,
        }
    except Exception:
        return {}


def _leer_errores_hoy(salida: str) -> list:
    """Lee TXT en errores/ del dia de hoy."""
    carpeta = Path(salida) / "errores"
    if not carpeta.exists():
        return []

    hoy = date.today()
    errores = []
    for f in sorted(carpeta.glob("*.txt")):
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        if mtime.date() != hoy:
            continue
        partes = f.stem.split("-")
        try:
            serie  = partes[2] if len(partes) >= 3 else "?"
            numero = int(partes[3]) if len(partes) >= 4 else 0
        except (ValueError, IndexError):
            serie, numero = "?", 0
        errores.append({
            "archivo": f.name,
            "serie":   serie,
            "numero":  numero,
            "hora":    mtime.strftime("%H:%M:%S"),
        })
    return errores


def generar_status(salida: str, ruc: str, razon_social: str,
                   nombre_comercial: str = "") -> tuple[Path, dict]:
    """
    Genera el reporte de status del dia.
    Retorna (ruta_archivo_txt, datos_dict).
    """
    hoy       = date.today()
    ahora     = datetime.now()
    enviados  = _leer_enviados_hoy(salida)
    errores   = _leer_errores_hoy(salida)

    # Agrupar por serie
    por_serie = defaultdict(list)
    for r in enviados:
        por_serie[r["serie"]].append(r)

    # Totales globales
    total_monto    = sum(r["total"]   for r in enviados)
    total_gravada  = sum(r["gravada"] for r in enviados)
    total_igv      = sum(r["igv"]     for r in enviados)
    total_exonerada= sum(r["exonerada"] for r in enviados)
    total_items    = sum(r["items"]   for r in enviados)

    # ── Generar TXT ──
    sep  = "=" * 62
    sep2 = "-" * 62
    lineas = []
    lineas.append(sep)
    lineas.append(f"  CPE DisateQ\u2122  \u2014  STATUS DEL DIA")
    lineas.append(f"  {nombre_comercial or razon_social}")
    lineas.append(f"  RUC: {ruc}")
    lineas.append(f"  Fecha: {hoy.strftime('%d/%m/%Y')}  |  Generado: {ahora.strftime('%H:%M:%S')}")
    lineas.append(sep)
    lineas.append("")

    if not enviados:
        lineas.append("  Sin comprobantes enviados hoy.")
    else:
        for serie in sorted(por_serie.keys()):
            registros = por_serie[serie]
            nums = [r["numero"] for r in registros]
            monto_serie = sum(r["total"] for r in registros)
            lineas.append(f"  Serie {serie}:")
            lineas.append(f"    Comprobantes enviados : {len(registros)}")
            lineas.append(f"    Rango correlativos    : {min(nums)} \u2014 {max(nums)}")
            lineas.append(f"    Monto total           : S/ {monto_serie:,.2f}")
            lineas.append("")

        lineas.append(sep2)
        lineas.append("  RESUMEN GLOBAL DEL DIA")
        lineas.append(sep2)
        lineas.append(f"  Total comprobantes enviados : {len(enviados)}")
        lineas.append(f"  Total items procesados      : {total_items}")
        lineas.append(f"  Monto total                 : S/ {total_monto:,.2f}")
        lineas.append(f"  Base gravada                : S/ {total_gravada:,.2f}")
        lineas.append(f"  IGV                         : S/ {total_igv:,.2f}")
        lineas.append(f"  Exonerada                   : S/ {total_exonerada:,.2f}")
        lineas.append("")

        # Detalle por comprobante
        lineas.append(sep2)
        lineas.append("  DETALLE DE ENVIOS")
        lineas.append(sep2)
        lineas.append(f"  {'SERIE':<8} {'NUMERO':<10} {'HORA':<10} {'TOTAL':>10} {'ITEMS':>6}")
        lineas.append(f"  {'-'*7} {'-'*9} {'-'*9} {'-'*10} {'-'*5}")
        for r in enviados:
            lineas.append(
                f"  {r['serie']:<8} {str(r['numero']).zfill(8):<10} "
                f"{r['hora']:<10} S/{r['total']:>9,.2f} {r['items']:>6}")

    lineas.append("")
    if errores:
        lineas.append(sep2)
        lineas.append(f"  ERRORES DEL DIA ({len(errores)})")
        lineas.append(sep2)
        for e in errores:
            lineas.append(f"  {e['serie']}-{str(e['numero']).zfill(8)}  [{e['hora']}]  {e['archivo']}")
        lineas.append("")

    lineas.append(sep)
    lineas.append(f"  Powered by CPE DisateQ\u2122  \u2014  @fhertejada\u2122")
    lineas.append(sep)

    # Guardar
    # Un solo archivo por dia — sobreescribe el anterior
    nombre_archivo = f"status_{hoy.strftime('%Y%m%d')}.txt"
    ruta = _ruta_status(salida) / nombre_archivo
    ruta.write_text("\n".join(lineas), encoding="utf-8")
    log.info(f"Status generado: {ruta}")

    datos = {
        "fecha":        hoy.isoformat(),
        "hora":         ahora.strftime("%H:%M:%S"),
        "enviados":     len(enviados),
        "errores":      len(errores),
        "total_monto":  total_monto,
        "total_gravada":total_gravada,
        "total_igv":    total_igv,
        "por_serie":    {s: len(v) for s, v in por_serie.items()},
        "detalle":      enviados,
        "errores_det":  errores,
    }

    return ruta, datos
