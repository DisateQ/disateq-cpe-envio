"""
bridge_api.py
=============
BridgeAPI — DisateQ Bridge™ | Etapa 2

API local FastAPI que actúa como intermediario entre:
    Motor Python (cpe_disateq.exe)  →  BridgeAPI  →  Dashboard React

Corre en: http://localhost:8765
Docs:     http://localhost:8765/docs   (Swagger automático)

Endpoints:
    GET  /                          health check
    GET  /status                    estado del Bridge + stats del día
    GET  /comprobantes              lista paginada con filtros
    GET  /comprobantes/{id}         detalle de un comprobante
    GET  /comprobantes/{id}/envios  historial de envíos del comprobante
    POST /comprobantes/registrar    registra un CPE desde el motor
    POST /comprobantes/{id}/reenviar  reenvía manualmente a APIFAS
    GET  /log                       últimos eventos del log
    GET  /config                    configuración del Bridge
    PUT  /config/{clave}            actualiza un valor de config

Uso:
    uvicorn bridge_api:app --host 0.0.0.0 --port 8765 --reload
"""

import time
import logging
import json
import configparser
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Importar la capa de datos del Bridge
from bridge_db import (
    get_conn, init_db, nuevo_id, ahora_iso,
    insertar_comprobante, insertar_envio, log_evento,
    actualizar_estado_comprobante, obtener_comprobante_por_archivo,
    stats_hoy, listar_comprobantes, ultimos_eventos,
)

# ── Configuración de logging ─────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("bridge_api")

# ── Inicializar BD al arrancar ────────────────────────────────────────────────

init_db()

# ── App FastAPI ───────────────────────────────────────────────────────────────

app = FastAPI(
    title       = "DisateQ Bridge™ API",
    description = "API local de integración entre el motor CPE y el dashboard",
    version     = "2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],   # en producción: restringir a localhost:5173
    allow_methods  = ["*"],
    allow_headers  = ["*"],
)

# ── Helpers internos ──────────────────────────────────────────────────────────

def _config_motor() -> configparser.ConfigParser:
    """Lee ffee_config.ini del motor. Retorna config vacía si no existe."""
    cfg = configparser.ConfigParser()
    ini = Path(r"D:\FFEESUNAT\CPE DisateQ\ffee_config.ini")
    if ini.exists():
        cfg.read(str(ini), encoding="utf-8")
    return cfg


def _row_to_dict(row) -> dict:
    """Convierte sqlite3.Row a dict serializable."""
    return dict(row) if row else {}


def _rows_to_list(rows) -> list:
    return [dict(r) for r in rows]


def _parse_nombre_txt(nombre: str) -> dict:
    """
    Extrae metadatos del nombre de archivo TXT.
    Formato: {RUC}-02-{SERIE}{NUMERO_3}-{NUMERO_8}.txt
    Ej: 10405206710-02-B001-00023168.txt
    """
    try:
        stem   = Path(nombre).stem           # sin .txt
        partes = stem.split("-")
        ruc    = partes[0]
        serie  = partes[2]                   # B001, F001
        numero = int(partes[3])
        tipo   = "F" if serie.startswith("F") else "B"
        return {"ruc": ruc, "serie": serie, "numero": numero, "tipo": tipo}
    except Exception:
        return {}


def _leer_txt(nombre_archivo: str) -> Optional[str]:
    """Lee el contenido del TXT desde enviados/ o errores/."""
    base = Path(r"D:\FFEESUNAT\CPE DisateQ")
    for subcarpeta in ("enviados", "errores", ""):
        ruta = base / subcarpeta / nombre_archivo
        if ruta.exists():
            try:
                return ruta.read_text(encoding="latin-1")
            except Exception:
                pass
    return None


def _extraer_campos_txt(contenido: str) -> dict:
    """Extrae campo→valor de un TXT APIFAS."""
    campos = {}
    items  = []
    for linea in contenido.split("\n"):
        linea = linea.strip()
        if not linea:
            continue
        if linea.startswith("item|"):
            items.append(linea)
        elif "|" in linea:
            partes = linea.split("|")
            if len(partes) >= 2:
                campos[partes[0].strip()] = partes[1].strip()
    campos["_items"] = items
    return campos


def _enviar_a_apifas(
    nombre: str,
    contenido: str,
    ruc: str,
    url: str,
    timeout: int = 30,
) -> tuple[bool, str, int]:
    """
    Envía TXT a APIFAS. Retorna (exito, mensaje, codigo_http).
    Mismo protocolo que sender.py del motor.
    """
    contenido_limpio = contenido.replace("\r\n", "").replace("\n", "").replace("\r", "")
    headers = {"Texto": contenido_limpio, "Ruc": ruc, "Nombre": nombre}

    _RESPUESTAS_OK = ["proceso-aceptado", "es un comprobante repetido", "por anular"]

    try:
        resp = requests.post(url, headers=headers, timeout=timeout)
        msg  = resp.text.strip() if resp.text else ""
        ok   = resp.status_code == 200 and any(r in msg.lower() for r in _RESPUESTAS_OK)
        return ok, msg, resp.status_code
    except requests.exceptions.ConnectionError:
        return False, "Sin conexión a APIFAS", 0
    except requests.exceptions.Timeout:
        return False, f"Timeout después de {timeout}s", 0
    except Exception as e:
        return False, str(e), 0


# ── Schemas Pydantic ──────────────────────────────────────────────────────────

class RegistrarCPERequest(BaseModel):
    """
    Payload que envía el motor al registrar un comprobante procesado.
    Compatible con los datos que ya produce monitor.py.
    """
    nombre_archivo:       str
    ruc_emisor:           str
    razon_social:         str = ""
    tipo_comprobante:     str             # 'B' | 'F' | 'NC'
    serie:                str
    numero:               int
    fecha_emision:        str             # YYYY-MM-DD
    cliente_tipo_doc:     str = "-"
    cliente_num_doc:      str = "00000000"
    cliente_denominacion: str = "CLIENTE VARIOS"
    total_gravada:        float = 0.0
    total_exonerada:      float = 0.0
    total_igv:            float = 0.0
    total_icbper:         float = 0.0
    total:                float
    forma_pago:           str = "Contado"
    estado:               str = "enviado"   # estado ya conocido al registrar
    origen:               str = "dbf"
    # Opcional: resultado del envío ya hecho por el motor
    envio_resultado:      Optional[str] = None
    envio_respuesta_api:  Optional[str] = None
    envio_duracion_ms:    Optional[int] = None
    envio_url:            Optional[str] = None


class ConfigUpdateRequest(BaseModel):
    valor: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/", tags=["Sistema"])
def health_check():
    """Health check del Bridge."""
    return {
        "servicio":  "DisateQ Bridge™ API",
        "version":   "2.0.0",
        "estado":    "activo",
        "timestamp": ahora_iso(),
    }


@app.get("/status", tags=["Sistema"])
def get_status():
    """
    Estado completo del Bridge:
    - Stats del día (enviados, errores, pendientes, monto)
    - Estado de conexión con APIFAS
    - Configuración activa del motor
    """
    cfg      = _config_motor()
    url_envio = cfg.get("ENVIO", "url_envio", fallback="")

    # Verificar conexión APIFAS
    apifas_ok = False
    if url_envio:
        try:
            r = requests.get(url_envio, timeout=5)
            apifas_ok = r.status_code < 500
        except Exception:
            apifas_ok = False

    with get_conn() as conn:
        hoy   = datetime.now().strftime("%Y-%m-%d")
        stats = stats_hoy(conn, hoy)

        # Últimos 5 eventos de error
        errores_recientes = _rows_to_list(
            ultimos_eventos(conn, limite=5, nivel="error")
        )

    return {
        "bridge": {
            "version":    "2.0.0",
            "timestamp":  ahora_iso(),
        },
        "motor": {
            "ruc":          cfg.get("EMPRESA", "ruc",          fallback="—"),
            "razon_social": cfg.get("EMPRESA", "razon_social", fallback="—"),
            "modalidad":    cfg.get("ENVIO",   "modalidad",    fallback="—"),
            "modo":         cfg.get("ENVIO",   "modo",         fallback="—"),
            "ruta_dbf":     cfg.get("RUTAS",   "data_dbf",     fallback="—"),
        },
        "apifas": {
            "url":    url_envio,
            "online": apifas_ok,
        },
        "stats_hoy":         stats,
        "errores_recientes": errores_recientes,
    }


@app.get("/comprobantes", tags=["Comprobantes"])
def get_comprobantes(
    fecha:  Optional[str] = Query(None, description="YYYY-MM-DD — filtrar por fecha"),
    estado: Optional[str] = Query(None, description="pendiente|enviado|error|repetido|anulado"),
    limite: int           = Query(100,  ge=1, le=500),
    offset: int           = Query(0,    ge=0),
):
    """
    Lista paginada de comprobantes con filtros opcionales.
    Por defecto retorna los últimos 100 ordenados por fecha DESC.
    """
    with get_conn() as conn:
        rows = listar_comprobantes(conn, fecha=fecha, estado=estado,
                                   limite=limite, offset=offset)
        total = conn.execute(
            "SELECT COUNT(*) FROM comprobantes"
            + (" WHERE fecha_emision = ?" if fecha else ""),
            ([fecha] if fecha else []),
        ).fetchone()[0]

    return {
        "total":   total,
        "limite":  limite,
        "offset":  offset,
        "items":   _rows_to_list(rows),
    }


@app.get("/comprobantes/{comp_id}", tags=["Comprobantes"])
def get_comprobante(comp_id: str):
    """Detalle completo de un comprobante por su ID."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM comprobantes WHERE id = ?", (comp_id,)
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")

    return _row_to_dict(row)


@app.get("/comprobantes/{comp_id}/envios", tags=["Comprobantes"])
def get_envios_comprobante(comp_id: str):
    """Historial completo de intentos de envío de un comprobante."""
    with get_conn() as conn:
        # Verificar que el comprobante exista
        existe = conn.execute(
            "SELECT id FROM comprobantes WHERE id = ?", (comp_id,)
        ).fetchone()
        if not existe:
            raise HTTPException(status_code=404, detail="Comprobante no encontrado")

        rows = conn.execute(
            "SELECT * FROM envios WHERE comprobante_id = ? ORDER BY intento ASC",
            (comp_id,),
        ).fetchall()

    return {"comprobante_id": comp_id, "envios": _rows_to_list(rows)}


@app.post("/comprobantes/registrar", tags=["Comprobantes"], status_code=201)
def registrar_comprobante(payload: RegistrarCPERequest):
    """
    Registra un comprobante procesado por el motor.
    Llamado por el motor después de cada envío exitoso (o fallido).

    Si el comprobante ya existe (por nombre_archivo), actualiza su estado
    en vez de duplicar — para soportar reintentos del motor.
    """
    # Validar total: boletas y facturas no pueden ser negativas
    if payload.tipo_comprobante in ("B", "F") and payload.total < 0:
        raise HTTPException(
            status_code=422,
            detail=f"total no puede ser negativo para tipo '{payload.tipo_comprobante}'"
        )
    with get_conn() as conn:
        existente = obtener_comprobante_por_archivo(conn, payload.nombre_archivo)

        if existente:
            # Ya existe — solo actualizar estado
            actualizar_estado_comprobante(conn, existente["id"], payload.estado)
            comp_id = existente["id"]
            accion  = "actualizado"
        else:
            # Nuevo comprobante
            datos = payload.model_dump(exclude={
                "envio_resultado", "envio_respuesta_api",
                "envio_duracion_ms", "envio_url",
            })
            comp_id = insertar_comprobante(conn, datos)
            accion  = "creado"

        # Registrar el envío si viene info de él
        if payload.envio_resultado:
            cfg      = _config_motor()
            modalidad = cfg.get("ENVIO", "modalidad", fallback="OSE")
            url       = payload.envio_url or cfg.get("ENVIO", "url_envio", fallback="")

            # Contar intentos previos
            n_intentos = conn.execute(
                "SELECT COUNT(*) FROM envios WHERE comprobante_id = ?", (comp_id,)
            ).fetchone()[0]

            insertar_envio(conn, {
                "comprobante_id": comp_id,
                "intento":        n_intentos + 1,
                "modalidad":      modalidad,
                "url_destino":    url,
                "resultado":      payload.envio_resultado,
                "respuesta_api":  payload.envio_respuesta_api,
                "codigo_http":    200 if payload.envio_resultado == "enviado" else 0,
                "contenido_txt":  None,
                "iniciado_at":    ahora_iso(),
                "completado_at":  ahora_iso(),
                "duracion_ms":    payload.envio_duracion_ms,
            })

        # Log del evento
        tipo_ev = "envio_ok" if payload.estado == "enviado" else "envio_error"
        log_evento(
            conn, tipo_ev,
            f"{payload.serie}-{str(payload.numero).zfill(8)} {accion} — estado: {payload.estado}",
            nivel="info" if payload.estado == "enviado" else "error",
            comprobante_id=comp_id,
            detalle={"serie": payload.serie, "numero": payload.numero,
                     "total": payload.total, "accion": accion},
        )

    log.info(f"[registrar] {payload.nombre_archivo} → {accion} ({payload.estado})")
    return {"id": comp_id, "accion": accion, "estado": payload.estado}


@app.post("/comprobantes/{comp_id}/reenviar", tags=["Comprobantes"])
def reenviar_comprobante(comp_id: str):
    """
    Reenvía manualmente un comprobante a APIFAS.
    Lee el TXT desde la carpeta del motor y lo envía.
    Útil para reintentar errores desde el dashboard.
    """
    with get_conn() as conn:
        comp = conn.execute(
            "SELECT * FROM comprobantes WHERE id = ?", (comp_id,)
        ).fetchone()
        if not comp:
            raise HTTPException(status_code=404, detail="Comprobante no encontrado")

        cfg       = _config_motor()
        ruc       = cfg.get("EMPRESA", "ruc",       fallback=comp["ruc_emisor"])
        url_envio = cfg.get("ENVIO",   "url_envio", fallback="")
        modalidad = cfg.get("ENVIO",   "modalidad", fallback="OSE")

        if not url_envio:
            raise HTTPException(status_code=503, detail="URL de APIFAS no configurada")

        # Leer TXT desde disco
        contenido = _leer_txt(comp["nombre_archivo"])
        if not contenido:
            raise HTTPException(
                status_code=404,
                detail=f"Archivo TXT no encontrado: {comp['nombre_archivo']}"
            )

        # Enviar
        t0 = time.time()
        exito, respuesta, codigo_http = _enviar_a_apifas(
            comp["nombre_archivo"], contenido, ruc, url_envio
        )
        duracion_ms = int((time.time() - t0) * 1000)

        resultado = "enviado" if exito else "error_respuesta"
        nuevo_estado = "enviado" if exito else "error"

        # Contar intentos previos
        n_intentos = conn.execute(
            "SELECT COUNT(*) FROM envios WHERE comprobante_id = ?", (comp_id,)
        ).fetchone()[0]

        insertar_envio(conn, {
            "comprobante_id": comp_id,
            "intento":        n_intentos + 1,
            "modalidad":      modalidad,
            "url_destino":    url_envio,
            "resultado":      resultado,
            "respuesta_api":  respuesta,
            "codigo_http":    codigo_http,
            "contenido_txt":  contenido,
            "iniciado_at":    ahora_iso(),
            "completado_at":  ahora_iso(),
            "duracion_ms":    duracion_ms,
        })

        actualizar_estado_comprobante(conn, comp_id, nuevo_estado)

        tipo_ev = "reenvio_ok" if exito else "reenvio_error"
        log_evento(
            conn, tipo_ev,
            f"Reenvío manual {comp['nombre_archivo']} → {resultado}",
            nivel="info" if exito else "error",
            comprobante_id=comp_id,
            detalle={"respuesta": respuesta, "duracion_ms": duracion_ms},
        )

    log.info(f"[reenviar] {comp['nombre_archivo']} → {resultado} ({duracion_ms}ms)")
    return {
        "comprobante_id": comp_id,
        "resultado":      resultado,
        "respuesta_api":  respuesta,
        "duracion_ms":    duracion_ms,
        "nuevo_estado":   nuevo_estado,
    }


@app.get("/log", tags=["Log"])
def get_log(
    limite: int           = Query(50,  ge=1, le=500),
    nivel:  Optional[str] = Query(None, description="info|warn|error"),
):
    """Últimos N eventos del log de auditoría."""
    with get_conn() as conn:
        rows = ultimos_eventos(conn, limite=limite, nivel=nivel)
    return {"total": len(rows), "items": _rows_to_list(rows)}


@app.get("/config", tags=["Configuración"])
def get_config():
    """
    Retorna la configuración completa del Bridge
    más los valores del motor (ffee_config.ini).
    """
    with get_conn() as conn:
        bridge_cfg = {
            r["clave"]: r["valor"]
            for r in conn.execute("SELECT clave, valor FROM config_bridge").fetchall()
        }

    cfg   = _config_motor()
    motor = {}
    for seccion in cfg.sections():
        for clave, valor in cfg.items(seccion):
            motor[f"{seccion.lower()}.{clave}"] = valor

    return {"bridge": bridge_cfg, "motor": motor}


@app.put("/config/{clave}", tags=["Configuración"])
def update_config(clave: str, body: ConfigUpdateRequest):
    """Actualiza un valor de configuración del Bridge."""
    with get_conn() as conn:
        existe = conn.execute(
            "SELECT clave FROM config_bridge WHERE clave = ?", (clave,)
        ).fetchone()
        if not existe:
            raise HTTPException(status_code=404, detail=f"Clave '{clave}' no existe")
        conn.execute(
            "UPDATE config_bridge SET valor = ?, updated_at = ? WHERE clave = ?",
            (body.valor, ahora_iso(), clave),
        )
        log_evento(conn, "config_actualizada",
                   f"config_bridge.{clave} = {body.valor}", nivel="info")

    return {"clave": clave, "valor": body.valor, "updated_at": ahora_iso()}


# ── Arranque directo ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "bridge_api:app",
        host    = "0.0.0.0",
        port    = 8765,
        reload  = True,
        log_level="info",
    )
