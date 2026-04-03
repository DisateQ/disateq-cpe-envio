"""
dbf_reader.py
=============
Lectura de archivos DBF del sistema de farmacia FoxPro.

Principios SOLID aplicados:
  S — Solo responsabilidad: leer y validar DBF. Nada mas.
  O — Extensible: _SafeFieldParser se puede extender sin modificar _leer().
  D — Depende de abstracciones: lanza excepciones tipadas, no strings.

Excepciones que puede lanzar:
  DBFNotFound  — archivo no existe
  DBFCorrupto  — archivo existe pero no se puede parsear
"""

from pathlib import Path
from collections import defaultdict
from dbfread import DBF, FieldParser

from exceptions import DBFNotFound, DBFCorrupto, DBFSinRegistros


class _SafeFieldParser(FieldParser):
    """
    Parser defensivo para DBF de FoxPro legacy.
    Convierte campos invalidos a valores neutros en vez de lanzar excepcion.
    """
    def parseD(self, field, data):
        """Fecha nula o invalida → None."""
        try:
            raw = data.strip()
            if not raw or set(raw) <= {b'\x00'[0], ord(' '), ord('0')}:
                return None
            return super().parseD(field, data)
        except Exception:
            return None

    def parseN(self, field, data):
        """Numerico vacio → 0."""
        try:
            return super().parseN(field, data)
        except Exception:
            return 0

    def parseF(self, field, data):
        """Float vacio → 0.0."""
        try:
            return super().parseF(field, data)
        except Exception:
            return 0.0


def _leer(ruta_data: str, nombre: str) -> list:
    """
    Lee un DBF y retorna lista de registros.
    Lanza DBFNotFound o DBFCorrupto segun el problema.
    """
    ruta = Path(ruta_data) / nombre
    if not ruta.exists():
        raise DBFNotFound(nombre, str(ruta_data))
    try:
        registros = list(DBF(
            str(ruta),
            encoding="latin-1",
            ignore_missing_memofile=True,
            char_decode_errors="ignore",
            parserclass=_SafeFieldParser,
        ))
        return registros
    except (DBFNotFound, DBFCorrupto):
        raise
    except Exception as e:
        raise DBFCorrupto(nombre, e) from e


def leer_pendientes(ruta_data: str) -> list:
    """
    Retorna comprobantes con FLAG_ENVIO=2 (pendientes de envio).
    Lanza DBFNotFound o DBFCorrupto si hay problema con el archivo.
    """
    registros = _leer(ruta_data, "enviosffee.dbf")
    return [r for r in registros if r.get("FLAG_ENVIO") == 2]


def leer_productos(ruta_data: str) -> dict:
    """
    Retorna dict {codigo: registro} desde productox.dbf.
    Lanza DBFNotFound o DBFCorrupto si hay problema con el archivo.
    """
    registros = _leer(ruta_data, "productox.dbf")
    return {str(r.get("CODIGO_PRO", "")).strip(): r for r in registros}


def leer_detalles(ruta_data: str, productos: dict) -> dict:
    """
    Retorna dict {(tipo, serie, numero): [items]} desde detalleventa.dbf.
    Enriquece cada item con descripcion y UNSPSC desde productox.
    Solo incluye items no anulados (FLAG_ANULA=0).
    Lanza DBFNotFound o DBFCorrupto si hay problema con el archivo.
    """
    registros = _leer(ruta_data, "detalleventa.dbf")
    idx = defaultdict(list)

    for r in registros:
        # Ignorar anulados
        try:
            if r.get("FLAG_ANULA") and int(r.get("FLAG_ANULA", 0)) != 0:
                continue
        except Exception:
            pass

        # Construir clave de relacion
        try:
            key = (
                str(r.get("TIPO_FACTU", "")).strip(),
                str(r.get("SERIE_FACT", "")).strip(),
                str(r.get("NUMERO_FAC", "")).strip(),
            )
        except Exception:
            continue

        # Enriquecer con datos de productox
        cod  = str(r.get("CODIGO_PRO", "")).strip()
        prod = productos.get(cod, {})

        r["_DESCRIPCIO"] = (
            str(prod.get("DESCRIPCIO", "")).strip() + " " +
            str(prod.get("PRESENTA_P", "")).strip()
        ).strip() or cod or "SIN DESCRIPCION"

        r["_CODIGO_UNS"] = (
            str(prod.get("CODIGO_UNS", "")).strip() or
            str(r.get("CODIGO_UNS", "")).strip() or
            "10000000"
        )

        try:
            r["_EXONERADO"] = (
                bool(prod.get("EXONERADO_", False)) or
                int(r.get("PRODUCTO_E", 0) or 0) == 1
            )
        except Exception:
            r["_EXONERADO"] = False

        try:
            r["_ICBPER"]   = int(r.get("ICBPER",    0) or 0) == 1
        except Exception:
            r["_ICBPER"]   = False

        try:
            r["_SERVICIO"] = int(r.get("FLAG_SERVI", 0) or 0) == 1
        except Exception:
            r["_SERVICIO"] = False

        idx[key].append(r)

    return idx


def verificar_rutas(ruta_data: str) -> tuple[bool, str]:
    """
    Verifica que los tres DBF existan.
    Retorna (ok, mensaje) — no lanza excepciones.
    """
    requeridos = ["enviosffee.dbf", "detalleventa.dbf", "productox.dbf"]
    faltantes  = [f for f in requeridos if not (Path(ruta_data) / f).exists()]
    if faltantes:
        return False, f"Archivos no encontrados: {', '.join(faltantes)}"
    return True, "OK"
