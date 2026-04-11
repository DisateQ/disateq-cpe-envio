"""
config.py
=========
Gestion de configuracion del sistema CPE DisateQ.

Cambios v2.1:
  - Modalidad CUSTOM: el tecnico puede definir URLs propias
  - actualizar_endpoints() ya NO sobreescribe si modalidad == CUSTOM
    o si las URLs ya fueron editadas manualmente en el .ini
  - Nuevas helpers: urls_son_personalizadas(), resetear_endpoints()
"""

import configparser
from pathlib import Path

BASE_DIR    = r"D:\FFEESUNAT\CPE DisateQ"
CONFIG_FILE = str(Path(BASE_DIR) / "ffee_config.ini")

# ── URLs conocidas por modalidad ─────────────────────────────
# CUSTOM = el tecnico define sus propias URLs.
# Agregar aqui nuevas modalidades a futuro (ej: Plataforma DisateQ CPE).
ENDPOINTS = {
    "OSE": {
        "label":    "OSE / PSE",
        "envio":    "https://apifas.disateq.com/ose_produccion.php",
        "anulacion":"https://apifas.disateq.com/ose_anular.php",
    },
    "SUNAT": {
        "label":    "SEE SUNAT",
        "envio":    "https://apifas.disateq.com/produccion_text.php",
        "anulacion":"https://apifas.disateq.com/produccion_anular.php",
        "rc":       "https://apifas.disateq.com/produccion_rc.php",
    },
    "CUSTOM": {
        "label":    "URL personalizada",
        "envio":    "",   # el tecnico define
        "anulacion":"",   # el tecnico define
    },
}

DEFAULTS = {
    "EMPRESA": {
        "ruc":             "",
        "razon_social":    "",
        "nombre_comercial":"",
        "alias":           "",          # ej: "Local Grau 1"
        "serie_boleta":    "B001",
        "serie_factura":   "F001",
        "serie_nota":      "NC01",
    },
    "ENVIO": {
        "modalidad":    "OSE",
        "modo":         "legacy",
        "url_envio":    ENDPOINTS["OSE"]["envio"],
        "url_anulacion":ENDPOINTS["OSE"]["anulacion"],
    },
    "RUTAS": {
        "data_dbf":   r"C:\Sistemas\data",
        "salida_txt": BASE_DIR,
    },
    "SEGURIDAD": {
        "pin": "",
    },
    "CORRELATIVO": {
        # Ultimo numero enviado correctamente por serie.
        # CPE DisateQ ignora todo comprobante con numero <= a este valor.
        # Formato: serie=numero  ej: B001=22180
        # Dejar en 0 para procesar todo (instalacion nueva).
    },
    "ALERTAS": {
        "whatsapp_activo":    "NO",
        "whatsapp_numero":    "",       # ej: 51999888777 (sin +)
        "whatsapp_apikey":    "",       # API key de CallMeBot
        "whatsapp_proveedor": "callmebot",
        "errores_umbral":     "3",      # errores consecutivos para alertar
    },
}


def leer_config() -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    cfg.read_dict(DEFAULTS)
    if Path(CONFIG_FILE).exists():
        cfg.read(CONFIG_FILE, encoding="utf-8")
    if not cfg.has_section("CORRELATIVO"):
        cfg.add_section("CORRELATIVO")
    if not cfg.has_section("ALERTAS"):
        cfg.add_section("ALERTAS")
    return cfg


def guardar_config(cfg: configparser.ConfigParser):
    Path(CONFIG_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        cfg.write(f)


def config_completa(cfg: configparser.ConfigParser) -> bool:
    return bool(
        cfg.get("EMPRESA", "ruc",          fallback="").strip() and
        cfg.get("EMPRESA", "razon_social", fallback="").strip() and
        cfg.get("SEGURIDAD", "pin",        fallback="").strip()
    )


# ── Gestión de endpoints ─────────────────────────────────────

def actualizar_endpoints(
    cfg:               configparser.ConfigParser,
    forzar_modalidad:  bool = False,
) -> None:
    """
    Sincroniza url_envio y url_anulacion con la modalidad seleccionada.

    Comportamiento:
      - OSE / SUNAT:  aplica las URLs hardcodeadas de ENDPOINTS.
                      Si forzar_modalidad=False (default) y el usuario
                      ya editó las URLs manualmente, las respeta.
      - CUSTOM:       nunca sobreescribe — el tecnico gestiona las URLs.

    Args:
        cfg:              ConfigParser con la configuracion actual.
        forzar_modalidad: True = sobreescribir aunque hayan sido editadas.
                          Usar solo cuando el tecnico cambia de modalidad
                          explicitamente en el wizard.
    """
    modalidad = cfg.get("ENVIO", "modalidad", fallback="OSE").upper()

    # CUSTOM: no tocar — el tecnico es el dueño de esas URLs
    if modalidad == "CUSTOM":
        return

    if modalidad not in ENDPOINTS:
        return

    url_actual    = cfg.get("ENVIO", "url_envio",    fallback="").strip()
    anul_actual   = cfg.get("ENVIO", "url_anulacion", fallback="").strip()
    url_expected  = ENDPOINTS[modalidad]["envio"]
    anul_expected = ENDPOINTS[modalidad]["anulacion"]

    # Si forzar=False, solo actualizar si las URLs son las defaults
    # o están vacías (instalación nueva). Si el usuario las editó, respetar.
    if not forzar_modalidad:
        # Verificar si la URL actual es una URL conocida de CUALQUIER modalidad
        urls_conocidas = {ep["envio"]    for ep in ENDPOINTS.values() if ep["envio"]}
        anuls_conocidas = {ep["anulacion"] for ep in ENDPOINTS.values() if ep["anulacion"]}

        url_fue_editada  = url_actual  and url_actual  not in urls_conocidas
        anul_fue_editada = anul_actual and anul_actual not in anuls_conocidas

        if url_fue_editada or anul_fue_editada:
            # Las URLs fueron personalizadas — no sobreescribir
            # Cambiar a CUSTOM para que el wizard lo refleje correctamente
            cfg.set("ENVIO", "modalidad", "CUSTOM")
            return

    cfg.set("ENVIO", "url_envio",    url_expected)
    cfg.set("ENVIO", "url_anulacion", anul_expected)


def resetear_endpoints(cfg: configparser.ConfigParser) -> None:
    """
    Fuerza el reset de URLs al default de la modalidad actual.
    Llamar cuando el tecnico quiere volver a los valores oficiales
    después de haber personalizado las URLs.
    """
    modalidad = cfg.get("ENVIO", "modalidad", fallback="OSE").upper()
    if modalidad in ENDPOINTS and modalidad != "CUSTOM":
        cfg.set("ENVIO", "url_envio",    ENDPOINTS[modalidad]["envio"])
        cfg.set("ENVIO", "url_anulacion", ENDPOINTS[modalidad]["anulacion"])


def urls_son_personalizadas(cfg: configparser.ConfigParser) -> bool:
    """
    Retorna True si las URLs del .ini son distintas a los defaults conocidos.
    Útil para mostrar indicador visual en el wizard.
    """
    modalidad = cfg.get("ENVIO", "modalidad", fallback="OSE").upper()
    if modalidad == "CUSTOM":
        return True

    url_actual  = cfg.get("ENVIO", "url_envio",    fallback="").strip()
    anul_actual = cfg.get("ENVIO", "url_anulacion", fallback="").strip()

    if modalidad in ENDPOINTS:
        return (
            url_actual  != ENDPOINTS[modalidad]["envio"] or
            anul_actual != ENDPOINTS[modalidad]["anulacion"]
        )
    return False


def label_modalidad(cfg: configparser.ConfigParser) -> str:
    modalidad = cfg.get("ENVIO", "modalidad", fallback="OSE").upper()
    return ENDPOINTS.get(modalidad, {}).get("label", modalidad)


def get_ultimo_correlativo(cfg: configparser.ConfigParser, serie: str) -> int:
    """Retorna el ultimo numero enviado para la serie dada. 0 = sin filtro."""
    try:
        return int(cfg.get("CORRELATIVO", serie.upper(), fallback="0"))
    except (ValueError, Exception):
        return 0


def set_ultimo_correlativo(cfg: configparser.ConfigParser, serie: str, numero: int):
    """Actualiza el ultimo correlativo enviado para la serie."""
    if not cfg.has_section("CORRELATIVO"):
        cfg.add_section("CORRELATIVO")
    cfg.set("CORRELATIVO", serie.upper(), str(numero))
