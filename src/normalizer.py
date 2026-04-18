"""
normalizer.py
=============
Estructura interna comun para comprobantes.
Convierte registros DBF a un dict normalizado.
Maneja campos nulos/vacios del sistema FoxPro.
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime


def _d(valor) -> Decimal:
    """Convierte a Decimal con 8 decimales. Retorna 0 si el valor es nulo."""
    try:
        if valor is None:
            return Decimal("0")
        v = float(valor)
        return Decimal(str(v)).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)
    except Exception:
        return Decimal("0")


def _safe_str(valor, default="") -> str:
    """Convierte a str seguro, manejando bytes nulos del DBF."""
    if valor is None:
        return default
    if isinstance(valor, bytes):
        cleaned = valor.replace(b'\x00', b'').strip()
        return cleaned.decode("latin-1", errors="ignore") or default
    return str(valor).strip() or default


def _safe_float(valor, default=0.0) -> float:
    """Convierte a float seguro."""
    try:
        if valor is None:
            return default
        return float(valor)
    except Exception:
        return default


def _safe_fecha(valor) -> tuple:
    """
    Extrae fecha del campo DBF.
    Retorna (fecha_str DD-MM-YYYY, fecha_iso YYYY-MM-DD).
    Si viene nula/invalida usa la fecha de hoy.
    """
    hoy = date.today()
    fallback = (hoy.strftime("%d-%m-%Y"), hoy.strftime("%Y-%m-%d"))

    if valor is None:
        return fallback

    if isinstance(valor, bytes):
        if not valor.replace(b'\x00', b'').strip():
            return fallback
        try:
            valor = valor.decode("latin-1").strip()
        except Exception:
            return fallback

    if hasattr(valor, "strftime"):
        try:
            return valor.strftime("%d-%m-%Y"), valor.strftime("%Y-%m-%d")
        except Exception:
            return fallback

    s = str(valor).strip()
    if not s or set(s) <= {'0', ' ', '-', '/'}:
        return fallback

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y%m%d"):
        try:
            d = datetime.strptime(s, fmt).date()
            return d.strftime("%d-%m-%Y"), d.strftime("%Y-%m-%d")
        except Exception:
            continue

    return fallback


def _afectacion_igv(item: dict) -> str:
    if item.get("_EXONERADO"):
        return "20"
    if item.get("_ICBPER"):
        return "20"
    return "10"


def _forma_pago(forma) -> str:
    return "Contado" if _safe_str(forma) in ("1", "") else "Credito"


def normalizar(envio: dict, items: list) -> dict:
    tipo   = _safe_str(envio.get("TIPO_FACTU"), "B")
    serie  = _safe_str(envio.get("SERIE_FACT"), "001").zfill(3)
    numero_raw = _safe_str(envio.get("NUMERO_FAC"), "0")
    try:
        numero = int(numero_raw)
    except ValueError:
        numero = 0

    fecha_str, fecha_iso = _safe_fecha(envio.get("FECHA_DOCU"))
    serie_fmt = f"{tipo}{serie}"

    total_gravada   = Decimal("0")
    total_exonerada = Decimal("0")
    total_inafecta  = Decimal("0")
    total_igv       = Decimal("0")
    total_icbper    = Decimal("0")
    total           = Decimal("0")

    items_norm = []
    for item in items:
        real  = _d(_safe_float(item.get("REAL_PEDID")))
        monto = _d(_safe_float(item.get("MONTO_PEDI")))
        igv   = _d(_safe_float(item.get("IGV_PEDIDO")))
        afect = _afectacion_igv(item)

        cant_mayor = _safe_float(item.get("CANTIDAD_P"))
        cant_menor = _safe_float(item.get("TABLETA_PE"))
        cantidad   = cant_mayor if cant_mayor > 0 else (cant_menor if cant_menor > 0 else 1)

        precio_con_igv = _d(
            _safe_float(item.get("PRECIO_UNI")) if cant_mayor > 0
            else _safe_float(item.get("PRECIO_FRA"))
        )

        if afect == "10":
            precio_sin_igv = (precio_con_igv / Decimal("1.18")).quantize(
                Decimal("0.00000001"), rounding=ROUND_HALF_UP)
            total_gravada += monto
            total_igv     += igv
        else:
            precio_sin_igv  = precio_con_igv
            total_exonerada += real

        total += real

        if item.get("_ICBPER"):
            total_icbper += real

        items_norm.append({
            "codigo":           _safe_str(item.get("CODIGO_PRO"), "000"),
            "descripcion":      _safe_str(item.get("_DESCRIPCIO"), "SIN DESCRIPCION").upper(),
            "unspsc":           _safe_str(item.get("_CODIGO_UNS"), "10000000"),
            "unidad":           "ZZ" if item.get("_SERVICIO") else "NIU",
            "cantidad":         cantidad,
            "precio_con_igv":   precio_con_igv,
            "precio_sin_igv":   precio_sin_igv,
            "subtotal_sin_igv": monto,
            "igv":              igv,
            "total":            real,
            "afectacion_igv":   afect,
            "icbper":           item.get("_ICBPER", False),
            "exonerado":        item.get("_EXONERADO", False),
        })

    forma_pago = _forma_pago(items[0].get("FORMA_FACT", "1") if items else "1")

    # ── Determinar tipo de documento SUNAT ───────────────────
    # Notas ANTES que factura/boleta: FC03 debe detectarse como NC, no como F
    if (tipo.upper() in ("N", "NC") or
            serie_fmt.upper().startswith("FC") or
            serie_fmt.upper().startswith("BC")):
        tipo_doc_sunat = "07"   # nota crédito → APIFAS tipo 3
    elif (tipo.upper() in ("D", "ND") or
            serie_fmt.upper().startswith("FD") or
            serie_fmt.upper().startswith("BD")):
        tipo_doc_sunat = "08"   # nota débito → APIFAS tipo 3
    elif tipo.upper().startswith("F") or serie_fmt.upper().startswith("F"):
        tipo_doc_sunat = "01"   # factura
    elif tipo.upper().startswith("B") or serie_fmt.upper().startswith("B"):
        tipo_doc_sunat = "03"   # boleta
    else:
        tipo_doc_sunat = "01"

    # ── Campos de referencia al documento original (NC/ND) ───
    doc_mod_tipo  = _safe_str(envio.get("DOC_MOD_TIPO",  envio.get("TIPO_DOC_MOD",  "")))
    doc_mod_serie = _safe_str(envio.get("DOC_MOD_SERIE", envio.get("SERIE_DOC_MOD", "")))
    doc_mod_num   = _safe_str(envio.get("DOC_MOD_NUM",   envio.get("NUM_DOC_MOD",   "")))
    tipo_nota_c   = _safe_str(envio.get("TIPO_NOTA_C",   envio.get("TIPO_NC",       "")))
    tipo_nota_d   = _safe_str(envio.get("TIPO_NOTA_D",   envio.get("TIPO_ND",       "")))

    return {
        "ruc_emisor":   None,
        "razon_social": None,
        "tipo_doc":     tipo_doc_sunat,
        "serie":        serie_fmt,
        "numero":       numero,
        "fecha_str":    fecha_str,
        "fecha_iso":    fecha_iso,
        "moneda":       "PEN",
        "cliente": {
            "tipo_doc":     "-",
            "numero_doc":   "00000000",
            "denominacion": "CLIENTE VARIOS",
            "direccion":    "-",
        },
        "totales": {
            "gravada":   total_gravada,
            "exonerada": total_exonerada,
            "inafecta":  total_inafecta,
            "igv":       total_igv,
            "icbper":    total_icbper,
            "total":     total,
        },
        "forma_pago":     forma_pago,
        "items":          items_norm,
        "es_nota":        tipo_doc_sunat in ("07", "08"),
        "doc_referencia": {
            "tipo":    doc_mod_tipo,
            "serie":   doc_mod_serie,
            "numero":  doc_mod_num,
            "tipo_nc": tipo_nota_c,
            "tipo_nd": tipo_nota_d,
        },
        "nombre_archivo": f"{{}}-02-{serie_fmt}-{str(numero).zfill(8)}.txt",
    }

# ── normalizar_desde_cpe() — Funcion hermana para DisateQ POS™ ──
# Decision de diseño Abril 2026

from exceptions import ConfigError


_CABECERA_REQUERIDA = [
    "tipo_doc", "serie", "numero", "fecha_emision",
    "total_gravada", "total_exonerada", "total_inafecta",
    "total_igv", "total_icbper", "total",
]

_ITEM_REQUERIDO = [
    "codigo", "descripcion", "unidad", "cantidad",
    "precio_con_igv", "precio_sin_igv", "subtotal_sin_igv",
    "igv", "total", "afectacion_igv",
]


def _validar_presencia(datos: dict, campos: list, contexto: str):
    """Lanza ConfigError si falta algun campo obligatorio."""
    faltantes = [c for c in campos if c not in datos or datos[c] is None]
    if faltantes:
        raise ConfigError(
            contexto,
            f"campos obligatorios ausentes: {', '.join(faltantes)}"
        )


def _validar_tipo_doc(tipo_doc: str):
    if tipo_doc not in ("01", "03"):
        raise ConfigError(
            "tipo_doc",
            f"valor invalido '{tipo_doc}' — esperado '01' (factura) o '03' (boleta)"
        )


def _validar_afectacion(afectacion: str, item_n: int):
    if afectacion not in ("10", "20", "30", "40"):
        raise ConfigError(
            f"item[{item_n}].afectacion_igv",
            f"valor invalido '{afectacion}' — esperado 10, 20, 30 o 40"
        )


def _fecha_str_a_iso(fecha_ddmmyyyy: str) -> str:
    """Convierte 'DD-MM-YYYY' a 'YYYY-MM-DD'."""
    try:
        d, m, a = fecha_ddmmyyyy.split("-")
        return f"{a}-{m}-{d}"
    except Exception:
        return date.today().strftime("%Y-%m-%d")


def normalizar_desde_cpe(cabecera: dict, items: list) -> dict:
    """
    Normaliza un comprobante proveniente del xlsx_adapter de DisateQ POS™.

    A diferencia de normalizar(), esta funcion confia en los valores
    calculados por POS — no re-deriva precios ni totales.
    Solo valida presencia de campos obligatorios y tipos basicos.

    Args:
        cabecera: dict con campos del comprobante (de xlsx_adapter.leer)
        items:    list[dict] con detalle (de xlsx_adapter.leer)

    Returns:
        sale_dict con el mismo shape que normalizar() para compatibilidad
        total con el flujo json_builder / txt_generator / sender.

    Raises:
        ConfigError si faltan campos obligatorios o los tipos son invalidos
    """
    # Validar cabecera
    _validar_presencia(cabecera, _CABECERA_REQUERIDA, "cabecera")
    _validar_tipo_doc(_safe_str(cabecera.get("tipo_doc")))

    if not items:
        raise ConfigError("items", "el comprobante no tiene items")

    # Validar cada item
    for i, item in enumerate(items):
        _validar_presencia(item, _ITEM_REQUERIDO, f"item[{i}]")
        _validar_afectacion(_safe_str(item.get("afectacion_igv")), i)

    # ── Construir dict de salida (mismo shape que normalizar()) ──

    tipo_doc  = _safe_str(cabecera.get("tipo_doc"))
    serie     = _safe_str(cabecera.get("serie"))
    numero    = int(cabecera.get("numero", 0))
    fecha_str = _safe_str(cabecera.get("fecha_emision"))   # DD-MM-YYYY
    fecha_iso = _fecha_str_a_iso(fecha_str)

    items_norm = []
    for item in items:
        items_norm.append({
            "codigo":           _safe_str(item.get("codigo"), "000"),
            "descripcion":      _safe_str(item.get("descripcion"), "SIN DESCRIPCION").upper(),
            "unspsc":           _safe_str(item.get("unspsc"), "10000000"),
            "unidad":           _safe_str(item.get("unidad"), "NIU"),
            "cantidad":         float(item.get("cantidad", 1)),
            "precio_con_igv":   _d(item.get("precio_con_igv")),
            "precio_sin_igv":   _d(item.get("precio_sin_igv")),
            "subtotal_sin_igv": _d(item.get("subtotal_sin_igv")),
            "igv":              _d(item.get("igv")),
            "total":            _d(item.get("total")),
            "afectacion_igv":   _safe_str(item.get("afectacion_igv"), "10"),
            "icbper":           False,
            "exonerado":        _safe_str(item.get("afectacion_igv")) in ("20", "30"),
        })

    forma_pago = _safe_str(cabecera.get("forma_pago"), "Contado")

    return {
        "ruc_emisor":   None,
        "razon_social": None,
        "tipo_doc":     tipo_doc,
        "serie":        serie,
        "numero":       numero,
        "fecha_str":    fecha_str,
        "fecha_iso":    fecha_iso,
        "moneda":       _safe_str(cabecera.get("moneda"), "PEN"),
        "cliente": {
            "tipo_doc":    _safe_str(cabecera.get("cliente_tipo_doc"), "-"),
            "numero_doc":  _safe_str(cabecera.get("cliente_numero_doc"), "00000000"),
            "denominacion":_safe_str(cabecera.get("cliente_denominacion"), "CLIENTE VARIOS"),
            "direccion":   _safe_str(cabecera.get("cliente_direccion"), "-"),
        },
        "totales": {
            "gravada":   _d(cabecera.get("total_gravada")),
            "exonerada": _d(cabecera.get("total_exonerada")),
            "inafecta":  _d(cabecera.get("total_inafecta")),
            "igv":       _d(cabecera.get("total_igv")),
            "icbper":    _d(cabecera.get("total_icbper")),
            "total":     _d(cabecera.get("total")),
        },
        "forma_pago":     forma_pago,
        "items":          items_norm,
        "es_nota":        False,
        "doc_referencia": {
            "tipo":    "",
            "serie":   "",
            "numero":  "",
            "tipo_nc": "",
            "tipo_nd": "",
        },
        "nombre_archivo": f"{{}}-02-{serie}-{str(numero).zfill(8)}.txt",
    }