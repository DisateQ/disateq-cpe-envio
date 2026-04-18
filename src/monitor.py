"""
monitor.py
==========
Orquestador del ciclo de envio de CPE.

Principios SOLID:
  S — Orquesta el flujo. La logica de cada paso esta en su modulo.
  O — Agregar nuevo paso no modifica _procesar_comprobante.
  D — Depende de interfaces (dispatcher), no de implementaciones concretas.

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

from normalizer    import normalizar, _safe_str
from txt_generator import generar_txt, guardar_txt
from sender        import enviar_txt, verificar_conexion
from report        import generar_reporte
from correlativo_store import ya_procesado, marcar_enviado
from txt_validator import txt_es_valido
from adapters.dispatcher import get_adapter
from adapters.base_adapter import AdapterError
from exceptions import (
    CPEError, DBFError, DBFNotFound, DBFCorrupto,
    GeneracionError, EnvioError, ConexionError, RespuestaError
)

log = logging.getLogger(__name__)

INTERVALO_BOLETA   = 1800  # 30 min entre ciclos automaticos de boletas
INTERVALO_CHECK    = 10    # revision cada 10 segundos
LOTE_MAXIMO        = 20    # max comprobantes por ciclo
DELAY_ENTRE_ENVIOS = 0.3   # segundos entre envios para no saturar APIFAS


def _es_factura(serie: str) -> bool:
    return str(serie).upper().startswith("F")


def _cpe_tipo(tipo: str, serie_fmt: str) -> str:
    tipo_upper = tipo.upper()
    if tipo_upper in ("N", "NC") or serie_fmt.upper().startswith(("FC", "NC", "BC")):
        return "NOTA CREDITO"
    if tipo_upper in ("D", "ND") or serie_fmt.upper().startswith(("FD", "ND", "BD")):
        return "NOTA DEBITO"
    if tipo_upper == "F" or serie_fmt.upper().startswith("F"):
        return "FACTURA"
    return "BOLETA"


class Monitor:
    """
    Orquesta el ciclo completo:
      Adaptador (DBF/xlsx/SQL) → normalizar → generar → enviar → registrar
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
        cpe_tipo  = _cpe_tipo(tipo, serie_fmt)
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
                        "msg": "Sin conexion a APIFAS"})
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

        # Marcar FLAG_ENVIO=3 en DBF si la fuente es DBF
        fuente = self.cfg.get("FUENTE", "tipo", fallback="dbf").lower()
        if fuente == "dbf":
            try:
                from dbf_reader import marcar_enviado_dbf
                ruta_data = self.cfg.get("RUTAS", "data_dbf")
                marcar_enviado_dbf(ruta_data, tipo, serie, numero)
            except Exception as e:
                log.warning(f"No se pudo marcar FLAG_ENVIO en DBF: {e}")

        monto_enviado = float(comp["totales"]["total"])
        tipo_doc_env  = comp.get("tipo_doc", "03")
        self._emit({"tipo": "evento", "estado": "enviado",
                    "nombre": nombre, "cpe_tipo": cpe_tipo, "msg": msg,
                    "monto": monto_enviado, "tipo_doc": tipo_doc_env})

        time.sleep(DELAY_ENTRE_ENVIOS)

    def _mover_txt(self, salida: str, nombre: str, modo: str, destino: str):
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

    def _ciclo(self, forzar_boletas: bool = False, verbose: bool = False):
        salida    = self.cfg.get("RUTAS", "salida_txt")
        url_envio = self.cfg.get("ENVIO", "url_envio")
        fuente    = self.cfg.get("FUENTE", "tipo", fallback="dbf").lower()

        # Verificar conexion a APIFAS
        self._emit({"tipo": "conexion", "ok": verificar_conexion(url_envio)})

        # Obtener adaptador segun fuente configurada
        try:
            adapter = get_adapter(self.cfg)
        except AdapterError as e:
            self._log(f"ERROR adaptador: {e}", "error")
            return

        # Determinar ruta segun fuente
        if fuente == "dbf":
            ruta = self.cfg.get("RUTAS", "data_dbf")
        elif fuente == "xlsx":
            ruta = self.cfg.get("FUENTE", "ruta_xlsx")
        else:
            ruta = self.cfg.get("FUENTE", "cadena_sql", fallback="")

        # Leer pendientes desde el adaptador
        try:
            resultado = adapter.leer(ruta)
        except AdapterError as e:
            self._log(f"ERROR rutas {fuente.upper()}: {e}", "error")
            self._emit({"tipo": "conexion", "ok": False})
            return
        except Exception as e:
            self._log(f"ERROR inesperado en adaptador: {e}", "error")
            return

        if not resultado:
            if verbose:
                self._log("Sin comprobantes pendientes.", "info")
            self._emit({"tipo": "contadores", "pendientes": 0})
            return

        # Filtrar ya procesados (solo DBF)
        if fuente == "dbf":
            def _no_procesado(par):
                envio, _ = par
                tipo      = _safe_str(envio.get("TIPO_FACTU"), "B")
                serie     = _safe_str(envio.get("SERIE_FACT"), "001").zfill(3)
                serie_fmt = f"{tipo}{serie}"
                try:
                    numero = int(_safe_str(envio.get("NUMERO_FAC"), "0"))
                except ValueError:
                    return True
                return not ya_procesado(salida, serie_fmt, numero)
            resultado = [p for p in resultado if _no_procesado(p)]

        if not resultado:
            if verbose:
                self._log("Sin comprobantes pendientes.", "info")
            self._emit({"tipo": "contadores", "pendientes": 0})
            return

        # Construir detalles_idx
        detalles_idx = {}
        envios = []
        for envio, items in resultado:
            tipo   = _safe_str(envio.get("TIPO_FACTU"), "B")
            serie  = _safe_str(envio.get("SERIE_FACT"), "001").zfill(3)
            numero = _safe_str(envio.get("NUMERO_FAC"), "0")
            detalles_idx[(tipo, serie, numero)] = items
            envios.append(envio)

        facturas = [e for e in envios if _es_factura(_safe_str(e.get("SERIE_FACT", "")))]
        boletas  = [e for e in envios if not _es_factura(_safe_str(e.get("SERIE_FACT", "")))]
        total    = len(facturas) + len(boletas)

        self._log(
            f"Pendientes: {total}  [{len(facturas)} facturas / {len(boletas)} boletas]"
            f"  — lote de hasta {LOTE_MAXIMO}", "info")

        # Facturas: siempre inmediato
        for envio in facturas[:LOTE_MAXIMO]:
            if self.stop.is_set():
                return
            self._procesar_comprobante(envio, detalles_idx)

        # Boletas: timer o forzado
        ahora = time.time()
        if boletas:
            if forzar_boletas or (ahora - self._ultimo_boleta) >= INTERVALO_BOLETA:
                lote  = boletas[:LOTE_MAXIMO]
                resto = len(boletas) - len(lote)
                self._log(
                    f"Enviando {len(lote)} boleta(s)"
                    + (f" — quedan {resto} para el siguiente ciclo" if resto else ""), "info")
                for envio in lote:
                    if self.stop.is_set():
                        return
                    self._procesar_comprobante(envio, detalles_idx)
                self._ultimo_boleta = ahora
            else:
                resta = int(INTERVALO_BOLETA - (ahora - self._ultimo_boleta))
                self._log(f"{len(boletas)} boleta(s) — proximo ciclo en {resta}s", "info")

        self._emit({"tipo": "contadores", "pendientes": total})

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
        self._ciclo(forzar_boletas=True, verbose=True)

    def iniciar(self):
        self._log("Monitor iniciado — ciclo automatico activo", "info")
        while not self.stop.is_set():
            try:
                self._ciclo(forzar_boletas=False)
            except Exception as e:
                self._log(f"Error inesperado en ciclo: {type(e).__name__}: {e}", "error")
            self.stop.wait(INTERVALO_CHECK)

    def detener(self):
        self.stop.set()