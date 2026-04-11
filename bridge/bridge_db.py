"""
bridge_db.py
============
Esquema SQLite — DisateQ Bridge™ | BridgeAPI Etapa 2

Responsabilidad única: definir y crear las tablas del Bridge.
No contiene lógica de negocio — solo estructura de datos.

Tablas:
  comprobantes   ← registro central de cada CPE procesado
  envios         ← historial de intentos de envío a APIFAS
  eventos_log    ← log de auditoría de todas las acciones del motor
  config_bridge  ← parámetros de configuración del Bridge (clave-valor)

Principios:
  - sqlite3 puro, sin ORM — máxima portabilidad en Windows
  - snake_case en español
  - UUID como TEXT generado en Python (no AUTOINCREMENT)
  - Toda tabla incluye created_at + updated_at
  - No se borra nada — se usa estado lógico (anulado, error, etc.)

Uso:
  from bridge_db import init_db, get_conn
  init_db()                        # crea tablas si no existen
  with get_conn() as conn:
      rows = conn.execute("SELECT * FROM comprobantes").fetchall()
"""

import sqlite3
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager

log = logging.getLogger(__name__)

# ── Ruta de la base de datos ────────────────────────────────────────────────

BASE_DIR = Path(r"D:\FFEESUNAT\CPE DisateQ")
DB_PATH  = BASE_DIR / "bridge.db"


def _db_path() -> Path:
    """Retorna la ruta del DB, creando el directorio si no existe."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return DB_PATH


# ── Conexión ────────────────────────────────────────────────────────────────

@contextmanager
def get_conn(db_path: Path | None = None):
    """
    Context manager para obtener una conexión SQLite.
    Usa row_factory=sqlite3.Row para acceso por nombre de columna.
    Hace commit al salir limpio, rollback si hay excepción.

    Uso:
        with get_conn() as conn:
            conn.execute("INSERT INTO ...")
    """
    path = db_path or _db_path()
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # mejor concurrencia lectura/escritura
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Helpers ─────────────────────────────────────────────────────────────────

def nuevo_id() -> str:
    """Genera UUID v4 como string. Usado como PK en todas las tablas."""
    return str(uuid.uuid4())


def ahora_iso() -> str:
    """Timestamp UTC en ISO 8601. Ej: 2026-04-10T15:30:00+00:00"""
    return datetime.now(timezone.utc).isoformat()


# ── DDL — Definición de tablas ───────────────────────────────────────────────

_DDL_COMPROBANTES = """
CREATE TABLE IF NOT EXISTS comprobantes (
    -- Identidad
    id              TEXT PRIMARY KEY,           -- UUID generado en Python
    nombre_archivo  TEXT NOT NULL UNIQUE,       -- 10405206710-02-B001-00023168.txt
    ruc_emisor      TEXT NOT NULL,              -- RUC de la farmacia
    razon_social    TEXT,

    -- Clasificación del CPE
    tipo_comprobante TEXT NOT NULL,             -- 'B' boleta / 'F' factura / 'NC' nota crédito
    serie           TEXT NOT NULL,              -- B001, F001, NC01
    numero          INTEGER NOT NULL,           -- correlativo numérico
    fecha_emision   TEXT NOT NULL,              -- YYYY-MM-DD

    -- Cliente
    cliente_tipo_doc    TEXT DEFAULT '-',       -- '-', '1' DNI, '6' RUC
    cliente_num_doc     TEXT DEFAULT '00000000',
    cliente_denominacion TEXT DEFAULT 'CLIENTE VARIOS',

    -- Totales (en soles, 2 decimales)
    total_gravada   REAL DEFAULT 0.0,
    total_exonerada REAL DEFAULT 0.0,
    total_igv       REAL DEFAULT 0.0,
    total_icbper    REAL DEFAULT 0.0,
    total           REAL NOT NULL DEFAULT 0.0,

    -- Pago
    forma_pago      TEXT DEFAULT 'Contado',     -- 'Contado' / 'Credito'

    -- Estado lógico del comprobante
    -- pendiente | enviado | error | repetido | anulado
    estado          TEXT NOT NULL DEFAULT 'pendiente',

    -- Origen: dónde fue detectado
    -- 'dbf' = leído del DBF por el motor
    -- 'txt' = importado de carpeta enviados/
    -- 'manual' = registrado manualmente
    origen          TEXT DEFAULT 'dbf',

    -- Auditoría
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,

    -- Constraint: serie+numero es único por empresa
    UNIQUE (ruc_emisor, serie, numero)
);
"""

_DDL_ENVIOS = """
CREATE TABLE IF NOT EXISTS envios (
    -- Identidad
    id                  TEXT PRIMARY KEY,
    comprobante_id      TEXT NOT NULL,          -- FK → comprobantes.id

    -- Intento de envío
    intento             INTEGER NOT NULL DEFAULT 1,  -- 1, 2, 3...
    modalidad           TEXT NOT NULL,          -- 'OSE' / 'SUNAT'
    url_destino         TEXT NOT NULL,          -- URL de APIFAS usada

    -- Resultado
    -- enviado | error_conexion | error_respuesta | timeout | repetido
    resultado           TEXT NOT NULL,
    respuesta_api       TEXT,                   -- texto crudo de APIFAS
    codigo_http         INTEGER,                -- 200, 400, 500...

    -- Contenido enviado (para auditoría y reenvíos)
    contenido_txt       TEXT,                   -- TXT completo enviado

    -- Tiempos
    iniciado_at         TEXT NOT NULL,
    completado_at       TEXT,
    duracion_ms         INTEGER,                -- milisegundos

    -- Auditoría
    created_at          TEXT NOT NULL,

    FOREIGN KEY (comprobante_id) REFERENCES comprobantes(id)
);
"""

_DDL_EVENTOS_LOG = """
CREATE TABLE IF NOT EXISTS eventos_log (
    -- Identidad
    id              TEXT PRIMARY KEY,

    -- Referencia opcional al comprobante
    comprobante_id  TEXT,                       -- NULL si es evento general

    -- Clasificación del evento
    -- ciclo_inicio | ciclo_fin | dbf_leido | txt_generado | txt_invalido
    -- envio_ok | envio_error | sin_detalle | correlativo_ignorado
    -- motor_inicio | motor_error | bridge_inicio | bridge_error
    nivel           TEXT NOT NULL,              -- 'info' | 'warn' | 'error'
    tipo_evento     TEXT NOT NULL,
    mensaje         TEXT NOT NULL,

    -- Contexto adicional (JSON serializado)
    detalle_json    TEXT,                       -- {'serie':'B001','numero':23168,...}

    -- Auditoría
    created_at      TEXT NOT NULL
);
"""

_DDL_CONFIG_BRIDGE = """
CREATE TABLE IF NOT EXISTS config_bridge (
    -- Clave-valor para configuración dinámica del Bridge
    clave           TEXT PRIMARY KEY,
    valor           TEXT,
    descripcion     TEXT,
    updated_at      TEXT NOT NULL
);
"""

# ── Índices ──────────────────────────────────────────────────────────────────

_DDL_INDICES = [
    # Comprobantes: búsquedas frecuentes
    "CREATE INDEX IF NOT EXISTS idx_comp_estado       ON comprobantes (estado);",
    "CREATE INDEX IF NOT EXISTS idx_comp_fecha        ON comprobantes (fecha_emision);",
    "CREATE INDEX IF NOT EXISTS idx_comp_serie_num    ON comprobantes (serie, numero);",
    "CREATE INDEX IF NOT EXISTS idx_comp_ruc          ON comprobantes (ruc_emisor);",

    # Envíos: historial por comprobante
    "CREATE INDEX IF NOT EXISTS idx_envios_comp_id    ON envios (comprobante_id);",
    "CREATE INDEX IF NOT EXISTS idx_envios_resultado  ON envios (resultado);",
    "CREATE INDEX IF NOT EXISTS idx_envios_iniciado   ON envios (iniciado_at);",

    # Eventos: log por comprobante y nivel
    "CREATE INDEX IF NOT EXISTS idx_log_comp_id       ON eventos_log (comprobante_id);",
    "CREATE INDEX IF NOT EXISTS idx_log_nivel         ON eventos_log (nivel);",
    "CREATE INDEX IF NOT EXISTS idx_log_tipo          ON eventos_log (tipo_evento);",
    "CREATE INDEX IF NOT EXISTS idx_log_created       ON eventos_log (created_at);",
]

# ── Datos iniciales de configuración ────────────────────────────────────────

_CONFIG_DEFAULTS = [
    ("bridge_version",    "2.0.0",   "Versión de BridgeAPI"),
    ("motor_ruta_salida", r"D:\FFEESUNAT\CPE DisateQ", "Ruta base del motor"),
    ("watcher_activo",    "true",    "Activar watcher de carpeta enviados/"),
    ("watcher_intervalo", "10",      "Segundos entre escaneos del watcher"),
    ("api_port",          "8765",    "Puerto local de BridgeAPI"),
    ("dashboard_url",     "http://localhost:5173", "URL del dashboard React"),
    ("log_nivel",         "INFO",    "Nivel de logging: DEBUG, INFO, WARNING, ERROR"),
    ("max_registros_log", "10000",   "Máximo de eventos_log a conservar por rotación"),
]


# ── Inicialización ───────────────────────────────────────────────────────────

def init_db(db_path: Path | None = None) -> Path:
    """
    Crea todas las tablas, índices y configuración inicial si no existen.
    Idempotente: puede llamarse múltiples veces sin problema.

    Returns:
        Path al archivo .db creado/existente.
    """
    path = db_path or _db_path()
    log.info(f"[bridge_db] Inicializando BD en: {path}")

    with get_conn(path) as conn:
        # Tablas
        conn.execute(_DDL_COMPROBANTES)
        conn.execute(_DDL_ENVIOS)
        conn.execute(_DDL_EVENTOS_LOG)
        conn.execute(_DDL_CONFIG_BRIDGE)

        # Índices
        for ddl in _DDL_INDICES:
            conn.execute(ddl)

        # Config defaults (INSERT OR IGNORE para no sobreescribir si ya existe)
        ahora = ahora_iso()
        for clave, valor, desc in _CONFIG_DEFAULTS:
            conn.execute(
                """
                INSERT OR IGNORE INTO config_bridge (clave, valor, descripcion, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (clave, valor, desc, ahora),
            )

    log.info("[bridge_db] BD lista.")
    return path


# ── CRUD básico — Comprobantes ───────────────────────────────────────────────

def insertar_comprobante(conn: sqlite3.Connection, datos: dict) -> str:
    """
    Inserta un comprobante nuevo. Retorna su ID.

    Solo nombre_archivo, ruc_emisor, tipo_comprobante, serie, numero,
    fecha_emision y total son obligatorios. El resto tiene defaults seguros.
    """
    comp_id = nuevo_id()
    ahora   = ahora_iso()
    # Aplicar defaults explícitos para todos los campos opcionales.
    # Evita ProgrammingError cuando el motor no envía ciertos campos.
    fila = {
        "id":                    comp_id,
        "nombre_archivo":        datos["nombre_archivo"],
        "ruc_emisor":            datos["ruc_emisor"],
        "razon_social":          datos.get("razon_social",          ""),
        "tipo_comprobante":      datos["tipo_comprobante"],
        "serie":                 datos["serie"],
        "numero":                datos["numero"],
        "fecha_emision":         datos["fecha_emision"],
        "cliente_tipo_doc":      datos.get("cliente_tipo_doc",      "-"),
        "cliente_num_doc":       datos.get("cliente_num_doc",       "00000000"),
        "cliente_denominacion":  datos.get("cliente_denominacion",  "CLIENTE VARIOS"),
        "total_gravada":         datos.get("total_gravada",         0.0),
        "total_exonerada":       datos.get("total_exonerada",       0.0),
        "total_igv":             datos.get("total_igv",             0.0),
        "total_icbper":          datos.get("total_icbper",          0.0),
        "total":                 datos["total"],
        "forma_pago":            datos.get("forma_pago",            "Contado"),
        "estado":                datos.get("estado",                "pendiente"),
        "origen":                datos.get("origen",                "dbf"),
        "created_at":            ahora,
        "updated_at":            ahora,
    }
    conn.execute(
        """
        INSERT INTO comprobantes (
            id, nombre_archivo, ruc_emisor, razon_social,
            tipo_comprobante, serie, numero, fecha_emision,
            cliente_tipo_doc, cliente_num_doc, cliente_denominacion,
            total_gravada, total_exonerada, total_igv, total_icbper, total,
            forma_pago, estado, origen, created_at, updated_at
        ) VALUES (
            :id, :nombre_archivo, :ruc_emisor, :razon_social,
            :tipo_comprobante, :serie, :numero, :fecha_emision,
            :cliente_tipo_doc, :cliente_num_doc, :cliente_denominacion,
            :total_gravada, :total_exonerada, :total_igv, :total_icbper, :total,
            :forma_pago, :estado, :origen, :created_at, :updated_at
        )
        """,
        fila,
    )
    return comp_id


def actualizar_estado_comprobante(
    conn: sqlite3.Connection, comp_id: str, estado: str
) -> None:
    """Actualiza el estado lógico de un comprobante."""
    conn.execute(
        "UPDATE comprobantes SET estado = ?, updated_at = ? WHERE id = ?",
        (estado, ahora_iso(), comp_id),
    )


def obtener_comprobante_por_archivo(
    conn: sqlite3.Connection, nombre_archivo: str
) -> sqlite3.Row | None:
    """Busca un comprobante por nombre de archivo TXT."""
    return conn.execute(
        "SELECT * FROM comprobantes WHERE nombre_archivo = ?",
        (nombre_archivo,),
    ).fetchone()


# ── CRUD básico — Envíos ─────────────────────────────────────────────────────

def insertar_envio(conn: sqlite3.Connection, datos: dict) -> str:
    """
    Registra un intento de envío. Retorna su ID.

    datos esperados:
        comprobante_id, intento, modalidad, url_destino,
        resultado, respuesta_api, codigo_http,
        contenido_txt, iniciado_at, completado_at, duracion_ms
    """
    envio_id = nuevo_id()
    ahora    = ahora_iso()
    conn.execute(
        """
        INSERT INTO envios (
            id, comprobante_id, intento, modalidad, url_destino,
            resultado, respuesta_api, codigo_http,
            contenido_txt, iniciado_at, completado_at, duracion_ms,
            created_at
        ) VALUES (
            :id, :comprobante_id, :intento, :modalidad, :url_destino,
            :resultado, :respuesta_api, :codigo_http,
            :contenido_txt, :iniciado_at, :completado_at, :duracion_ms,
            :created_at
        )
        """,
        {**datos, "id": envio_id, "created_at": ahora},
    )
    return envio_id


# ── CRUD básico — Log de eventos ─────────────────────────────────────────────

def log_evento(
    conn: sqlite3.Connection,
    tipo_evento: str,
    mensaje: str,
    nivel: str = "info",
    comprobante_id: str | None = None,
    detalle: dict | None = None,
) -> None:
    """
    Registra un evento de auditoría.

    Uso rápido:
        log_evento(conn, "envio_ok", "B001-00023168 enviado correctamente",
                   comprobante_id=comp_id)
    """
    import json as _json
    conn.execute(
        """
        INSERT INTO eventos_log (
            id, comprobante_id, nivel, tipo_evento, mensaje, detalle_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            nuevo_id(),
            comprobante_id,
            nivel,
            tipo_evento,
            mensaje,
            _json.dumps(detalle, ensure_ascii=False) if detalle else None,
            ahora_iso(),
        ),
    )


# ── Consultas de resumen para el Dashboard ───────────────────────────────────

def stats_hoy(conn: sqlite3.Connection, fecha: str | None = None) -> dict:
    """
    Retorna KPIs del día para el dashboard.
    fecha: 'YYYY-MM-DD' — por defecto hoy.

    Returns:
        {
            "enviados": int,
            "errores": int,
            "pendientes": int,
            "total_monto": float,
            "fecha": str,
        }
    """
    if fecha is None:
        fecha = datetime.now().strftime("%Y-%m-%d")

    row = conn.execute(
        """
        SELECT
            COUNT(CASE WHEN estado = 'enviado'   THEN 1 END) AS enviados,
            COUNT(CASE WHEN estado = 'error'     THEN 1 END) AS errores,
            COUNT(CASE WHEN estado = 'pendiente' THEN 1 END) AS pendientes,
            COALESCE(SUM(CASE WHEN estado = 'enviado' THEN total ELSE 0 END), 0) AS total_monto
        FROM comprobantes
        WHERE fecha_emision = ?
        """,
        (fecha,),
    ).fetchone()

    return {
        "enviados":    row["enviados"]   or 0,
        "errores":     row["errores"]    or 0,
        "pendientes":  row["pendientes"] or 0,
        "total_monto": round(row["total_monto"] or 0.0, 2),
        "fecha":       fecha,
    }


def listar_comprobantes(
    conn: sqlite3.Connection,
    fecha: str | None = None,
    estado: str | None = None,
    limite: int = 100,
    offset: int = 0,
) -> list[sqlite3.Row]:
    """
    Lista comprobantes con filtros opcionales.
    Ordenados por fecha_emision DESC, numero DESC.
    """
    filtros = []
    params: list = []

    if fecha:
        filtros.append("fecha_emision = ?")
        params.append(fecha)
    if estado:
        filtros.append("estado = ?")
        params.append(estado)

    where = ("WHERE " + " AND ".join(filtros)) if filtros else ""
    params += [limite, offset]

    return conn.execute(
        f"""
        SELECT * FROM comprobantes
        {where}
        ORDER BY fecha_emision DESC, numero DESC
        LIMIT ? OFFSET ?
        """,
        params,
    ).fetchall()


def ultimos_eventos(
    conn: sqlite3.Connection,
    limite: int = 50,
    nivel: str | None = None,
) -> list[sqlite3.Row]:
    """Retorna los últimos N eventos del log, opcionalmente filtrados por nivel."""
    if nivel:
        return conn.execute(
            "SELECT * FROM eventos_log WHERE nivel = ? ORDER BY created_at DESC LIMIT ?",
            (nivel, limite),
        ).fetchall()
    return conn.execute(
        "SELECT * FROM eventos_log ORDER BY created_at DESC LIMIT ?",
        (limite,),
    ).fetchall()


# ── Entry point de prueba ────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

    # Para desarrollo: usar BD local en vez de D:\
    db_dev = Path("bridge_dev.db")
    path   = init_db(db_dev)
    print(f"\n✅  BD creada en: {path}")

    # Insertar comprobante de prueba
    with get_conn(db_dev) as conn:
        comp_id = insertar_comprobante(conn, {
            "nombre_archivo":       "10405206710-02-B001-00023170.txt",
            "ruc_emisor":           "10405206710",
            "razon_social":         "FARMACIA DEL PUEBLO S.A.C.",
            "tipo_comprobante":     "B",
            "serie":                "B001",
            "numero":               23170,
            "fecha_emision":        "2026-04-10",
            "cliente_tipo_doc":     "-",
            "cliente_num_doc":      "00000000",
            "cliente_denominacion": "CLIENTE VARIOS",
            "total_gravada":        16.95,
            "total_exonerada":      0.0,
            "total_igv":            3.05,
            "total_icbper":         0.0,
            "total":                20.0,
            "forma_pago":           "Contado",
            "estado":               "enviado",
            "origen":               "dbf",
        })
        print(f"✅  Comprobante insertado: {comp_id}")

        # Registrar envío exitoso
        insertar_envio(conn, {
            "comprobante_id": comp_id,
            "intento":        1,
            "modalidad":      "OSE",
            "url_destino":    "https://apifas.disateq.com/ose_produccion.php",
            "resultado":      "enviado",
            "respuesta_api":  "proceso-aceptado",
            "codigo_http":    200,
            "contenido_txt":  None,
            "iniciado_at":    ahora_iso(),
            "completado_at":  ahora_iso(),
            "duracion_ms":    342,
        })
        print("✅  Envío registrado")

        # Log de evento
        log_evento(conn, "envio_ok", "B001-00023170 enviado correctamente",
                   comprobante_id=comp_id,
                   detalle={"serie": "B001", "numero": 23170, "total": 20.0})
        print("✅  Evento logueado")

        # Stats
        stats = stats_hoy(conn, "2026-04-10")
        print(f"\n📊  Stats hoy: {json.dumps(stats, indent=2)}")

        # Listar
        rows = listar_comprobantes(conn, fecha="2026-04-10")
        print(f"\n📋  Comprobantes del día: {len(rows)}")
        for r in rows:
            print(f"    {r['serie']}-{str(r['numero']).zfill(8)}  [{r['estado']}]  S/ {r['total']:.2f}")
