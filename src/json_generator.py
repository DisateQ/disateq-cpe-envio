"""
json_generator.py
=================
Genera payload JSON normalizado a partir de la estructura interna.
Modos: json (API DISATEQ) y ffee (Plataforma FFEE).
"""

import json
from decimal import Decimal
from pathlib import Path


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def generar_json(comprobante: dict, ruc: str, razon_social: str) -> tuple:
    c  = comprobante
    t  = c["totales"]
    cl = c["cliente"]

    nombre = f"{ruc}-02-{c['serie']}-{str(c['numero']).zfill(8)}.json"

    payload = {
        "emisor": {
            "ruc":          ruc,
            "razon_social": razon_social,
        },
        "comprobante": {
            "tipo_doc":       c["tipo_doc"],
            "serie":          c["serie"],
            "numero":         c["numero"],
            "fecha_emision":  c["fecha_iso"],
            "moneda":         c["moneda"],
            "forma_pago":     c["forma_pago"],
        },
        "cliente": {
            "tipo_doc":    cl["tipo_doc"],
            "numero_doc":  cl["numero_doc"],
            "denominacion":cl["denominacion"],
            "direccion":   cl["direccion"],
        },
        "totales": {
            "gravada":   float(t["gravada"]),
            "exonerada": float(t["exonerada"]),
            "inafecta":  float(t["inafecta"]),
            "igv":       float(t["igv"]),
            "icbper":    float(t["icbper"]),
            "total":     float(t["total"]),
        },
        "items": [
            {
                "codigo":          item["codigo"],
                "descripcion":     item["descripcion"],
                "unspsc":          item["unspsc"],
                "unidad":          item["unidad"],
                "cantidad":        item["cantidad"],
                "precio_unitario": float(item["precio_con_igv"]),
                "precio_sin_igv":  float(item["precio_sin_igv"]),
                "subtotal":        float(item["subtotal_sin_igv"]),
                "igv":             float(item["igv"]),
                "total":           float(item["total"]),
                "afectacion_igv":  item["afectacion_igv"],
            }
            for item in c["items"]
        ],
    }

    return nombre, payload


def payload_a_str(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, cls=DecimalEncoder)


def guardar_json(nombre: str, payload: dict, carpeta_salida: str) -> Path:
    ruta = Path(carpeta_salida) / nombre
    ruta.write_text(payload_a_str(payload), encoding="utf-8")
    return ruta
