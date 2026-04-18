"""
adapters/dbf_adapter.py
=======================
Adaptador DBF para DisateQ CPE™.
Envuelve dbf_reader.py implementando la interfaz BaseAdapter.

Fuente: archivos DBF del sistema FoxPro legacy.
  - enviosffee.dbf
  - detalleventa.dbf
  - productox.dbf

Busca cada archivo en ruta_principal primero,
luego en rutas_secundarias en orden.
"""

import logging
from pathlib import Path
from adapters.base_adapter import BaseAdapter, AdapterError
from normalizer import _safe_str

log = logging.getLogger(__name__)

_ARCHIVOS = {
    "principal": "enviosffee.dbf",
    "detalle":   "detalleventa.dbf",
    "catalogo":  "productox.dbf",
}


class DBFAdapter(BaseAdapter):

    @property
    def nombre(self) -> str:
        return "DBFAdapter (FoxPro)"

    def _resolver_ruta(self, archivo: str, rutas: list[str]) -> str:
        """
        Busca el archivo en la lista de rutas en orden.
        Retorna la primera ruta donde lo encuentra.
        Lanza AdapterError si no lo encuentra en ninguna.
        """
        for ruta in rutas:
            candidato = Path(ruta) / archivo
            if candidato.exists():
                log.debug(f"DBFAdapter: {archivo} encontrado en {ruta}")
                return str(Path(ruta))
        raise AdapterError(
            f"Archivo '{archivo}' no encontrado en ninguna ruta configurada.\n"
            f"Rutas buscadas: {', '.join(rutas)}"
        )

    def leer(self, ruta: str) -> list:
        """
        Lee todos los comprobantes pendientes desde los DBF.

        Args:
            ruta: ruta principal (string separado por | para múltiples rutas)

        Returns:
            Lista de (envio_dict, items_list) — uno por comprobante pendiente

        Raises:
            AdapterError si los archivos no existen o están corruptos
        """
        # Parsear rutas — ruta puede venir como "ruta1|ruta2|ruta3"
        rutas = [r.strip() for r in ruta.split("|") if r.strip()]
        if not rutas:
            raise AdapterError("No se configuró ninguna ruta de datos.")

        try:
            from dbf_reader import leer_pendientes, leer_productos, leer_detalles
            from exceptions import DBFError

            ruta_principal  = self._resolver_ruta(_ARCHIVOS["principal"], rutas)
            ruta_detalle    = self._resolver_ruta(_ARCHIVOS["detalle"],   rutas)
            ruta_catalogo   = self._resolver_ruta(_ARCHIVOS["catalogo"],  rutas)

            pendientes = leer_pendientes(ruta_principal)
            productos  = leer_productos(ruta_catalogo)
            detalles   = leer_detalles(ruta_detalle, productos)

        except AdapterError:
            raise
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

        log.info(f"DBFAdapter: {len(resultado)} comprobante(s) pendientes")
        return resultado