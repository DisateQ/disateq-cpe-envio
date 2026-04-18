"""
adapters/base_adapter.py
========================
Interfaz base para todos los adaptadores de fuente de datos.

Cada adaptador (DBF, xlsx, SQL, MDB, ODBC) debe heredar de
BaseAdapter e implementar el método leer().

Firma uniforme:
    leer(ruta: str) -> tuple[dict, list[dict]]

Retorna:
    cabecera — dict con datos del comprobante
    items    — list[dict] con cada línea de detalle
"""

from abc import ABC, abstractmethod


class BaseAdapter(ABC):
    """
    Interfaz común para todos los adaptadores de fuente.
    Todo adaptador debe implementar leer().
    """

    @abstractmethod
    def leer(self, ruta: str) -> tuple[dict, list[dict]]:
        """
        Lee comprobantes desde la fuente configurada.

        Args:
            ruta: Path o cadena de conexión a la fuente

        Returns:
            (cabecera, items) listos para normalizar_desde_cpe()

        Raises:
            AdapterError si la fuente no es accesible o los datos son inválidos
        """
        ...

    @property
    @abstractmethod
    def nombre(self) -> str:
        """Nombre descriptivo del adaptador para logs."""
        ...


class AdapterError(Exception):
    """Error controlado de cualquier adaptador."""
    pass