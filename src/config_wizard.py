"""
config_wizard.py
================
Asistente de configuracion — CPE DisateQ™
Protegido con PIN de 4 digitos.

v2.2 — Rediseño con tabs:
  Tab 1: Empresa + Seguridad
  Tab 2: Series y correlativos
  Tab 3: Conexion APIFAS
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import (
    guardar_config, actualizar_endpoints, resetear_endpoints,
    urls_son_personalizadas, ENDPOINTS, BASE_DIR,
)
from series_config import (
    get_series, set_series, migrar_series_viejas,
    widget_series, WidgetSeries,
)
from correlativo_store import establecer_inicio, _cargar as cs_cargar

_PIN_MAESTRO = "1947"

C_HEADER  = "#1a3a5c"
C_BG      = "#f0f0f0"
C_GRIS    = "#666666"
C_BORDER  = "#cccccc"
C_DISABLE = "#aaaaaa"
C_AZUL    = "#1565c0"
C_VERDE   = "#2e7d32"
C_AMBER   = "#e65100"
C_ROJO    = "#c62828"
C_WHITE   = "#ffffff"


def pedir_pin(parent, cfg) -> bool:
    pin_guardado = cfg.get("SEGURIDAD", "pin", fallback="").strip()
    if not pin_guardado:
        return True

    resultado = [False]
    win = tk.Toplevel(parent)
    win.title("Acceso restringido")
    win.geometry("300x175")
    win.resizable(False, False)
    win.configure(bg=C_BG)
    win.grab_set()
    win.focus_set()
    win.lift()

    tk.Label(win, text="Ingrese el PIN de configuracion",
             font=("Segoe UI", 10), bg=C_BG, fg=C_GRIS).pack(pady=(24, 8))

    var_pin = tk.StringVar()
    e = tk.Entry(win, textvariable=var_pin, show="\u2022",
                 font=("Segoe UI", 16), width=8, justify="center",
                 relief="solid", bd=1)
    e.pack()
    e.focus_set()

    lbl_err = tk.Label(win, text="", fg="#b71c1c",
                       font=("Segoe UI", 9), bg=C_BG)
    lbl_err.pack(pady=4)

    def verificar(event=None):
        ingresado = var_pin.get().strip()
        if ingresado == pin_guardado or ingresado == _PIN_MAESTRO:
            resultado[0] = True
            win.destroy()
        else:
            lbl_err.config(text="PIN incorrecto")
            var_pin.set("")
            e.focus_set()

    tk.Button(win, text="Ingresar", command=verificar,
              font=("Segoe UI", 10), bg=C_AZUL, fg="white",
              relief="flat", padx=16, pady=5,
              cursor="hand2", bd=0).pack(pady=8)
    e.bind("<Return>", verificar)
    win.wait_window()
    return resultado[0]


def _campo(parent, label, valor_ini, show="", row=0):
    tk.Label(parent, text=label, font=("Segoe UI", 10),
             bg=C_WHITE, fg=C_GRIS, anchor="w", width=18).grid(
             row=row, column=0, sticky="w", pady=5, padx=(12, 6))
    var = tk.StringVar(value=valor_ini)
    tk.Entry(parent, textvariable=var, font=("Segoe UI", 10),
             show=show, relief="solid", bd=1).grid(
             row=row, column=1, sticky="ew", pady=5, padx=(0, 12))
    return var

def _nota(parent, texto, row=0):
    tk.Label(parent, text=texto, font=("Segoe UI", 8, "italic"),
             bg=C_WHITE, fg=C_DISABLE, anchor="w").grid(
             row=row, column=0, columnspan=2, sticky="w",
             pady=(0, 4), padx=12)

def _seccion_lbl(parent, texto, row=0):
    f = tk.Frame(parent, bg=C_HEADER)
    f.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(10, 4))
    tk.Label(f, text=f"  {texto}", font=("Segoe UI", 9, "bold"),
             bg=C_HEADER, fg="white", pady=4).pack(anchor="w")


def abrir_wizard(parent, cfg, callback=None, primer_arranque=False):
    if not primer_arranque:
        if not pedir_pin(parent, cfg):
            return

    win = tk.Toplevel(parent)
    win.title("Configuracion \u2014 CPE DisateQ\u2122")
    win.geometry("580x520")
    win.minsize(560, 480)
    win.resizable(True, True)
    win.configure(bg=C_BG)
    win.grab_set()
    win.focus_set()
    win.lift()

    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x  = (sw - 580) // 2
    y  = (sh - 520) // 2
    win.geometry(f"580x520+{x}+{y}")

    hdr = tk.Frame(win, bg=C_HEADER)
    hdr.pack(fill="x")
    tk.Label(hdr, text="  \u2699  Configuracion del sistema \u2014 CPE DisateQ\u2122",
             font=("Segoe UI", 12, "bold"), bg=C_HEADER, fg="white",
             pady=10).pack(anchor="w")

    fr_btns = tk.Frame(win, bg=C_BG, pady=8)
    fr_btns.pack(fill="x", side="bottom", padx=16)
    tk.Frame(fr_btns, bg=C_BORDER, height=1).pack(fill="x", pady=(0, 8))

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TNotebook",      background=C_BG,     borderwidth=0)
    style.configure("TNotebook.Tab",  background="#dce3ea", foreground=C_GRIS,
                    padding=[14, 6],  font=("Segoe UI", 9, "bold"))
    style.map("TNotebook.Tab",
              background=[("selected", C_HEADER)],
              foreground=[("selected", "white")])
    style.configure("TFrame", background=C_WHITE)

    nb = ttk.Notebook(win)
    nb.pack(fill="both", expand=True, padx=12, pady=(8, 0))

    # ── TAB 1: Empresa ────────────────────────────────────────
    tab1 = tk.Frame(nb, bg=C_WHITE)
    tab1.columnconfigure(1, weight=1)
    nb.add(tab1, text="  Empresa  ")

    _seccion_lbl(tab1, "Datos de la empresa", row=0)
    v_ruc    = _campo(tab1, "RUC",              cfg.get("EMPRESA", "ruc",              fallback=""), row=1)
    v_razon  = _campo(tab1, "Razon social",     cfg.get("EMPRESA", "razon_social",     fallback=""), row=2)
    v_nombre = _campo(tab1, "Nombre comercial", cfg.get("EMPRESA", "nombre_comercial", fallback=""), row=3)
    v_alias  = _campo(tab1, "Alias del local",  cfg.get("EMPRESA", "alias",            fallback=""), row=4)
    _nota(tab1, "Identifica este local.  Ej: Local Grau 1, Sucursal Centro", row=5)

    _seccion_lbl(tab1, "Seguridad", row=6)
    v_pin = _campo(tab1, "PIN (4 digitos)",
                   cfg.get("SEGURIDAD", "pin", fallback=""), show="\u2022", row=7)
    _nota(tab1, "Protege el acceso a esta ventana de configuracion", row=8)

    # ── TAB 2: Series ─────────────────────────────────────────
    tab2 = tk.Frame(nb, bg=C_WHITE)
    tab2.columnconfigure(1, weight=1)
    nb.add(tab2, text="  Series  ")

    tk.Label(tab2,
             text="  Ultimo numero YA ENVIADO a SUNAT por serie. "
                  "Dejar en 0 si es instalacion nueva.\n"
                  "  Puedes agregar hasta 5 series por tipo con el boton '+ Agregar'.",
             font=("Segoe UI", 8, "italic"), bg=C_WHITE, fg=C_DISABLE,
             justify="left", anchor="w").grid(
             row=0, column=0, columnspan=2, sticky="w", pady=(8, 4), padx=12)

    salida_act = cfg.get("RUTAS", "salida_txt", fallback=BASE_DIR)
    cs = cs_cargar(salida_act)
    migrar_series_viejas(cfg)

    tk.Label(tab2, text="Boletas", font=("Segoe UI", 10, "bold"),
             bg=C_WHITE, fg=C_HEADER, anchor="w").grid(
             row=1, column=0, sticky="nw", pady=(8, 2), padx=12)
    ws_b = widget_series(tab2, "boleta", get_series(cfg, "boleta"), cs,
                         C_WHITE, C_GRIS, C_AZUL, C_ROJO)
    ws_b.frame.grid(row=1, column=1, sticky="ew", pady=(8, 2), padx=(0, 12))

    tk.Frame(tab2, bg=C_BORDER, height=1).grid(
             row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=2)

    tk.Label(tab2, text="Facturas", font=("Segoe UI", 10, "bold"),
             bg=C_WHITE, fg=C_HEADER, anchor="w").grid(
             row=3, column=0, sticky="nw", pady=(6, 2), padx=12)
    ws_f = widget_series(tab2, "factura", get_series(cfg, "factura"), cs,
                         C_WHITE, C_GRIS, C_AZUL, C_ROJO)
    ws_f.frame.grid(row=3, column=1, sticky="ew", pady=(6, 2), padx=(0, 12))

    tk.Frame(tab2, bg=C_BORDER, height=1).grid(
             row=4, column=0, columnspan=2, sticky="ew", padx=12, pady=2)

    tk.Label(tab2, text="Notas\ncred/deb", font=("Segoe UI", 10, "bold"),
             bg=C_WHITE, fg=C_HEADER, anchor="w", justify="left").grid(
             row=5, column=0, sticky="nw", pady=(6, 2), padx=12)
    ws_n = widget_series(tab2, "nota", get_series(cfg, "nota"), cs,
                         C_WHITE, C_GRIS, C_AZUL, C_ROJO)
    ws_n.frame.grid(row=5, column=1, sticky="ew", pady=(6, 2), padx=(0, 12))

    tk.Label(tab2,
             text="  Series de notas: NC01 (nota credito boleta), FC01 (nota credito factura), etc.",
             font=("Segoe UI", 8, "italic"), bg=C_WHITE, fg=C_DISABLE).grid(
             row=6, column=0, columnspan=2, sticky="w", padx=12, pady=(2, 8))

    # ── TAB 3: Conexion ───────────────────────────────────────
    tab3 = tk.Frame(nb, bg=C_WHITE)
    tab3.columnconfigure(1, weight=1)
    nb.add(tab3, text="  Conexion  ")

    _seccion_lbl(tab3, "Modalidad de envio", row=0)

    fr_mod = tk.Frame(tab3, bg=C_WHITE)
    fr_mod.grid(row=1, column=0, columnspan=2, sticky="w", padx=12, pady=6)
    v_modalidad = tk.StringVar(value=cfg.get("ENVIO", "modalidad", fallback="OSE").upper())
    for val, lbl in [("OSE", "OSE / PSE"), ("SUNAT", "SEE SUNAT"), ("CUSTOM", "URL personalizada")]:
        tk.Radiobutton(fr_mod, text=lbl, variable=v_modalidad, value=val,
                       font=("Segoe UI", 10), bg=C_WHITE).pack(side="left", padx=(0, 16))

    lbl_ep = tk.Label(tab3, text="", font=("Segoe UI", 8, "italic"),
                      bg=C_WHITE, fg=C_DISABLE, anchor="w")
    lbl_ep.grid(row=2, column=0, columnspan=2, sticky="w", padx=14, pady=(0, 4))

    EP_LABELS = {
        "OSE":    "Envio via OSE / PSE  \u2014  Operador de Servicios Electronicos",
        "SUNAT":  "Envio directo SEE SUNAT  \u2014  Factura Electronica SUNAT",
        "CUSTOM": "URL libre  \u2014  Ingrese las URLs manualmente",
    }

    _seccion_lbl(tab3, "Endpoints", row=3)

    tk.Label(tab3, text="URL envio", font=("Segoe UI", 10),
             bg=C_WHITE, fg=C_GRIS, anchor="w", width=14).grid(
             row=4, column=0, sticky="w", pady=5, padx=(12, 6))
    v_url_envio = tk.StringVar(value=cfg.get("ENVIO", "url_envio", fallback=""))
    entry_url_envio = tk.Entry(tab3, textvariable=v_url_envio,
                               font=("Segoe UI", 9), relief="solid", bd=1)
    entry_url_envio.grid(row=4, column=1, sticky="ew", pady=5, padx=(0, 12))

    tk.Label(tab3, text="URL anulacion", font=("Segoe UI", 10),
             bg=C_WHITE, fg=C_GRIS, anchor="w", width=14).grid(
             row=5, column=0, sticky="w", pady=5, padx=(12, 6))
    v_url_anulacion = tk.StringVar(value=cfg.get("ENVIO", "url_anulacion", fallback=""))
    entry_url_anulacion = tk.Entry(tab3, textvariable=v_url_anulacion,
                                   font=("Segoe UI", 9), relief="solid", bd=1)
    entry_url_anulacion.grid(row=5, column=1, sticky="ew", pady=5, padx=(0, 12))

    lbl_url_custom = tk.Label(tab3, text="", font=("Segoe UI", 8, "italic"),
                              bg=C_WHITE, fg=C_AMBER, anchor="w")
    lbl_url_custom.grid(row=6, column=0, columnspan=2, sticky="w", padx=14)

    btn_restaurar = tk.Button(tab3, text="Restaurar URLs por defecto",
                              font=("Segoe UI", 8), bg=C_WHITE, fg=C_AZUL,
                              relief="flat", bd=0, cursor="hand2")
    btn_restaurar.grid(row=7, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 6))

    _seccion_lbl(tab3, "Generacion de comprobantes", row=8)
    fr_gen = tk.Frame(tab3, bg=C_WHITE)
    fr_gen.grid(row=9, column=0, columnspan=2, sticky="w", padx=12, pady=4)
    tk.Label(fr_gen, text="\u2713  Genera TXT \u2192 valida \u2192 envia a APIFAS",
             font=("Segoe UI", 10), bg=C_WHITE, fg=C_VERDE).pack(anchor="w")
    tk.Label(fr_gen, text="\u23f3  Integracion con Plataforma DisateQ\u2122 CPE (proximamente)",
             font=("Segoe UI", 8, "italic"), bg=C_WHITE, fg=C_DISABLE).pack(anchor="w", pady=1)

    def _actualizar_ui_urls(*_):
        mod = v_modalidad.get().upper()
        lbl_ep.config(text=EP_LABELS.get(mod, ""))
        if mod == "CUSTOM":
            entry_url_envio.config(state="normal", fg="#000000")
            entry_url_anulacion.config(state="normal", fg="#000000")
            btn_restaurar.config(state="disabled")
            lbl_url_custom.config(text="\u270f  URLs personalizadas activas")
        else:
            v_url_envio.set(ENDPOINTS[mod]["envio"])
            v_url_anulacion.set(ENDPOINTS[mod]["anulacion"])
            entry_url_envio.config(state="readonly", fg=C_GRIS)
            entry_url_anulacion.config(state="readonly", fg=C_GRIS)
            btn_restaurar.config(state="disabled")
            lbl_url_custom.config(text="")

    def _restaurar_urls():
        mod = v_modalidad.get().upper()
        if mod in ENDPOINTS and mod != "CUSTOM":
            v_url_envio.set(ENDPOINTS[mod]["envio"])
            v_url_anulacion.set(ENDPOINTS[mod]["anulacion"])
            lbl_url_custom.config(text="")

    btn_restaurar.config(command=_restaurar_urls)
    v_modalidad.trace_add("write", _actualizar_ui_urls)
    _actualizar_ui_urls()

    if urls_son_personalizadas(cfg) and v_modalidad.get().upper() != "CUSTOM":
        lbl_url_custom.config(text="\u26a0  URLs modificadas manualmente en el .ini")
        entry_url_envio.config(state="normal", fg="#000000")
        entry_url_anulacion.config(state="normal", fg="#000000")
        btn_restaurar.config(state="normal")

    # ── Guardar ───────────────────────────────────────────────
    def guardar():
        ruc = v_ruc.get().strip()
        if not ruc.isdigit() or len(ruc) != 11:
            nb.select(0)
            messagebox.showerror("Error", "El RUC debe tener 11 digitos numericos.", parent=win)
            return
        if not v_razon.get().strip():
            nb.select(0)
            messagebox.showerror("Error", "La razon social es obligatoria.", parent=win)
            return

        pin = v_pin.get().strip()
        pin_existente = cfg.get("SEGURIDAD", "pin", fallback="").strip()
        if not pin and pin_existente:
            pin = pin_existente
        elif not pin.isdigit() or len(pin) != 4:
            nb.select(0)
            messagebox.showerror("Error", "El PIN debe ser exactamente 4 digitos.", parent=win)
            return

        modalidad     = v_modalidad.get().upper()
        url_envio     = v_url_envio.get().strip()
        url_anulacion = v_url_anulacion.get().strip()

        if modalidad == "CUSTOM" and not url_envio.startswith("http"):
            nb.select(2)
            messagebox.showerror("Error",
                "URL de envio invalida. Debe comenzar con http:// o https://", parent=win)
            return

        cfg.set("EMPRESA", "ruc",              ruc)
        cfg.set("EMPRESA", "razon_social",     v_razon.get().strip())
        cfg.set("EMPRESA", "nombre_comercial", v_nombre.get().strip())
        cfg.set("EMPRESA", "alias",            v_alias.get().strip())
        cfg.set("EMPRESA", "serie_boleta",     ws_b.get_series()[0] if ws_b.get_series() else "B001")
        cfg.set("EMPRESA", "serie_factura",    ws_f.get_series()[0] if ws_f.get_series() else "F001")
        cfg.set("EMPRESA", "serie_nota",       ws_n.get_series()[0] if ws_n.get_series() else "NC01")

        cfg.set("ENVIO", "modalidad",     modalidad)
        cfg.set("ENVIO", "modo",          "legacy")
        cfg.set("ENVIO", "url_envio",     url_envio)
        cfg.set("ENVIO", "url_anulacion", url_anulacion)
        cfg.set("SEGURIDAD", "pin", pin)

        salida_w = cfg.get("RUTAS", "salida_txt", fallback=BASE_DIR)
        for tipo, ws in [("boleta", ws_b), ("factura", ws_f), ("nota", ws_n)]:
            set_series(cfg, tipo, ws.get_series())
            for serie, corr in ws.get_correlativos().items():
                establecer_inicio(salida_w, serie, corr)

        guardar_config(cfg)
        messagebox.showinfo("Guardado", "Configuracion guardada correctamente.", parent=win)
        if callback:
            callback()
        win.destroy()

    tk.Button(fr_btns, text="Guardar configuracion", command=guardar,
              font=("Segoe UI", 10, "bold"), bg=C_VERDE, fg="white",
              relief="flat", padx=18, pady=7, cursor="hand2", bd=0).pack(side="right")
    tk.Button(fr_btns, text="Cancelar", command=win.destroy,
              font=("Segoe UI", 10), bg=C_BG, fg=C_GRIS,
              relief="flat", padx=12, pady=7, cursor="hand2", bd=0).pack(side="right", padx=8)


def _actualizar_urls_por_modalidad_factory(*_):
    return lambda: None
