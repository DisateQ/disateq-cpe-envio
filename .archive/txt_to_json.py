"""
txt_to_json.py
==============
Conversor de TXT (formato APIFAS) a JSON (formato DisateQ Plataforma CPE).

ESTADO: Preparado — pendiente de integracion con DisateQ Plataforma CPE.

Principios SOLID:
  S — Responsabilidad unica: convertir formato TXT a JSON. Nada mas.
  O — La estructura JSON de destino puede extenderse sin modificar el parser.
  D — No depende del DBF ni de APIFAS. Opera solo sobre el TXT ya generado.

Flujo futuro:
  TXT guardado en enviados/ → convertir a JSON → enviar a DisateQ Plataforma CPE

Uso (cuando este disponible):
  from txt_to_json import txt_a_json, convertir_archivo
  payload = txt_a_json(contenido_txt, ruc_emisor, razon_social)
  # POST payload a https://api.disateq.com/v1/cpe
"""

import re
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path


# ── Parser del TXT ────────────────────────────────────────────

def _parsear_campos(contenido: str) -> dict:
    """Extrae los campos clave=valor del TXT."""
    campos = {}
    for linea in contenido.split("\n"):
        linea = linea.strip()
        if not linea or "|" not in linea or linea.startswith("item|"):
            continue
        partes = linea.split("|")
        if len(partes) >= 2:
            campos[partes[0].strip()] = partes[1].strip()
    return campos


def _parsear_items(contenido: str) -> list:
    """Extrae los items del TXT."""
    items = []
    for linea in contenido.split("\n"):
        linea = linea.strip()
        if not linea.startswith("item|"):
            continue
        p = linea.split("|")
        if len(p) < 13:
            continue
        try:
            items.append({
                "unidad":         p[1].strip(),
                "codigo":         p[2].strip(),
                "descripcion":    p[3].strip(),
                "cantidad":       float(p[4].strip() or "0"),
                "precio_sin_igv": float(p[5].strip() or "0"),
                "precio_con_igv": float(p[6].strip() or "0"),
                "subtotal":       float(p[8].strip() or "0"),
                "afectacion_igv": p[9].strip(),
                "igv":            float(p[10].strip() or "0"),
                "total":          float(p[11].strip() or "0"),
                "unspsc":         p[14].strip() if len(p) > 14 else "10000000",
            })
        except (ValueError, IndexError):
            continue
    return items


def _safe_decimal(valor: str) -> float:
    try:
        return float(Decimal(valor or "0"))
    except (InvalidOperation, TypeError):
        return 0.0


def _fecha_iso(fecha_ddmmyyyy: str) -> str:
    """Convierte DD-MM-YYYY a YYYY-MM-DD."""
    try:
        d, m, a = fecha_ddmmyyyy.split("-")
        return f"{a}-{m}-{d}"
    except Exception:
        return fecha_ddmmyyyy


def _doc_referencia(campos: dict) -> dict | None:
    """Extrae datos del documento original si es nota de credito/debito."""
    tipo   = campos.get("documento_que_se_modifica_tipo",   "").strip()
    serie  = campos.get("documento_que_se_modifica_serie",  "").strip()
    numero = campos.get("documento_que_se_modifica_numero", "").strip()
    nc     = campos.get("tipo_de_nota_de_credito", "").strip()
    nd     = campos.get("tipo_de_nota_de_debito",  "").strip()

    if not (tipo and serie and numero):
        return None

    return {
        "tipo_doc":          tipo,
        "serie":             serie,
        "numero":            numero,
        "tipo_nota_credito": nc or None,
        "tipo_nota_debito":  nd or None,
    }


# ── Conversor principal ───────────────────────────────────────

def txt_a_json(contenido_txt: str, ruc_emisor: str, razon_social: str) -> dict:
    """
    Convierte el contenido de un TXT APIFAS al formato JSON
    de DisateQ Plataforma CPE.
    Retorna dict listo para serializar y enviar a api.disateq.com/v1/cpe.

    Raises ValueError si el TXT no tiene los campos minimos necesarios.
    """
    campos = _parsear_campos(contenido_txt)
    items  = _parsear_items(contenido_txt)

    campos_requeridos = ["serie", "numero", "fecha_de_emision",
                         "tipo_de_comprobante", "total"]
    faltantes = [c for c in campos_requeridos if not campos.get(c)]
    if faltantes:
        raise ValueError(f"TXT incompleto — faltan campos: {', '.join(faltantes)}")

    if not items:
        raise ValueError("TXT sin items — no se puede convertir")

    tipo_doc_map = {"1": "01", "2": "03"}
    tipo_doc = tipo_doc_map.get(campos.get("tipo_de_comprobante", "2"), "03")

    payload = {
        "version": "1.0",
        "emisor": {
            "ruc":          ruc_emisor,
            "razon_social": razon_social,
        },
        "comprobante": {
            "tipo_doc":      tipo_doc,
            "serie":         campos.get("serie", ""),
            "numero":        int(campos.get("numero", "0")),
            "fecha_emision": _fecha_iso(campos.get("fecha_de_emision", "")),
            "moneda":        "PEN" if campos.get("moneda", "1") == "1" else "USD",
            "forma_pago":    campos.get("condiciones_de_pago", "Contado"),
        },
        "cliente": {
            "tipo_doc":    campos.get("cliente_tipo_de_documento",   "-"),
            "numero_doc":  campos.get("cliente_numero_de_documento", "00000000"),
            "denominacion":campos.get("cliente_denominacion",        "CLIENTE VARIOS"),
            "direccion":   campos.get("cliente_direccion",           "-"),
        },
        "totales": {
            "gravada":   _safe_decimal(campos.get("total_gravada",   "0")),
            "exonerada": _safe_decimal(campos.get("total_exonerada", "0")),
            "inafecta":  _safe_decimal(campos.get("total_inafecta",  "0")),
            "igv":       _safe_decimal(campos.get("total_igv",       "0")),
            "icbper":    _safe_decimal(campos.get("total_impuestos_bolsas", "0")),
            "total":     _safe_decimal(campos.get("total",           "0")),
        },
        "items": items,
        "documento_referencia": _doc_referencia(campos),
    }

    return payload


# ── Utilidades de archivo ─────────────────────────────────────

def convertir_archivo(ruta_txt: Path, ruc: str, razon_social: str) -> dict:
    """Lee un TXT y retorna el payload JSON para DisateQ Plataforma CPE."""
    contenido = ruta_txt.read_text(encoding="latin-1")
    return txt_a_json(contenido, ruc, razon_social)


def convertir_carpeta(
    carpeta: Path,
    ruc: str,
    razon_social: str,
    carpeta_json: Path = None
) -> tuple[int, int]:
    """
    Convierte todos los TXT de una carpeta a JSON.
    Si carpeta_json es None, guarda junto al TXT original.
    Retorna (convertidos, errores).
    """
    if carpeta_json:
        carpeta_json.mkdir(parents=True, exist_ok=True)

    convertidos = errores = 0

    for ruta_txt in carpeta.glob("*.txt"):
        destino = (carpeta_json or carpeta) / ruta_txt.with_suffix(".json").name
        try:
            payload  = convertir_archivo(ruta_txt, ruc, razon_social)
            json_str = json.dumps(payload, ensure_ascii=False, indent=2)
            destino.write_text(json_str, encoding="utf-8")
            convertidos += 1
        except Exception:
            errores += 1

    return convertidos, errores
