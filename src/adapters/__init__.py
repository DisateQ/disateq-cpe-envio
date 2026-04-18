"""
adapters/__init__.py
====================
Registro de adaptadores disponibles en DisateQ CPE™.
"""

from adapters.base_adapter import BaseAdapter, AdapterError
from adapters.dbf_adapter  import DBFAdapter
from adapters.xlsx_adapter import leer as xlsx_leer

__all__ = [
    "BaseAdapter",
    "AdapterError",
    "DBFAdapter",
    "xlsx_leer",
]