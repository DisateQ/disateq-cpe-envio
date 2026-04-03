"""
sender.py
=========
Envio de comprobantes a APIFAS (API para DisateQ).

Principios SOLID:
  S — Solo responsabilidad: enviar. No genera, no lee DBF.
  O — Agregar nuevo tipo de envio (ej: SFTP) no modifica las funciones existentes.
  D — Depende de strings/dicts, no de modulos concretos.

Excepciones que puede lanzar:
  ConexionError  — sin red o APIFAS inaccesible
  TimeoutError   — APIFAS no respondio a tiempo
  RespuestaError — APIFAS respondio con error
"""

import requests
import logging
from exceptions import ConexionError, RespuestaError
from exceptions import TimeoutError as CPETimeoutError

log = logging.getLogger(__name__)

TIMEOUT = 30

# Fragmentos de respuesta que APIFAS considera exito
_RESPUESTAS_OK = [
    "proceso-aceptado",
    "es un comprobante repetido",
    "por anular",
]


def verificar_conexion(url: str) -> bool:
    """Retorna True si APIFAS esta accesible. No lanza excepciones."""
    try:
        requests.get(url, timeout=5)
        return True
    except Exception:
        return False


def _es_ok(texto: str) -> bool:
    t = texto.lower().strip()
    return any(r in t for r in _RESPUESTAS_OK)


def enviar_txt(nombre: str, contenido: str, ruc: str, url: str) -> tuple[bool, str]:
    """
    Envia TXT a APIFAS via headers HTTP.
    Retorna (exito, mensaje).
    Lanza ConexionError, CPETimeoutError o RespuestaError segun el fallo.
    """
    contenido_limpio = contenido.replace("\r\n", "").replace("\n", "").replace("\r", "")
    headers = {"Texto": contenido_limpio, "Ruc": ruc, "Nombre": nombre}

    try:
        resp = requests.post(url, headers=headers, timeout=TIMEOUT)
    except requests.exceptions.ConnectionError:
        raise ConexionError(url)
    except requests.exceptions.Timeout:
        raise CPETimeoutError(nombre, TIMEOUT)
    except Exception as e:
        raise ConexionError(url) from e

    msg = resp.text.strip() if resp.text else ""

    if resp.status_code == 200 and _es_ok(msg):
        return True, msg

    raise RespuestaError(nombre, msg or f"HTTP {resp.status_code}")


def enviar_json(payload: dict, ruc: str, url: str, api_key: str = "") -> tuple[bool, str]:
    """
    Envia JSON a APIFAS.
    Retorna (exito, mensaje).
    Lanza ConexionError, CPETimeoutError o RespuestaError segun el fallo.
    """
    headers = {"Content-Type": "application/json", "Ruc": ruc}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
    except requests.exceptions.ConnectionError:
        raise ConexionError(url)
    except requests.exceptions.Timeout:
        raise CPETimeoutError("json", TIMEOUT)
    except Exception as e:
        raise ConexionError(url) from e

    if resp.status_code in (200, 201):
        try:
            data = resp.json()
            msg  = data.get("mensaje", data.get("message", resp.text[:100]))
        except Exception:
            msg = resp.text[:100]
        return True, msg

    raise RespuestaError("json", f"HTTP {resp.status_code}: {resp.text[:100]}")
