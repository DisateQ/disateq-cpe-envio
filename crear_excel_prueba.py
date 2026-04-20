"""
crear_excel_prueba.py
=====================
Crea Excel de prueba con 1 comprobante mínimo para APIFAS

Comprobante:
- Boleta B001-00000001
- Cliente VARIOS
- Producto VARIOS x1 = S/ 0.10
"""

from openpyxl import Workbook
from datetime import datetime

# Crear workbook
wb = Workbook()
ws = wb.active
ws.title = "_CPE"

# Encabezados (formato DisateQ POS™ v1.2)
headers = [
    "TIPO_DOC",           # 03=Boleta
    "SERIE",              # B001
    "NUMERO",             # 1
    "FECHA_EMISION",      # 2026-04-20
    "CLIENTE_TIPO_DOC",   # 1=DNI
    "CLIENTE_NUM_DOC",    # 00000000
    "CLIENTE_NOMBRE",     # CLIENTE VARIOS
    "MONEDA",             # PEN
    "TOTAL_GRAVADA",      # 0.08
    "TOTAL_IGV",          # 0.02
    "TOTAL_VENTA",        # 0.10
    "PRODUCTO_CODIGO",    # PROD001
    "PRODUCTO_DESC",      # PRODUCTO VARIOS
    "PRODUCTO_UNIDAD",    # NIU
    "PRODUCTO_CANT",      # 1
    "PRODUCTO_PRECIO",    # 0.10
    "PRODUCTO_SUBTOTAL",  # 0.08
    "PRODUCTO_IGV",       # 0.02
    "PRODUCTO_TOTAL",     # 0.10
    "ENVIADO"             # 0=Pendiente
]

ws.append(headers)

# Datos del comprobante
hoy = datetime.now().strftime("%Y-%m-%d")

datos = [
    "03",                 # Boleta
    "B001",              
    1,                   
    hoy,                 
    "1",                 # DNI
    "00000000",          # Cliente varios
    "CLIENTE VARIOS",    
    "PEN",               
    0.08,                # Gravada (sin IGV)
    0.02,                # IGV 18%
    0.10,                # Total
    "PROD001",           
    "PRODUCTO VARIOS",   
    "NIU",               # Unidad
    1,                   
    0.10,                
    0.08,                
    0.02,                
    0.10,                
    0                    # Pendiente de envío
]

ws.append(datos)

# Guardar
output_file = "comprobante_prueba_apifas.xlsx"
wb.save(output_file)

print(f"\n✅ Excel creado: {output_file}")
print(f"\nComprobante generado:")
print(f"   Tipo: BOLETA")
print(f"   Serie-Número: B001-00000001")
print(f"   Fecha: {hoy}")
print(f"   Cliente: CLIENTE VARIOS (DNI 00000000)")
print(f"   Producto: PRODUCTO VARIOS x1")
print(f"   Total: S/ 0.10 (Gravada: S/ 0.08 + IGV: S/ 0.02)")
print(f"   Estado: Pendiente de envío\n")
