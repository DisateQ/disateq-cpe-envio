"""
correlativo_store.py
====================
Registro local de comprobantes ya procesados por CPE DisateQ.
Evita reenvios sin modificar el DBF del sistema FoxPro.

Guarda un archivo JSON en la carpeta de salida:
  D:\FFEESUNAT\CPE DisateQ\procesados.json

Estructura:
{
  "B001": {"hasta": 22180, "enviados": [22181, 22182, ...]},
  "F001": {"hasta": 0,     "enviados": [1, 2, ...]}
}

  - "hasta": todos los numeros <= este valor se consideran procesados
  - "enviados": numeros individuales enviados exitosamente por esta sesion
"""

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

_ARCHIVO = "procesados.json"


def _ruta(salida: str) -> Path:
    return Path(salida) / _ARCHIVO


def _cargar(salida: str) -> dict:
    ruta = _ruta(salida)
    if ruta.exists():
        try:
            return json.loads(ruta.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _guardar(salida: str, datos: dict):
    ruta = _ruta(salida)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, indent=2), encoding="utf-8")


def establecer_inicio(salida: str, serie: str, hasta: int):
    """
    Marca todos los comprobantes <= hasta como ya procesados.
    Llamado cuando el tecnico define el correlativo de inicio.
    """
    serie = serie.upper()
    datos = _cargar(salida)
    entrada = datos.get(serie, {"hasta": 0, "enviados": []})

    # Solo actualizar si el nuevo valor es mayor
    if hasta > entrada.get("hasta", 0):
        entrada["hasta"] = hasta
        # Limpiar enviados que ya quedan cubiertos por "hasta"
        entrada["enviados"] = [n for n in entrada.get("enviados", []) if n > hasta]
        datos[serie] = entrada
        _guardar(salida, datos)
        log.info(f"Correlativo de inicio establecido: {serie} <= {hasta}")


def marcar_enviado(salida: str, serie: str, numero: int):
    """Registra un numero como enviado exitosamente."""
    serie = serie.upper()
    datos = _cargar(salida)
    entrada = datos.get(serie, {"hasta": 0, "enviados": []})

    # Si ya esta cubierto por "hasta", no hace falta agregarlo
    if numero <= entrada.get("hasta", 0):
        return

    enviados = entrada.get("enviados", [])
    if numero not in enviados:
        enviados.append(numero)
        # Compactar: si enviados cubre hasta+1, hasta+2... subir "hasta"
        enviados_set = set(enviados)
        hasta = entrada.get("hasta", 0)
        siguiente = hasta + 1
        while siguiente in enviados_set:
            enviados_set.remove(siguiente)
            hasta = siguiente
            siguiente += 1
        entrada["hasta"]    = hasta
        entrada["enviados"] = sorted(enviados_set)
        datos[serie]        = entrada
        _guardar(salida, datos)


def ya_procesado(salida: str, serie: str, numero: int) -> bool:
    """Retorna True si el numero ya fue procesado (no debe enviarse)."""
    serie  = serie.upper()
    datos  = _cargar(salida)
    entrada = datos.get(serie, {"hasta": 0, "enviados": []})
    if numero <= entrada.get("hasta", 0):
        return True
    return numero in entrada.get("enviados", [])


def resumen(salida: str) -> str:
    """Retorna texto con el estado de correlativos procesados."""
    datos = _cargar(salida)
    if not datos:
        return "Sin historial de correlativos."
    lineas = []
    for serie in sorted(datos.keys()):
        e = datos[serie]
        hasta    = e.get("hasta", 0)
        enviados = e.get("enviados", [])
        lineas.append(
            f"  {serie}: procesados hasta {hasta}"
            + (f"  +  enviados individuales: {enviados[:5]}{'...' if len(enviados)>5 else ''}"
               if enviados else "")
        )
    return "\n".join(lineas)
