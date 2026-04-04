"""
simulacion.py
=============
Servicio de simulacion de envios (modo dry-run).

Principios SOLID:
  S — Responsabilidad unica: simular sin enviar. Extraido de gui.py.
  D — No depende de la GUI. Retorna resultados via callback/queue.

Uso:
  from simulacion import SimulacionService
  svc = SimulacionService(cfg, queue)
  svc.ejecutar()
"""

import json
import logging
from pathlib import Path

from dbf_reader    import leer_pendientes, leer_productos, leer_detalles, verificar_rutas
from normalizer    import normalizar, _safe_str
from txt_generator import generar_txt
from json_generator import generar_json
from exceptions    import DBFNotFound, DBFCorrupto, DBFError

log = logging.getLogger(__name__)


class SimulacionService:
    """
    Procesa los DBF y muestra que se enviaria, sin llamar a APIFAS.
    Los resultados se emiten via gui_queue para que la GUI los muestre.
    """

    def __init__(self, cfg, gui_queue):
        self.cfg   = cfg
        self.queue = gui_queue

    def _emit(self, msg: str, tag: str = "info"):
        self.queue.put({"tipo": "log", "msg": msg, "tag": tag})

    def ejecutar(self):
        ruta_data = self.cfg.get("RUTAS", "data_dbf")
        ruc       = self.cfg.get("EMPRESA", "ruc")
        rs        = self.cfg.get("EMPRESA", "razon_social")
        modo      = self.cfg.get("ENVIO", "modo", fallback="legacy")

        # Verificar rutas
        ok, msg_v = verificar_rutas(ruta_data)
        if not ok:
            self._emit(f"[VERIFICACION] ERROR rutas: {msg_v}", "error")
            return

        # ── Inspeccion interna del DBF (sin exponer datos sensibles) ──
        from dbf_reader import inspeccionar_flag_envio
        self._emit("─" * 60, "info")
        self._emit("INSPECCION INFORMACION DE ENVIO", "warn")
        insp = inspeccionar_flag_envio(ruta_data)
        if "error" in insp:
            self._emit(f"  ✗ No se pudo leer la base de datos: {insp['error']}", "error")
        else:
            valores = insp["valores"]
            pendientes_n = valores.get(2, 0)
            procesados_n = sum(v for k, v in valores.items() if k != 2 and k != -1)
            self._emit(f"  Comprobantes pendientes de envio : {pendientes_n}", "info")
            self._emit(f"  Comprobantes ya procesados       : {procesados_n}", "ok")
            self._emit(f"  ✓ Estructura de base de datos verificada correctamente", "ok")
        self._emit("─" * 60, "info")

        # Leer DBF con errores descriptivos
        try:
            pendientes = leer_pendientes(ruta_data)
            productos  = leer_productos(ruta_data)
            detalles   = leer_detalles(ruta_data, productos)
        except DBFNotFound as e:
            self._emit(f"[VERIFICACION] Archivo no encontrado: {e.archivo}", "error")
            return
        except DBFCorrupto as e:
            self._emit(
                f"[VERIFICACION] Archivo corrupto: {e.archivo} — {e.causa}", "error")
            return
        except DBFError as e:
            self._emit(f"[VERIFICACION] Error DBF: {e}", "error")
            return

        if not pendientes:
            self._emit("[VERIFICACION] No hay comprobantes pendientes en el DBF.", "warn")
            return

        self._emit(
            f"[VERIFICACION] {len(pendientes)} comprobante(s) encontrado(s) — "
            f"modo: {modo.upper()} — sin enviar a APIFAS", "warn")

        ok_count  = 0
        err_count = 0

        for envio in pendientes:
            tipo      = _safe_str(envio.get("TIPO_FACTU"), "B")
            serie     = _safe_str(envio.get("SERIE_FACT"), "001").zfill(3)
            numero    = _safe_str(envio.get("NUMERO_FAC"), "0")
            cpe_tipo  = "FACTURA" if tipo == "F" else "BOLETA"
            items     = detalles.get((tipo, serie, numero), [])

            if not items:
                self._emit(
                    f"  ⚠ [{cpe_tipo}] {tipo}{serie}-{numero.zfill(8)} — sin detalle en DBF",
                    "warn")
                err_count += 1
                continue

            try:
                comp  = normalizar(envio, items)
                total = float(comp["totales"]["total"])
                n_items = len(comp["items"])

                if modo == "legacy":
                    nombre, _ = generar_txt(comp, ruc, rs)
                    grav = float(comp["totales"]["gravada"])
                    exon = float(comp["totales"]["exonerada"])
                    igv  = float(comp["totales"]["igv"])
                    preview = f"grav={grav:.2f} igv={igv:.2f} exon={exon:.2f}"
                else:
                    nombre, payload = generar_json(comp, ruc, rs)
                    preview = json.dumps(payload["totales"])

                self._emit(
                    f"  ✓ [{cpe_tipo}] {nombre}  S/ {total:.2f}  |  {n_items} item(s)  |  {preview}",
                    "ok")
                ok_count += 1

            except Exception as e:
                self._emit(
                    f"  ✗ [{cpe_tipo}] {tipo}{serie}-{numero.zfill(8)} — Error: {e}",
                    "error")
                err_count += 1

        self._emit(
            f"[VERIFICACION] Fin — {ok_count} OK / {err_count} con problemas — "
            f"Ningun dato fue enviado a APIFAS.", "warn")
