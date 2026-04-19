"""
create_test_dbf.py
==================
Genera los tres DBF de prueba para DisateQ CPE™.
Simula la estructura del sistema de farmacia FoxPro.

Uso:
    python create_test_dbf.py

Genera en tests/samples/:
    enviosffee.dbf
    detalleventa.dbf
    productox.dbf
"""

import dbf
from pathlib import Path
from datetime import date

# Carpeta de salida
SAMPLES = Path("tests/samples")
SAMPLES.mkdir(parents=True, exist_ok=True)


# ── 1. productox.dbf ─────────────────────────────────────────
print("Creando productox.dbf...")

tabla_prod = dbf.Table(
    str(SAMPLES / "productox.dbf"),
    "CODIGO_PRO C(20); DESCRIPCIO C(60); PRESENTA_P C(30); "
    "CODIGO_UNS C(10); EXONERADO_ L; PRECIO_UNI N(10,2)",
    codepage="cp1252",
)
tabla_prod.open(dbf.READ_WRITE)

productos = [
    ("786341", "PARACETAMOL",      "500MG X 100 TAB",  "51191905", False, 1.10),
    ("787266", "IBUPROFENO",       "400MG X 100 TAB",  "51191905", False, 1.30),
    ("788100", "AMOXICILINA",      "500MG X 21 CAP",   "51191905", False, 15.00),
    ("900001", "AGUA OXIGENADA",   "120ML",             "51201900", True,  3.50),
    ("900002", "ALCOHOL 70°",      "500ML",             "51201900", True,  6.00),
]

for cod, desc, pres, uns, exon, precio in productos:
    tabla_prod.append({
        "CODIGO_PRO": cod,
        "DESCRIPCIO": desc,
        "PRESENTA_P": pres,
        "CODIGO_UNS": uns,
        "EXONERADO_": exon,
        "PRECIO_UNI": precio,
    })

tabla_prod.close()
print(f"  ✓ {len(productos)} productos")


# ── 2. enviosffee.dbf ────────────────────────────────────────
print("Creando enviosffee.dbf...")

tabla_env = dbf.Table(
    str(SAMPLES / "enviosffee.dbf"),
    "TIPO_FACTU C(1); SERIE_FACT C(3); NUMERO_FAC C(10); "
    "FECHA_DOCU D; FLAG_ENVIO N(1,0); "
    "FILE_ENVIO C(50)",
    codepage="cp1252",
)
tabla_env.open(dbf.READ_WRITE)

hoy = date.today()

comprobantes = [
    # Boletas pendientes (FLAG_ENVIO=2)
    ("B", "001", "0000000101", hoy, 2, "10412530590-02-B001-00000101.txt"),
    ("B", "001", "0000000102", hoy, 2, "10412530590-02-B001-00000102.txt"),
    ("B", "001", "0000000103", hoy, 2, "10412530590-02-B001-00000103.txt"),
    # Factura pendiente
    ("F", "001", "0000000011", hoy, 2, "10412530590-02-F001-00000011.txt"),
    # Ya enviados (FLAG_ENVIO=3)
    ("B", "001", "0000000100", hoy, 3, "10412530590-02-B001-00000100.txt"),
]

for tipo, serie, numero, fecha, flag, archivo in comprobantes:
    tabla_env.append({
        "TIPO_FACTU": tipo,
        "SERIE_FACT": serie,
        "NUMERO_FAC": numero,
        "FECHA_DOCU": fecha,
        "FLAG_ENVIO": flag,
        "FILE_ENVIO": archivo,
    })

tabla_env.close()
print(f"  ✓ {len(comprobantes)} comprobantes (3 boletas + 1 factura pendientes, 1 enviado)")


# ── 3. detalleventa.dbf ──────────────────────────────────────
print("Creando detalleventa.dbf...")

tabla_det = dbf.Table(
    str(SAMPLES / "detalleventa.dbf"),
    "TIPO_FACTU C(1); SERIE_FACT C(3); NUMERO_FAC C(10); "
    "CODIGO_PRO C(20); CODIGO_UNS C(10); "
    "CANTIDAD_P N(8,2); TABLETA_PE N(8,2); "
    "PRECIO_UNI N(10,2); PRECIO_FRA N(10,2); "
    "MONTO_PEDI N(10,5); IGV_PEDIDO N(10,5); REAL_PEDID N(10,2); "
    "PRODUCTO_E N(1,0); ICBPER N(1,0); FLAG_SERVI N(1,0); "
    "FLAG_ANULA N(1,0); FORMA_FACT C(1)",
    codepage="cp1252",
)
tabla_det.open(dbf.READ_WRITE)

items = [
    # B001-0000000101: 2 items gravados
    ("B","001","0000000101","786341","51191905", 0, 10, 1.10, 1.10, 9.322, 1.678, 11.00, 0,0,0,0,"1"),
    ("B","001","0000000101","787266","51191905", 0, 10, 1.30, 1.30,11.017, 1.983, 13.00, 0,0,0,0,"1"),
    # B001-0000000102: 1 item gravado + 1 exonerado
    ("B","001","0000000102","788100","51191905", 1,  0,15.00,15.00,12.712, 2.288, 15.00, 0,0,0,0,"1"),
    ("B","001","0000000102","900001","51201900", 1,  0, 3.50, 3.50, 3.500, 0.000,  3.50, 1,0,0,0,"1"),
    # B001-0000000103: 1 item exonerado
    ("B","001","0000000103","900002","51201900", 1,  0, 6.00, 6.00, 6.000, 0.000,  6.00, 1,0,0,0,"2"),
    # F001-0000000011: factura con 1 item
    ("F","001","0000000011","788100","51191905", 2,  0,15.00,15.00,25.424, 4.576, 30.00, 0,0,0,0,"1"),
]

for row in items:
    tabla_det.append({
        "TIPO_FACTU": row[0],
        "SERIE_FACT": row[1],
        "NUMERO_FAC": row[2],
        "CODIGO_PRO": row[3],
        "CODIGO_UNS": row[4],
        "CANTIDAD_P": row[5],
        "TABLETA_PE": row[6],
        "PRECIO_UNI": row[7],
        "PRECIO_FRA": row[8],
        "MONTO_PEDI": row[9],
        "IGV_PEDIDO": row[10],
        "REAL_PEDID": row[11],
        "PRODUCTO_E": row[12],
        "ICBPER":     row[13],
        "FLAG_SERVI": row[14],
        "FLAG_ANULA": row[15],
        "FORMA_FACT": row[16],
    })

tabla_det.close()
print(f"  ✓ {len(items)} items de detalle")

print("\n✅ DBF de prueba generados en tests/samples/")
print(f"   {SAMPLES}/enviosffee.dbf")
print(f"   {SAMPLES}/detalleventa.dbf")
print(f"   {SAMPLES}/productox.dbf")