"""
bridge_watcher.py
=================
Watcher de carpeta enviados/ — DisateQ Bridge™ | Etapa 2

Responsabilidad:
    Monitorear la carpeta enviados/ del motor y registrar en BridgeAPI
    todos los comprobantes TXT que aún no estén en SQLite.

Dos modos de uso:

    1. IMPORTACIÓN INICIAL (--importar)
       Lee TODOS los TXT de enviados/ y los registra en la BD.
       Usar una sola vez al instalar BridgeAPI en un cliente con historial.

    2. WATCHER CONTINUO (default / --watch)
       Escanea enviados/ cada N segundos y registra los TXT nuevos.
       Complementa al bridge_hook: si el motor falla al notificar,
       el watcher lo recoge en el siguiente ciclo.

Cómo correrlo:

    # Importación inicial (una vez, al instalar):
    python bridge_watcher.py --importar

    # Watcher continuo en background (junto con BridgeAPI):
    python bridge_watcher.py --watch

    # Solo verificar cuántos TXT no están en BD:
    python bridge_watcher.py --check

Integración sugerida en bridge_api.py:
    Arrancar el watcher como hilo daemon al iniciar uvicorn.
    Ver función start_watcher_thread() al final de este archivo.
"""

import argparse
import logging
import re
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

log = logging.getLogger(__name__)

# ── Configuración ─────────────────────────────────────────────────────────────

BRIDGE_URL       = "http://localhost:8765"
ENDPOINT_REG     = f"{BRIDGE_URL}/comprobantes/registrar"
RUTA_BASE        = Path(r"D:\FFEESUNAT\CPE DisateQ")
RUTA_ENVIADOS    = RUTA_BASE / "enviados"
RUTA_ERRORES     = RUTA_BASE / "errores"
INTERVALO_SEG    = 10      # segundos entre escaneos en modo watch
TIMEOUT_HTTP     = 8       # timeout por petición a BridgeAPI
LOTE_MAX         = 50      # máx. TXT a procesar por ciclo (evita saturar)

# Regex para parsear nombre: {RUC}-02-{SERIE}{NUM3}-{NUM8}.txt
# Ej: 10405206710-02-B001-00023168.txt
_RE_NOMBRE = re.compile(
    r'^(?P<ruc>\d{11})-02-(?P<serie>[A-Z]{1,3}\d{2,3})-(?P<numero>\d{8})\.txt$',
    re.IGNORECASE,
)


# ── Parseo de TXT ─────────────────────────────────────────────────────────────

def _parsear_nombre(nombre: str) -> Optional[dict]:
    """
    Extrae ruc, serie, numero del nombre del TXT.
    Retorna None si el formato no coincide.
    """
    m = _RE_NOMBRE.match(Path(nombre).name)
    if not m:
        return None
    serie  = m.group("serie").upper()
    numero = int(m.group("numero"))
    tipo   = "F" if serie.upper().startswith("F") else "NC" if serie.upper().startswith("N") else "B"
    return {
        "ruc":    m.group("ruc"),
        "serie":  serie,
        "numero": numero,
        "tipo":   tipo,
    }


def _parsear_txt(contenido: str) -> dict:
    """
    Extrae campos clave del contenido TXT de APIFAS.
    Retorna dict con los campos encontrados.
    """
    campos: dict = {}
    items_count  = 0

    for linea in contenido.split("\n"):
        linea = linea.strip()
        if not linea:
            continue
        if linea.startswith("item|"):
            items_count += 1
            continue
        if "|" in linea:
            partes = linea.split("|")
            if len(partes) >= 2:
                campos[partes[0].strip()] = partes[1].strip()

    campos["_items_count"] = items_count
    return campos


def _fecha_iso(fecha_ddmmyyyy: str) -> str:
    """Convierte DD-MM-YYYY a YYYY-MM-DD. Retorna hoy si falla."""
    try:
        d, m, a = fecha_ddmmyyyy.split("-")
        return f"{a}-{m}-{d}"
    except Exception:
        return datetime.now().strftime("%Y-%m-%d")


def _safe_float(valor: str, default: float = 0.0) -> float:
    try:
        return float(valor) if valor else default
    except (ValueError, TypeError):
        return default


def _construir_payload_desde_txt(
    ruta_txt: Path,
    meta: dict,
    estado: str,
) -> Optional[dict]:
    """
    Lee el TXT y construye el payload para POST /comprobantes/registrar.
    Retorna None si el archivo no se puede leer o parsear.
    """
    try:
        contenido = ruta_txt.read_text(encoding="latin-1")
    except Exception as e:
        log.warning("[watcher] No se pudo leer %s: %s", ruta_txt.name, e)
        return None

    campos = _parsear_txt(contenido)

    # Fecha de emisión: preferir campo del TXT, sino mtime del archivo
    fecha_raw  = campos.get("fecha_de_emision", "")
    fecha_iso  = _fecha_iso(fecha_raw) if fecha_raw else \
                 datetime.fromtimestamp(ruta_txt.stat().st_mtime).strftime("%Y-%m-%d")

    # Cliente
    cli_tipo  = campos.get("cliente_tipo_de_documento", "-")
    cli_num   = campos.get("cliente_numero_de_documento", "00000000")
    cli_den   = campos.get("cliente_denominacion", "CLIENTE VARIOS")

    # Totales
    total = _safe_float(campos.get("total"))
    if total < 0 and meta["tipo"] in ("B", "F"):
        log.warning("[watcher] total negativo en %s — ignorando", ruta_txt.name)
        return None

    return {
        "nombre_archivo":       ruta_txt.name,
        "ruc_emisor":           meta["ruc"],
        "razon_social":         "",           # el TXT no lo contiene
        "tipo_comprobante":     meta["tipo"],
        "serie":                meta["serie"],
        "numero":               meta["numero"],
        "fecha_emision":        fecha_iso,
        "cliente_tipo_doc":     cli_tipo,
        "cliente_num_doc":      cli_num,
        "cliente_denominacion": cli_den,
        "total_gravada":        _safe_float(campos.get("total_gravada")),
        "total_exonerada":      _safe_float(campos.get("total_exonerada")),
        "total_igv":            _safe_float(campos.get("total_igv")),
        "total_icbper":         _safe_float(campos.get("total_impuestos_bolsas")),
        "total":                total,
        "forma_pago":           campos.get("condiciones_de_pago", "Contado"),
        "estado":               estado,
        "origen":               "txt",         # importado desde carpeta, no desde DBF
        "envio_resultado":      "enviado" if estado == "enviado" else "error_respuesta",
        "envio_respuesta_api":  "importado-desde-disco",
        "envio_duracion_ms":    None,
        "envio_url":            None,
    }


# ── Registro en BridgeAPI ─────────────────────────────────────────────────────

def _registrar_en_bridge(payload: dict) -> bool:
    """
    Envía payload a BridgeAPI. Retorna True si fue registrado (201 o ya existe).
    """
    try:
        r = requests.post(ENDPOINT_REG, json=payload, timeout=TIMEOUT_HTTP)
        if r.status_code in (200, 201):
            return True
        log.warning("[watcher] BridgeAPI rechazó %s: HTTP %d — %s",
                    payload["nombre_archivo"], r.status_code, r.text[:80])
        return False
    except requests.exceptions.ConnectionError:
        log.debug("[watcher] BridgeAPI no disponible")
        return False
    except Exception as e:
        log.warning("[watcher] Error al registrar %s: %s", payload["nombre_archivo"], e)
        return False


def _bridge_online() -> bool:
    try:
        r = requests.get(f"{BRIDGE_URL}/", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


# ── Núcleo del escaneo ────────────────────────────────────────────────────────

def _archivos_ya_registrados() -> set:
    """
    Consulta BridgeAPI para obtener los nombres de archivo ya en BD.
    Retorna set vacío si BridgeAPI no está disponible.
    """
    try:
        r = requests.get(
            f"{BRIDGE_URL}/comprobantes",
            params={"limite": 5000},
            timeout=TIMEOUT_HTTP,
        )
        if r.status_code == 200:
            return {item["nombre_archivo"] for item in r.json().get("items", [])}
    except Exception:
        pass
    return set()


def escanear_carpeta(
    ruta: Path,
    estado: str,
    ya_registrados: set,
    lote: int = LOTE_MAX,
) -> tuple[int, int]:
    """
    Escanea una carpeta de TXT y registra los no conocidos en BridgeAPI.

    Args:
        ruta:           carpeta a escanear (enviados/ o errores/)
        estado:         'enviado' | 'error'
        ya_registrados: set de nombres ya en BD (para evitar re-registrar)
        lote:           máx. archivos a procesar en este ciclo

    Returns:
        (registrados, omitidos)
    """
    if not ruta.exists():
        return 0, 0

    txts = sorted(ruta.glob("*.txt"), key=lambda f: f.stat().st_mtime)
    pendientes = [f for f in txts if f.name not in ya_registrados]

    registrados = 0
    omitidos    = 0

    for ruta_txt in pendientes[:lote]:
        meta = _parsear_nombre(ruta_txt.name)
        if not meta:
            log.debug("[watcher] Nombre no reconocido: %s — omitido", ruta_txt.name)
            omitidos += 1
            continue

        payload = _construir_payload_desde_txt(ruta_txt, meta, estado)
        if not payload:
            omitidos += 1
            continue

        if _registrar_en_bridge(payload):
            ya_registrados.add(ruta_txt.name)  # evitar re-procesar en este ciclo
            registrados += 1
        else:
            omitidos += 1

    return registrados, omitidos


# ── Modos de operación ────────────────────────────────────────────────────────

def importar_inicial(
    ruta_enviados: Path = RUTA_ENVIADOS,
    ruta_errores:  Path = RUTA_ERRORES,
    verbose: bool = True,
) -> dict:
    """
    Importación inicial: registra en BridgeAPI TODOS los TXT de disco.
    Idempotente — los ya registrados se actualizan sin duplicar.

    Returns:
        {"enviados_reg": int, "errores_reg": int, "omitidos": int}
    """
    if not _bridge_online():
        msg = f"BridgeAPI no disponible en {BRIDGE_URL}. Arranca uvicorn primero."
        if verbose:
            print(f"❌  {msg}")
        log.error("[watcher] %s", msg)
        return {"enviados_reg": 0, "errores_reg": 0, "omitidos": 0}

    if verbose:
        print(f"🔍  Consultando BridgeAPI para obtener archivos ya registrados...")

    ya = _archivos_ya_registrados()
    if verbose:
        print(f"    {len(ya)} archivos ya en BD")

    # Contar primero
    n_env = len(list(ruta_enviados.glob("*.txt"))) if ruta_enviados.exists() else 0
    n_err = len(list(ruta_errores.glob("*.txt")))  if ruta_errores.exists()  else 0
    nuevos = (n_env + n_err) - len({
        f.name for f in list(ruta_enviados.glob("*.txt")) + list(ruta_errores.glob("*.txt"))
    } & ya)

    if verbose:
        print(f"    {n_env} TXT en enviados/, {n_err} en errores/")
        print(f"    {nuevos} nuevos a importar")
        print()

    # Importar sin límite de lote
    reg_env, om_env = escanear_carpeta(ruta_enviados, "enviado", ya, lote=99999)
    reg_err, om_err = escanear_carpeta(ruta_errores,  "error",   ya, lote=99999)

    total_reg = reg_env + reg_err
    total_om  = om_env  + om_err

    if verbose:
        print(f"✅  Importados: {reg_env} enviados + {reg_err} errores = {total_reg} total")
        if total_om:
            print(f"⚠️  Omitidos (formato inválido o error): {total_om}")

    return {"enviados_reg": reg_env, "errores_reg": reg_err, "omitidos": total_om}


def watch_loop(
    ruta_enviados: Path = RUTA_ENVIADOS,
    ruta_errores:  Path = RUTA_ERRORES,
    intervalo: int = INTERVALO_SEG,
    stop_event: threading.Event = None,
) -> None:
    """
    Loop continuo: escanea cada `intervalo` segundos.
    Detener pasando un threading.Event y llamando stop_event.set().
    """
    log.info("[watcher] Loop iniciado — intervalo %ds — carpeta: %s", intervalo, ruta_enviados)
    ya_registrados: set = set()

    # Carga inicial de nombres ya en BD (para no re-procesar al arrancar)
    if _bridge_online():
        ya_registrados = _archivos_ya_registrados()
        log.info("[watcher] %d archivos ya en BD al arrancar", len(ya_registrados))

    while not (stop_event and stop_event.is_set()):
        if _bridge_online():
            reg_env, _ = escanear_carpeta(ruta_enviados, "enviado", ya_registrados)
            reg_err, _ = escanear_carpeta(ruta_errores,  "error",   ya_registrados)
            if reg_env + reg_err > 0:
                log.info("[watcher] Ciclo: %d nuevo(s) registrados", reg_env + reg_err)
        else:
            log.debug("[watcher] BridgeAPI offline — esperando...")

        # Esperar en fragmentos de 1s para responder rápido a stop_event
        for _ in range(intervalo):
            if stop_event and stop_event.is_set():
                break
            time.sleep(1)

    log.info("[watcher] Loop detenido.")


# ── Integración con BridgeAPI (hilo daemon) ───────────────────────────────────

_watcher_stop = threading.Event()
_watcher_thread: Optional[threading.Thread] = None


def start_watcher_thread(
    ruta_enviados: Path = RUTA_ENVIADOS,
    ruta_errores:  Path = RUTA_ERRORES,
    intervalo: int = INTERVALO_SEG,
) -> threading.Thread:
    """
    Arranca el watcher como hilo daemon en background.
    Llamar desde bridge_api.py al iniciar la app:

        from bridge_watcher import start_watcher_thread
        @app.on_event("startup")
        async def startup():
            start_watcher_thread()
    """
    global _watcher_thread, _watcher_stop
    _watcher_stop.clear()
    _watcher_thread = threading.Thread(
        target=watch_loop,
        args=(ruta_enviados, ruta_errores, intervalo, _watcher_stop),
        name="bridge-watcher",
        daemon=True,
    )
    _watcher_thread.start()
    log.info("[watcher] Hilo daemon iniciado.")
    return _watcher_thread


def stop_watcher_thread() -> None:
    """Detiene el watcher daemon."""
    global _watcher_stop
    _watcher_stop.set()
    log.info("[watcher] Señal de detención enviada.")


# ── CLI ───────────────────────────────────────────────────────────────────────

def _check(ruta_env: Path, ruta_err: Path) -> None:
    """Muestra cuántos TXT hay y cuántos no están en BD."""
    print(f"\nDisateQ Bridge™ — Watcher check")
    print(f"{'='*45}")
    print(f"Carpeta enviados/: {ruta_env}")
    print(f"Carpeta errores/ : {ruta_err}")
    print()

    n_env = len(list(ruta_env.glob("*.txt"))) if ruta_env.exists() else 0
    n_err = len(list(ruta_err.glob("*.txt"))) if ruta_err.exists() else 0
    print(f"TXT en enviados/ : {n_env}")
    print(f"TXT en errores/  : {n_err}")
    print(f"Total en disco   : {n_env + n_err}")
    print()

    if _bridge_online():
        ya = _archivos_ya_registrados()
        print(f"BridgeAPI        : ✅  online ({BRIDGE_URL})")
        print(f"En BD            : {len(ya)}")
        todos = set()
        if ruta_env.exists():
            todos |= {f.name for f in ruta_env.glob("*.txt")}
        if ruta_err.exists():
            todos |= {f.name for f in ruta_err.glob("*.txt")}
        faltantes = todos - ya
        print(f"Sin registrar    : {len(faltantes)}")
        if faltantes:
            print(f"\n  {'—'*40}")
            print(f"  Ejecuta: python bridge_watcher.py --importar")
            print(f"  {'—'*40}")
    else:
        print(f"BridgeAPI        : ❌  offline ({BRIDGE_URL})")
        print(f"  Arranca uvicorn bridge_api:app --port 8765")
    print()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(
        description="DisateQ Bridge™ — Watcher de carpeta enviados/"
    )
    parser.add_argument("--importar", action="store_true",
                        help="Importar TODOS los TXT de disco a BridgeAPI (una sola vez)")
    parser.add_argument("--watch",    action="store_true",
                        help="Modo watcher continuo (default si no se especifica nada)")
    parser.add_argument("--check",    action="store_true",
                        help="Solo verificar estado sin modificar nada")
    parser.add_argument("--enviados", default=str(RUTA_ENVIADOS),
                        help=f"Ruta carpeta enviados/ (default: {RUTA_ENVIADOS})")
    parser.add_argument("--errores",  default=str(RUTA_ERRORES),
                        help=f"Ruta carpeta errores/ (default: {RUTA_ERRORES})")
    parser.add_argument("--intervalo", type=int, default=INTERVALO_SEG,
                        help=f"Segundos entre ciclos en modo watch (default: {INTERVALO_SEG})")
    args = parser.parse_args()

    ruta_env = Path(args.enviados)
    ruta_err = Path(args.errores)

    if args.check:
        _check(ruta_env, ruta_err)

    elif args.importar:
        print(f"\nDisateQ Bridge™ — Importación inicial")
        print(f"{'='*45}")
        resultado = importar_inicial(ruta_env, ruta_err, verbose=True)
        sys.exit(0 if resultado["omitidos"] == 0 else 1)

    else:
        # Modo watch (default)
        print(f"\nDisateQ Bridge™ — Watcher continuo")
        print(f"{'='*45}")
        print(f"Carpeta: {ruta_env}")
        print(f"Intervalo: {args.intervalo}s")
        print(f"Ctrl+C para detener\n")
        try:
            watch_loop(ruta_env, ruta_err, args.intervalo)
        except KeyboardInterrupt:
            print("\nDetenido.")
