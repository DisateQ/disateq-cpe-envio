"""
exceptions.py
=============
Jerarquia de excepciones de DisateQ Bridge(tm).

Permite distinguir exactamente QUE fallo y DONDE,
en vez de capturar Exception generica en todos lados.

                    BridgeError
                   /           \
          DBFError               EnvioError
         /        \             /          \
  DBFNotFound  DBFCorrupto  ConexionError  RespuestaError
                                               |
                                          TimeoutError
"""


class BridgeError(Exception):
    """Base para todos los errores de DisateQ Bridge."""
    pass

# Alias para compatibilidad con codigo existente
CPEError = BridgeError


# ── Errores de lectura de fuente ────────────────────────────

class DBFError(BridgeError):
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


class ReaderError(BridgeError):
    """Error genérico de cualquier reader (DBF, Excel, SQL)."""
    def __init__(self, fuente: str, detalle: str):
        self.fuente  = fuente
        self.detalle = detalle
        super().__init__(f"Error leyendo '{fuente}': {detalle}")


# ── Errores de generación ───────────────────────────────────

class GeneracionError(BridgeError):
    """Error al generar el TXT o JSON del comprobante."""
    def __init__(self, nombre: str, causa: Exception):
        self.nombre = nombre
        self.causa  = causa
        super().__init__(f"Error generando '{nombre}': {type(causa).__name__}: {causa}")


# ── Errores de envío ────────────────────────────────────────

class EnvioError(BridgeError):
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


class CPETimeoutError(EnvioError):
    """APIFAS no respondió a tiempo."""
    def __init__(self, nombre: str, segundos: int):
        super().__init__(nombre, f"timeout después de {segundos}s")

# Alias para compatibilidad
TimeoutError = CPETimeoutError


# ── Errores de configuración ────────────────────────────────

class ConfigError(BridgeError):
    """Configuración incompleta o inválida."""
    def __init__(self, campo: str, detalle: str = ""):
        self.campo = campo
        super().__init__(
            f"Configuración inválida — '{campo}': {detalle}" if detalle
            else f"Falta configurar '{campo}'"
        )
