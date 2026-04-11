"""
rc_diario.py
============
Resumen de Comprobantes (RC) diario para modalidad SEE SUNAT — CPE DisateQ™

SUNAT exige un RC diario para boletas emitidas en modalidad SEE (Sistema de
Emisión Electrónica). El RC agrupa las boletas del día por serie, indicando:
  - Correlativo inicial y final de cada serie
  - Total de comprobantes emitidos
  - Total de comprobantes anulados (si los hay)

El RC se genera una vez al día, al cierre de operaciones, y se envía a APIFAS
con un endpoint específico.

Referencia SUNAT: RS 097-2012/SUNAT y modificatorias.

Uso:
    from rc_diario import generar_rc, enviar_rc, RCDiario

    rc = generar_rc(salida, ruc, razon_social)
    if rc:
        exito, msg = enviar_rc(rc, url_rc, ruc)
"""

import json
import logging
import requests
from datetime import date, datetime
from pathlib import Path
from collections import defaultdict

log = logging.getLogger(__name__)

RC_DIR = "rc"


# ── Estructura de datos ───────────────────────────────────────

class RCDiario:
    """Representa un Resumen de Comprobantes diario."""

    def __init__(self, ruc: str, razon_social: str, fecha: date):
        self.ruc          = ruc
        self.razon_social = razon_social
        self.fecha        = fecha
        self.series:      list[dict] = []   # una entrada por serie
        self.generado_en: datetime   = datetime.now()

    def agregar_serie(
        self,
        serie:      str,
        tipo_doc:   str,   # "03" boleta, "07" NC boleta
        correlativo_inicio: int,
        correlativo_fin:    int,
        total_emitidos:     int,
        total_anulados:     int = 0,
    ):
        self.series.append({
            "serie":                serie,
            "tipo_doc":             tipo_doc,
            "correlativo_inicio":   correlativo_inicio,
            "correlativo_fin":      correlativo_fin,
            "total_emitidos":       total_emitidos,
            "total_anulados":       total_anulados,
        })

    def tiene_datos(self) -> bool:
        return bool(self.series)

    def a_dict(self) -> dict:
        return {
            "ruc":          self.ruc,
            "razon_social": self.razon_social,
            "fecha":        self.fecha.strftime("%d-%m-%Y"),
            "fecha_iso":    self.fecha.isoformat(),
            "generado_en":  self.generado_en.strftime("%Y-%m-%d %H:%M:%S"),
            "series":       self.series,
        }

    def a_txt(self) -> str:
        """Genera el contenido TXT en formato APIFAS para el RC."""
        lineas = [
            "operacion|generar_resumen|",
            f"ruc|{self.ruc}|",
            f"fecha_de_generacion|{self.generado_en.strftime('%d-%m-%Y')}|",
            f"fecha_inicio_periodo|{self.fecha.strftime('%d-%m-%Y')}|",
            f"fecha_fin_periodo|{self.fecha.strftime('%d-%m-%Y')}|",
        ]
        for s in self.series:
            lineas.append(
                f"resumen|{s['serie']}|{s['tipo_doc']}|"
                f"{s['correlativo_inicio']}|{s['correlativo_fin']}|"
                f"{s['total_emitidos']}|{s['total_anulados']}|"
            )
        return "\n".join(lineas)


# ── Generación del RC ─────────────────────────────────────────

def generar_rc(
    salida:       str,
    ruc:          str,
    razon_social: str,
    fecha:        date = None,
) -> "RCDiario | None":
    """
    Lee los TXT enviados del día y construye el RCDiario.

    Solo incluye boletas (series B*) y notas de crédito de boletas (BC*).
    Las facturas NO van en el RC diario SEE.

    Retorna None si no hay boletas del día.
    """
    fecha = fecha or date.today()
    carpeta_enviados = Path(salida) / "enviados"

    if not carpeta_enviados.exists():
        log.info("RC: carpeta enviados/ no existe aún")
        return None

    # Leer TXT del día y agrupar por serie
    por_serie: dict[str, list[int]] = defaultdict(list)

    for f in sorted(carpeta_enviados.glob("*.txt")):
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        if mtime.date() != fecha:
            continue

        # Parsear nombre: RUC-02-SERIE-NUMERO.txt
        partes = f.stem.split("-")
        if len(partes) < 4:
            continue
        try:
            serie  = partes[2].upper()
            numero = int(partes[3])
        except (ValueError, IndexError):
            continue

        # Solo boletas y NC de boletas
        if not (serie.startswith("B") or serie.startswith("BC")):
            continue

        por_serie[serie].append(numero)

    if not por_serie:
        log.info(f"RC {fecha}: sin boletas del día")
        return None

    rc = RCDiario(ruc, razon_social, fecha)

    for serie in sorted(por_serie.keys()):
        nums = sorted(por_serie[serie])
        # Tipo SUNAT: B* → "03", BC* → "07"
        tipo_doc = "07" if serie.startswith("BC") else "03"
        rc.agregar_serie(
            serie             = serie,
            tipo_doc          = tipo_doc,
            correlativo_inicio = nums[0],
            correlativo_fin   = nums[-1],
            total_emitidos    = len(nums),
            total_anulados    = 0,
        )

    log.info(
        f"RC {fecha} generado: {len(rc.series)} serie(s), "
        f"{sum(s['total_emitidos'] for s in rc.series)} boletas"
    )
    return rc


# ── Guardado local del RC ─────────────────────────────────────

def _ruta_rc(salida: str) -> Path:
    p = Path(salida) / RC_DIR
    p.mkdir(exist_ok=True)
    return p


def guardar_rc(rc: RCDiario, salida: str) -> Path:
    """
    Guarda el RC en rc/ como JSON y TXT.
    Un archivo por día — sobreescribe si se regenera.
    """
    ruta_dir   = _ruta_rc(salida)
    nombre_base = f"rc_{rc.fecha.strftime('%Y%m%d')}"

    # JSON (para auditoría y reenvíos)
    ruta_json = ruta_dir / f"{nombre_base}.json"
    ruta_json.write_text(
        json.dumps(rc.a_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # TXT (formato APIFAS)
    ruta_txt = ruta_dir / f"{nombre_base}.txt"
    ruta_txt.write_text(rc.a_txt(), encoding="utf-8")

    log.info(f"RC guardado: {ruta_txt}")
    return ruta_txt


def rc_ya_enviado(salida: str, fecha: date = None) -> bool:
    """Retorna True si el RC del día ya fue enviado (existe .enviado)."""
    fecha = fecha or date.today()
    ruta  = _ruta_rc(salida) / f"rc_{fecha.strftime('%Y%m%d')}.enviado"
    return ruta.exists()


def marcar_rc_enviado(salida: str, fecha: date = None):
    """Crea el archivo .enviado para que no se reenvíe el RC."""
    fecha = fecha or date.today()
    ruta  = _ruta_rc(salida) / f"rc_{fecha.strftime('%Y%m%d')}.enviado"
    ruta.write_text(datetime.now().isoformat(), encoding="utf-8")


# ── Envío a APIFAS ────────────────────────────────────────────

TIMEOUT_RC = 30

def enviar_rc(rc: RCDiario, url_rc: str, ruc: str) -> tuple[bool, str]:
    """
    Envía el RC a APIFAS.
    Retorna (exito, mensaje).

    El endpoint de RC es distinto al de comprobantes individuales:
      SEE SUNAT RC: https://apifas.disateq.com/produccion_rc.php
    """
    if not url_rc:
        return False, "URL de RC no configurada"

    contenido = rc.a_txt().replace("\n", "")
    nombre    = f"{ruc}-RC-{rc.fecha.strftime('%Y%m%d')}.txt"

    try:
        resp = requests.post(
            url_rc,
            headers={"Texto": contenido, "Ruc": ruc, "Nombre": nombre},
            timeout=TIMEOUT_RC,
        )
        msg = resp.text.strip() if resp.text else ""
        if resp.status_code == 200 and _es_ok_rc(msg):
            log.info(f"RC {rc.fecha} enviado: {msg}")
            return True, msg
        log.warning(f"RC {rc.fecha} rechazado: {msg}")
        return False, msg or f"HTTP {resp.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Sin conexión a APIFAS"
    except requests.exceptions.Timeout:
        return False, f"Timeout al enviar RC ({TIMEOUT_RC}s)"
    except Exception as e:
        return False, str(e)


def _es_ok_rc(texto: str) -> bool:
    """Respuestas APIFAS que indican RC aceptado."""
    t = texto.lower().strip()
    return any(r in t for r in [
        "proceso-aceptado",
        "resumen aceptado",
        "rc aceptado",
        "ticket",
    ])


# ── Flujo completo: generar + guardar + enviar ────────────────

def procesar_rc_diario(
    salida:       str,
    ruc:          str,
    razon_social: str,
    url_rc:       str,
    forzar:       bool = False,
) -> tuple[bool, str]:
    """
    Flujo completo del RC diario.
    Se llama desde monitor.py al cierre del día.

    Args:
        forzar: True = reenviar aunque ya esté marcado como enviado.

    Returns:
        (exito, mensaje) — False si no hay boletas o ya fue enviado.
    """
    hoy = date.today()

    if not forzar and rc_ya_enviado(salida, hoy):
        return True, "RC del día ya enviado anteriormente"

    rc = generar_rc(salida, ruc, razon_social, hoy)
    if rc is None:
        return True, "Sin boletas del día — RC no requerido"

    guardar_rc(rc, salida)

    exito, msg = enviar_rc(rc, url_rc, ruc)
    if exito:
        marcar_rc_enviado(salida, hoy)

    return exito, msg


# ── Tests ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import tempfile, os
    from pathlib import Path

    print("=== Tests rc_diario ===\n")

    with tempfile.TemporaryDirectory() as tmp:
        salida = tmp
        enviados = Path(salida) / "enviados"
        enviados.mkdir()
        hoy = date.today()

        # Crear TXT de prueba con fecha de hoy
        def crear_txt(nombre):
            f = enviados / nombre
            f.write_text("operacion|generar_comprobante|\ntotal|100.00|\n",
                          encoding="utf-8")
            # Ajustar mtime a hoy
            import time
            ts = datetime.combine(hoy, datetime.min.time()).timestamp() + 3600
            os.utime(str(f), (ts, ts))

        # Boletas serie B001: correlativos 1,2,3
        crear_txt(f"20123456789-02-B001-00000001.txt")
        crear_txt(f"20123456789-02-B001-00000002.txt")
        crear_txt(f"20123456789-02-B001-00000003.txt")
        # Boletas serie B002: correlativo 1
        crear_txt(f"20123456789-02-B002-00000001.txt")
        # Factura (NO debe ir en RC)
        crear_txt(f"20123456789-02-F001-00000001.txt")
        # NC boleta BC01
        crear_txt(f"20123456789-02-BC01-00000001.txt")

        rc = generar_rc(salida, "20123456789", "FARMACIA TEST S.A.C.", hoy)

        assert rc is not None, "RC no generado"
        assert rc.tiene_datos()
        assert len(rc.series) == 3, f"Esperaba 3 series, got {len(rc.series)}"

        series_names = [s["serie"] for s in rc.series]
        assert "B001" in series_names
        assert "B002" in series_names
        assert "BC01" in series_names
        assert "F001" not in series_names, "Factura no debe estar en RC"
        print("✅  generar_rc() excluye facturas, incluye boletas y NC boletas")

        b001 = next(s for s in rc.series if s["serie"] == "B001")
        assert b001["correlativo_inicio"] == 1
        assert b001["correlativo_fin"]    == 3
        assert b001["total_emitidos"]     == 3
        assert b001["tipo_doc"]           == "03"
        print("✅  Serie B001: correlativos 1-3, tipo 03")

        bc01 = next(s for s in rc.series if s["serie"] == "BC01")
        assert bc01["tipo_doc"] == "07"
        print("✅  Serie BC01: tipo 07 (NC boleta)")

        # Test TXT
        txt = rc.a_txt()
        assert "operacion|generar_resumen|" in txt
        assert "B001" in txt
        assert "B002" in txt
        assert "F001" not in txt
        print("✅  a_txt() formato correcto")

        # Test guardado
        ruta_txt = guardar_rc(rc, salida)
        assert ruta_txt.exists()
        ruta_json = ruta_txt.with_suffix(".json")
        assert ruta_json.exists()
        data = json.loads(ruta_json.read_text())
        assert data["ruc"] == "20123456789"
        print("✅  guardar_rc() genera TXT y JSON")

        # Test marcado enviado
        assert not rc_ya_enviado(salida, hoy)
        marcar_rc_enviado(salida, hoy)
        assert rc_ya_enviado(salida, hoy)
        print("✅  marcar_rc_enviado() / rc_ya_enviado()")

        # Test sin boletas
        with tempfile.TemporaryDirectory() as tmp2:
            Path(tmp2, "enviados").mkdir()
            rc_vacio = generar_rc(tmp2, "20123456789", "TEST", hoy)
            assert rc_vacio is None
            print("✅  Sin boletas → retorna None")

    print()
    print("🎉  Todos los tests en verde.")
