"""
gui.py  —  CPE DisateQ™  v1.0.0
Interfaz grafica principal.
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import queue
import logging
import re
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)

VERSION = "v1.0.0"

# Patron de nombre de comprobante valido: RUC-02-SERIE-NUMERO.txt
# Ejemplo: 20611706678-02-B001-00000123.txt
_RE_CPE = re.compile(r'^\d{11}-0[12]-[A-Z]\d{3}-\d+\.txt$', re.IGNORECASE)

def _es_cpe(nombre: str) -> bool:
    """Verifica que el archivo TXT corresponde a un CPE valido."""
    return bool(_RE_CPE.match(Path(nombre).name))


def iniciar_gui(cfg, monitor_cls, report_fn):
    ruc          = cfg.get("EMPRESA", "ruc")
    razon_social     = cfg.get("EMPRESA", "razon_social")
    nombre_comercial = cfg.get("EMPRESA", "nombre_comercial", fallback="").strip()
    serie        = cfg.get("EMPRESA", "serie", fallback="B001")
    salida       = cfg.get("RUTAS", "salida_txt")
    url_envio    = cfg.get("ENVIO", "url_envio")

    from config import label_modalidad
    lbl_modalidad = label_modalidad(cfg)

    gui_queue = queue.Queue()

    root = tk.Tk()
    root.title(f"CPE DisateQ\u2122  \u2014  {razon_social}")
    root.geometry("820x620")
    root.resizable(True, True)
    root.configure(bg="#f0f0f0")

    C_HEADER  = "#1a3a5c"
    C_WHITE   = "#ffffff"
    C_BG      = "#f0f0f0"
    C_BORDER  = "#e0e0e0"
    C_VERDE   = "#2e7d32"
    C_ROJO    = "#c62828"
    C_NARANJA = "#e65100"
    C_AZUL    = "#1565c0"
    C_GRIS    = "#546e7a"

    # ── Header ──
    header = tk.Frame(root, bg=C_HEADER)
    header.pack(fill="x")

    fr_title = tk.Frame(header, bg=C_HEADER)
    fr_title.pack(side="left", padx=14, pady=10)
    tk.Label(fr_title, text="CPE DisateQ\u2122",
             font=("Segoe UI", 15, "bold"), bg=C_HEADER, fg="white").pack(side="left")
    tk.Label(fr_title, text="  Env\u00edo de Facturaci\u00f3n Electr\u00f3nica",
             font=("Segoe UI", 10), bg=C_HEADER, fg="#90b8d8").pack(side="left")

    # Semaforo conexion
    fr_conn = tk.Frame(header, bg=C_HEADER)
    fr_conn.pack(side="right", padx=18)
    lbl_dot = tk.Label(fr_conn, text="\u25cf", font=("Segoe UI", 13),
                       bg=C_HEADER, fg="#d50000")
    lbl_dot.pack(side="left")
    lbl_conn_txt = tk.Label(fr_conn, text="Sin conexi\u00f3n",
                            font=("Segoe UI", 10), bg=C_HEADER, fg="#ff1744")
    lbl_conn_txt.pack(side="left", padx=4)

    # ── Barra empresa ──
    emp_bar = tk.Frame(root, bg=C_WHITE,
                       highlightbackground=C_BORDER, highlightthickness=1)
    emp_bar.pack(fill="x")
    fr_emp = tk.Frame(emp_bar, bg=C_WHITE)
    fr_emp.pack(side="left", padx=14, pady=8)
    tk.Label(fr_emp, text=razon_social.upper(),
             font=("Segoe UI", 12, "bold"), bg=C_WHITE, fg=C_HEADER).pack(anchor="w")
    tk.Label(fr_emp, text=f"RUC {ruc}  \u00b7  Serie {serie}  \u00b7  {lbl_modalidad}",
             font=("Segoe UI", 9), bg=C_WHITE, fg=C_GRIS).pack(anchor="w")
    # Endpoint activo
    fr_ep = tk.Frame(emp_bar, bg=C_WHITE)
    fr_ep.pack(side="right", padx=14, pady=8)
    tk.Label(fr_ep, text="Endpoint activo:",
             font=("Segoe UI", 8), bg=C_WHITE, fg=C_GRIS).pack(anchor="e")
    tk.Label(fr_ep, text=url_envio,
             font=("Segoe UI", 7), bg=C_WHITE, fg="#546e7a").pack(anchor="e")

    # ── Contadores ──
    fr_stats = tk.Frame(root, bg=C_BG)
    fr_stats.pack(fill="x", padx=12, pady=12)

    def stat_card(parent, label, init, color):
        f = tk.Frame(parent, bg=C_WHITE,
                     highlightbackground=C_BORDER, highlightthickness=1)
        f.pack(side="left", expand=True, fill="x", padx=5)
        tk.Label(f, text=label, font=("Segoe UI", 9),
                 bg=C_WHITE, fg="#757575").pack(pady=(10, 2))
        lbl = tk.Label(f, text=str(init),
                       font=("Segoe UI", 26, "bold"), bg=C_WHITE, fg=color)
        lbl.pack(pady=(0, 10))
        return lbl

    lbl_pend = stat_card(fr_stats, "Pendientes",     0, C_NARANJA)
    lbl_env  = stat_card(fr_stats, "Enviados hoy",   0, C_VERDE)
    lbl_err  = stat_card(fr_stats, "En errores",     0, C_ROJO)

    # ── Botones ──
    fr_btns = tk.Frame(root, bg=C_BG)
    fr_btns.pack(fill="x", padx=12, pady=(0, 8))

    def mk_btn(parent, text, cmd, color):
        b = tk.Button(parent, text=text, command=cmd,
                      font=("Segoe UI", 10, "bold"), bg=color, fg="white",
                      relief="flat", padx=14, pady=7, cursor="hand2",
                      activebackground=color, bd=0)
        b.pack(side="left", padx=3)
        return b

    def enviar_ahora():
        agregar_log("[MANUAL] Procesando pendientes ahora...", "info")
        threading.Thread(target=lambda: monitor_cls(cfg, gui_queue).ciclo_manual(),
                         daemon=True).start()

    def reenviar_errores():
        agregar_log("[REENVIO] Reintentando comprobantes con error...", "warn")
        threading.Thread(target=_run_reenvio, daemon=True).start()

    def _run_reenvio():
        try:
            from sender import enviar_txt
            carpeta_err = Path(salida) / "errores"
            # Solo TXT que sean CPE válidos
            archivos = [f for f in carpeta_err.glob("*.txt") if _es_cpe(f.name)] \
                       if carpeta_err.exists() else []
            if not archivos:
                gui_queue.put({"tipo": "log",
                               "msg": "[REENVIO] Sin comprobantes pendientes en errores.", "tag": "warn"})
                return
            ruc_e = cfg.get("EMPRESA", "ruc")
            url   = cfg.get("ENVIO", "url_envio")
            for f in archivos:
                contenido = f.read_text(encoding="latin-1")
                exito, msg = enviar_txt(f.name, contenido, ruc_e, url)
                if exito:
                    enviados = Path(salida) / "enviados"
                    enviados.mkdir(exist_ok=True)
                    f.rename(enviados / f.name)
                    gui_queue.put({"tipo": "evento", "estado": "enviado",
                                   "nombre": f.name, "cpe_tipo": "CPE", "msg": msg})
                else:
                    gui_queue.put({"tipo": "evento", "estado": "error",
                                   "nombre": f.name, "cpe_tipo": "CPE", "msg": msg})
        except Exception as e:
            gui_queue.put({"tipo": "log", "msg": f"[REENVIO] Error: {e}", "tag": "error"})

    def ver_reporte():
        rpt = report_fn(Path(salida))
        win = tk.Toplevel(root)
        win.title("Reporte de correlativos")
        win.geometry("640x460")
        st = scrolledtext.ScrolledText(win, font=("Courier New", 10), wrap="none")
        st.pack(fill="both", expand=True, padx=10, pady=10)
        st.insert("end", rpt.read_text(encoding="utf-8"))
        st.config(state="disabled")

    def abrir_carpeta(subcarpeta):
        import subprocess
        ruta = Path(salida) / subcarpeta
        ruta.mkdir(exist_ok=True)
        subprocess.Popen(f'explorer "{ruta}"')

    def simular():
        agregar_log("[SIMULACION] Procesando DBF sin enviar...", "warn")
        threading.Thread(target=_run_simulacion, daemon=True).start()

    def _run_simulacion():
        try:
            import json as _json
            from dbf_reader import leer_pendientes, leer_productos, leer_detalles, verificar_rutas
            from normalizer import normalizar
            from txt_generator import generar_txt
            from json_generator import generar_json

            ruta_data = cfg.get("RUTAS", "data_dbf")
            ok, msg_v = verificar_rutas(ruta_data)
            if not ok:
                gui_queue.put({"tipo": "log", "msg": f"[SIMULACION] ERROR: {msg_v}", "tag": "error"})
                return

            pendientes = leer_pendientes(ruta_data)
            if not pendientes:
                gui_queue.put({"tipo": "log",
                               "msg": "[SIMULACION] No hay comprobantes pendientes.", "tag": "warn"})
                return

            productos = leer_productos(ruta_data)
            detalles  = leer_detalles(ruta_data, productos)
            modo      = cfg.get("ENVIO", "modo", fallback="legacy")
            ruc_e     = cfg.get("EMPRESA", "ruc")
            rs        = cfg.get("EMPRESA", "razon_social")

            gui_queue.put({"tipo": "log",
                           "msg": f"[SIMULACION] {len(pendientes)} comprobante(s) encontrados:", "tag": "warn"})

            for envio in pendientes:
                tipo  = str(envio["TIPO_FACTU"]).strip()
                serie = str(envio["SERIE_FACT"]).strip().zfill(3)
                num   = str(envio["NUMERO_FAC"]).strip()
                items = detalles.get((tipo, serie, num), [])

                if not items:
                    gui_queue.put({"tipo": "log",
                                   "msg": f"  \u26a0 {tipo}{serie}-{num.zfill(8)} \u2014 sin detalle en DBF",
                                   "tag": "warn"})
                    continue

                comp     = normalizar(envio, items)
                total    = float(comp["totales"]["total"])
                n_items  = len(comp["items"])
                cpe_tipo = "FACTURA" if tipo == "F" else "BOLETA"

                if modo == "legacy":
                    nombre, _ = generar_txt(comp, ruc_e, rs)
                    preview   = (f"gravada={float(comp['totales']['gravada']):.2f}"
                                 f"  igv={float(comp['totales']['igv']):.2f}"
                                 f"  exonerada={float(comp['totales']['exonerada']):.2f}")
                else:
                    nombre, payload = generar_json(comp, ruc_e, rs)
                    preview = _json.dumps(payload["totales"])

                gui_queue.put({"tipo": "log",
                               "msg": f"  \u2713 [{cpe_tipo}] {nombre}  S/ {total:.2f}  |  {n_items} item(s)  |  {preview}",
                               "tag": "ok"})

            gui_queue.put({"tipo": "log",
                           "msg": "[SIMULACION] Fin. Ningun dato fue enviado a la API.",
                           "tag": "warn"})
        except Exception as e:
            gui_queue.put({"tipo": "log", "msg": f"[SIMULACION] Error: {e}", "tag": "error"})

    mk_btn(fr_btns, "Enviar ahora",     enviar_ahora,                    C_AZUL)
    mk_btn(fr_btns, "Reenviar errores", reenviar_errores,                C_NARANJA)
    mk_btn(fr_btns, "Ver reporte",      ver_reporte,                     C_GRIS)
    mk_btn(fr_btns, "Abrir enviados",   lambda: abrir_carpeta("enviados"), C_VERDE)
    mk_btn(fr_btns, "Abrir errores",    lambda: abrir_carpeta("errores"),  C_ROJO)
    mk_btn(fr_btns, "Simular",          simular,                         "#6a1b9a")

    # ── Log en tiempo real ──
    fr_log = tk.Frame(root, bg=C_BG, padx=12)
    fr_log.pack(fill="both", expand=True)
    tk.Label(fr_log, text="Actividad en tiempo real",
             font=("Segoe UI", 9, "bold"), bg=C_BG, fg="#757575").pack(anchor="w")
    log_box = scrolledtext.ScrolledText(
        fr_log, height=14, font=("Consolas", 9),
        bg="#1e1e1e", fg="#d4d4d4", wrap="word", state="disabled", relief="flat")
    log_box.pack(fill="both", expand=True)
    log_box.tag_config("ok",    foreground="#4ec9b0")
    log_box.tag_config("error", foreground="#f48771")
    log_box.tag_config("info",  foreground="#9cdcfe")
    log_box.tag_config("warn",  foreground="#dcdcaa")

    def agregar_log(msg: str, tag="info"):
        ts = datetime.now().strftime("%H:%M:%S")
        log_box.config(state="normal")
        log_box.insert("end", f"[{ts}]  {msg}\n", tag)
        log_box.see("end")
        log_box.config(state="disabled")

    # ── Status bar ──
    status_bar = tk.Frame(root, bg="#cfd8dc", height=24)
    status_bar.pack(fill="x", side="bottom")
    status_bar.pack_propagate(False)
    lbl_hora = tk.Label(status_bar, text="",
                        font=("Segoe UI", 8), bg="#cfd8dc", fg="#37474f")
    lbl_hora.pack(side="right", padx=10)
    tk.Label(status_bar,
             text=(f"Monitoreo activo  |  Facturas: inmediato  |  Boletas: cada 5 min"
                   f"  |  {lbl_modalidad}  |  CPE DisateQ\u2122 {VERSION}"
                   f"  |  @fhertejada\u2122"),
             font=("Segoe UI", 8), bg="#cfd8dc", fg="#37474f").pack(side="left", padx=10)

    def actualizar_hora():
        lbl_hora.config(text=datetime.now().strftime("%d/%m/%Y  %H:%M:%S"))
        root.after(1000, actualizar_hora)
    actualizar_hora()

    # ── Procesador de cola ──
    enviados_hoy_cnt = [0]
    errores_cnt      = [0]

    def procesar_cola():
        try:
            while True:
                msg  = gui_queue.get_nowait()
                tipo = msg.get("tipo")
                if tipo == "conexion":
                    if msg["ok"]:
                        lbl_dot.config(fg="#00c853")
                        lbl_conn_txt.config(text="Conectado", fg="#00c853")
                    else:
                        lbl_dot.config(fg="#ef9a9a")
                        lbl_conn_txt.config(text="Sin conexi\u00f3n", fg="#ef9a9a")
                elif tipo == "evento":
                    if msg["estado"] == "enviado":
                        enviados_hoy_cnt[0] += 1
                        lbl_env.config(text=str(enviados_hoy_cnt[0]))
                        agregar_log(
                            f"OK  [{msg['cpe_tipo']}]  {msg['nombre']}  \u2014  {msg['msg']}", "ok")
                    elif msg["estado"] == "error":
                        errores_cnt[0] += 1
                        lbl_err.config(text=str(errores_cnt[0]))
                        agregar_log(
                            f"FAIL  [{msg['cpe_tipo']}]  {msg['nombre']}  \u2014  {msg['msg']}", "error")
                    elif msg["estado"] == "sin_detalle":
                        agregar_log(
                            f"SIN DETALLE  {msg['nombre']}  \u2014  {msg['msg']}", "warn")
                elif tipo == "contadores":
                    lbl_pend.config(text=str(msg["pendientes"]))
                elif tipo == "log":
                    agregar_log(msg["msg"], msg.get("tag", "info"))
        except queue.Empty:
            pass
        root.after(500, procesar_cola)

    procesar_cola()

    monitor = monitor_cls(cfg, gui_queue)
    threading.Thread(target=monitor.iniciar, daemon=True).start()
    agregar_log(f"Monitoreo iniciado  |  {razon_social}  |  RUC: {ruc}  |  {lbl_modalidad}", "info")

    def on_close():
        monitor.detener()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
