"""
txt_validator.py
================
Validacion del contenido TXT antes de enviarlo a APIFAS.

Principios SOLID:
  S — Responsabilidad unica: validar. No genera ni envia.
  O — Agregar nueva regla = agregar funcion _validar_X(), sin tocar las demas.

Retorna lista de errores encontrados. Lista vacia = TXT valido.
"""

import re
from decimal import Decimal, InvalidOperation

# Campos obligatorios que deben estar presentes y no vacios
_CAMPOS_OBLIGATORIOS = [
    "operacion",
    "tipo_de_comprobante",
    "serie",
    "numero",
    "fecha_de_emision",
    "total_gravada",
    "total_igv",
    "total",
    "condiciones_de_pago",
]

_RE_FECHA    = re.compile(r'^\d{2}-\d{2}-\d{4}$')
_RE_SERIE    = re.compile(r'^[A-Z]\d{3}$', re.IGNORECASE)
_RE_ITEM     = re.compile(r'^item\|')


def _parsear(contenido: str) -> dict:
    """Convierte el TXT en dict {campo: valor}."""
    resultado = {}
    for linea in contenido.split("\n"):
        linea = linea.strip()
        if not linea or not "|" in linea:
            continue
        partes = linea.split("|")
        if len(partes) >= 2:
            resultado[partes[0].strip()] = partes[1].strip()
    return resultado


def _validar_campos_obligatorios(campos: dict) -> list:
    errores = []
    for campo in _CAMPOS_OBLIGATORIOS:
        if campo not in campos or not campos[campo]:
            errores.append(f"Campo obligatorio ausente o vacio: '{campo}'")
    return errores


def _validar_fecha(campos: dict) -> list:
    fecha = campos.get("fecha_de_emision", "")
    if fecha and not _RE_FECHA.match(fecha):
        return [f"Fecha invalida '{fecha}' — formato esperado: DD-MM-YYYY"]
    return []


def _validar_serie(campos: dict) -> list:
    serie = campos.get("serie", "")
    if serie and not _RE_SERIE.match(serie):
        return [f"Serie invalida '{serie}' — formato esperado: B001, F001, etc."]
    return []


def _validar_numero(campos: dict) -> list:
    numero = campos.get("numero", "")
    if numero and not numero.isdigit():
        return [f"Numero de comprobante invalido: '{numero}'"]
    return []


def _validar_tipo(campos: dict) -> list:
    tipo = campos.get("tipo_de_comprobante", "")
    if tipo and tipo not in ("1", "2", "3"):
        return [f"Tipo de comprobante invalido: '{tipo}' — esperado 1 (factura), 2 (boleta) o 3 (nota credito/debito)"]
    return []


def _validar_totales(campos: dict) -> list:
    errores = []
    def _dec(campo):
        try:
            return Decimal(campos.get(campo, "0") or "0")
        except InvalidOperation:
            errores.append(f"Valor numerico invalido en '{campo}': '{campos.get(campo)}'")
            return Decimal("0")

    gravada   = _dec("total_gravada")
    exonerada = _dec("total_exonerada")
    igv       = _dec("total_igv")
    total     = _dec("total")

    if not errores:
        calculado = gravada + exonerada + igv
        diferencia = abs(calculado - total)
        if diferencia > Decimal("0.05"):
            errores.append(
                f"Totales inconsistentes: gravada({gravada}) + exonerada({exonerada}) "
                f"+ igv({igv}) = {calculado} ≠ total({total})")
    return errores


def _validar_items(contenido: str) -> list:
    errores = []
    lineas_item = [l for l in contenido.split("\n") if _RE_ITEM.match(l.strip())]

    if not lineas_item:
        return ["El comprobante no tiene items"]

    for i, linea in enumerate(lineas_item, 1):
        partes = linea.split("|")
        if len(partes) < 13:
            errores.append(f"Item {i}: linea con formato incorrecto ({len(partes)} campos, esperado >= 13)")
            continue

        unidad      = partes[1].strip()
        descripcion = partes[3].strip()
        afectacion  = partes[9].strip()

        if unidad not in ("NIU", "ZZ"):
            errores.append(f"Item {i}: unidad invalida '{unidad}' — esperado NIU o ZZ")

        if not descripcion:
            errores.append(f"Item {i}: descripcion vacia")

        if afectacion not in ("10", "20", "30", "40"):
            errores.append(f"Item {i}: afectacion IGV invalida '{afectacion}' — esperado 10, 20, 30 o 40")

        # Verificar que los valores numericos sean validos
        for pos, nombre in [(5, "precio_sin_igv"), (6, "precio_con_igv"),
                             (8, "subtotal"), (10, "igv"), (11, "total")]:
            try:
                Decimal(partes[pos].strip())
            except (InvalidOperation, IndexError):
                errores.append(f"Item {i}: valor invalido en '{nombre}': '{partes[pos] if pos < len(partes) else 'ausente'}'")

    return errores


def _validar_condiciones_pago(campos: dict) -> list:
    cond = campos.get("condiciones_de_pago", "")
    if cond and cond not in ("Contado", "Credito"):
        return [f"Condicion de pago invalida: '{cond}' — esperado 'Contado' o 'Credito'"]
    return []


def validar_txt(contenido: str) -> list:
    """
    Valida el contenido TXT completo.
    Retorna lista de errores. Lista vacia = valido.
    """
    if not contenido or not contenido.strip():
        return ["El contenido del TXT esta vacio"]

    campos  = _parsear(contenido)
    errores = []

    errores += _validar_campos_obligatorios(campos)
    errores += _validar_tipo(campos)
    errores += _validar_serie(campos)
    errores += _validar_numero(campos)
    errores += _validar_fecha(campos)
    errores += _validar_totales(campos)
    errores += _validar_condiciones_pago(campos)
    errores += _validar_items(contenido)

    return errores


def txt_es_valido(contenido: str) -> tuple[bool, list]:
    """
    Retorna (es_valido, lista_de_errores).
    Conveniente para usar en monitor.py.
    """
    errores = validar_txt(contenido)
    return len(errores) == 0, errores
