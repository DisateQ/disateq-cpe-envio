import openpyxl
from datetime import date

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "_CPE"

# Headers — contrato v1.1
headers = [
    "cpe_tipo", "cpe_serie", "cpe_numero", "cpe_fecha",
    "cli_tipo_doc", "cli_num_doc", "cli_nombre", "cli_direccion",
    "venta_subtotal", "venta_igv", "venta_total",
    "pago_forma", "estado",
    "item_orden", "item_codigo", "item_descripcion",
    "item_unidad", "item_unspsc", "item_cantidad",
    "item_precio_unit", "item_valor_unitario", "item_descuento",
    "item_subtotal_sin_igv", "item_igv", "item_total",
    "item_afectacion_igv",
]
ws.append(headers)

# Comprobante 1 — Boleta B001-00000100, 2 items gravados
# Item 1
ws.append([
    "03", "B001", "00000100", "2026-04-18",
    "-", "00000000", "CLIENTES VARIOS", "-",
    16.949, 3.051, 20.00,
    "EFECTIVO", "BORRADOR",
    1, "P001", "PARACETAMOL 500MG X 10",
    "NIU", "10000000", 2,
    10.00, 8.4746, 0.00,
    16.949, 3.051, 20.00,
    "10",
])

# Comprobante 2 — Boleta B001-00000101, 1 item exonerado
ws.append([
    "03", "B001", "00000101", "2026-04-18",
    "-", "00000000", "CLIENTES VARIOS", "-",
    6.00, 0.00, 6.00,
    "YAPE", "BORRADOR",
    1, "P002", "AGUA OXIGENADA 120ML",
    "NIU", "10000000", 1,
    6.00, 6.00, 0.00,
    6.00, 0.00, 6.00,
    "20",
])

# Comprobante 3 — Factura F001-00000011, 1 item gravado
ws.append([
    "01", "F001", "00000011", "2026-04-18",
    "6", "20100070970", "EMPRESA EJEMPLO S.A.C.", "AV. LIMA 123",
    100.00, 18.00, 118.00,
    "TRANSFERENCIA", "BORRADOR",
    1, "P003", "AMOXICILINA 500MG X 21",
    "NIU", "10000000", 2,
    59.00, 50.00, 0.00,
    100.00, 18.00, 118.00,
    "10",
])

wb.save("test_cpe.xlsx")
print("test_cpe.xlsx creado con contrato v1.1 — 3 comprobantes")