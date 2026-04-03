"""
exceptions.py
=============
Jerarquia de excepciones del sistema CPE DisateQ.

Permite distinguir exactamente QUE fallo y DONDE,
en vez de capturar Exception generica en todos lados.

                    CPEError
                   /        \
          DBFError            EnvioError
         /        \          /          \
  DBFNotFound  DBFCorrupto  ConexionError  RespuestaError
"""


class CPEError(Exception):
    """Base para todos los errores de CPE DisateQ."""
    pass


# ── Errores de lectura DBF ──────────────────────────────────

class DBFError(CPEError):
    """Error relacionado con los archivos DBF."""
    def __init__(self, archivo: str, detalle: str):
        self.archivo = archivo
        self.detalle = detalle
        super().__init__(f"DBF '{archivo}': {detalle}")


class DBFNotFound(DBFError):
    """El archivo DBF no existe en la ruta configurada."""
    def __init__(self, archivo: str, ruta: str):
        self.ruta = ruta
        super().__init__(archivo, f"no encontrado en {ruta}")


class DBFCorrupto(DBFError):
    """El archivo DBF existe pero no se puede leer (corrupto o bloqueado)."""
    def __init__(self, archivo: str, causa: Exception):
        self.causa = causa
        super().__init__(archivo, f"corrupto o bloqueado — {type(causa).__name__}: {causa}")


class DBFSinRegistros(DBFError):
    """El DBF se leyó pero no contiene registros válidos."""
    def __init__(self, archivo: str):
        super().__init__(archivo, "sin registros válidos")


# ── Errores de generación ───────────────────────────────────

class GeneracionError(CPEError):
    """Error al generar el TXT o JSON del comprobante."""
    def __init__(self, nombre: str, causa: Exception):
        self.nombre = nombre
        self.causa  = causa
        super().__init__(f"Error generando '{nombre}': {type(causa).__name__}: {causa}")


# ── Errores de envío ────────────────────────────────────────

class EnvioError(CPEError):
    """Error al enviar el comprobante a APIFAS."""
    def __init__(self, nombre: str, detalle: str):
        self.nombre  = nombre
        self.detalle = detalle
        super().__init__(f"Error enviando '{nombre}': {detalle}")


class ConexionError(EnvioError):
    """Sin conexión a APIFAS."""
    def __init__(self, url: str):
        self.url = url
        super().__init__("", f"sin conexión a {url}")


class RespuestaError(EnvioError):
    """APIFAS respondió pero con error."""
    def __init__(self, nombre: str, respuesta: str):
        self.respuesta = respuesta
        super().__init__(nombre, f"respuesta inesperada: {respuesta}")


class TimeoutError(EnvioError):
    """APIFAS no respondió a tiempo."""
    def __init__(self, nombre: str, segundos: int):
        super().__init__(nombre, f"timeout después de {segundos}s")


# ── Errores de configuración ────────────────────────────────

class ConfigError(CPEError):
    """Configuración incompleta o inválida."""
    def __init__(self, campo: str, detalle: str = ""):
        self.campo = campo
        super().__init__(f"Configuración inválida — '{campo}': {detalle}" if detalle
                         else f"Falta configurar '{campo}'")
