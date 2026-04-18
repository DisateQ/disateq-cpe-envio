import openpyxl

wb = openpyxl.Workbook()
ws = wb.active
ws.title = '_CPE'

headers = ['tipo_doc', 'serie', 'numero', 'fecha_emision', 'moneda', 'forma_pago',
           'cliente_tipo_doc', 'cliente_numero_doc', 'cliente_denominacion', 'cliente_direccion',
           'total_gravada', 'total_exonerada', 'total_inafecta', 'total_igv', 'total_icbper', 'total',
           'item_codigo', 'item_descripcion', 'item_unspsc', 'item_unidad', 'item_cantidad',
           'item_precio_con_igv', 'item_precio_sin_igv', 'item_subtotal_sin_igv', 'item_igv', 'item_total', 'item_afectacion_igv']
ws.append(headers)

# Fila 2: datos del comprobante
ws.append(['03', 'B001', 100, '18-04-2026', 'PEN', 'Contado',
           '-', '00000000', 'CLIENTE VARIOS', '-',
           16.95, 0.0, 0.0, 3.05, 0.0, 20.0,
           None, None, None, None, None, None, None, None, None, None, None])

# Fila 3: item 1
ws.append([None, None, None, None, None, None,
           None, None, None, None,
           None, None, None, None, None, None,
           '001', 'PRODUCTO TEST', '10000000', 'NIU', 1,
           20.0, 16.95, 16.95, 3.05, 20.0, '10'])

wb.save('test_cpe.xlsx')
print('test_cpe.xlsx creado (3 filas)')
