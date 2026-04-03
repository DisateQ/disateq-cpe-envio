"""
test_generator.py
=================
Tests del generador TXT y JSON con simulación de datos DBF.
Ejecutar con: python -m pytest tests/ -v
"""

import pytest
import sys
import os
from decimal import Decimal
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from normalizer import normalizar, _afectacion_igv, _forma_pago
from txt_generator import generar_txt
from json_generator import generar_json, payload_a_str


def make_envio(tipo="B", serie="001", numero="0000063532", fecha=None) -> dict:
    return {
        "TIPO_FACTU":  tipo,
        "SERIE_FACT":  serie,
        "NUMERO_FAC":  numero,
        "FECHA_DOCU":  fecha or date(2026, 3, 27),
        "FLAG_ENVIO":  2,
        "FILE_ENVIO":  f"10412530590-02-B{serie}-{numero}.txt",
    }

def make_item(codigo="786341", descripcio="PRODUCTO TEST X 10 UND",
              unspsc="51191905", cantidad=2, tableta=0,
              precio_uni=10.0, precio_fra=0.0,
              monto=16.949, igv=3.051, real=20.0,
              producto_e=0, icbper=0, flag_servi=0,
              forma_fact="1") -> dict:
    return {
        "CODIGO_PRO":  codigo,
        "CODIGO_UNS":  unspsc,
        "CANTIDAD_P":  cantidad,
        "TABLETA_PE":  tableta,
        "PRECIO_UNI":  precio_uni,
        "PRECIO_FRA":  precio_fra,
        "MONTO_PEDI":  monto,
        "IGV_PEDIDO":  igv,
        "REAL_PEDID":  real,
        "PRODUCTO_E":  producto_e,
        "ICBPER":      icbper,
        "FLAG_SERVI":  flag_servi,
        "FLAG_ANULA":  0,
        "FORMA_FACT":  forma_fact,
        "_DESCRIPCIO": descripcio,
        "_CODIGO_UNS": unspsc,
        "_EXONERADO":  bool(producto_e),
        "_ICBPER":     bool(icbper),
        "_SERVICIO":   bool(flag_servi),
    }

RUC   = "10412530590"
RAZON = "FARMACIA DEL PUEBLO S.A.C."


class TestAfectacionIGV:
    def test_gravado(self):
        item = make_item(producto_e=0, icbper=0)
        assert _afectacion_igv(item) == "10"

    def test_exonerado(self):
        item = make_item(producto_e=1)
        item["_EXONERADO"] = True
        assert _afectacion_igv(item) == "20"

    def test_icbper(self):
        item = make_item(icbper=1)
        item["_ICBPER"] = True
        assert _afectacion_igv(item) == "20"


class TestFormaPago:
    def test_contado(self):
        assert _forma_pago("1") == "Contado"

    def test_credito(self):
        assert _forma_pago("2") == "Credito"

    def test_vacio_es_contado(self):
        assert _forma_pago("") == "Contado"


class TestNormalizer:
    def test_boleta_simple(self):
        envio = make_envio()
        items = [make_item()]
        comp = normalizar(envio, items)
        assert comp["serie"] == "B001"
        assert comp["numero"] == 63532
        assert comp["tipo_doc"] == "03"
        assert comp["forma_pago"] == "Contado"
        assert len(comp["items"]) == 1
        assert comp["items"][0]["afectacion_igv"] == "10"

    def test_totales_gravada(self):
        envio = make_envio()
        items = [make_item(monto=16.949, igv=3.051, real=20.0)]
        comp = normalizar(envio, items)
        assert comp["totales"]["total"] == Decimal("20.0")
        assert comp["totales"]["exonerada"] == Decimal("0")

    def test_item_exonerado(self):
        envio = make_envio()
        items = [make_item(producto_e=1, monto=20.0, igv=0.0, real=20.0)]
        items[0]["_EXONERADO"] = True
        comp = normalizar(envio, items)
        assert comp["items"][0]["afectacion_igv"] == "20"
        assert comp["totales"]["exonerada"] == Decimal("20.0")
        assert comp["totales"]["gravada"] == Decimal("0")

    def test_cantidad_usa_tabletas_si_cantidad_cero(self):
        envio = make_envio()
        items = [make_item(cantidad=0, tableta=10, precio_fra=1.1, real=11.0, monto=9.322, igv=1.678)]
        comp = normalizar(envio, items)
        assert comp["items"][0]["cantidad"] == 10

    def test_multiple_items(self):
        envio = make_envio()
        items = [
            make_item(real=20.0, monto=16.949, igv=3.051),
            make_item(real=5.0,  monto=4.237,  igv=0.763),
        ]
        comp = normalizar(envio, items)
        assert len(comp["items"]) == 2
        assert comp["totales"]["total"] == Decimal("25.0")


class TestTxtGenerator:
    def _comp(self, **kwargs):
        envio = make_envio(**kwargs)
        items = [make_item()]
        return normalizar(envio, items)

    def test_genera_nombre_correcto(self):
        comp = self._comp()
        nombre, _ = generar_txt(comp, RUC, RAZON)
        assert nombre == f"{RUC}-02-B001-00063532.txt"

    def test_contiene_campos_obligatorios(self):
        comp = self._comp()
        _, contenido = generar_txt(comp, RUC, RAZON)
        campos = [
            "operacion|generar_comprobante|",
            "tipo_de_comprobante|2|",
            "serie|B001|",
            "numero|63532|",
            "fecha_de_emision|27-03-2026|",
            "total_gravada|",
            "total_igv|",
            "total|",
            "item|NIU|",
        ]
        for campo in campos:
            assert campo in contenido, f"Campo faltante: {campo}"

    def test_forma_pago_contado(self):
        comp = self._comp()
        _, contenido = generar_txt(comp, RUC, RAZON)
        assert "condiciones_de_pago|Contado|" in contenido

    def test_item_con_afectacion_exonerada(self):
        envio = make_envio()
        items = [make_item(producto_e=1, monto=20.0, igv=0.0, real=20.0)]
        items[0]["_EXONERADO"] = True
        comp = normalizar(envio, items)
        _, contenido = generar_txt(comp, RUC, RAZON)
        assert "|20|" in contenido

    def test_cliente_varios(self):
        comp = self._comp()
        _, contenido = generar_txt(comp, RUC, RAZON)
        assert "cliente_tipo_de_documento|-|" in contenido
        assert "cliente_numero_de_documento|00000000|" in contenido
        assert "cliente_denominacion|CLIENTE VARIOS|" in contenido

    def test_totales_consistentes(self):
        comp = self._comp()
        _, contenido = generar_txt(comp, RUC, RAZON)
        lineas = {l.split("|")[0]: l.split("|")[1]
                  for l in contenido.split("\n") if "|" in l and l.count("|") >= 2}
        gravada = Decimal(lineas.get("total_gravada","0"))
        igv     = Decimal(lineas.get("total_igv","0"))
        total   = Decimal(lineas.get("total","0"))
        assert abs((gravada + igv) - total) < Decimal("0.01")


class TestJsonGenerator:
    def _comp(self):
        envio = make_envio()
        items = [make_item()]
        return normalizar(envio, items)

    def test_genera_nombre_json(self):
        comp = self._comp()
        nombre, _ = generar_json(comp, RUC, RAZON)
        assert nombre.endswith(".json")
        assert RUC in nombre

    def test_estructura_correcta(self):
        comp = self._comp()
        _, payload = generar_json(comp, RUC, RAZON)
        assert "emisor" in payload
        assert "comprobante" in payload
        assert "cliente" in payload
        assert "totales" in payload
        assert "items" in payload

    def test_emisor_correcto(self):
        comp = self._comp()
        _, payload = generar_json(comp, RUC, RAZON)
        assert payload["emisor"]["ruc"] == RUC
        assert payload["emisor"]["razon_social"] == RAZON

    def test_item_tiene_afectacion(self):
        comp = self._comp()
        _, payload = generar_json(comp, RUC, RAZON)
        assert "afectacion_igv" in payload["items"][0]
        assert payload["items"][0]["afectacion_igv"] == "10"

    def test_serializable_json(self):
        import json
        comp = self._comp()
        _, payload = generar_json(comp, RUC, RAZON)
        json_str = payload_a_str(payload)
        parsed = json.loads(json_str)
        assert parsed["comprobante"]["serie"] == "B001"

    def test_totales_float(self):
        comp = self._comp()
        _, payload = generar_json(comp, RUC, RAZON)
        assert isinstance(payload["totales"]["total"], float)
        assert isinstance(payload["totales"]["igv"], float)


class TestSimulacionCompleta:
    def test_flujo_boleta_simple(self):
        envio = make_envio(tipo="B", serie="002", numero="0000063532")
        items = [
            make_item(codigo="786341", real=11.0, monto=9.322, igv=1.678, cantidad=0, tableta=10, precio_fra=1.1),
            make_item(codigo="787266", real=13.0, monto=11.017, igv=1.983, cantidad=0, tableta=10, precio_fra=1.3),
        ]
        comp = normalizar(envio, items)
        assert comp["totales"]["total"] == Decimal("24.0")
        assert len(comp["items"]) == 2
        nombre_txt, contenido = generar_txt(comp, RUC, RAZON)
        assert f"{RUC}-02-B002-00063532.txt" == nombre_txt
        assert "item|NIU|786341|" in contenido
        assert "item|NIU|787266|" in contenido
        nombre_json, payload = generar_json(comp, RUC, RAZON)
        assert len(payload["items"]) == 2
        assert payload["totales"]["total"] == pytest.approx(24.0, abs=0.01)

    def test_flujo_boleta_mixta_gravada_exonerada(self):
        envio = make_envio()
        items = [
            make_item(codigo="001", real=20.0, monto=16.949, igv=3.051, producto_e=0),
            make_item(codigo="002", real=10.0, monto=10.0, igv=0.0, producto_e=1),
        ]
        items[1]["_EXONERADO"] = True
        comp = normalizar(envio, items)
        assert comp["totales"]["gravada"]   == Decimal("16.949")
        assert comp["totales"]["exonerada"] == Decimal("10.0")
        assert comp["totales"]["total"]     == Decimal("30.0")
        assert comp["items"][0]["afectacion_igv"] == "10"
        assert comp["items"][1]["afectacion_igv"] == "20"
        _, contenido = generar_txt(comp, RUC, RAZON)
        assert "total_exonerada|10.00000000|" in contenido

    def test_flujo_factura_simple(self):
        envio = make_envio(tipo="F", serie="001", numero="0000001234")
        items = [make_item(real=118.0, monto=100.0, igv=18.0, cantidad=1)]
        comp = normalizar(envio, items)
        assert comp["tipo_doc"] == "01"
        nombre, contenido = generar_txt(comp, RUC, RAZON)
        assert "F001" in nombre
        assert "tipo_de_comprobante|1|" in contenido


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
