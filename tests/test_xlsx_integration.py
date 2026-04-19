"""
test_xlsx_integration.py
========================
Prueba de integracion: XlsxAdapter (contrato v1.1) → normalizar_desde_cpe → generadores
"""

import sys
import os
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from adapters.xlsx_adapter import XlsxAdapter
from normalizer import normalizar_desde_cpe
from txt_generator import generar_txt
from json_generator import generar_json

RUC   = "10412530590"
RAZON = "FARMACIA DEL PUEBLO S.A.C."


def test_flujo_boleta_gravada():
    """Boleta B001-00000100 — 1 item gravado."""
    ruta = str(Path(__file__).parent.parent / "test_cpe.xlsx")
    resultado = XlsxAdapter().leer(ruta)

    # Debe haber 3 comprobantes
    assert len(resultado) == 3

    cab, items = resultado[0]
    assert cab["tipo_doc"]  == "03"
    assert cab["serie"]     == "B001"
    assert cab["numero"]    == 100
    assert cab["forma_pago"] == "Contado"
    assert len(items) == 1
    assert items[0]["afectacion_igv"] == "10"

    comp = normalizar_desde_cpe(cab, items)
    assert float(comp["totales"]["total"]) == 20.0

    nombre_txt, contenido = generar_txt(comp, RUC, RAZON)
    assert "B001" in nombre_txt
    assert "operacion|generar_comprobante|" in contenido

    nombre_json, payload = generar_json(comp, RUC, RAZON)
    assert payload["totales"]["total"] == 20.0
    assert payload["items"][0]["afectacion_igv"] == "10"

    print(f"  ✓ Boleta gravada: {nombre_txt}  S/ {payload['totales']['total']:.2f}")


def test_flujo_boleta_exonerada():
    """Boleta B001-00000101 — 1 item exonerado."""
    ruta = str(Path(__file__).parent.parent / "test_cpe.xlsx")
    resultado = XlsxAdapter().leer(ruta)

    cab, items = resultado[1]
    assert cab["tipo_doc"] == "03"
    assert cab["serie"]    == "B001"
    assert cab["numero"]   == 101
    assert items[0]["afectacion_igv"] == "20"

    comp = normalizar_desde_cpe(cab, items)
    assert float(comp["totales"]["total"])     == 6.0
    assert float(comp["totales"]["exonerada"]) == 6.0
    assert float(comp["totales"]["igv"])       == 0.0

    nombre_txt, contenido = generar_txt(comp, RUC, RAZON)
    assert "|20|" in contenido

    print(f"  ✓ Boleta exonerada: {nombre_txt}  S/ {float(comp['totales']['total']):.2f}")


def test_flujo_factura_gravada():
    """Factura F001-00000011 — cliente con RUC, direccion obligatoria."""
    ruta = str(Path(__file__).parent.parent / "test_cpe.xlsx")
    resultado = XlsxAdapter().leer(ruta)

    cab, items = resultado[2]
    assert cab["tipo_doc"]           == "01"
    assert cab["serie"]              == "F001"
    assert cab["numero"]             == 11
    assert cab["cliente_tipo_doc"]   == "6"
    assert cab["cliente_numero_doc"] == "20100070970"
    assert cab["cliente_direccion"]  == "AV. LIMA 123"

    comp = normalizar_desde_cpe(cab, items)
    assert float(comp["totales"]["total"]) == 118.0

    nombre_txt, contenido = generar_txt(comp, RUC, RAZON)
    assert "F001" in nombre_txt
    assert "tipo_de_comprobante|1|" in contenido

    print(f"  ✓ Factura gravada: {nombre_txt}  S/ {float(comp['totales']['total']):.2f}")


def test_xlsx_completo():
    """Prueba el flujo completo con los 3 comprobantes."""
    test_flujo_boleta_gravada()
    test_flujo_boleta_exonerada()
    test_flujo_factura_gravada()
    print("\n  ✅ Flujo completo XlsxAdapter v1.1 OK")


if __name__ == "__main__":
    test_xlsx_completo()