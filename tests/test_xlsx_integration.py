"""
test_xlsx_integration.py
========================
Prueba de integración: xlsx_adapter → normalizar_desde_cpe → generadores
"""

import sys
import os
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from adapters.xlsx_adapter import leer as xlsx_leer
from normalizer import normalizar_desde_cpe
from txt_generator import generar_txt
from json_generator import generar_json


def test_flujo_xlsx_completo():
    """Prueba el flujo: xlsx → normalizar_desde_cpe → txt/json"""
    
    # Leer desde xlsx
    ruta_xlsx = Path(__file__).parent.parent / "test_cpe.xlsx"
    cabecera, items = xlsx_leer(str(ruta_xlsx))
    
    print(f"✓ xlsx_adapter: {len(items)} item(s) leído(s)")
    
    # Normalizar
    comp = normalizar_desde_cpe(cabecera, items)
    
    print(f"✓ normalizar_desde_cpe: {comp['serie']}-{str(comp['numero']).zfill(8)}")
    assert comp['totales']['total'] == Decimal('20.0')
    assert comp['totales']['gravada'] == Decimal('16.95')
    
    # Generar TXT
    nombre_txt, contenido_txt = generar_txt(comp, "10412530590", "TEST S.A.C.")
    
    print(f"✓ txt_generator: {nombre_txt}")
    assert "operacion|generar_comprobante|" in contenido_txt
    assert "total|20.00000000|" in contenido_txt
    
    # Generar JSON
    nombre_json, payload_json = generar_json(comp, "10412530590", "TEST S.A.C.")
    
    print(f"✓ json_generator: {nombre_json}")
    assert payload_json["totales"]["total"] == 20.0
    assert payload_json["items"][0]["afectacion_igv"] == "10"
    
    print("\n✅ Flujo completo OK")


if __name__ == "__main__":
    test_flujo_xlsx_completo()