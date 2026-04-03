"""
monitor.py
==========
Orquestador del ciclo de envio de CPE.

Principios SOLID:
  S — Orquesta el flujo. La logica de cada paso esta en su modulo.
  O — Agregar nuevo paso (ej: notificacion) no modifica _procesar_comprobante.
  D — Depende de interfaces (funciones importadas), no instancia nada directamente.

Manejo de errores:
  Captura excepciones TIPADAS de cada capa y las reporta con contexto preciso.
  Nunca silencia errores con except Exception generico sin loguear.
"""

import time
import logging
import threading
import queue
from datetime import date
from pathlib import Path

from dbf_reader   import leer_pendientes, leer_productos, leer_detalles, verificar_rutas
from normalizer   import normalizar, _safe_str
from txt_generator import generar_txt, guardar_txt
from sender       import enviar_txt, enviar_json, verificar_conexion
from report       import generar_reporte
from correlativo_store import ya_procesado, marcar_enviado
from txt_validator import txt_es_valido
from exceptions   import (
    CPEError, DBFError, DBFNotFound, DBFCorrupto,
    GeneracionError, EnvioError, ConexionError, RespuestaError
)

log = logging.getLogger(__name__)

INTERVALO_BOLETA   = 300   # 5 min entre ciclos automaticos de boletas
INTERVALO_CHECK    = 10    # revision cada 10 segundos
LOTE_MAXIMO        = 20    # max comprobantes por ciclo
DELAY_ENTRE_ENVIOS = 0.3   # segundos entre envios para no saturar APIFAS


def _es_factura(serie: str) -> bool:
    return str(serie).upper().startswith("F")


class Monitor:
    """
    Orquesta el ciclo completo:
      leer DBF → filtrar → normalizar → generar → enviar → registrar
    """

    def __init__(self, cfg, gui_queue: queue.Queue = None):
        self.cfg             = cfg
        self.queue           = gui_queue
        self.stop            = threading.Event()
        self._ultimo_boleta  = 0
        self._ultimo_reporte = date.today()

    # ── Comunicacion con GUI ─────────────────────────────────

    def _emit(self, msg: dict):
        if self.queue:
            self.queue.put(msg)

    def _log(self, msg: str, tag: str = "info"):
        log.info(msg)
        self._emit({"tipo": "log", "msg": msg, "tag": tag})

    # ── Procesamiento de un comprobante ──────────────────────

    def _procesar_comprobante(self, envio: dict, detalles_idx: dict):
        """
        Procesa un comprobante completo: normalizar → generar → enviar.
        Captura excepciones tipadas y reporta con contexto preciso.
        """
        tipo      = _safe_str(envio.get("TIPO_FACTU"), "B")
        serie     = _safe_str(envio.get("SERIE_FACT"), "001").zfill(3)
        numero    = _safe_str(envio.get("NUMERO_FAC"), "0")
        serie_fmt = f"{tipo}{serie}"
        cpe_tipo  = "FACTURA" if tipo == "F" else "BOLETA"
        ruc       = self.cfg.get("EMPRESA", "ruc")
        nombre_arc = f"{ruc}-02-{serie_fmt}-{numero.zfill(8)}.txt"

        items = detalles_idx.get((tipo, serie, numero), [])
        if not items:
            self._log(f"SIN DETALLE  [{cpe_tipo}]  {nombre_arc}", "warn")
            self._emit({"tipo": "evento", "estado": "sin_detalle",
                        "nombre": nombre_arc, "cpe_tipo": cpe_tipo,
                        "msg": "Sin items en detalleventa.dbf"})
            return

        # Normalizar
        try:
            comp = normalizar(envio, items)
        except Exception as e:
            self._log(f"ERROR normalizando {nombre_arc}: {e}", "error")
            return

        razon_social = self.cfg.get("EMPRESA", "razon_social")
        modo         = self.cfg.get("ENVIO", "modo", fallback="legacy")
        url_envio    = self.cfg.get("ENVIO", "url_envio")
        salida       = self.cfg.get("RUTAS", "salida_txt")

        Path(salida).mkdir(parents=True, exist_ok=True)

        # Generar TXT
        try:
            nombre, contenido = generar_txt(comp, ruc, razon_social)
            guardar_txt(nombre, contenido, salida)
            # Validar TXT antes de enviar
            valido, errores_txt = txt_es_valido(contenido)
            if not valido:
                resumen = "; ".join(errores_txt[:3])
                self._log(f"TXT INVALIDO {nombre}: {resumen}", "error")
                self._emit({"tipo": "evento", "estado": "error",
                            "nombre": nombre, "cpe_tipo": cpe_tipo,
                            "msg": f"TXT invalido: {resumen}"})
                self._mover_txt(salida, nombre, "legacy", destino="errores")
                return
        except GeneracionError as e:
            self._log(f"ERROR generando {nombre_arc}: {e}", "error")
            self._emit({"tipo": "evento", "estado": "error",
                        "nombre": nombre_arc, "cpe_tipo": cpe_tipo,
                        "msg": str(e)})
            return

        # Enviar a APIFAS
        try:
            exito, msg = enviar_txt(nombre, contenido, ruc, url_envio)

        except ConexionError as e:
            self._log(f"SIN CONEXION — {nombre}: {e}", "error")
            self._emit({"tipo": "evento", "estado": "error",
                        "nombre": nombre, "cpe_tipo": cpe_tipo,
                        "msg": "Sin conexión a APIFAS"})
            self._mover_txt(salida, nombre, modo, destino="errores")
            return

        except RespuestaError as e:
            self._log(f"APIFAS rechazo {nombre}: {e.respuesta}", "error")
            self._emit({"tipo": "evento", "estado": "error",
                        "nombre": nombre, "cpe_tipo": cpe_tipo,
                        "msg": e.respuesta})
            self._mover_txt(salida, nombre, "legacy", destino="errores")
            return

        except EnvioError as e:
            self._log(f"ERROR envio {nombre}: {e}", "error")
            self._emit({"tipo": "evento", "estado": "error",
                        "nombre": nombre, "cpe_tipo": cpe_tipo,
                        "msg": str(e)})
            self._mover_txt(salida, nombre, modo, destino="errores")
            return

        # Exito
        self._mover_txt(salida, nombre, "legacy", destino="enviados")
        try:
            marcar_enviado(salida, serie_fmt, int(numero))
        except Exception:
            pass
        self._emit({"tipo": "evento", "estado": "enviado",
                    "nombre": nombre, "cpe_tipo": cpe_tipo, "msg": msg})

        time.sleep(DELAY_ENTRE_ENVIOS)

    def _mover_txt(self, salida: str, nombre: str, modo: str, destino: str):
        """Mueve el TXT generado a enviados/ o errores/."""
        if modo != "legacy":
            return
        try:
            src = Path(salida) / nombre
            dst = Path(salida) / destino
            dst.mkdir(exist_ok=True)
            if src.exists():
                src.rename(dst / nombre)
        except Exception as e:
            log.warning(f"No se pudo mover {nombre} a {destino}/: {e}")

    # ── Ciclo principal ──────────────────────────────────────

    def _ciclo(self, forzar_boletas: bool = False):
        ruta_data = self.cfg.get("RUTAS", "data_dbf")
        salida    = self.cfg.get("RUTAS", "salida_txt")
        url_envio = self.cfg.get("ENVIO", "url_envio")

        # Verificar rutas antes de intentar leer
        ok, msg_v = verificar_rutas(ruta_data)
        if not ok:
            self._log(f"ERROR rutas DBF: {msg_v}", "error")
            self._emit({"tipo": "conexion", "ok": False})
            return

        # Verificar conexion a APIFAS
        self._emit({"tipo": "conexion", "ok": verificar_conexion(url_envio)})

        # Leer DBF con manejo especifico por tipo de error
        try:
            pendientes = leer_pendientes(ruta_data)
            productos  = leer_productos(ruta_data)
            detalles   = leer_detalles(ruta_data, productos)

        except DBFNotFound as e:
            self._log(f"ARCHIVO NO ENCONTRADO: {e}", "error")
            return

        except DBFCorrupto as e:
            self._log(
                f"ARCHIVO CORRUPTO O BLOQUEADO: {e.archivo}\n"
                f"  Causa: {e.causa}\n"
                f"  Posibles soluciones:\n"
                f"  — Verificar que el sistema de farmacia no este usando el archivo\n"
                f"  — Restaurar desde backup si el archivo esta danado", "error")
            return

        except DBFError as e:
            self._log(f"ERROR DBF: {e}", "error")
            return

        # Filtrar ya procesados
        def _no_procesado(p):
            tipo      = _safe_str(p.get("TIPO_FACTU"), "B")
            serie     = _safe_str(p.get("SERIE_FACT"), "001").zfill(3)
            serie_fmt = f"{tipo}{serie}"
            try:
                numero = int(_safe_str(p.get("NUMERO_FAC"), "0"))
            except ValueError:
                return True
            return not ya_procesado(salida, serie_fmt, numero)

        pendientes = [p for p in pendientes if _no_procesado(p)]
        facturas   = [p for p in pendientes if _es_factura(str(p.get("SERIE_FACT", "")))]
        boletas    = [p for p in pendientes if not _es_factura(str(p.get("SERIE_FACT", "")))]

        total = len(facturas) + len(boletas)
        if total == 0:
            self._log("Sin comprobantes pendientes.", "info")
            self._emit({"tipo": "contadores", "pendientes": 0})
            return

        self._log(
            f"Pendientes: {total}  [{len(facturas)} facturas / {len(boletas)} boletas]"
            f"  — lote de hasta {LOTE_MAXIMO}", "info")

        # Facturas: siempre inmediato
        for envio in facturas[:LOTE_MAXIMO]:
            if self.stop.is_set():
                return
            self._procesar_comprobante(envio, detalles)

        # Boletas: timer o forzado
        ahora = time.time()
        if boletas:
            if forzar_boletas or (ahora - self._ultimo_boleta) >= INTERVALO_BOLETA:
                lote = boletas[:LOTE_MAXIMO]
                resto = len(boletas) - len(lote)
                self._log(
                    f"Enviando {len(lote)} boleta(s)"
                    + (f" — quedan {resto} para el siguiente ciclo" if resto else ""), "info")
                for envio in lote:
                    if self.stop.is_set():
                        return
                    self._procesar_comprobante(envio, detalles)
                self._ultimo_boleta = ahora
            else:
                resta = int(INTERVALO_BOLETA - (ahora - self._ultimo_boleta))
                self._log(f"{len(boletas)} boleta(s) — proximo ciclo en {resta}s", "info")

        # Actualizar contador
        try:
            self._emit({"tipo": "contadores",
                        "pendientes": len(leer_pendientes(ruta_data))})
        except DBFError:
            pass

        # Reporte diario
        hoy = date.today()
        if hoy != self._ultimo_reporte:
            try:
                rpt = generar_reporte(Path(salida))
                self._log(f"Reporte diario: {rpt.name}", "info")
            except Exception:
                pass
            self._ultimo_reporte = hoy

    def ciclo_manual(self):
        """Boton 'Enviar ahora' — fuerza boletas tambien."""
        self._ciclo(forzar_boletas=True)

    def iniciar(self):
        self._log("Monitor iniciado — ciclo automatico activo", "info")
        while not self.stop.is_set():
            try:
                self._ciclo(forzar_boletas=False)
            except Exception as e:
                # Captura residual — no deberia llegar aqui si los modulos
                # manejan sus propias excepciones correctamente
                self._log(f"Error inesperado en ciclo: {type(e).__name__}: {e}", "error")
            self.stop.wait(INTERVALO_CHECK)

    def detener(self):
        self.stop.set()
