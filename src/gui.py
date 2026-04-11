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
    ruc              = cfg.get("EMPRESA", "ruc")
    razon_social     = cfg.get("EMPRESA", "razon_social")
    nombre_comercial = cfg.get("EMPRESA", "nombre_comercial", fallback="").strip()
    alias            = cfg.get("EMPRESA", "alias",            fallback="").strip()
    serie            = cfg.get("EMPRESA", "serie", fallback="B001")
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
    # Nombre comercial como titulo principal si existe, sino razon social
    nombre_display = nombre_comercial.upper() if nombre_comercial else razon_social.upper()
    tk.Label(fr_emp, text=nombre_display,
             font=("Segoe UI", 12, "bold"), bg=C_WHITE, fg=C_HEADER).pack(anchor="w")
    # Si hay nombre comercial, mostrar razon social debajo en gris pequeño
    if nombre_comercial:
        tk.Label(fr_emp, text=razon_social.upper(),
                 font=("Segoe UI", 8), bg=C_WHITE, fg=C_GRIS).pack(anchor="w")
    tk.Label(fr_emp, text=f"RUC {ruc}  \u00b7  Serie {serie}  \u00b7  {lbl_modalidad}",
             font=("Segoe UI", 9), bg=C_WHITE, fg=C_GRIS).pack(anchor="w")


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
        """Abre ventana separada de verificacion — no toca el log principal."""
        import queue as _queue
        from tkinter import scrolledtext as _st

        win_ver = tk.Toplevel(root)
        win_ver.title("Verificar Base \u2014 CPE DisateQ\u2122")
        win_ver.geometry("900x540")
        win_ver.minsize(800, 420)
        win_ver.configure(bg="#1e1e1e")
        win_ver.focus_set()

        # Header
        hdr_v = tk.Frame(win_ver, bg=C_HEADER)
        hdr_v.pack(fill="x")
        tk.Label(hdr_v, text="  Verificar Base  \u2014  Lectura DBF sin enviar a APIFAS",
                 font=("Segoe UI", 11, "bold"), bg=C_HEADER, fg="white",
                 pady=9).pack(side="left")
        lbl_estado = tk.Label(hdr_v, text="Procesando...",
                              font=("Segoe UI", 9), bg=C_HEADER, fg="#90b8d8")
        lbl_estado.pack(side="right", padx=14)

        # Log
        log_v = _st.ScrolledText(
            win_ver, font=("Consolas", 9),
            bg="#1e1e1e", fg="#d4d4d4",
            wrap="none", state="disabled", relief="flat")
        log_v.pack(fill="both", expand=True, padx=4, pady=4)
        log_v.tag_config("ok",    foreground="#4ec9b0")
        log_v.tag_config("error", foreground="#f48771")
        log_v.tag_config("info",  foreground="#9cdcfe")
        log_v.tag_config("warn",  foreground="#dcdcaa")

        # Barra inferior
        fr_bot_v = tk.Frame(win_ver, bg="#0f2d47", pady=8)
        fr_bot_v.pack(fill="x", side="bottom")
        tk.Button(fr_bot_v, text="Cerrar", command=win_ver.destroy,
                  font=("Segoe UI", 10), bg=C_GRIS, fg="white",
                  relief="flat", padx=16, pady=5,
                  cursor="hand2", bd=0).pack(side="right", padx=12)
        lbl_resumen_v = tk.Label(fr_bot_v, text="",
                                 font=("Segoe UI", 9), bg="#0f2d47", fg="#90b8d8")
        lbl_resumen_v.pack(side="left", padx=12)

        q_ver = _queue.Queue()

        def _escribir_v(msg, tag="info"):
            from datetime import datetime as _dt
            ts = _dt.now().strftime("%H:%M:%S")
            log_v.config(state="normal")
            log_v.insert("end", f"[{ts}]  {msg}\n", tag)
            log_v.see("end")
            log_v.config(state="disabled")

        def _poll():
            try:
                while True:
                    m = q_ver.get_nowait()
                    if m.get("tipo") == "log":
                        _escribir_v(m["msg"], m.get("tag", "info"))
            except _queue.Empty:
                pass
            if win_ver.winfo_exists():
                win_ver.after(80, _poll)
        _poll()

        def _run_ver():
            from simulacion import SimulacionService
            SimulacionService(cfg, q_ver).ejecutar()
            if win_ver.winfo_exists():
                contenido = log_v.get("1.0", "end")
                ok_n  = contenido.count("  \u2713 ")
                err_n = contenido.count("  \u26a0 ") + contenido.count("  \u2717 ")
                lbl_estado.config(text="Completado")
                lbl_resumen_v.config(
                    text=f"Resultado:  {ok_n} comprobante(s) OK  |  {err_n} con problema(s)")

        threading.Thread(target=_run_ver, daemon=True).start()

    def salir():
        monitor.detener()
        root.destroy()

    def abrir_info():
        _abrir_ventana_info()

    def _abrir_ventana_info():
        import queue as _queue
        from tkinter import scrolledtext as _st
        from status_dia import generar_status

        win_info = tk.Toplevel(root)
        win_info.title("INFO — Status del día  —  CPE DisateQ™")
        win_info.geometry("820x560")
        win_info.minsize(700, 440)
        win_info.configure(bg="#1e1e1e")
        win_info.focus_set()

        hdr_i = tk.Frame(win_info, bg=C_HEADER)
        hdr_i.pack(fill="x")
        tk.Label(hdr_i, text="  Status del día  —  Comprobantes enviados",
                 font=("Segoe UI", 11, "bold"), bg=C_HEADER, fg="white",
                 pady=9).pack(side="left")
        lbl_est_i = tk.Label(hdr_i, text="Generando...",
                             font=("Segoe UI", 9), bg=C_HEADER, fg="#90b8d8")
        lbl_est_i.pack(side="right", padx=14)

        log_i = _st.ScrolledText(
            win_info, font=("Consolas", 9),
            bg="#1e1e1e", fg="#d4d4d4",
            wrap="none", state="disabled", relief="flat")
        log_i.pack(fill="both", expand=True, padx=4, pady=4)
        log_i.tag_config("titulo",  foreground="#dcdcaa", font=("Consolas", 9, "bold"))
        log_i.tag_config("ok",      foreground="#4ec9b0")
        log_i.tag_config("error",   foreground="#f48771")
        log_i.tag_config("info",    foreground="#9cdcfe")
        log_i.tag_config("resumen", foreground="#ce9178")

        fr_bot_i = tk.Frame(win_info, bg="#0f2d47", pady=8)
        fr_bot_i.pack(fill="x", side="bottom")
        tk.Button(fr_bot_i, text="Cerrar", command=win_info.destroy,
                  font=("Segoe UI", 10), bg=C_GRIS, fg="white",
                  relief="flat", padx=16, pady=5,
                  cursor="hand2", bd=0).pack(side="right", padx=12)
        lbl_arch = tk.Label(fr_bot_i, text="",
                            font=("Segoe UI", 8), bg="#0f2d47", fg="#90b8d8")
        lbl_arch.pack(side="left", padx=12)

        def _escribir_i(msg, tag="info"):
            log_i.config(state="normal")
            log_i.insert("end", msg + "\n", tag)
            log_i.see("end")
            log_i.config(state="disabled")

        def _run_info():
            try:
                ruc_e = cfg.get("EMPRESA", "ruc")
                rs    = cfg.get("EMPRESA", "razon_social")
                nc    = cfg.get("EMPRESA", "nombre_comercial", fallback="")
                sal   = cfg.get("RUTAS",   "salida_txt")
                ruta, datos = generar_status(sal, ruc_e, rs, nc)
                # Mostrar contenido del reporte en el log
                contenido = ruta.read_text(encoding="utf-8")
                for linea in contenido.split("\n"):
                    if linea.startswith("="):
                        tag = "titulo"
                    elif linea.startswith("  Serie") or "RESUMEN" in linea or "DETALLE" in linea or "ERROR" in linea:
                        tag = "resumen"
                    elif linea.strip().startswith("B0") or linea.strip().startswith("F0"):
                        tag = "ok"
                    else:
                        tag = "info"
                    _escribir_i(linea, tag)

                if win_info.winfo_exists():
                    lbl_est_i.config(text="Completado")
                    lbl_arch.config(text=f"Guardado en: {ruta.name}")
            except Exception as e:
                _escribir_i(f"Error generando status: {e}", "error")
                if win_info.winfo_exists():
                    lbl_est_i.config(text="Error")

        threading.Thread(target=_run_info, daemon=True).start()

    # Orden de botones: izquierda a derecha
    mk_btn(fr_btns, "Verificar Envio",    simular,                           "#6a1b9a")
    mk_btn(fr_btns, "Envio Manual",      enviar_ahora,                      C_AZUL)
    mk_btn(fr_btns, "Abrir Procesados",  lambda: abrir_carpeta("enviados"),  C_VERDE)
    mk_btn(fr_btns, "Abrir Errores",     lambda: abrir_carpeta("errores"),   C_ROJO)
    mk_btn(fr_btns, "Reenviar Errores",  reenviar_errores,                   C_NARANJA)
    mk_btn(fr_btns, "Correlativos",       ver_reporte,                        C_GRIS)
    mk_btn(fr_btns, "Reporte Envios",              abrir_info,                         "#00695c")
    mk_btn(fr_btns, "Salir",             salir,                              "#37474f")

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

    # ── Alerta sin conexion ──
    _parpadeando    = [False]
    _parpadeo_id    = [None]
    _parpadeo_estado = [True]

    def _alertar_sin_conexion():
        # Sonido del sistema Windows
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass
        # Log visible
        agregar_log("⚠  SIN CONEXION A APIFAS — Verificar internet", "error")
        # Iniciar parpadeo si no esta activo
        if not _parpadeando[0]:
            _parpadeando[0] = True
            _parpadear()

    def _parpadear():
        if not _parpadeando[0]:
            return
        _parpadeo_estado[0] = not _parpadeo_estado[0]
        color = "#d50000" if _parpadeo_estado[0] else C_HEADER
        lbl_dot.config(fg=color)
        _parpadeo_id[0] = root.after(600, _parpadear)

    def _detener_parpadeo():
        _parpadeando[0] = False
        if _parpadeo_id[0]:
            root.after_cancel(_parpadeo_id[0])
            _parpadeo_id[0] = None

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
    # Ajustar ventana al contenido al cargar
    root.update_idletasks()
    ancho  = max(root.winfo_reqwidth(),  760)
    alto   = max(root.winfo_reqheight(), 520)
    # No superar la pantalla
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    ancho = min(ancho, sw - 40)
    alto  = min(alto,  sh - 60)
    root.geometry(f"{ancho}x{alto}")
    root.mainloop()
