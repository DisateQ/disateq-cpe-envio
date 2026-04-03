"""
config.py
=========
Gestion de configuracion del sistema CPE DisateQ.
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
    },
}

DEFAULTS = {
    "EMPRESA": {
        "ruc":             "",
        "razon_social":    "",
        "nombre_comercial":"",
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
}


def leer_config() -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    cfg.read_dict(DEFAULTS)
    if Path(CONFIG_FILE).exists():
        cfg.read(CONFIG_FILE, encoding="utf-8")
    # Asegurar que la seccion CORRELATIVO existe
    if not cfg.has_section("CORRELATIVO"):
        cfg.add_section("CORRELATIVO")
    return cfg


def guardar_config(cfg: configparser.ConfigParser):
    Path(CONFIG_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        cfg.write(f)


def config_completa(cfg: configparser.ConfigParser) -> bool:
    return bool(
        cfg.get("EMPRESA", "ruc", fallback="").strip() and
        cfg.get("EMPRESA", "razon_social", fallback="").strip() and
        cfg.get("SEGURIDAD", "pin", fallback="").strip()
    )


def actualizar_endpoints(cfg: configparser.ConfigParser):
    modalidad = cfg.get("ENVIO", "modalidad", fallback="OSE").upper()
    if modalidad in ENDPOINTS:
        cfg.set("ENVIO", "url_envio",    ENDPOINTS[modalidad]["envio"])
        cfg.set("ENVIO", "url_anulacion",ENDPOINTS[modalidad]["anulacion"])


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
