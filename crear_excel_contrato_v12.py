"""
crear_excel_contrato_v12.py
============================
Crea Excel de prueba según CONTRATO DisateQ POS™ v1.2
29 campos exactos del contrato
"""

from openpyxl import Workbook
from datetime import datetime

# Crear workbook
wb = Workbook()
ws = wb.active
ws.title = "_CPE"

# ========================================
# HEADERS - CONTRATO v1.2 (29 CAMPOS)
# ========================================

headers = [
    # Cabecera (1-5)
    "cpe_tipo",
    "cpe_serie",
    "cpe_numero",
    "cpe_fecha",
    "cpe_moneda",
    
    # Cliente (6-9)
    "cli_tipo_doc",
    "cli_nro_doc",
    "cli_nombre",
    "cli_direccion",
    
    # Ítem (10-20)
    "item_codigo",
    "item_descripcion",
    "item_cantidad",
    "item_unidad",
    "item_precio_unitario",
    "item_valor_unitario",
    "item_subtotal_sin_igv",
    "item_igv",
    "item_total",
    "item_afectacion_igv",
    "item_unspsc",
    
    # Totales (21-26)
    "venta_subtotal",
    "venta_exonerada",
    "venta_inafecta",     # ⭐ Nuevo v1.2
    "venta_icbper",       # ⭐ Nuevo v1.2
    "venta_igv",
    "venta_total",
    
    # Pago (27-28)
    "pago_forma",
    "pago_monto",
    
    # Estado (29)
    "estado"
]

ws.append(headers)

# ========================================
# DATOS - Boleta de prueba S/ 0.10
# ========================================

hoy = datetime.now().strftime("%Y-%m-%d")

# Cálculos:
# Precio con IGV: 0.10
# Precio sin IGV: 0.10 / 1.18 = 0.085 (redondeado a 0.08)
# IGV: 0.10 - 0.08 = 0.02

datos = [
    # Cabecera
    "03",                 # Boleta
    "B001",
    1,
    hoy,
    "PEN",
    
    # Cliente
    "1",                  # DNI
    "00000000",
    "CLIENTE VARIOS",
    "-",
    
    # Ítem
    "PROD001",
    "PRODUCTO VARIOS",
    1.0,                  # cantidad
    "NIU",
    0.10,                 # precio_unitario (con IGV)
    0.08,                 # valor_unitario (sin IGV)
    0.08,                 # subtotal_sin_igv
    0.02,                 # igv
    0.10,                 # total
    "10",                 # afectacion_igv (10=gravado)
    "10000000",           # unspsc
    
    # Totales
    0.08,                 # venta_subtotal (gravada)
    0.00,                 # venta_exonerada
    0.00,                 # venta_inafecta ⭐
    0.00,                 # venta_icbper ⭐
    0.02,                 # venta_igv
    0.10,                 # venta_total
    
    # Pago
    "Contado",
    0.10,
    
    # Estado
    "BORRADOR"
]

ws.append(datos)

# Guardar
output_file = "ventas.xlsx"
wb.save(output_file)

print(f"\n✅ Excel creado: {output_file}")
print(f"\n📋 CONTRATO DisateQ POS™ v1.2")
print(f"   ✅ 29 campos correctos")
print(f"\n📄 Comprobante generado:")
print(f"   Tipo: BOLETA")
print(f"   Serie-Número: B001-00000001")
print(f"   Fecha: {hoy}")
print(f"   Cliente: CLIENTE VARIOS (DNI 00000000)")
print(f"   Producto: PRODUCTO VARIOS x1")
print(f"   Total: S/ 0.10")
print(f"   Gravada: S/ 0.08 + IGV: S/ 0.02")
print(f"   Inafecta: S/ 0.00 (nuevo v1.2)")
print(f"   ICBPER: S/ 0.00 (nuevo v1.2)")
print(f"   Estado: BORRADOR\n")
