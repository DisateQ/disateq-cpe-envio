"""
gui.py  —  CPE DisateQ™  v2.0.0
Interfaz grafica principal.

Cambios v2.0:
  - KPIs de montos por tipo: Facturas / Boletas / Notas
  - Total del día: cantidad + monto acumulado
  - ALIAS badge en barra empresa
  - 4to KPI: countdown próximo ciclo boletas
  - Modalidad visible en semáforo
  - Timer boletas: 30 min
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

VERSION = "v2.0.0"

_RE_CPE = re.compile(r'^\d{11}-0[12]-[A-Z]\d{3}-\d+\.txt$', re.IGNORECASE)

def _es_cpe(nombre: str) -> bool:
    return bool(_RE_CPE.match(Path(nombre).name))


def iniciar_gui(cfg, monitor_cls, report_fn):
    ruc              = cfg.get("EMPRESA", "ruc")
    razon_social     = cfg.get("EMPRESA", "razon_social")
    nombre_comercial = cfg.get("EMPRESA", "nombre_comercial", fallback="").strip()
    alias            = cfg.get("EMPRESA", "alias",            fallback="").strip()
    serie_b          = cfg.get("EMPRESA", "serie_boleta",   fallback="B001")
    serie_f          = cfg.get("EMPRESA", "serie_factura",  fallback="F001")
    salida           = cfg.get("RUTAS",   "salida_txt")
    url_envio        = cfg.get("ENVIO",   "url_envio")

    from config import label_modalidad
    from monitor import INTERVALO_BOLETA
    lbl_modalidad    = label_modalidad(cfg)
    intervalo_boleta = INTERVALO_BOLETA

    gui_queue = queue.Queue()

    root = tk.Tk()
    root.title(f"CPE DisateQ™  —  {razon_social}")
    root.resizable(True, True)
    root.configure(bg="#f5f6f7")

    # ── Colores ──────────────────────────────────────────────
    C_HEADER  = "#1a3a5c"
    C_WHITE   = "#ffffff"
    C_BG      = "#f5f6f7"
    C_BORDER  = "#e0e0e0"
    C_VERDE   = "#2e7d32"
    C_ROJO    = "#c62828"
    C_NARANJA = "#e65100"
    C_AZUL    = "#1565c0"
    C_GRIS    = "#546e7a"
    C_PURPLE  = "#6a1b9a"
    C_TEAL    = "#00695c"
    C_DARK    = "#37474f"

    # ── Header ───────────────────────────────────────────────
    header = tk.Frame(root, bg=C_HEADER)
    header.pack(fill="x")

    fr_title = tk.Frame(header, bg=C_HEADER)
    fr_title.pack(side="left", padx=14, pady=10)
    tk.Label(fr_title, text="CPE DisateQ™",
             font=("Segoe UI", 15, "bold"), bg=C_HEADER, fg="white").pack(side="left")
    tk.Label(fr_title, text="  Motor de facturación electrónica",
             font=("Segoe UI", 10), bg=C_HEADER, fg="#90b8d8").pack(side="left")

    # Boton configuracion (rueda dentada) — header derecha
    def _abrir_config():
        from config_wizard import abrir_wizard
        abrir_wizard(root, cfg, callback=lambda: None)

    tk.Button(header, text="\u2699", font=("Segoe UI", 14),
              bg=C_HEADER, fg="#90b8d8",
              relief="flat", bd=0, cursor="hand2",
              activebackground=C_HEADER, activeforeground="white",
              command=_abrir_config).pack(side="right", padx=(0, 6), pady=6)

    fr_conn = tk.Frame(header, bg=C_HEADER)
    fr_conn.pack(side="right", padx=(0, 4))
    lbl_dot = tk.Label(fr_conn, text="●", font=("Segoe UI", 11),
                       bg=C_HEADER, fg="#d50000")
    lbl_dot.pack(side="left")
    lbl_conn_txt = tk.Label(fr_conn, text="Sin conexión",
                            font=("Segoe UI", 9), bg=C_HEADER, fg="#ff1744")
    lbl_conn_txt.pack(side="left", padx=4)

    # ── Barra empresa ─────────────────────────────────────────
    emp_bar = tk.Frame(root, bg=C_WHITE,
                       highlightbackground=C_BORDER, highlightthickness=1)
    emp_bar.pack(fill="x")

    fr_emp = tk.Frame(emp_bar, bg=C_WHITE)
    fr_emp.pack(side="left", padx=14, pady=8)

    nombre_display = nombre_comercial.upper() if nombre_comercial else razon_social.upper()
    tk.Label(fr_emp, text=nombre_display,
             font=("Segoe UI", 12, "bold"), bg=C_WHITE, fg=C_HEADER).pack(anchor="w")
    if nombre_comercial:
        tk.Label(fr_emp, text=razon_social.upper(),
                 font=("Segoe UI", 8), bg=C_WHITE, fg=C_GRIS).pack(anchor="w")
    tk.Label(fr_emp,
             text=f"RUC {ruc}  ·  {serie_b} / {serie_f}  ·  {lbl_modalidad}",
             font=("Segoe UI", 9), bg=C_WHITE, fg=C_GRIS).pack(anchor="w")

    # ALIAS badge (solo si está configurado)
    if alias:
        fr_alias = tk.Frame(emp_bar, bg=C_WHITE)
        fr_alias.pack(side="right", padx=14)
        tk.Label(fr_alias, text=alias,
                 font=("Segoe UI", 10, "bold"),
                 bg="#e8f0fe", fg="#185FA5",
                 padx=12, pady=4,
                 relief="flat").pack()

    # ── KPIs fila 1: contadores ───────────────────────────────
    fr_kpi1 = tk.Frame(root, bg=C_BG)
    fr_kpi1.pack(fill="x", padx=12, pady=(12, 4))

    def kpi_card(parent, label, init_val, init_sub, color):
        f = tk.Frame(parent, bg=C_WHITE,
                     highlightbackground=C_BORDER, highlightthickness=1)
        f.pack(side="left", expand=True, fill="x", padx=4)
        tk.Label(f, text=label, font=("Segoe UI", 9),
                 bg=C_WHITE, fg="#757575").pack(pady=(10, 2))
        lbl_v = tk.Label(f, text=str(init_val),
                         font=("Segoe UI", 24, "bold"), bg=C_WHITE, fg=color)
        lbl_v.pack()
        lbl_s = tk.Label(f, text=init_sub,
                         font=("Segoe UI", 8), bg=C_WHITE, fg="#9e9e9e")
        lbl_s.pack(pady=(0, 10))
        return lbl_v, lbl_s

    lbl_pend,  lbl_pend_sub  = kpi_card(fr_kpi1, "Pendientes",       0, "",          C_NARANJA)
    lbl_env,   lbl_env_sub   = kpi_card(fr_kpi1, "Enviados hoy",     0, "",          C_VERDE)
    lbl_err,   lbl_err_sub   = kpi_card(fr_kpi1, "En errores",       0, "carpeta /errores", C_ROJO)
    lbl_timer, lbl_timer_sub = kpi_card(fr_kpi1, "Próximo ciclo",    "—", "boletas", C_AZUL)

    # ── KPIs fila 2: montos por tipo ──────────────────────────
    tk.Label(root, text="  Totales del día",
             font=("Segoe UI", 9, "bold"), bg=C_BG, fg="#757575").pack(anchor="w", padx=16)

    fr_kpi2 = tk.Frame(root, bg=C_BG)
    fr_kpi2.pack(fill="x", padx=12, pady=(2, 8))

    def monto_card(parent, label, color_accent):
        f = tk.Frame(parent, bg=C_WHITE,
                     highlightbackground=C_BORDER, highlightthickness=1)
        f.pack(side="left", expand=True, fill="x", padx=4)
        # Franja de color izquierda
        tk.Frame(f, bg=color_accent, width=4).pack(side="left", fill="y")
        fr_inner = tk.Frame(f, bg=C_WHITE)
        fr_inner.pack(side="left", fill="both", expand=True, padx=10, pady=8)
        tk.Label(fr_inner, text=label, font=("Segoe UI", 9),
                 bg=C_WHITE, fg="#757575").pack(anchor="w")
        lbl_cnt = tk.Label(fr_inner, text="0 comprobantes",
                           font=("Segoe UI", 10, "bold"), bg=C_WHITE, fg=color_accent)
        lbl_cnt.pack(anchor="w")
        lbl_mnt = tk.Label(fr_inner, text="S/ 0.00",
                           font=("Segoe UI", 13, "bold"), bg=C_WHITE, fg=color_accent)
        lbl_mnt.pack(anchor="w")
        return lbl_cnt, lbl_mnt

    lbl_fact_cnt, lbl_fact_mnt = monto_card(fr_kpi2, "Facturas",  C_AZUL)
    lbl_bol_cnt,  lbl_bol_mnt  = monto_card(fr_kpi2, "Boletas",   C_VERDE)
    lbl_nota_cnt, lbl_nota_mnt = monto_card(fr_kpi2, "Notas",     C_PURPLE)

    # Total del día
    fr_total = tk.Frame(fr_kpi2, bg="#1a3a5c",
                        highlightbackground=C_BORDER, highlightthickness=1)
    fr_total.pack(side="left", expand=True, fill="x", padx=4)
    fr_total_inner = tk.Frame(fr_total, bg="#1a3a5c")
    fr_total_inner.pack(fill="both", expand=True, padx=10, pady=8)
    tk.Label(fr_total_inner, text="Total del día",
             font=("Segoe UI", 9), bg="#1a3a5c", fg="#90b8d8").pack(anchor="w")
    lbl_total_cnt = tk.Label(fr_total_inner, text="0 comprobantes",
                             font=("Segoe UI", 10, "bold"), bg="#1a3a5c", fg="white")
    lbl_total_cnt.pack(anchor="w")
    lbl_total_mnt = tk.Label(fr_total_inner, text="S/ 0.00",
                             font=("Segoe UI", 13, "bold"), bg="#1a3a5c", fg="white")
    lbl_total_mnt.pack(anchor="w")

    # ── Acumuladores internos ─────────────────────────────────
    _totales = {
        "01": {"cnt": 0, "monto": 0.0},  # facturas
        "03": {"cnt": 0, "monto": 0.0},  # boletas
        "07": {"cnt": 0, "monto": 0.0},  # notas crédito
        "08": {"cnt": 0, "monto": 0.0},  # notas débito
    }

    def _actualizar_montos():
        fact_cnt  = _totales["01"]["cnt"]
        fact_mnt  = _totales["01"]["monto"]
        bol_cnt   = _totales["03"]["cnt"]
        bol_mnt   = _totales["03"]["monto"]
        nota_cnt  = _totales["07"]["cnt"] + _totales["08"]["cnt"]
        nota_mnt  = _totales["07"]["monto"] + _totales["08"]["monto"]
        total_cnt = fact_cnt + bol_cnt + nota_cnt
        total_mnt = fact_mnt + bol_mnt + nota_mnt

        lbl_fact_cnt.config(text=f"{fact_cnt} comprobante{'s' if fact_cnt != 1 else ''}")
        lbl_fact_mnt.config(text=f"S/ {fact_mnt:,.2f}")
        lbl_bol_cnt.config(text=f"{bol_cnt} comprobante{'s' if bol_cnt != 1 else ''}")
        lbl_bol_mnt.config(text=f"S/ {bol_mnt:,.2f}")
        lbl_nota_cnt.config(text=f"{nota_cnt} comprobante{'s' if nota_cnt != 1 else ''}")
        lbl_nota_mnt.config(text=f"S/ {nota_mnt:,.2f}")
        lbl_total_cnt.config(text=f"{total_cnt} comprobante{'s' if total_cnt != 1 else ''}")
        lbl_total_mnt.config(text=f"S/ {total_mnt:,.2f}")

    # ── Botones ───────────────────────────────────────────────
    tk.Label(root, text="  Acciones",
             font=("Segoe UI", 9, "bold"), bg=C_BG, fg="#757575").pack(anchor="w", padx=16)

    fr_btns = tk.Frame(root, bg=C_BG)
    fr_btns.pack(fill="x", padx=12, pady=(2, 8))

    def mk_btn(parent, text, cmd, color, tooltip=None):
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
            archivos = [f for f in carpeta_err.glob("*.txt") if _es_cpe(f.name)] \
                       if carpeta_err.exists() else []
            if not archivos:
                gui_queue.put({"tipo": "log",
                               "msg": "[REENVIO] Sin comprobantes en errores.", "tag": "warn"})
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
                                   "nombre": f.name, "cpe_tipo": "CPE",
                                   "msg": msg, "monto": 0.0, "tipo_doc": "03"})
                else:
                    gui_queue.put({"tipo": "evento", "estado": "error",
                                   "nombre": f.name, "cpe_tipo": "CPE", "msg": msg})
        except Exception as e:
            gui_queue.put({"tipo": "log",
                           "msg": f"[REENVIO] Error: {e}", "tag": "error"})

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
        import queue as _queue
        from tkinter import scrolledtext as _st

        win_ver = tk.Toplevel(root)
        win_ver.title("Verificar Envío — CPE DisateQ™")
        win_ver.geometry("900x540")
        win_ver.minsize(800, 420)
        win_ver.configure(bg="#1e1e1e")
        win_ver.focus_set()

        hdr_v = tk.Frame(win_ver, bg=C_HEADER)
        hdr_v.pack(fill="x")
        tk.Label(hdr_v, text="  Verificar Envío  —  Lectura DBF sin enviar a APIFAS",
                 font=("Segoe UI", 11, "bold"), bg=C_HEADER, fg="white",
                 pady=9).pack(side="left")
        lbl_estado = tk.Label(hdr_v, text="Procesando...",
                              font=("Segoe UI", 9), bg=C_HEADER, fg="#90b8d8")
        lbl_estado.pack(side="right", padx=14)

        log_v = _st.ScrolledText(
            win_ver, font=("Consolas", 9),
            bg="#1e1e1e", fg="#d4d4d4",
            wrap="none", state="disabled", relief="flat")
        log_v.pack(fill="both", expand=True, padx=4, pady=4)
        log_v.tag_config("ok",    foreground="#4ec9b0")
        log_v.tag_config("error", foreground="#f48771")
        log_v.tag_config("info",  foreground="#9cdcfe")
        log_v.tag_config("warn",  foreground="#dcdcaa")

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
            ts = datetime.now().strftime("%H:%M:%S")
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
                ok_n  = contenido.count("  ✓ ")
                err_n = contenido.count("  ⚠ ") + contenido.count("  ✗ ")
                lbl_estado.config(text="Completado")
                lbl_resumen_v.config(
                    text=f"Resultado:  {ok_n} OK  |  {err_n} con problema(s)")

        threading.Thread(target=_run_ver, daemon=True).start()

    def abrir_info():
        import queue as _queue
        from tkinter import scrolledtext as _st
        from status_dia import generar_status

        win_info = tk.Toplevel(root)
        win_info.title("Reporte del día — CPE DisateQ™")
        win_info.geometry("820x560")
        win_info.minsize(700, 440)
        win_info.configure(bg="#1e1e1e")
        win_info.focus_set()

        hdr_i = tk.Frame(win_info, bg=C_HEADER)
        hdr_i.pack(fill="x")
        tk.Label(hdr_i, text="  Reporte del día  —  Comprobantes enviados",
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

        # Inyectar totales acumulados del día en el reporte
        fact_cnt = _totales["01"]["cnt"]
        fact_mnt = _totales["01"]["monto"]
        bol_cnt  = _totales["03"]["cnt"]
        bol_mnt  = _totales["03"]["monto"]
        nota_cnt = _totales["07"]["cnt"] + _totales["08"]["cnt"]
        nota_mnt = _totales["07"]["monto"] + _totales["08"]["monto"]
        tot_cnt  = fact_cnt + bol_cnt + nota_cnt
        tot_mnt  = fact_mnt + bol_mnt + nota_mnt

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
                contenido = ruta.read_text(encoding="utf-8")
                for linea in contenido.split("\n"):
                    if linea.startswith("="):
                        tag = "titulo"
                    elif "RESUMEN" in linea or "DETALLE" in linea or "ERROR" in linea:
                        tag = "resumen"
                    elif linea.strip().startswith("B0") or linea.strip().startswith("F0"):
                        tag = "ok"
                    else:
                        tag = "info"
                    _escribir_i(linea, tag)

                # Totales de la sesión actual
                _escribir_i("", "info")
                _escribir_i("=" * 60, "titulo")
                _escribir_i("  TOTALES DE LA SESIÓN ACTUAL", "titulo")
                _escribir_i("=" * 60, "titulo")
                _escribir_i(f"  Facturas : {fact_cnt:>4} comprobantes   S/ {fact_mnt:>12,.2f}", "ok")
                _escribir_i(f"  Boletas  : {bol_cnt:>4} comprobantes   S/ {bol_mnt:>12,.2f}", "ok")
                _escribir_i(f"  Notas    : {nota_cnt:>4} comprobantes   S/ {nota_mnt:>12,.2f}", "ok")
                _escribir_i("-" * 60, "resumen")
                _escribir_i(f"  TOTAL    : {tot_cnt:>4} comprobantes   S/ {tot_mnt:>12,.2f}", "resumen")

                if win_info.winfo_exists():
                    lbl_est_i.config(text="Completado")
                    lbl_arch.config(text=f"Guardado en: {ruta.name}")
            except Exception as e:
                _escribir_i(f"Error generando reporte: {e}", "error")
                if win_info.winfo_exists():
                    lbl_est_i.config(text="Error")

        threading.Thread(target=_run_info, daemon=True).start()

    def salir():
        monitor.detener()
        root.destroy()

    mk_btn(fr_btns, "Verificar Envío",   simular,                           C_PURPLE)
    mk_btn(fr_btns, "Envío Manual",      enviar_ahora,                      C_AZUL)
    mk_btn(fr_btns, "Abrir Procesados",  lambda: abrir_carpeta("enviados"), C_VERDE)
    mk_btn(fr_btns, "Abrir Errores",     lambda: abrir_carpeta("errores"),  C_ROJO)
    mk_btn(fr_btns, "Reenviar Errores",  reenviar_errores,                  C_NARANJA)
    mk_btn(fr_btns, "Correlativos",      ver_reporte,                       C_GRIS)
    mk_btn(fr_btns, "Reporte del Día",   abrir_info,                        C_TEAL)
    mk_btn(fr_btns, "Salir",             salir,                             C_DARK)

    # ── Log en tiempo real ────────────────────────────────────
    tk.Label(root, text="  Actividad en tiempo real",
             font=("Segoe UI", 9, "bold"), bg=C_BG, fg="#757575").pack(anchor="w", padx=16)

    fr_log = tk.Frame(root, bg=C_BG, padx=12)
    fr_log.pack(fill="both", expand=True, pady=(2, 0))

    log_box = scrolledtext.ScrolledText(
        fr_log, height=12, font=("Consolas", 9),
        bg="#1e1e1e", fg="#d4d4d4", wrap="word",
        state="disabled", relief="flat")
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

    # ── Status bar ────────────────────────────────────────────
    status_bar = tk.Frame(root, bg="#cfd8dc", height=24)
    status_bar.pack(fill="x", side="bottom")
    status_bar.pack_propagate(False)
    lbl_hora = tk.Label(status_bar, text="",
                        font=("Segoe UI", 8), bg="#cfd8dc", fg="#37474f")
    lbl_hora.pack(side="right", padx=10)
    tk.Label(status_bar,
             text=(f"Monitoreo activo  |  Facturas: inmediato  |  "
                   f"Boletas: cada 30 min  |  {lbl_modalidad}  |  "
                   f"CPE DisateQ™ {VERSION}  |  @fhertejada™"),
             font=("Segoe UI", 8), bg="#cfd8dc", fg="#37474f").pack(side="left", padx=10)

    def actualizar_hora():
        lbl_hora.config(text=datetime.now().strftime("%d/%m/%Y  %H:%M:%S"))
        root.after(1000, actualizar_hora)
    actualizar_hora()

    # ── Countdown boletas ─────────────────────────────────────
    _ultimo_boleta_ts = [0.0]

    def _actualizar_countdown():
        import time
        if _ultimo_boleta_ts[0] > 0:
            resta = int(intervalo_boleta - (time.time() - _ultimo_boleta_ts[0]))
            if resta > 0:
                mins = resta // 60
                segs = resta % 60
                lbl_timer.config(text=f"{mins}:{segs:02d}")
                lbl_timer_sub.config(text="próximo ciclo boletas")
            else:
                lbl_timer.config(text="—")
                lbl_timer_sub.config(text="boletas listas")
        root.after(1000, _actualizar_countdown)
    _actualizar_countdown()

    # ── Alerta sin conexión ───────────────────────────────────
    _parpadeando     = [False]
    _parpadeo_id     = [None]
    _parpadeo_estado = [True]

    def _alertar_sin_conexion():
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass
        agregar_log("⚠  SIN CONEXIÓN A APIFAS — Verificar internet", "error")
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

    # ── Procesador de cola ────────────────────────────────────
    import time as _time
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
                        lbl_conn_txt.config(
                            text=f"Conectado · {lbl_modalidad}", fg="#00c853")
                        _detener_parpadeo()
                    else:
                        lbl_dot.config(fg="#ef9a9a")
                        lbl_conn_txt.config(text="Sin conexión", fg="#ef9a9a")
                        _alertar_sin_conexion()

                elif tipo == "evento":
                    if msg["estado"] == "enviado":
                        enviados_hoy_cnt[0] += 1
                        lbl_env.config(text=str(enviados_hoy_cnt[0]))

                        # Acumular monto por tipo
                        tipo_doc = msg.get("tipo_doc", "03")
                        monto    = float(msg.get("monto", 0.0))
                        if tipo_doc in _totales:
                            _totales[tipo_doc]["cnt"]   += 1
                            _totales[tipo_doc]["monto"] += monto
                        _actualizar_montos()

                        # Actualizar timestamp último boleta si aplica
                        if tipo_doc in ("03",):
                            _ultimo_boleta_ts[0] = _time.time()

                        # Sub-label enviados: desglose
                        f = _totales["01"]["cnt"]
                        b = _totales["03"]["cnt"]
                        n = _totales["07"]["cnt"] + _totales["08"]["cnt"]
                        partes = []
                        if f: partes.append(f"{f} fact.")
                        if b: partes.append(f"{b} bol.")
                        if n: partes.append(f"{n} notas")
                        lbl_env_sub.config(text=" · ".join(partes))

                        agregar_log(
                            f"OK  [{msg['cpe_tipo']}]  {msg['nombre']}"
                            f"  S/ {monto:,.2f}  —  {msg['msg']}", "ok")

                    elif msg["estado"] == "error":
                        errores_cnt[0] += 1
                        lbl_err.config(text=str(errores_cnt[0]))
                        agregar_log(
                            f"FAIL  [{msg['cpe_tipo']}]  {msg['nombre']}"
                            f"  —  {msg['msg']}", "error")

                    elif msg["estado"] == "sin_detalle":
                        agregar_log(
                            f"SIN DETALLE  {msg['nombre']}  —  {msg['msg']}", "warn")

                elif tipo == "contadores":
                    pend = msg["pendientes"]
                    lbl_pend.config(text=str(pend))
                    lbl_pend_sub.config(text="" if pend == 0 else "en cola")

                elif tipo == "log":
                    agregar_log(msg["msg"], msg.get("tag", "info"))

        except queue.Empty:
            pass
        root.after(500, procesar_cola)

    procesar_cola()

    monitor = monitor_cls(cfg, gui_queue)
    threading.Thread(target=monitor.iniciar, daemon=True).start()
    agregar_log(
        f"Monitoreo iniciado  |  {razon_social}  |  RUC: {ruc}  |  {lbl_modalidad}",
        "info")

    def on_close():
        monitor.detener()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.update_idletasks()
    ancho = max(root.winfo_reqwidth(),  860)
    alto  = max(root.winfo_reqheight(), 600)
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    ancho = min(ancho, sw - 40)
    alto  = min(alto,  sh - 60)
    root.geometry(f"{ancho}x{alto}")
    root.mainloop()
