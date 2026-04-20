"""
test_nivel1_lectura.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from adapters.xlsx_adapter import XlsxAdapter

def test_lectura():
    print("="*60)
    print("NIVEL 1: PRUEBA DE LECTURA")
    print("="*60)
    
    archivo = r'D:\FFEESUNAT\test\ventas_test.xlsx'
    
    print(f"\n[1/5] Abriendo archivo...")
    print(f"        {archivo}")
    adapter = XlsxAdapter(archivo)
    adapter.connect()
    print("        ✓ Archivo abierto")
    
    print(f"\n[2/5] Leyendo comprobantes...")
    pendientes = adapter.read_pending()
    print(f"        ✓ {len(pendientes)} encontrado(s)")
    
    if len(pendientes) == 0:
        print("\n        ❌ ERROR: No se encontraron comprobantes")
        return False
    
    print(f"\n[3/5] Verificando estructura...")
    comp = pendientes[0]
    print(f"        tipo_doc: {comp.get('tipo_doc')} (tipo: {type(comp.get('tipo_doc')).__name__})")
    print(f"        serie: {comp.get('serie')} (tipo: {type(comp.get('serie')).__name__})")
    print(f"        numero: {comp.get('numero')} (tipo: {type(comp.get('numero')).__name__})")
    
    assert str(comp['tipo_doc']) == '03', f"tipo_doc incorrecto: {comp.get('tipo_doc')}"
    assert str(comp['serie']) == 'B001', f"serie incorrecta: {comp.get('serie')}"
    assert int(comp['numero']) == 1, f"numero incorrecto: {comp.get('numero')}"
    print("        ✓ Estructura correcta")
    
    print(f"\n[4/5] Leyendo ítems...")
    items = adapter.read_items(comp)
    print(f"        ✓ {len(items)} ítem(s)")
    
    if len(items) == 0:
        print("\n        ❌ ERROR: No se encontraron ítems")
        return False
    
    print(f"\n[5/5] Verificando ítem...")
    item = items[0]
    print(f"        código: {item.get('item_codigo')}")
    print(f"        cantidad: {item.get('item_cantidad')}")
    
    assert str(item['item_codigo']) == 'PROD001', f"código incorrecto"
    assert float(item['item_cantidad']) == 2.0, f"cantidad incorrecta"
    print("        ✓ Ítem correcto")
    
    print("\n" + "="*60)
    print("✅ NIVEL 1: LECTURA OK")
    print("="*60)
    print("\nDatos leídos correctamente:")
    print(f"  Comprobante: {comp['serie']}-{comp['numero']}")
    print(f"  Cliente: {comp.get('cliente_denominacion', 'N/A')}")
    print(f"  Ítem: {item['item_codigo']} x {item['item_cantidad']}")
    return True

if __name__ == '__main__':
    try:
        exito = test_lectura()
        sys.exit(0 if exito else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
