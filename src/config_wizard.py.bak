"""
config_wizard.py
================
Asistente de configuracion — CPE DisateQ™
Protegido con PIN de 4 digitos.

Cambios v2.1:
  - Sección APIFAS muestra URLs editables
  - Modalidad CUSTOM desbloquea campos de URL para edición libre
  - Botón "Restaurar URLs por defecto" para volver a valores oficiales
  - Indicador visual cuando las URLs son personalizadas
"""

import tkinter as tk
from tkinter import messagebox
from config import (
    guardar_config, actualizar_endpoints, resetear_endpoints,
    urls_son_personalizadas, ENDPOINTS, BASE_DIR,
)
from correlativo_store import establecer_inicio, _cargar as cs_cargar

# PIN maestro DisateQ — solo conocido por el equipo tecnico
_PIN_MAESTRO = "1947"

# ── Colores ──────────────────────────────────────────────────
C_HEADER  = "#1a3a5c"
C_BG      = "#f0f0f0"
C_GRIS    = "#666666"
C_BORDER  = "#cccccc"
C_DISABLE = "#aaaaaa"
C_AZUL    = "#1565c0"
C_VERDE   = "#2e7d32"
C_AMBER   = "#e65100"


# ── PIN ──────────────────────────────────────────────────────

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


# ── Wizard principal ─────────────────────────────────────────

def abrir_wizard(parent, cfg, callback=None, primer_arranque=False):
    if not primer_arranque:
        if not pedir_pin(parent, cfg):
            return

    win = tk.Toplevel(parent)
    win.title("Configuracion \u2014 CPE DisateQ\u2122")
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

    # ── Botones fijos abajo ──
    fr_btns = tk.Frame(win, bg=C_BG, pady=10)
    fr_btns.pack(fill="x", side="bottom", padx=16)
    tk.Frame(fr_btns, bg=C_BORDER, height=1).pack(fill="x", pady=(0, 8))

    # ── Contenido ──
    fr = tk.Frame(win, bg=C_BG)
    fr.pack(fill="both", expand=True, padx=20, pady=(10, 0))
    fr.columnconfigure(1, weight=1)

    row = [0]

    def next_row():
        r = row[0]; row[0] += 1; return r

    def seccion(texto):
        r = next_row()
        tk.Label(fr, text=f"  {texto}",
                 font=("Segoe UI", 9, "bold"),
                 bg=C_HEADER, fg="white", pady=3, padx=6).grid(
                 row=r, column=0, columnspan=2, sticky="ew", pady=(10, 3))

    def campo(label, valor_ini, show=""):
        r = next_row()
        tk.Label(fr, text=label, font=("Segoe UI", 10),
                 bg=C_BG, fg=C_GRIS, anchor="w").grid(
                 row=r, column=0, sticky="w", pady=4, padx=(0, 10))
        var = tk.StringVar(value=valor_ini)
        tk.Entry(fr, textvariable=var, font=("Segoe UI", 10),
                 show=show, relief="solid", bd=1).grid(
                 row=r, column=1, sticky="ew", pady=4)
        return var

    def nota(texto):
        r = next_row()
        tk.Label(fr, text=texto, font=("Segoe UI", 8, "italic"),
                 bg=C_BG, fg=C_DISABLE).grid(
                 row=r, column=1, sticky="w", pady=(0, 2))

    def fila_serie(tipo_label, serie_ini, corr_ini):
        r = next_row()
        tk.Label(fr, text=tipo_label, font=("Segoe UI", 10),
                 bg=C_BG, fg=C_GRIS, anchor="w").grid(
                 row=r, column=0, sticky="w", pady=3, padx=(0, 10))
        ff = tk.Frame(fr, bg=C_BG)
        ff.grid(row=r, column=1, sticky="ew", pady=3)
        tk.Label(ff, text="Serie:", font=("Segoe UI", 9),
                 bg=C_BG, fg=C_GRIS).pack(side="left")
        vs = tk.StringVar(value=serie_ini)
        tk.Entry(ff, textvariable=vs, font=("Segoe UI", 10),
                 width=7, relief="solid", bd=1).pack(side="left", padx=(4, 14))
        tk.Label(ff, text="Ultimo enviado:", font=("Segoe UI", 9),
                 bg=C_BG, fg=C_GRIS).pack(side="left")
        vc = tk.StringVar(value=corr_ini)
        tk.Entry(ff, textvariable=vc, font=("Segoe UI", 10),
                 width=10, relief="solid", bd=1).pack(side="left", padx=(4, 0))
        return vs, vc

    # ══ Empresa ══════════════════════════════════════════════
    seccion("Datos de la empresa")
    v_ruc    = campo("RUC",              cfg.get("EMPRESA", "ruc",              fallback=""))
    v_razon  = campo("Razon social",     cfg.get("EMPRESA", "razon_social",     fallback=""))
    v_nombre = campo("Nombre comercial", cfg.get("EMPRESA", "nombre_comercial", fallback=""))
    v_alias  = campo("Alias del local",  cfg.get("EMPRESA", "alias",            fallback=""))
    nota("Identifica este local. Ej: Local Grau 1, Sucursal Centro")

    # ══ Seguridad ═════════════════════════════════════════════
    seccion("Seguridad")
    v_pin = campo("PIN de acceso (4 dig.)",
                  cfg.get("SEGURIDAD", "pin", fallback=""), show="\u2022")
    nota("Protege el acceso a esta ventana de configuracion")

    # ══ Series y Correlativos ═════════════════════════════════
    seccion("Series y correlativos de inicio")
    r_n = next_row()
    tk.Label(fr,
             text="Ultimo numero YA ENVIADO a SUNAT por serie. Dejar en 0 si es instalacion nueva.",
             font=("Segoe UI", 8, "italic"), bg=C_BG, fg=C_DISABLE,
             wraplength=360, justify="left").grid(
             row=r_n, column=0, columnspan=2, sticky="w", pady=(0, 4))

    salida_act = cfg.get("RUTAS", "salida_txt", fallback=BASE_DIR)
    cs = cs_cargar(salida_act)

    def ultimo(k):
        v = cs.get(k.upper(), {}).get("hasta", 0)
        return str(v) if v else ""

    serie_b = cfg.get("EMPRESA", "serie_boleta",  fallback="B001").upper()
    serie_f = cfg.get("EMPRESA", "serie_factura", fallback="F001").upper()
    serie_n = cfg.get("EMPRESA", "serie_nota",    fallback="NC01").upper()

    v_serie_b, v_corr_b = fila_serie("Boletas",        serie_b, ultimo(serie_b))
    v_serie_f, v_corr_f = fila_serie("Facturas",        serie_f, ultimo(serie_f))
    v_serie_n, v_corr_n = fila_serie("Notas cred/deb",  serie_n, ultimo(serie_n))

    # ══ Conexión APIFAS ═══════════════════════════════════════
    seccion("Conexion APIFAS")

    # Modalidad (radio buttons: OSE, SUNAT, CUSTOM)
    r_mod = next_row()
    tk.Label(fr, text="Modalidad", font=("Segoe UI", 10),
             bg=C_BG, fg=C_GRIS, anchor="w").grid(
             row=r_mod, column=0, sticky="w", pady=5, padx=(0, 10))
    fr_mod = tk.Frame(fr, bg=C_BG)
    fr_mod.grid(row=r_mod, column=1, sticky="w", pady=5)
    v_modalidad = tk.StringVar(value=cfg.get("ENVIO", "modalidad", fallback="OSE").upper())
    for val, lbl in [("OSE", "OSE / PSE"), ("SUNAT", "SEE SUNAT"), ("CUSTOM", "URL personalizada")]:
        tk.Radiobutton(fr_mod, text=lbl, variable=v_modalidad, value=val,
                       font=("Segoe UI", 10), bg=C_BG,
                       command=_actualizar_urls_por_modalidad_factory(
                           v_modalidad, None, None, None  # se inyectan abajo
                       )).pack(side="left", padx=(0, 12))

    # Descripción dinámica de la modalidad
    r_ep = next_row()
    lbl_ep = tk.Label(fr, text="", font=("Segoe UI", 8, "italic"),
                      bg=C_BG, fg=C_DISABLE)
    lbl_ep.grid(row=r_ep, column=1, sticky="w", pady=(0, 3))

    EP_LABELS = {
        "OSE":    "Envio via OSE / PSE  \u2014  Operador de Servicios Electronicos",
        "SUNAT":  "Envio directo SEE SUNAT  \u2014  Factura Electronica SUNAT",
        "CUSTOM": "URL libre  \u2014  Ingrese las URLs manualmente",
    }

    # ── Campo URL envío ──
    r_url = next_row()
    tk.Label(fr, text="URL envio", font=("Segoe UI", 10),
             bg=C_BG, fg=C_GRIS, anchor="w").grid(
             row=r_url, column=0, sticky="w", pady=4, padx=(0, 10))
    v_url_envio = tk.StringVar(value=cfg.get("ENVIO", "url_envio", fallback=""))
    entry_url_envio = tk.Entry(fr, textvariable=v_url_envio, font=("Segoe UI", 9),
                               relief="solid", bd=1)
    entry_url_envio.grid(row=r_url, column=1, sticky="ew", pady=4)

    # ── Campo URL anulación ──
    r_anul = next_row()
    tk.Label(fr, text="URL anulacion", font=("Segoe UI", 10),
             bg=C_BG, fg=C_GRIS, anchor="w").grid(
             row=r_anul, column=0, sticky="w", pady=4, padx=(0, 10))
    v_url_anulacion = tk.StringVar(value=cfg.get("ENVIO", "url_anulacion", fallback=""))
    entry_url_anulacion = tk.Entry(fr, textvariable=v_url_anulacion, font=("Segoe UI", 9),
                                   relief="solid", bd=1)
    entry_url_anulacion.grid(row=r_anul, column=1, sticky="ew", pady=4)

    # ── Indicador de URLs personalizadas ──
    r_ind = next_row()
    lbl_url_custom = tk.Label(fr, text="", font=("Segoe UI", 8, "italic"),
                              bg=C_BG, fg=C_AMBER)
    lbl_url_custom.grid(row=r_ind, column=1, sticky="w", pady=(0, 2))

    # ── Botón restaurar URLs ──
    r_rst = next_row()
    btn_restaurar = tk.Button(fr, text="Restaurar URLs por defecto",
                              font=("Segoe UI", 8), bg=C_BG, fg=C_AZUL,
                              relief="flat", bd=0, cursor="hand2",
                              command=lambda: _restaurar_urls(
                                  v_modalidad, v_url_envio, v_url_anulacion, lbl_url_custom
                              ))
    btn_restaurar.grid(row=r_rst, column=1, sticky="w", pady=(0, 4))

    # ── Lógica dinámica de URLs ──
    def _actualizar_ui_urls(*_):
        """Actualiza labels, estados y contenido de campos según modalidad."""
        mod = v_modalidad.get().upper()
        lbl_ep.config(text=EP_LABELS.get(mod, ""))

        if mod == "CUSTOM":
            # URLs libres — habilitadas para editar
            entry_url_envio.config(state="normal", fg="#000000")
            entry_url_anulacion.config(state="normal", fg="#000000")
            btn_restaurar.config(state="disabled")
            lbl_url_custom.config(text="\u270f  URLs personalizadas activas")
        else:
            # Cargar URLs del preset elegido
            v_url_envio.set(ENDPOINTS[mod]["envio"])
            v_url_anulacion.set(ENDPOINTS[mod]["anulacion"])
            # Solo lectura para evitar edición accidental
            entry_url_envio.config(state="readonly", fg=C_GRIS)
            entry_url_anulacion.config(state="readonly", fg=C_GRIS)
            btn_restaurar.config(state="disabled")
            lbl_url_custom.config(text="")

    def _restaurar_urls(v_mod, v_url, v_anul, lbl):
        mod = v_mod.get().upper()
        if mod in ENDPOINTS and mod != "CUSTOM":
            v_url.set(ENDPOINTS[mod]["envio"])
            v_anul.set(ENDPOINTS[mod]["anulacion"])
            lbl.config(text="")

    # Inicializar estado de los campos al abrir
    v_modalidad.trace_add("write", _actualizar_ui_urls)
    _actualizar_ui_urls()   # estado inicial

    # Si el .ini tiene URLs personalizadas que no son CUSTOM, mostrar aviso
    if urls_son_personalizadas(cfg) and v_modalidad.get().upper() != "CUSTOM":
        lbl_url_custom.config(
            text="\u26a0  Las URLs fueron modificadas manualmente en el .ini"
        )
        entry_url_envio.config(state="normal", fg="#000000")
        entry_url_anulacion.config(state="normal", fg="#000000")
        btn_restaurar.config(state="normal")

    # ══ Generacion ════════════════════════════════════════════
    seccion("Generacion de comprobantes")
    r_gen = next_row()
    fr_gen = tk.Frame(fr, bg=C_BG)
    fr_gen.grid(row=r_gen, column=0, columnspan=2, sticky="w", pady=3)
    tk.Label(fr_gen,
             text="\u2713  Genera TXT \u2192 valida \u2192 envia a APIFAS",
             font=("Segoe UI", 10), bg=C_BG, fg=C_VERDE).pack(anchor="w")
    tk.Label(fr_gen,
             text="\u23f3  Integracion con Plataforma DisateQ\u2122 CPE (proximamente)",
             font=("Segoe UI", 8, "italic"), bg=C_BG, fg=C_DISABLE).pack(anchor="w", pady=1)

    # Espaciador final
    tk.Frame(fr, bg=C_BG, height=8).grid(row=next_row(), column=0, columnspan=2)

    # ── Calcular altura y centrar ──
    win.update_idletasks()
    contenido_h = fr.winfo_reqheight()
    header_h    = hdr.winfo_reqheight()
    btns_h      = fr_btns.winfo_reqheight()
    total_h     = contenido_h + header_h + btns_h + 40
    ancho       = 600
    pantalla_h  = win.winfo_screenheight()
    alto_final  = min(total_h, pantalla_h - 80)
    win.geometry(f"{ancho}x{alto_final}")
    win.minsize(560, min(alto_final, 600))

    # ── Guardar ───────────────────────────────────────────────
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
        if not pin and pin_existente:
            pin = pin_existente
        elif not pin.isdigit() or len(pin) != 4:
            messagebox.showerror("Error", "El PIN debe ser exactamente 4 digitos.", parent=win)
            return

        # Validar URLs si modalidad es CUSTOM
        modalidad = v_modalidad.get().upper()
        url_envio    = v_url_envio.get().strip()
        url_anulacion = v_url_anulacion.get().strip()

        if modalidad == "CUSTOM":
            if not url_envio.startswith("http"):
                messagebox.showerror(
                    "Error", "URL de envio invalida. Debe comenzar con http:// o https://",
                    parent=win)
                return
            if url_anulacion and not url_anulacion.startswith("http"):
                messagebox.showerror(
                    "Error", "URL de anulacion invalida. Debe comenzar con http:// o https://",
                    parent=win)
                return

        # Guardar empresa
        cfg.set("EMPRESA", "ruc",              ruc)
        cfg.set("EMPRESA", "razon_social",     v_razon.get().strip())
        cfg.set("EMPRESA", "nombre_comercial", v_nombre.get().strip())
        cfg.set("EMPRESA", "alias",            v_alias.get().strip())
        cfg.set("EMPRESA", "serie_boleta",     v_serie_b.get().strip().upper() or "B001")
        cfg.set("EMPRESA", "serie_factura",    v_serie_f.get().strip().upper() or "F001")
        cfg.set("EMPRESA", "serie_nota",       v_serie_n.get().strip().upper() or "NC01")

        # Guardar envío
        cfg.set("ENVIO", "modalidad",    modalidad)
        cfg.set("ENVIO", "modo",         "legacy")
        cfg.set("ENVIO", "url_envio",    url_envio)
        cfg.set("ENVIO", "url_anulacion", url_anulacion)

        cfg.set("SEGURIDAD", "pin", pin)

        # Correlativos
        salida_w = cfg.get("RUTAS", "salida_txt", fallback=BASE_DIR)
        for vs, vc in [(v_serie_b, v_corr_b), (v_serie_f, v_corr_f), (v_serie_n, v_corr_n)]:
            try:
                sw = vs.get().strip().upper()
                cw = int(vc.get().strip()) if vc.get().strip() else 0
                if cw > 0:
                    establecer_inicio(salida_w, sw, cw)
            except ValueError:
                pass

        # Nota: NO llamamos a actualizar_endpoints() aquí porque
        # las URLs ya fueron seteadas explícitamente arriba.
        guardar_config(cfg)
        messagebox.showinfo("Guardado", "Configuracion guardada correctamente.", parent=win)

        if callback:
            callback()
        win.destroy()

    tk.Button(fr_btns, text="Guardar configuracion", command=guardar,
              font=("Segoe UI", 10, "bold"), bg=C_VERDE, fg="white",
              relief="flat", padx=18, pady=7, cursor="hand2", bd=0).pack(side="right")
    tk.Button(fr_btns, text="Cancelar",
              command=win.destroy,
              font=("Segoe UI", 10), bg=C_BG, fg=C_GRIS,
              relief="flat", padx=12, pady=7, cursor="hand2", bd=0).pack(side="right", padx=8)


def _actualizar_urls_por_modalidad_factory(*_):
    """Placeholder para compatibilidad — la lógica real está en _actualizar_ui_urls."""
    return lambda: None
