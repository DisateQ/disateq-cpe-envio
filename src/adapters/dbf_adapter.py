"""
adapters/dbf_adapter.py
=======================
Adaptador DBF para DisateQ CPE™.
Envuelve dbf_reader.py implementando la interfaz BaseAdapter.

Fuente: archivos DBF del sistema FoxPro legacy.
  - enviosffee.dbf
  - detalleventa.dbf
  - productox.dbf
"""

import logging
from adapters.base_adapter import BaseAdapter, AdapterError
from dbf_reader import (
    leer_pendientes, leer_productos, leer_detalles,
    verificar_rutas
)
from normalizer import _safe_str

log = logging.getLogger(__name__)


class DBFAdapter(BaseAdapter):
    """
    Adaptador para sistemas FoxPro/DBF.
    Lee enviosffee.dbf, detalleventa.dbf y productox.dbf.
    """

    @property
    def nombre(self) -> str:
        return "DBFAdapter (FoxPro)"

    def leer(self, ruta: str) -> tuple[dict, list[dict]]:
        """
        Lee todos los comprobantes pendientes desde los DBF.

        Args:
            ruta: carpeta que contiene los tres archivos DBF

        Returns:
            Lista de (cabecera, items) — uno por comprobante pendiente

        Raises:
            AdapterError si los archivos no existen o están corruptos
        """
        ok, msg = verificar_rutas(ruta)
        if not ok:
            raise AdapterError(f"DBF no accesible: {msg}")

        try:
            from exceptions import DBFError
            pendientes = leer_pendientes(ruta)
            productos  = leer_productos(ruta)
            detalles   = leer_detalles(ruta, productos)
        except Exception as e:
            raise AdapterError(f"Error leyendo DBF: {e}") from e

        resultado = []
        for envio in pendientes:
            tipo   = _safe_str(envio.get("TIPO_FACTU"), "B")
            serie  = _safe_str(envio.get("SERIE_FACT"), "001").zfill(3)
            numero = _safe_str(envio.get("NUMERO_FAC"), "0")
            items  = detalles.get((tipo, serie, numero), [])

            if not items:
                log.warning(f"DBFAdapter: sin detalle para {tipo}{serie}-{numero}")
                continue

            resultado.append((envio, items))

        log.info(f"DBFAdapter: {len(resultado)} comprobante(s) pendientes en {ruta}")
        return resultado