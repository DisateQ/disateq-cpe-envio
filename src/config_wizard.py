"""
config_wizard.py
================
Asistente de configuracion — CPE DisateQ™
Protegido con PIN de 4 digitos.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import guardar_config, actualizar_endpoints, ENDPOINTS, BASE_DIR
from correlativo_store import establecer_inicio, _cargar as cs_cargar


# PIN maestro DisateQ — solo conocido por el equipo tecnico
_PIN_MAESTRO = "1947"

# ── Colores ──────────────────────────────────────────────────
C_HEADER  = "#1a3a5c"
C_BG      = "#f0f0f0"
C_WHITE   = "#ffffff"
C_GRIS    = "#666666"
C_BORDER  = "#cccccc"
C_DISABLE = "#aaaaaa"
C_AZUL    = "#1565c0"
C_VERDE   = "#2e7d32"


# ── Dialogo PIN ───────────────────────────────────────────────

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


# ── Wizard principal ──────────────────────────────────────────

def abrir_wizard(parent, cfg, callback=None, primer_arranque=False):
    if not primer_arranque:
        if not pedir_pin(parent, cfg):
            return

    win = tk.Toplevel(parent)
    win.title("Configuracion \u2014 CPE DisateQ\u2122")
    win.geometry("580x780")
    win.minsize(560, 720)
    win.resizable(True, True)
    win.configure(bg=C_BG)
    win.grab_set()
    win.focus_set()

    # ── Header ──
    hdr = tk.Frame(win, bg=C_HEADER)
    hdr.pack(fill="x")
    tk.Label(hdr, text="  Configuracion del sistema",
             font=("Segoe UI", 13, "bold"), bg=C_HEADER, fg="white",
             pady=11).pack(anchor="w")

    # ── Botones fijos abajo (antes del contenido) ──
    fr_btns = tk.Frame(win, bg=C_BG, pady=10)
    fr_btns.pack(fill="x", side="bottom", padx=16)
    tk.Frame(fr_btns, bg=C_BORDER, height=1).pack(fill="x", pady=(0, 10))

    # ── Contenido con grid ──
    fr = tk.Frame(win, bg=C_BG)
    fr.pack(fill="both", expand=True, padx=20, pady=10)
    fr.columnconfigure(1, weight=1)

    row = [0]  # contador de fila mutable

    def next_row():
        r = row[0]
        row[0] += 1
        return r

    def seccion(texto):
        r = next_row()
        lbl = tk.Label(fr, text=f"  {texto}",
                       font=("Segoe UI", 9, "bold"),
                       bg=C_HEADER, fg="white", pady=3, padx=6)
        lbl.grid(row=r, column=0, columnspan=2,
                 sticky="ew", pady=(12, 4))

    def campo(label, valor_ini, show=""):
        r = next_row()
        tk.Label(fr, text=label, font=("Segoe UI", 10),
                 bg=C_BG, fg=C_GRIS, anchor="w").grid(
                 row=r, column=0, sticky="w", pady=5, padx=(0, 10))
        var = tk.StringVar(value=valor_ini)
        e = tk.Entry(fr, textvariable=var, font=("Segoe UI", 10),
                     show=show, relief="solid", bd=1)
        e.grid(row=r, column=1, sticky="ew", pady=5)
        return var

    def nota(texto):
        r = next_row()
        tk.Label(fr, text=texto, font=("Segoe UI", 8, "italic"),
                 bg=C_BG, fg=C_DISABLE).grid(
                 row=r, column=1, sticky="w", pady=(0, 4))

    # ══ Empresa ══
    seccion("Datos de la empresa")
    v_razon  = campo("Razon social",
                     cfg.get("EMPRESA", "razon_social",     fallback=""))
    v_nombre = campo("Nombre comercial",
                     cfg.get("EMPRESA", "nombre_comercial", fallback=""))
    nota("Se muestra en la interfaz principal")
    v_ruc    = campo("RUC",
                     cfg.get("EMPRESA", "ruc",              fallback=""))

    # ══ Seguridad ══
    seccion("Seguridad")
    v_pin = campo("PIN de acceso (4 dig.)",
                  cfg.get("SEGURIDAD", "pin", fallback=""), show="•")
    nota("Protege el acceso a esta ventana de configuracion")

    # ══ Series y Correlativos ══
    seccion("Series y correlativos de inicio")

    r_nota = next_row()
    tk.Label(fr,
             text="Ultimo numero YA ENVIADO a SUNAT. Dejar en 0 si es instalacion nueva.",
             font=("Segoe UI", 8, "italic"), bg=C_BG, fg=C_DISABLE,
             wraplength=380, justify="left").grid(
             row=r_nota, column=0, columnspan=2,
             sticky="w", pady=(0, 6))

    salida_act = cfg.get("RUTAS", "salida_txt", fallback=BASE_DIR)
    cs = cs_cargar(salida_act)

    def ultimo(serie_key):
        v = cs.get(serie_key.upper(), {}).get("hasta", 0)
        return str(v) if v else ""

    serie_b = cfg.get("EMPRESA", "serie_boleta",  fallback="B001").upper()
    serie_f = cfg.get("EMPRESA", "serie_factura", fallback="F001").upper()
    serie_n = cfg.get("EMPRESA", "serie_nota",    fallback="NC01").upper()

    def fila_serie(tipo_label, serie_ini, corr_ini):
        r = next_row()
        tk.Label(fr, text=tipo_label, font=("Segoe UI", 10),
                 bg=C_BG, fg=C_GRIS, anchor="w").grid(
                 row=r, column=0, sticky="w", pady=4, padx=(0, 10))

        fr_fila = tk.Frame(fr, bg=C_BG)
        fr_fila.grid(row=r, column=1, sticky="ew", pady=4)

        tk.Label(fr_fila, text="Serie:", font=("Segoe UI", 9),
                 bg=C_BG, fg=C_GRIS).pack(side="left")
        vs = tk.StringVar(value=serie_ini)
        tk.Entry(fr_fila, textvariable=vs, font=("Segoe UI", 10),
                 width=7, relief="solid", bd=1).pack(side="left", padx=(4, 16))

        tk.Label(fr_fila, text="Ultimo enviado:", font=("Segoe UI", 9),
                 bg=C_BG, fg=C_GRIS).pack(side="left")
        vc = tk.StringVar(value=corr_ini)
        tk.Entry(fr_fila, textvariable=vc, font=("Segoe UI", 10),
                 width=10, relief="solid", bd=1).pack(side="left", padx=(4, 0))
        return vs, vc

    v_serie_b, v_corr_b = fila_serie("Boletas",       serie_b, ultimo(serie_b))
    v_serie_f, v_corr_f = fila_serie("Facturas",       serie_f, ultimo(serie_f))
    v_serie_n, v_corr_n = fila_serie("Notas cred/deb", serie_n, ultimo(serie_n))

    # ══ Conexion APIFAS ══
    seccion("Conexion APIFAS")

    r_mod = next_row()
    tk.Label(fr, text="Modalidad", font=("Segoe UI", 10),
             bg=C_BG, fg=C_GRIS, anchor="w").grid(
             row=r_mod, column=0, sticky="w", pady=6, padx=(0, 10))

    fr_mod = tk.Frame(fr, bg=C_BG)
    fr_mod.grid(row=r_mod, column=1, sticky="w", pady=6)
    v_modalidad = tk.StringVar(value=cfg.get("ENVIO", "modalidad", fallback="OSE"))
    for val, lbl in [("OSE", "OSE / PSE"), ("SUNAT", "SEE SUNAT")]:
        tk.Radiobutton(fr_mod, text=lbl, variable=v_modalidad, value=val,
                       font=("Segoe UI", 10), bg=C_BG).pack(side="left", padx=(0, 16))

    r_ep = next_row()
    lbl_ep = tk.Label(fr, text="", font=("Segoe UI", 8, "italic"),
                      bg=C_BG, fg=C_DISABLE)
    lbl_ep.grid(row=r_ep, column=1, sticky="w", pady=(0, 4))

    EP_LABELS = {
        "OSE":   "Envio via OSE / PSE  \u2014  Operador de Servicios Electronicos",
        "SUNAT": "Envio directo SEE SUNAT  \u2014  Factura Electronica SUNAT",
    }
    def actualizar_ep(*a):
        lbl_ep.config(text=EP_LABELS.get(v_modalidad.get().upper(), ""))
    v_modalidad.trace_add("write", actualizar_ep)
    actualizar_ep()

    # ══ Generacion ══
    seccion("Generacion de comprobantes")
    r_gen = next_row()
    fr_gen = tk.Frame(fr, bg=C_BG)
    fr_gen.grid(row=r_gen, column=0, columnspan=2, sticky="w", pady=4)
    tk.Label(fr_gen, text="\u2713  Genera TXT \u2192 valida \u2192 envia a APIFAS",
             font=("Segoe UI", 10), bg=C_BG, fg=C_VERDE).pack(anchor="w")
    tk.Label(fr_gen,
             text="\u23f3  Conversion TXT \u2192 JSON para FFEE Platform DisateQ\u2122 (proximamente)",
             font=("Segoe UI", 8, "italic"), bg=C_BG, fg=C_DISABLE).pack(anchor="w", pady=2)

    # ══ Seguridad ══
    seccion("Seguridad")
    v_pin = campo("PIN de acceso (4 dig.)",
                  cfg.get("SEGURIDAD", "pin", fallback=""), show="\u2022")
    nota("Protege el acceso a esta ventana de configuracion")

    # ── Guardar ──
    def guardar():
        ruc = v_ruc.get().strip()
        if not ruc.isdigit() or len(ruc) != 11:
            messagebox.showerror("Error", "El RUC debe tener 11 digitos numericos.", parent=win)
            return
        if not v_razon.get().strip():
            messagebox.showerror("Error", "La razon social es obligatoria.", parent=win)
            return
        pin = v_pin.get().strip()
        pin_existente = cfg.get("SEGURIDAD", "pin", fallback="").strip()
        # Si el campo esta vacio pero ya habia PIN configurado, mantener el existente
        if not pin and pin_existente:
            pin = pin_existente
        elif not pin.isdigit() or len(pin) != 4:
            messagebox.showerror("Error", "El PIN debe ser exactamente 4 digitos numericos.", parent=win)
            return

        cfg.set("EMPRESA",  "ruc",              ruc)
        cfg.set("EMPRESA",  "razon_social",      v_razon.get().strip())
        cfg.set("EMPRESA",  "nombre_comercial",  v_nombre.get().strip())
        cfg.set("EMPRESA",  "serie_boleta",      v_serie_b.get().strip().upper() or "B001")
        cfg.set("EMPRESA",  "serie_factura",     v_serie_f.get().strip().upper() or "F001")
        cfg.set("EMPRESA",  "serie_nota",        v_serie_n.get().strip().upper() or "NC01")
        cfg.set("ENVIO",    "modalidad",         v_modalidad.get())
        cfg.set("ENVIO",    "modo",              "legacy")
        cfg.set("SEGURIDAD","pin",               pin)

        salida_w = cfg.get("RUTAS", "salida_txt", fallback=BASE_DIR)
        for vs, vc in [(v_serie_b, v_corr_b),
                       (v_serie_f, v_corr_f),
                       (v_serie_n, v_corr_n)]:
            try:
                sw = vs.get().strip().upper()
                cw = int(vc.get().strip()) if vc.get().strip() else 0
                if cw > 0:
                    establecer_inicio(salida_w, sw, cw)
            except ValueError:
                pass

        actualizar_endpoints(cfg)
        guardar_config(cfg)
        messagebox.showinfo("Guardado", "Configuracion guardada correctamente.", parent=win)
        if callback:
            callback()
        win.destroy()

    tk.Button(fr_btns, text="Guardar", command=guardar,
              font=("Segoe UI", 10), bg=C_AZUL, fg="white",
              relief="flat", padx=20, pady=7,
              cursor="hand2", bd=0).pack(side="right")
    tk.Button(fr_btns, text="Cancelar", command=win.destroy,
              font=("Segoe UI", 10), bg="#757575", fg="white",
              relief="flat", padx=20, pady=7,
              cursor="hand2", bd=0).pack(side="right", padx=8)
