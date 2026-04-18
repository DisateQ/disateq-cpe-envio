"""
adapters/dispatcher.py
======================
Dispatcher de adaptadores — DisateQ CPE™.

Decide qué adaptador usar según la configuración del sistema.
monitor.py llama a get_adapter() y recibe el adaptador correcto
sin saber nada del formato de origen.

Fuentes soportadas:
  dbf   — FoxPro/DBF (default)
  xlsx  — Excel _CPE (DisateQ POS™)
  sql   — SQL Server / PostgreSQL / SQLite (futuro)
  mdb   — Access MDB (futuro)
  odbc  — ODBC genérico (futuro)
"""

import logging
from configparser import ConfigParser
from adapters.base_adapter import AdapterError

log = logging.getLogger(__name__)

# Fuentes disponibles actualmente
_FUENTES_DISPONIBLES = ("dbf", "xlsx")

# Fuentes planificadas pero no implementadas
_FUENTES_FUTURAS = ("sql", "mdb", "odbc", "sqlserver", "oracle", "db2")


def get_adapter(cfg: ConfigParser):
    """
    Retorna el adaptador configurado.

    Args:
        cfg: ConfigParser con la configuración del sistema

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
        from adapters.xlsx_adapter import leer
        log.info("Dispatcher: usando xlsx_adapter")
        return leer  # función directa, no clase

    if fuente in _FUENTES_FUTURAS:
        raise AdapterError(
            f"Fuente '{fuente}' está en el roadmap pero aún no implementada.\n"
            f"Fuentes disponibles: {', '.join(_FUENTES_DISPONIBLES)}"
        )

    raise AdapterError(
        f"Fuente desconocida: '{fuente}'.\n"
        f"Fuentes disponibles: {', '.join(_FUENTES_DISPONIBLES)}"
    )


def fuentes_disponibles() -> list[str]:
    """Retorna lista de fuentes actualmente operativas."""
    return list(_FUENTES_DISPONIBLES)


def fuentes_futuras() -> list[str]:
    """Retorna lista de fuentes planificadas."""
    return list(_FUENTES_FUTURAS)