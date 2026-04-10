"""
config.py
=========
Configuracion de DisateQ Bridge(tm).

Los endpoints son completamente configurables en bridge_config.ini.
Los valores por defecto apuntan a APIFAS (proveedor actual),
pero pueden cambiarse sin tocar el codigo.
"""

import configparser
from pathlib import Path

BASE_DIR    = r"D:\DisateQ\Bridge"
CONFIG_FILE = str(Path(BASE_DIR) / "bridge_config.ini")

# ── Endpoints por defecto (APIFAS) ──────────────────────────
# Estos valores se usan solo si el .ini no los tiene definidos.
# Para cambiar de proveedor: editar bridge_config.ini, no este archivo.

_EP_OSE_ENVIO     = "https://apifas.disateq.com/ose_produccion.php"
_EP_OSE_ANULACION = "https://apifas.disateq.com/ose_anular.php"
_EP_SEE_ENVIO     = "https://apifas.disateq.com/produccion_text.php"
_EP_SEE_ANULACION = "https://apifas.disateq.com/produccion_anular.php"

DEFAULTS = {
    "EMPRESA": {
        "ruc":              "",
        "razon_social":     "",
        "nombre_comercial": "",
        "serie_boleta":     "B001",
        "serie_factura":    "F001",
        "serie_nota":       "NC01",
    },
    "ENVIO": {
        # modalidad: OSE o SEE
        "modalidad":         "OSE",
        # modo: legacy (TXT) o json
        "modo":              "legacy",
        # Endpoints — editables en bridge_config.ini sin tocar el codigo
        "url_ose_envio":     _EP_OSE_ENVIO,
        "url_ose_anulacion": _EP_OSE_ANULACION,
        "url_see_envio":     _EP_SEE_ENVIO,
        "url_see_anulacion": _EP_SEE_ANULACION,
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
        # DisateQ Bridge ignora correlativos <= a este valor.
        # Formato: SERIE=numero   ej: B001=22180
        # Dejar en 0 para procesar todo (instalacion nueva).
    },
}


def leer_config() -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    cfg.read_dict(DEFAULTS)
    if Path(CONFIG_FILE).exists():
        cfg.read(CONFIG_FILE, encoding="utf-8")
    if not cfg.has_section("CORRELATIVO"):
        cfg.add_section("CORRELATIVO")
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


def url_envio(cfg: configparser.ConfigParser) -> str:
    """Retorna la URL de envio segun la modalidad configurada."""
    modalidad = cfg.get("ENVIO", "modalidad", fallback="OSE").upper()
    if modalidad == "SEE":
        return cfg.get("ENVIO", "url_see_envio", fallback=_EP_SEE_ENVIO)
    return cfg.get("ENVIO", "url_ose_envio", fallback=_EP_OSE_ENVIO)


def url_anulacion(cfg: configparser.ConfigParser) -> str:
    """Retorna la URL de anulacion segun la modalidad configurada."""
    modalidad = cfg.get("ENVIO", "modalidad", fallback="OSE").upper()
    if modalidad == "SEE":
        return cfg.get("ENVIO", "url_see_anulacion", fallback=_EP_SEE_ANULACION)
    return cfg.get("ENVIO", "url_ose_anulacion", fallback=_EP_OSE_ANULACION)


def label_modalidad(cfg: configparser.ConfigParser) -> str:
    """Etiqueta legible de la modalidad para mostrar en GUI y logs."""
    modalidad = cfg.get("ENVIO", "modalidad", fallback="OSE").upper()
    return "SEE SUNAT" if modalidad == "SEE" else "OSE / PSE"


def get_ultimo_correlativo(cfg: configparser.ConfigParser, serie: str) -> int:
    """Retorna el ultimo numero enviado para la serie. 0 = sin filtro."""
    try:
        return int(cfg.get("CORRELATIVO", serie.upper(), fallback="0"))
    except (ValueError, Exception):
        return 0


def set_ultimo_correlativo(cfg: configparser.ConfigParser, serie: str, numero: int):
    """Actualiza el ultimo correlativo enviado para la serie."""
    if not cfg.has_section("CORRELATIVO"):
        cfg.add_section("CORRELATIVO")
    cfg.set("CORRELATIVO", serie.upper(), str(numero))
