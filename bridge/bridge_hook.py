"""
bridge_hook.py
==============
Conector motor → BridgeAPI — DisateQ Bridge™ | Etapa 2

Responsabilidad única:
    Notificar a la BridgeAPI cada vez que el motor procesa un comprobante.

Diseño:
    - NO bloquea al motor si BridgeAPI no está disponible
    - Cola en memoria + hilo background para envíos asíncronos
    - Reintento simple con backoff
    - Falla silenciosa con log: la facturación NO puede detenerse por el Bridge

Integración en monitor.py (una sola línea por evento):

    from bridge_hook import notificar_bridge

    # Tras envío exitoso:
    notificar_bridge(comp, nombre, exito=True,  msg="proceso-aceptado", ms=342)

    # Tras error:
    notificar_bridge(comp, nombre, exito=False, msg="Sin conexión",     ms=0)

Compatibilidad:
    Python 3.10+ | No requiere dependencias externas (solo requests, ya en requirements.txt)
"""

import json
import logging
import queue
import threading
import time
from datetime import datetime
from typing import Optional

import requests

log = logging.getLogger(__name__)

# ── Configuración ─────────────────────────────────────────────────────────────

BRIDGE_URL      = "http://localhost:8765"          # BridgeAPI local
ENDPOINT        = f"{BRIDGE_URL}/comprobantes/registrar"
TIMEOUT_SEG     = 5                                # timeout por intento (no bloquear motor)
MAX_REINTENTOS  = 3                                # intentos antes de descartar
BACKOFF_SEG     = 2                                # espera entre reintentos
COLA_MAX        = 500                              # máx. eventos en cola (evita memory leak)

# ── Estado del hook ───────────────────────────────────────────────────────────

_cola: queue.Queue = queue.Queue(maxsize=COLA_MAX)
_worker_activo     = False
_lock              = threading.Lock()


# ── API pública ───────────────────────────────────────────────────────────────

def notificar_bridge(
    comp:     dict,
    nombre:   str,
    exito:    bool,
    msg:      str = "",
    ms:       int = 0,
    url_envio: Optional[str] = None,
) -> None:
    """
    Notifica a BridgeAPI que el motor procesó un comprobante.
    Retorna inmediatamente — el envío ocurre en background.

    Args:
        comp:      dict normalizado del comprobante (salida de normalizar())
        nombre:    nombre del archivo TXT generado (ej: 10405206710-02-B001-00023171.txt)
        exito:     True si APIFAS aceptó el comprobante
        msg:       respuesta cruda de APIFAS (o mensaje de error)
        ms:        duración del envío en milisegundos
        url_envio: URL de APIFAS usada (opcional, para auditoría)
    """
    _asegurar_worker()

    payload = _construir_payload(comp, nombre, exito, msg, ms, url_envio)
    if payload is None:
        return  # error al construir — ya logueado

    try:
        _cola.put_nowait(payload)
    except queue.Full:
        log.warning("[bridge_hook] Cola llena — descartando notificación para %s", nombre)


def bridge_disponible() -> bool:
    """
    Verifica si BridgeAPI está activa. No lanza excepciones.
    Útil para mostrar indicador de estado en la GUI del motor.
    """
    try:
        r = requests.get(f"{BRIDGE_URL}/", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def flush_y_detener(timeout_seg: int = 10) -> None:
    """
    Espera a que la cola se vacíe y detiene el worker.
    Llamar al cerrar el motor para no perder notificaciones pendientes.
    """
    global _worker_activo
    log.info("[bridge_hook] Flushing cola (%d pendientes)...", _cola.qsize())
    deadline = time.time() + timeout_seg
    while not _cola.empty() and time.time() < deadline:
        time.sleep(0.2)
    with _lock:
        _worker_activo = False
    log.info("[bridge_hook] Worker detenido.")


# ── Construcción del payload ──────────────────────────────────────────────────

def _construir_payload(
    comp:     dict,
    nombre:   str,
    exito:    bool,
    msg:      str,
    ms:       int,
    url_envio: Optional[str],
) -> Optional[dict]:
    """
    Transforma el dict normalizado del motor al formato de RegistrarCPERequest.
    Retorna None si faltan campos mínimos.
    """
    try:
        cabecera = comp.get("cabecera", {})
        totales  = comp.get("totales",  {})
        cliente  = comp.get("cliente",  {})

        # Extraer serie y número del nombre del archivo
        # Formato: {RUC}-02-{SERIE}{NUM3}-{NUM8}.txt
        meta   = _parsear_nombre(nombre)
        ruc    = meta.get("ruc",    cabecera.get("ruc_emisor", ""))
        serie  = meta.get("serie",  cabecera.get("serie",      ""))
        numero = meta.get("numero", cabecera.get("numero",     0))

        # Validar RUC: 11 dígitos numéricos exactos
        ruc_str = str(ruc).strip()
        if not ruc_str.isdigit() or len(ruc_str) != 11:
            log.warning("[bridge_hook] RUC inválido '%s' para '%s' — descartado", ruc, nombre)
            return None

        # Validar serie no vacía
        if not str(serie).strip():
            log.warning("[bridge_hook] Serie vacía para '%s' — descartado", nombre)
            return None

        # Validar que el número sea entero
        try:
            numero = int(numero)
        except (TypeError, ValueError):
            log.warning("[bridge_hook] Número inválido '%s' para '%s' — descartado", numero, nombre)
            return None

        # Tipo comprobante: B=boleta, F=factura, NC=nota crédito
        tipo = "F" if serie.upper().startswith("F") else "B"

        # Fecha en YYYY-MM-DD
        fecha = _normalizar_fecha(cabecera.get("fecha_emision", ""))

        estado         = "enviado" if exito else "error"
        envio_resultado = "enviado" if exito else "error_respuesta"

        return {
            "nombre_archivo":       nombre,
            "ruc_emisor":           ruc,
            "razon_social":         cabecera.get("razon_social", ""),
            "tipo_comprobante":     tipo,
            "serie":                serie,
            "numero":               int(numero),
            "fecha_emision":        fecha,
            "cliente_tipo_doc":     cliente.get("tipo_doc",    "-"),
            "cliente_num_doc":      cliente.get("numero_doc",  "00000000"),
            "cliente_denominacion": cliente.get("denominacion","CLIENTE VARIOS"),
            "total_gravada":        float(totales.get("total_gravada",   0)),
            "total_exonerada":      float(totales.get("total_exonerada", 0)),
            "total_igv":            float(totales.get("total_igv",       0)),
            "total_icbper":         float(totales.get("total_icbper",    0)),
            "total":                float(totales.get("total",           0)),
            "forma_pago":           cabecera.get("forma_pago", "Contado"),
            "estado":               estado,
            "origen":               "dbf",
            "envio_resultado":      envio_resultado,
            "envio_respuesta_api":  msg[:500] if msg else None,
            "envio_duracion_ms":    ms,
            "envio_url":            url_envio,
        }

    except Exception as e:
        log.warning("[bridge_hook] Error construyendo payload para '%s': %s", nombre, e)
        return None


def _parsear_nombre(nombre: str) -> dict:
    """Extrae ruc, serie, numero del nombre del archivo TXT."""
    from pathlib import Path
    try:
        stem   = Path(nombre).stem           # sin .txt
        partes = stem.split("-")
        return {
            "ruc":    partes[0],
            "serie":  partes[2],             # B001 / F001
            "numero": int(partes[3]),
        }
    except Exception:
        return {}


def _normalizar_fecha(fecha: str) -> str:
    """
    Convierte fecha a YYYY-MM-DD.
    Acepta: DD-MM-YYYY (formato motor), YYYY-MM-DD, datetime.
    """
    if not fecha:
        return datetime.now().strftime("%Y-%m-%d")
    if isinstance(fecha, datetime):
        return fecha.strftime("%Y-%m-%d")
    fecha = str(fecha).strip()
    # DD-MM-YYYY → YYYY-MM-DD
    if len(fecha) == 10 and fecha[2] == "-" and fecha[5] == "-":
        try:
            d, m, a = fecha.split("-")
            return f"{a}-{m}-{d}"
        except Exception:
            pass
    # Ya en YYYY-MM-DD
    if len(fecha) >= 10:
        return fecha[:10]
    return datetime.now().strftime("%Y-%m-%d")


# ── Worker background ─────────────────────────────────────────────────────────

def _asegurar_worker() -> None:
    """Inicia el hilo worker si no está corriendo."""
    global _worker_activo
    with _lock:
        if not _worker_activo:
            _worker_activo = True
            t = threading.Thread(
                target=_worker_loop,
                name="bridge-hook-worker",
                daemon=True,   # muere con el proceso principal
            )
            t.start()
            log.info("[bridge_hook] Worker iniciado.")


def _worker_loop() -> None:
    """
    Loop del hilo background.
    Consume la cola y envía notificaciones a BridgeAPI con reintentos.
    """
    global _worker_activo
    log.debug("[bridge_hook] Worker loop corriendo.")

    while _worker_activo or not _cola.empty():
        try:
            payload = _cola.get(timeout=1.0)
        except queue.Empty:
            continue

        _enviar_con_reintentos(payload)
        _cola.task_done()

    log.debug("[bridge_hook] Worker loop terminado.")


def _enviar_con_reintentos(payload: dict) -> None:
    """
    Intenta enviar el payload a BridgeAPI.
    Si falla todos los reintentos, descarta y loguea warning.
    NUNCA lanza excepciones — el motor no puede verse afectado.
    """
    nombre = payload.get("nombre_archivo", "?")

    for intento in range(1, MAX_REINTENTOS + 1):
        try:
            resp = requests.post(
                ENDPOINT,
                json    = payload,
                timeout = TIMEOUT_SEG,
            )
            if resp.status_code in (200, 201):
                log.debug(
                    "[bridge_hook] ✅ %s notificado (intento %d)", nombre, intento
                )
                return
            else:
                log.warning(
                    "[bridge_hook] HTTP %d al notificar %s (intento %d)",
                    resp.status_code, nombre, intento,
                )

        except requests.exceptions.ConnectionError:
            log.debug(
                "[bridge_hook] BridgeAPI no disponible al notificar %s (intento %d)",
                nombre, intento,
            )
        except requests.exceptions.Timeout:
            log.warning(
                "[bridge_hook] Timeout al notificar %s (intento %d)", nombre, intento
            )
        except Exception as e:
            log.warning(
                "[bridge_hook] Error inesperado al notificar %s: %s", nombre, e
            )

        # Esperar antes del siguiente intento (excepto el último)
        if intento < MAX_REINTENTOS:
            time.sleep(BACKOFF_SEG)

    # Todos los intentos fallaron — descartar silenciosamente
    log.warning(
        "[bridge_hook] ⚠️  %s descartado tras %d intentos fallidos. "
        "BridgeAPI no disponible.",
        nombre, MAX_REINTENTOS,
    )


# ── Integración con monitor.py ────────────────────────────────────────────────
#
# En src/monitor.py, dentro de _procesar_uno(), después del bloque de envío:
#
#   ANTES (código actual):
#   ─────────────────────────────────────────────────────────
#   exito, msg = enviar_txt(nombre, contenido, ruc, url_envio)
#   if exito:
#       self._mover_txt(salida, nombre, modo, destino="enviados")
#       registrar_procesado(salida, serie_fmt, numero)
#       self._emit({...})
#   else:
#       self._mover_txt(salida, nombre, modo, destino="errores")
#       self._emit({...})
#
#   DESPUÉS (agregar 1 línea en cada rama):
#   ─────────────────────────────────────────────────────────
#   from bridge_hook import notificar_bridge   # ← al inicio del archivo
#
#   exito, msg = enviar_txt(nombre, contenido, ruc, url_envio)
#   if exito:
#       self._mover_txt(salida, nombre, modo, destino="enviados")
#       registrar_procesado(salida, serie_fmt, numero)
#       notificar_bridge(comp, nombre, exito=True,  msg=msg, ms=duracion_ms)  # ← NUEVA
#       self._emit({...})
#   else:
#       self._mover_txt(salida, nombre, modo, destino="errores")
#       notificar_bridge(comp, nombre, exito=False, msg=msg, ms=duracion_ms)  # ← NUEVA
#       self._emit({...})
#
#   # Al cerrar el motor (en main.py o gui.py):
#   from bridge_hook import flush_y_detener
#   flush_y_detener()
#
# ─────────────────────────────────────────────────────────────────────────────


# ── Entry point de prueba ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level  = logging.DEBUG,
        format = "%(asctime)s  %(levelname)-8s  %(message)s",
    )

    print("DisateQ Bridge™ — bridge_hook.py")
    print("=" * 50)

    # ── Modo 1: verificar disponibilidad
    if "--check" in sys.argv:
        ok = bridge_disponible()
        estado = "✅  ONLINE" if ok else "❌  OFFLINE"
        print(f"BridgeAPI {BRIDGE_URL}  →  {estado}")
        sys.exit(0 if ok else 1)

    # ── Modo 2: prueba de notificación real (BridgeAPI debe estar corriendo)
    print(f"Probando notificación hacia: {ENDPOINT}")
    print()

    # Simular el dict 'comp' que produce normalizar() en el motor
    comp_simulado = {
        "cabecera": {
            "ruc_emisor":   "10405206710",
            "razon_social": "FARMACIA DEL PUEBLO S.A.C.",
            "serie":        "B001",
            "numero":       23172,
            "fecha_emision":"10-04-2026",   # formato del motor: DD-MM-YYYY
            "forma_pago":   "Contado",
        },
        "cliente": {
            "tipo_doc":    "-",
            "numero_doc":  "00000000",
            "denominacion":"CLIENTE VARIOS",
        },
        "totales": {
            "total_gravada":   25.42,
            "total_exonerada": 0.0,
            "total_igv":       4.58,
            "total_icbper":    0.0,
            "total":           30.0,
        },
        "items": [],
    }

    nombre_txt = "10405206710-02-B001-00023172.txt"

    # Verificar disponibilidad primero
    if not bridge_disponible():
        print("⚠️  BridgeAPI no disponible en", BRIDGE_URL)
        print("   Para probar con BridgeAPI activa:")
        print("   1. uvicorn bridge_api:app --port 8765")
        print("   2. python bridge_hook.py")
        print()
        print("   Probando construcción de payload sin conexión...")
        payload = _construir_payload(
            comp_simulado, nombre_txt, exito=True,
            msg="proceso-aceptado", ms=312, url_envio=None
        )
        print()
        print("📦  Payload construido:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        print()
        print("✅  Construcción de payload OK (sin conexión a BridgeAPI)")
        sys.exit(0)

    # BridgeAPI disponible → notificar de verdad
    print("✅  BridgeAPI online. Enviando notificación...")
    notificar_bridge(
        comp_simulado, nombre_txt,
        exito=True, msg="proceso-aceptado", ms=312,
    )

    # Dar tiempo al worker
    time.sleep(2)

    print()
    print("✅  Notificación enviada. Verifica en:")
    print(f"   {BRIDGE_URL}/comprobantes")
    print(f"   {BRIDGE_URL}/log")
