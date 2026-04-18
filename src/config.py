"""
config.py
=========
Gestion de configuracion del sistema CPE DisateQ.

Cambios v2.1:
  - Modalidad CUSTOM: el tecnico puede definir URLs propias
  - actualizar_endpoints() ya NO sobreescribe si modalidad == CUSTOM
    o si las URLs ya fueron editadas manualmente en el .ini
  - Nuevas helpers: urls_son_personalizadas(), resetear_endpoints()
  - Seccion FUENTE: tipo de origen de datos (dbf/xlsx/sql)
"""

import configparser
from pathlib import Path

BASE_DIR    = r"D:\FFEESUNAT\CPE DisateQ"
CONFIG_FILE = str(Path(BASE_DIR) / "ffee_config.ini")

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
        "envio":    "",
        "anulacion":"",
    },
}

DEFAULTS = {
    "EMPRESA": {
        "ruc":             "",
        "razon_social":    "",
        "nombre_comercial":"",
        "alias":           "",
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
    "CORRELATIVO": {},
    "FUENTE": {
        "tipo":       "dbf",
        "ruta_xlsx":  "",
        "cadena_sql": "",
    },
    "ALERTAS": {
        "whatsapp_activo":    "NO",
        "whatsapp_numero":    "",
        "whatsapp_apikey":    "",
        "whatsapp_proveedor": "callmebot",
        "errores_umbral":     "3",
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
    if not cfg.has_section("FUENTE"):
        cfg.add_section("FUENTE")
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


def actualizar_endpoints(
    cfg:              configparser.ConfigParser,
    forzar_modalidad: bool = False,
) -> None:
    modalidad = cfg.get("ENVIO", "modalidad", fallback="OSE").upper()

    if modalidad == "CUSTOM":
        return

    if modalidad not in ENDPOINTS:
        return

    url_actual    = cfg.get("ENVIO", "url_envio",     fallback="").strip()
    anul_actual   = cfg.get("ENVIO", "url_anulacion",  fallback="").strip()
    url_expected  = ENDPOINTS[modalidad]["envio"]
    anul_expected = ENDPOINTS[modalidad]["anulacion"]

    if not forzar_modalidad:
        urls_conocidas  = {ep["envio"]     for ep in ENDPOINTS.values() if ep["envio"]}
        anuls_conocidas = {ep["anulacion"] for ep in ENDPOINTS.values() if ep["anulacion"]}

        url_fue_editada  = url_actual  and url_actual  not in urls_conocidas
        anul_fue_editada = anul_actual and anul_actual not in anuls_conocidas

        if url_fue_editada or anul_fue_editada:
            cfg.set("ENVIO", "modalidad", "CUSTOM")
            return

    cfg.set("ENVIO", "url_envio",     url_expected)
    cfg.set("ENVIO", "url_anulacion", anul_expected)


def resetear_endpoints(cfg: configparser.ConfigParser) -> None:
    modalidad = cfg.get("ENVIO", "modalidad", fallback="OSE").upper()
    if modalidad in ENDPOINTS and modalidad != "CUSTOM":
        cfg.set("ENVIO", "url_envio",     ENDPOINTS[modalidad]["envio"])
        cfg.set("ENVIO", "url_anulacion", ENDPOINTS[modalidad]["anulacion"])


def urls_son_personalizadas(cfg: configparser.ConfigParser) -> bool:
    modalidad = cfg.get("ENVIO", "modalidad", fallback="OSE").upper()
    if modalidad == "CUSTOM":
        return True

    url_actual  = cfg.get("ENVIO", "url_envio",     fallback="").strip()
    anul_actual = cfg.get("ENVIO", "url_anulacion",  fallback="").strip()

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
    try:
        return int(cfg.get("CORRELATIVO", serie.upper(), fallback="0"))
    except (ValueError, Exception):
        return 0


def set_ultimo_correlativo(cfg: configparser.ConfigParser, serie: str, numero: int):
    if not cfg.has_section("CORRELATIVO"):
        cfg.add_section("CORRELATIVO")
    cfg.set("CORRELATIVO", serie.upper(), str(numero))