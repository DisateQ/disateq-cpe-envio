"""
adapters/xlsx_adapter.py
========================
Adaptador para leer comprobantes exportados por DisateQ POS™
en formato _CPE (xlsx).

Decisiones de diseño (Abril 2026 — memo cerrado):
  - Misma firma leer() que dbf_adapter.py  →  interfaz uniforme
  - Columnas leidas por NOMBRE (fila 1), nunca por indice
  - El adaptador confia en los valores calculados por POS; no re-deriva

Firma:
    leer(ruta: str) -> tuple[dict, list[dict]]

Retorna:
    (cabecera, items) donde:
      cabecera — dict con datos del comprobante
      items    — list[dict] con cada línea del detalle

Excepciones:
    AdapterError   — archivo no encontrado, hoja _CPE ausente,
                     columnas requeridas faltantes, datos invalidos
"""

from __future__ import annotations

import logging
from pathlib import Path

try:
    import openpyxl
except ImportError as e:
    raise ImportError(
        "openpyxl no instalado. Ejecutar: pip install openpyxl"
    ) from e

log = logging.getLogger(__name__)

# ── Nombre de la hoja oculta exportada por POS ───────────────
_HOJA = "_CPE"

# ── Columnas requeridas en la hoja _CPE ──────────────────────
# Cabecera (fila 1, columna A en adelante — valores en fila 2)
_COLS_CABECERA = {
    "tipo_doc",           # "01" factura / "03" boleta
    "serie",              # "F001", "B001", etc.
    "numero",             # correlativo entero
    "fecha_emision",      # "DD-MM-YYYY" o date/datetime
    "moneda",             # "PEN" / "USD"
    "forma_pago",         # "Contado" / "Credito"
    "cliente_tipo_doc",
    "cliente_numero_doc",
    "cliente_denominacion",
    "cliente_direccion",
    "total_gravada",
    "total_exonerada",
    "total_inafecta",
    "total_igv",
    "total_icbper",
    "total",
}

# Columnas requeridas por cada fila de item
_COLS_ITEM = {
    "item_codigo",
    "item_descripcion",
    "item_unspsc",
    "item_unidad",        # "NIU" / "ZZ"
    "item_cantidad",
    "item_precio_con_igv",
    "item_precio_sin_igv",
    "item_subtotal_sin_igv",
    "item_igv",
    "item_total",
    "item_afectacion_igv",  # "10" / "20" / "30"
}


# ── Excepcion propia del adaptador ───────────────────────────

class AdapterError(Exception):
    """Error controlado del xlsx_adapter."""
    pass


# ── Helpers internos ─────────────────────────────────────────

def _str(valor, default: str = "") -> str:
    if valor is None:
        return default
    return str(valor).strip() or default


def _float(valor, campo: str) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        raise AdapterError(
            f"Valor no numerico en columna '{campo}': {valor!r}"
        )


def _int(valor, campo: str) -> int:
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        raise AdapterError(
            f"Valor entero invalido en columna '{campo}': {valor!r}"
        )


def _fecha(valor, campo: str) -> str:
    """
    Normaliza a string 'DD-MM-YYYY'.
    Acepta date/datetime de openpyxl o string 'DD-MM-YYYY' / 'YYYY-MM-DD'.
    """
    from datetime import date, datetime

    if isinstance(valor, (date, datetime)):
        return valor.strftime("%d-%m-%Y")

    s = _str(valor)
    if not s:
        raise AdapterError(f"Fecha vacia en columna '{campo}'")

    # DD-MM-YYYY
    if len(s) == 10 and s[2] == "-" and s[5] == "-":
        return s

    # YYYY-MM-DD
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        a, m, d = s.split("-")
        return f"{d}-{m}-{a}"

    raise AdapterError(
        f"Formato de fecha no reconocido en '{campo}': {s!r} "
        f"— esperado DD-MM-YYYY o date"
    )


def _validar_columnas(encabezados: set, requeridas: set, contexto: str):
    faltantes = requeridas - encabezados
    if faltantes:
        raise AdapterError(
            f"{contexto}: columnas requeridas ausentes en _CPE: "
            + ", ".join(sorted(faltantes))
        )


# ── Función principal ─────────────────────────────────────────

def leer(ruta: str) -> tuple[dict, list[dict]]:
    """
    Lee el archivo xlsx exportado por DisateQ POS™ y retorna
    (cabecera, items) listos para pasar a normalizar_desde_cpe().

    Args:
        ruta: Path al archivo .xlsx

    Returns:
        cabecera — dict con campos del comprobante
        items    — list[dict] con cada línea de detalle

    Raises:
        AdapterError si el archivo, la hoja o los datos son inválidos
    """
    ruta_p = Path(ruta)
    if not ruta_p.exists():
        raise AdapterError(f"Archivo no encontrado: {ruta}")

    try:
        wb = openpyxl.load_workbook(ruta_p, data_only=True)
    except Exception as e:
        raise AdapterError(f"No se pudo abrir el archivo xlsx: {e}") from e

    if _HOJA not in wb.sheetnames:
        raise AdapterError(
            f"Hoja '{_HOJA}' no encontrada en {ruta_p.name}. "
            f"Hojas disponibles: {wb.sheetnames}"
        )

    ws = wb[_HOJA]
    filas = list(ws.iter_rows(values_only=True))

    if len(filas) < 3:
        raise AdapterError(
            f"Hoja _CPE con menos de 3 filas — "
            f"se esperan: fila 1=cabecera, fila 2=valores, fila 3+=items"
        )

    # Fila 1: nombres de columnas
    nombres = [_str(c).lower() for c in filas[0]]

    # Validar columnas de cabecera
    _validar_columnas(set(nombres), _COLS_CABECERA, "Cabecera")
    _validar_columnas(set(nombres), _COLS_ITEM,     "Items")

    idx = {nombre: i for i, nombre in enumerate(nombres)}

    def col(fila, nombre):
        return fila[idx[nombre]] if idx[nombre] < len(fila) else None

    # ── Leer cabecera (fila 2) ───────────────────────────────
    f_cab = filas[1]

    cabecera = {
        "tipo_doc":            _str(col(f_cab, "tipo_doc")),
        "serie":               _str(col(f_cab, "serie")),
        "numero":              _int(col(f_cab, "numero"), "numero"),
        "fecha_emision":       _fecha(col(f_cab, "fecha_emision"), "fecha_emision"),
        "moneda":              _str(col(f_cab, "moneda"), "PEN"),
        "forma_pago":          _str(col(f_cab, "forma_pago"), "Contado"),
        "cliente_tipo_doc":    _str(col(f_cab, "cliente_tipo_doc"), "-"),
        "cliente_numero_doc":  _str(col(f_cab, "cliente_numero_doc"), "00000000"),
        "cliente_denominacion":_str(col(f_cab, "cliente_denominacion"), "CLIENTE VARIOS"),
        "cliente_direccion":   _str(col(f_cab, "cliente_direccion"), "-"),
        "total_gravada":       _float(col(f_cab, "total_gravada"),   "total_gravada"),
        "total_exonerada":     _float(col(f_cab, "total_exonerada"), "total_exonerada"),
        "total_inafecta":      _float(col(f_cab, "total_inafecta"),  "total_inafecta"),
        "total_igv":           _float(col(f_cab, "total_igv"),       "total_igv"),
        "total_icbper":        _float(col(f_cab, "total_icbper"),    "total_icbper"),
        "total":               _float(col(f_cab, "total"),           "total"),
    }

    # ── Leer items (filas 3..N) ──────────────────────────────
    items = []
    for fila_n, fila in enumerate(filas[2:], start=3):
        # Fila completamente vacía → fin de datos
        if all(v is None for v in fila):
            break

        try:
            item = {
                "codigo":           _str(col(fila, "item_codigo")),
                "descripcion":      _str(col(fila, "item_descripcion")).upper(),
                "unspsc":           _str(col(fila, "item_unspsc"), "10000000"),
                "unidad":           _str(col(fila, "item_unidad"), "NIU"),
                "cantidad":         _float(col(fila, "item_cantidad"),         f"item_cantidad (fila {fila_n})"),
                "precio_con_igv":   _float(col(fila, "item_precio_con_igv"),   f"item_precio_con_igv (fila {fila_n})"),
                "precio_sin_igv":   _float(col(fila, "item_precio_sin_igv"),   f"item_precio_sin_igv (fila {fila_n})"),
                "subtotal_sin_igv": _float(col(fila, "item_subtotal_sin_igv"), f"item_subtotal_sin_igv (fila {fila_n})"),
                "igv":              _float(col(fila, "item_igv"),               f"item_igv (fila {fila_n})"),
                "total":            _float(col(fila, "item_total"),             f"item_total (fila {fila_n})"),
                "afectacion_igv":   _str(col(fila, "item_afectacion_igv"), "10"),
            }
        except AdapterError:
            raise
        except Exception as e:
            raise AdapterError(f"Error leyendo fila {fila_n}: {e}") from e

        items.append(item)

    if not items:
        raise AdapterError("Hoja _CPE sin items — filas 3 en adelante vacías")

    log.info(
        f"xlsx_adapter: {ruta_p.name} → "
        f"{cabecera['serie']}-{str(cabecera['numero']).zfill(8)} "
        f"| {len(items)} item(s)"
    )

    return cabecera, items
