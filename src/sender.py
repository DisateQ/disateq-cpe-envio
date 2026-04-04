"""
sender.py
=========
Envio de comprobantes a APIFAS (API para DisateQ).

Manejo de red:
  - Reintentos automaticos con backoff exponencial
  - Timeout configurable
  - Excepciones tipadas para cada tipo de fallo
"""

import time
import requests
import logging
from exceptions import ConexionError, RespuestaError
from exceptions import TimeoutError as CPETimeoutError

log = logging.getLogger(__name__)

TIMEOUT        = 30    # segundos por intento
MAX_REINTENTOS = 3     # intentos totales
BACKOFF_BASE   = 5     # segundos de espera inicial entre reintentos

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


def _con_reintentos(fn, nombre: str):
    """
    Ejecuta fn() con reintentos y backoff exponencial.
    fn debe lanzar ConexionError o CPETimeoutError para reintentar.
    RespuestaError no se reintenta — es un rechazo definitivo de APIFAS.
    """
    ultimo_error = None
    for intento in range(1, MAX_REINTENTOS + 1):
        try:
            return fn()
        except RespuestaError:
            raise  # No reintentar rechazos definitivos
        except (ConexionError, CPETimeoutError) as e:
            ultimo_error = e
            if intento < MAX_REINTENTOS:
                espera = BACKOFF_BASE * (2 ** (intento - 1))  # 5s, 10s, 20s
                log.warning(
                    f"Intento {intento}/{MAX_REINTENTOS} fallido para {nombre}: {e}. "
                    f"Reintentando en {espera}s...")
                time.sleep(espera)
            else:
                log.error(f"Todos los reintentos agotados para {nombre}: {e}")
    raise ultimo_error


def enviar_txt(nombre: str, contenido: str, ruc: str, url: str) -> tuple[bool, str]:
    """
    Envia TXT a APIFAS con reintentos automaticos.
    Retorna (exito, mensaje).
    """
    contenido_limpio = contenido.replace("\r\n", "").replace("\n", "").replace("\r", "")
    headers = {"Texto": contenido_limpio, "Ruc": ruc, "Nombre": nombre}

    def _enviar():
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

    try:
        return _con_reintentos(_enviar, nombre)
    except RespuestaError as e:
        return False, e.respuesta
    except (ConexionError, CPETimeoutError) as e:
        return False, str(e)


def enviar_json(payload: dict, ruc: str, url: str, api_key: str = "") -> tuple[bool, str]:
    """
    Envia JSON a APIFAS con reintentos automaticos.
    Retorna (exito, mensaje).
    """
    headers = {"Content-Type": "application/json", "Ruc": ruc}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    def _enviar():
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

    try:
        return _con_reintentos(_enviar, "json")
    except RespuestaError as e:
        return False, e.respuesta
    except (ConexionError, CPETimeoutError) as e:
        return False, str(e)
