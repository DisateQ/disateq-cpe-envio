"""
series_config.py
================
Gestión de múltiples series por local — CPE DisateQ™ v2.1

Responsabilidad única: leer, escribir y validar la configuración
de series de comprobantes en el .ini.

Permite que un local maneje múltiples series por tipo:
  Boletas:  B001, B002, B003
  Facturas: F001, F002
  Notas:    NC01

Formato en ffee_config.ini:
  [EMPRESA]
  series_boleta  = B001,B002,B003
  series_factura = F001
  series_nota    = NC01

Retrocompatibilidad:
  Si el .ini tiene claves antiguas (serie_boleta, serie_factura, serie_nota)
  se leen y convierten automáticamente al nuevo formato sin pérdida de datos.

Uso:
  from series_config import get_series, set_series, todas_las_series
  
  boletas = get_series(cfg, "boleta")   # → ["B001", "B002", "B003"]
  set_series(cfg, "boleta", ["B001", "B002"])
  todas   = todas_las_series(cfg)       # → ["B001","B002","F001","NC01"]
"""

import re
import configparser

# ── Claves en el .ini ────────────────────────────────────────
_CLAVE_NUEVA = {
    "boleta":  "series_boleta",
    "factura": "series_factura",
    "nota":    "series_nota",
}
_CLAVE_VIEJA = {
    "boleta":  "serie_boleta",
    "factura": "serie_factura",
    "nota":    "serie_nota",
}
_DEFAULT = {
    "boleta":  "B001",
    "factura": "F001",
    "nota":    "NC01",
}

# ── Validación de formato de serie ───────────────────────────
# Serie válida: 1-3 letras + 2-3 dígitos  (B001, F001, NC01, B002...)
_RE_SERIE = re.compile(r'^[A-Z]{1,3}\d{2,3}$')


def serie_valida(serie: str) -> bool:
    """Retorna True si el formato de serie es válido (ej: B001, F001, NC01)."""
    return bool(_RE_SERIE.match(serie.strip().upper()))


# ── Lectura ──────────────────────────────────────────────────

def get_series(cfg: configparser.ConfigParser, tipo: str) -> list[str]:
    """
    Retorna la lista de series configuradas para el tipo dado.

    Args:
        tipo: "boleta" | "factura" | "nota"

    Returns:
        Lista de series en mayúsculas. Mínimo ["B001"], ["F001"] o ["NC01"]
        si no hay configuración.

    Retrocompatibilidad:
        Si existe la clave nueva (series_boleta) la usa.
        Si solo existe la clave vieja (serie_boleta) migra automáticamente.
    """
    if tipo not in _CLAVE_NUEVA:
        raise ValueError(f"Tipo inválido: '{tipo}'. Usar: boleta, factura, nota")

    clave_nueva = _CLAVE_NUEVA[tipo]
    clave_vieja = _CLAVE_VIEJA[tipo]
    default     = _DEFAULT[tipo]

    # Intentar clave nueva primero
    raw = cfg.get("EMPRESA", clave_nueva, fallback="").strip()

    # Si no existe, intentar clave vieja (retrocompatibilidad)
    if not raw:
        raw = cfg.get("EMPRESA", clave_vieja, fallback="").strip()

    # Si tampoco existe, usar default
    if not raw:
        raw = default

    # Parsear lista separada por comas, filtrar inválidas
    series = []
    for s in raw.split(","):
        s = s.strip().upper()
        if s and serie_valida(s):
            series.append(s)

    # Garantizar al menos la serie default si la lista quedó vacía
    return series if series else [default]


def set_series(
    cfg:   configparser.ConfigParser,
    tipo:  str,
    series: list[str],
) -> None:
    """
    Guarda la lista de series para el tipo dado.
    Escribe en la clave nueva (series_boleta, etc.)
    y elimina la clave vieja si existe para evitar duplicados.

    Args:
        tipo:   "boleta" | "factura" | "nota"
        series: lista de series — se validan y normalizan a mayúsculas
    """
    if tipo not in _CLAVE_NUEVA:
        raise ValueError(f"Tipo inválido: '{tipo}'")

    # Normalizar y validar
    series_limpias = []
    for s in series:
        s = s.strip().upper()
        if s and serie_valida(s):
            if s not in series_limpias:
                series_limpias.append(s)

    if not series_limpias:
        series_limpias = [_DEFAULT[tipo]]

    valor = ",".join(series_limpias)
    cfg.set("EMPRESA", _CLAVE_NUEVA[tipo], valor)

    # Eliminar clave vieja si existe (migración limpia)
    if cfg.has_option("EMPRESA", _CLAVE_VIEJA[tipo]):
        cfg.remove_option("EMPRESA", _CLAVE_VIEJA[tipo])


def todas_las_series(cfg: configparser.ConfigParser) -> list[str]:
    """
    Retorna todas las series configuradas (boletas + facturas + notas)
    en orden: boletas primero, luego facturas, luego notas.
    """
    resultado = []
    for tipo in ("boleta", "factura", "nota"):
        for s in get_series(cfg, tipo):
            if s not in resultado:
                resultado.append(s)
    return resultado


def tipo_de_serie(serie: str) -> str:
    """
    Infiere el tipo de una serie por su prefijo.
    Returns: "factura" | "nota" | "boleta"
    """
    s = serie.strip().upper()
    if s.startswith("F"):
        return "factura"
    if s.startswith("N"):
        return "nota"
    return "boleta"


def migrar_series_viejas(cfg: configparser.ConfigParser) -> bool:
    """
    Migra claves antiguas (serie_boleta) al nuevo formato (series_boleta).
    Idempotente — se puede llamar múltiples veces sin problema.
    Retorna True si realizó alguna migración.
    """
    migrado = False
    for tipo in ("boleta", "factura", "nota"):
        clave_vieja = _CLAVE_VIEJA[tipo]
        clave_nueva = _CLAVE_NUEVA[tipo]
        if (cfg.has_option("EMPRESA", clave_vieja) and
                not cfg.has_option("EMPRESA", clave_nueva)):
            valor_viejo = cfg.get("EMPRESA", clave_vieja, fallback="").strip()
            if valor_viejo:
                cfg.set("EMPRESA", clave_nueva, valor_viejo)
                cfg.remove_option("EMPRESA", clave_vieja)
                migrado = True
    return migrado


# ── Widget Tkinter para el wizard ─────────────────────────────

def widget_series(
    parent,
    tipo:         str,
    series_ini:   list[str],
    correlativos: dict,
    C_BG:         str = "#f0f0f0",
    C_GRIS:       str = "#666666",
    C_AZUL:       str = "#1565c0",
    C_ROJO:       str = "#c62828",
) -> "WidgetSeries":
    """
    Crea y retorna un WidgetSeries listo para embeber en el wizard.

    Uso en config_wizard.py:
        ws_b = widget_series(fr, "boleta", get_series(cfg,"boleta"),
                             correlativos, C_BG, C_GRIS, C_AZUL, C_ROJO)
        ws_b.frame.grid(row=r, column=0, columnspan=2, sticky="ew")

        # Al guardar:
        set_series(cfg, "boleta", ws_b.get_series())
        for serie, corr in ws_b.get_correlativos().items():
            if corr > 0:
                establecer_inicio(salida, serie, corr)
    """
    return WidgetSeries(
        parent, tipo, series_ini, correlativos,
        C_BG, C_GRIS, C_AZUL, C_ROJO,
    )


class WidgetSeries:
    """
    Widget Tkinter para configurar múltiples series de un tipo.

    Muestra una lista editable:
      B001  [último enviado: ___]  [✕]
      B002  [último enviado: ___]  [✕]
      [+ Agregar serie]

    Máximo 5 series por tipo.
    """

    MAX_SERIES = 5

    def __init__(
        self, parent, tipo, series_ini, correlativos,
        C_BG, C_GRIS, C_AZUL, C_ROJO,
    ):
        import tkinter as tk
        self._tk    = tk
        self._tipo  = tipo
        self._C_BG  = C_BG
        self._C_GRIS = C_GRIS
        self._C_AZUL = C_AZUL
        self._C_ROJO = C_ROJO

        self.frame = tk.Frame(parent, bg=C_BG)
        self._filas: list[dict] = []   # cada fila: {frame, var_serie, var_corr}
        self._correlativos = correlativos

        for serie in series_ini:
            corr = str(correlativos.get(serie.upper(), {}).get("hasta", 0) or "")
            self._agregar_fila(serie, corr)

        self._btn_agregar = tk.Button(
            self.frame,
            text=f"+ Agregar serie de {tipo}",
            font=("Segoe UI", 8), bg=C_BG, fg=C_AZUL,
            relief="flat", bd=0, cursor="hand2",
            command=self._on_agregar,
        )
        self._btn_agregar.pack(anchor="w", pady=(2, 0))
        self._actualizar_btn()

    def _agregar_fila(self, serie: str = "", corr: str = "") -> None:
        import tkinter as tk
        fr = tk.Frame(self.frame, bg=self._C_BG)
        fr.pack(fill="x", pady=2)

        tk.Label(fr, text="Serie:", font=("Segoe UI", 9),
                 bg=self._C_BG, fg=self._C_GRIS).pack(side="left")

        var_serie = tk.StringVar(value=serie)
        ent_serie = tk.Entry(fr, textvariable=var_serie,
                             font=("Segoe UI", 10), width=6,
                             relief="solid", bd=1)
        ent_serie.pack(side="left", padx=(4, 10))

        tk.Label(fr, text="Último enviado:", font=("Segoe UI", 9),
                 bg=self._C_BG, fg=self._C_GRIS).pack(side="left")

        var_corr = tk.StringVar(value=corr)
        tk.Entry(fr, textvariable=var_corr,
                 font=("Segoe UI", 10), width=10,
                 relief="solid", bd=1).pack(side="left", padx=(4, 8))

        fila = {"frame": fr, "var_serie": var_serie, "var_corr": var_corr}

        btn_quitar = tk.Button(
            fr, text="✕", font=("Segoe UI", 9),
            bg=self._C_BG, fg=self._C_ROJO,
            relief="flat", bd=0, cursor="hand2",
            command=lambda f=fila: self._on_quitar(f),
        )
        btn_quitar.pack(side="left")
        fila["btn_quitar"] = btn_quitar

        self._filas.append(fila)

    def _on_agregar(self) -> None:
        if len(self._filas) < self.MAX_SERIES:
            self._agregar_fila()
            self._btn_agregar.pack_forget()
            self._btn_agregar.pack(anchor="w", pady=(2, 0))
            self._actualizar_btn()

    def _on_quitar(self, fila: dict) -> None:
        if len(self._filas) <= 1:
            return   # siempre mantener al menos una
        fila["frame"].destroy()
        self._filas.remove(fila)
        self._actualizar_btn()

    def _actualizar_btn(self) -> None:
        if len(self._filas) >= self.MAX_SERIES:
            self._btn_agregar.config(state="disabled", fg=self._C_GRIS)
        else:
            self._btn_agregar.config(state="normal", fg=self._C_AZUL)
        # No se puede quitar si solo queda una
        for fila in self._filas:
            estado = "disabled" if len(self._filas) <= 1 else "normal"
            fila["btn_quitar"].config(state=estado)

    def get_series(self) -> list[str]:
        """Retorna la lista de series válidas ingresadas."""
        result = []
        for fila in self._filas:
            s = fila["var_serie"].get().strip().upper()
            if s and serie_valida(s) and s not in result:
                result.append(s)
        return result if result else [_DEFAULT[self._tipo]]

    def get_correlativos(self) -> dict[str, int]:
        """Retorna {serie: correlativo} para las series con correlativo > 0."""
        result = {}
        for fila in self._filas:
            s = fila["var_serie"].get().strip().upper()
            try:
                c = int(fila["var_corr"].get().strip())
                if c > 0 and serie_valida(s):
                    result[s] = c
            except ValueError:
                pass
        return result


# ── Tests ────────────────────────────────────────────────────

if __name__ == "__main__":
    import configparser as cp

    print("=== Tests series_config ===")
    print()

    # ── Test 1: get_series con clave nueva
    cfg = cp.ConfigParser()
    cfg.add_section("EMPRESA")
    cfg.set("EMPRESA", "series_boleta", "B001,B002,B003")
    cfg.set("EMPRESA", "series_factura", "F001,F002")
    assert get_series(cfg, "boleta")  == ["B001","B002","B003"]
    assert get_series(cfg, "factura") == ["F001","F002"]
    print("✅  get_series con clave nueva")

    # ── Test 2: retrocompatibilidad con clave vieja
    cfg2 = cp.ConfigParser()
    cfg2.add_section("EMPRESA")
    cfg2.set("EMPRESA", "serie_boleta",  "B001")
    cfg2.set("EMPRESA", "serie_factura", "F001")
    cfg2.set("EMPRESA", "serie_nota",    "NC01")
    assert get_series(cfg2, "boleta")  == ["B001"]
    assert get_series(cfg2, "factura") == ["F001"]
    assert get_series(cfg2, "nota")    == ["NC01"]
    print("✅  get_series retrocompatible con claves viejas")

    # ── Test 3: set_series migra y limpia vieja
    cfg3 = cp.ConfigParser()
    cfg3.add_section("EMPRESA")
    cfg3.set("EMPRESA", "serie_boleta", "B001")
    set_series(cfg3, "boleta", ["B001","B002","B003"])
    assert cfg3.get("EMPRESA","series_boleta") == "B001,B002,B003"
    assert not cfg3.has_option("EMPRESA","serie_boleta")
    print("✅  set_series migra y elimina clave vieja")

    # ── Test 4: serie_valida
    validas   = ["B001","F001","NC01","B002","F002","BB01","B999"]
    invalidas = ["1234","BXXX","B1","","B0001X","boleta"]
    for s in validas:
        assert serie_valida(s), f"Debería ser válida: {s}"
    for s in invalidas:
        assert not serie_valida(s), f"Debería ser inválida: {s}"
    print("✅  serie_valida() detecta correctamente")

    # ── Test 5: todas_las_series
    cfg4 = cp.ConfigParser()
    cfg4.add_section("EMPRESA")
    cfg4.set("EMPRESA","series_boleta",  "B001,B002")
    cfg4.set("EMPRESA","series_factura", "F001")
    cfg4.set("EMPRESA","series_nota",    "NC01")
    assert todas_las_series(cfg4) == ["B001","B002","F001","NC01"]
    print("✅  todas_las_series() orden correcto")

    # ── Test 6: tipo_de_serie
    assert tipo_de_serie("B001") == "boleta"
    assert tipo_de_serie("F001") == "factura"
    assert tipo_de_serie("NC01") == "nota"
    print("✅  tipo_de_serie() correcto")

    # ── Test 7: migrar_series_viejas
    cfg5 = cp.ConfigParser()
    cfg5.add_section("EMPRESA")
    cfg5.set("EMPRESA","serie_boleta",  "B001")
    cfg5.set("EMPRESA","serie_factura", "F001")
    cfg5.set("EMPRESA","serie_nota",    "NC01")
    migrado = migrar_series_viejas(cfg5)
    assert migrado
    assert cfg5.get("EMPRESA","series_boleta") == "B001"
    assert not cfg5.has_option("EMPRESA","serie_boleta")
    # Idempotente
    migrado2 = migrar_series_viejas(cfg5)
    assert not migrado2
    print("✅  migrar_series_viejas() idempotente")

    # ── Test 8: get_series default si está vacío
    cfg6 = cp.ConfigParser()
    cfg6.add_section("EMPRESA")
    assert get_series(cfg6, "boleta")  == ["B001"]
    assert get_series(cfg6, "factura") == ["F001"]
    assert get_series(cfg6, "nota")    == ["NC01"]
    print("✅  defaults correctos si config vacía")

    print()
    print("🎉  Todos los tests en verde.")
