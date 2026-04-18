"""
adapters/dispatcher.py
======================
Dispatcher de adaptadores — DisateQ CPE™.

Decide qué adaptador usar según la configuración del sistema.
Construye la ruta combinada (principal + secundarias) y la
entrega al adaptador correspondiente.

Fuentes soportadas:
  dbf   — FoxPro/DBF
  xlsx  — Excel _CPE
  sql   — SQL Server / PostgreSQL / SQLite (futuro)
  mdb   — Access MDB (futuro)
  odbc  — ODBC genérico (futuro)
"""

import logging
from configparser import ConfigParser
from adapters.base_adapter import AdapterError

log = logging.getLogger(__name__)

_FUENTES_DISPONIBLES = ("dbf", "xlsx")
_FUENTES_FUTURAS     = ("sql", "mdb", "odbc", "sqlserver", "oracle", "db2")


def _construir_ruta(cfg: ConfigParser) -> str:
    """
    Construye la ruta completa combinando ruta_principal y rutas_secundarias.
    Retorna string con rutas separadas por '|'.
    """
    principal   = cfg.get("FUENTE", "ruta_principal",    fallback="").strip()
    secundarias = cfg.get("FUENTE", "rutas_secundarias", fallback="").strip()

    rutas = [r.strip() for r in [principal] + secundarias.split("|") if r.strip()]
    return "|".join(rutas)


def get_adapter(cfg: ConfigParser):
    """
    Retorna el adaptador configurado.

    Args:
        cfg: ConfigParser con la configuracion del sistema

    Returns:
        Instancia del adaptador correspondiente

    Raises:
        AdapterError si la fuente no está soportada
    """
    fuente = cfg.get("FUENTE", "tipo", fallback="dbf").lower().strip()

    if fuente == "dbf":
        from adapters.dbf_adapter import DBFAdapter
        log.info("Dispatcher: usando DBFAdapter")
        return DBFAdapter()

    if fuente == "xlsx":
        from adapters.xlsx_adapter import XlsxAdapter
        log.info("Dispatcher: usando XlsxAdapter")
        return XlsxAdapter()

    if fuente in _FUENTES_FUTURAS:
        raise AdapterError(
            f"Fuente '{fuente}' esta en el roadmap pero aun no implementada.\n"
            f"Fuentes disponibles: {', '.join(_FUENTES_DISPONIBLES)}"
        )

    raise AdapterError(
        f"Fuente desconocida: '{fuente}'.\n"
        f"Fuentes disponibles: {', '.join(_FUENTES_DISPONIBLES)}"
    )


def get_ruta(cfg: ConfigParser) -> str:
    """
    Retorna la ruta combinada (principal + secundarias) para el adaptador.
    """
    return _construir_ruta(cfg)


def fuentes_disponibles() -> list[str]:
    return list(_FUENTES_DISPONIBLES)


def fuentes_futuras() -> list[str]:
    return list(_FUENTES_FUTURAS)