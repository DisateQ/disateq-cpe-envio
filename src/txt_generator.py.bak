"""
txt_generator.py
================
Genera archivos TXT en el formato APIFAS.

Principios SOLID:
  S — Una sola responsabilidad: generar y guardar TXT. Nada mas.
  O — La logica de cabecera e items esta separada para extensibilidad.

Excepciones que puede lanzar:
  GeneracionError — si falla la generacion del contenido o el guardado.
"""

from pathlib import Path
from exceptions import GeneracionError


def _cabecera(c: dict, t: dict, cl: dict) -> list:
    """Genera las lineas de cabecera del TXT."""
    return [
        "operacion|generar_comprobante|",
        f"tipo_de_comprobante|{2 if c['tipo_doc'] == '03' else 1}|",
        f"serie|{c['serie']}|",
        f"numero|{c['numero']}|",
        "sunat_transaction|1|",
        f"cliente_tipo_de_documento|{cl['tipo_doc']}|",
        f"cliente_numero_de_documento|{cl['numero_doc']}|",
        f"cliente_denominacion|{cl['denominacion']}|",
        f"cliente_direccion|{cl['direccion']}|",
        "cliente_email||",
        "cliente_email_1||",
        "cliente_email_2||",
        f"fecha_de_emision|{c['fecha_str']}|",
        "fecha_de_vencimiento||",
        "moneda|1|",
        "tipo_de_cambio||",
        "porcentaje_de_igv|18.00|",
        "descuento_global||",
        "total_descuento||",
        "total_anticipo||",
        f"total_gravada|{t['gravada']:.8f}|",
        "total_inafecta||",
        f"total_exonerada|{t['exonerada']:.8f}|",
        f"total_igv|{t['igv']:.8f}|",
        f"total_impuestos_bolsas|{t['icbper']:.8f}|",
        "total_gratuita|0.00000000|",
        "total_otros_cargos||",
        f"total|{t['total']:.8f}|",
        "percepcion_tipo||",
        "percepcion_base_imponible||",
        "total_percepcion||",
        "total_incluido_percepcion||",
        "detraccion|false|",
        "observaciones||",
        "documento_que_se_modifica_tipo||",
        "documento_que_se_modifica_serie||",
        "documento_que_se_modifica_numero||",
        "tipo_de_nota_de_credito||",
        "tipo_de_nota_de_debito||",
        "enviar_automaticamente_a_la_sunat|false|",
        "enviar_automaticamente_al_cliente|false|",
        f"condiciones_de_pago|{c['forma_pago']}|",
        "medio_de_pago||",
        "placa_vehiculo||",
        "orden_compra_servicio||",
        "detraccion_tipo||",
        "detraccion_total||",
        "ubigeo_origen||",
        "direccion_origen||",
        "ubigeo_destino||",
        "direccion_destino||",
        "detalle_viaje||",
        "val_ref_serv_trans||",
        "val_ref_carga_efec||",
        "val_ref_carga_util||",
        "formato_de_pdf||",
        "generado_por_contingencia||",
    ]


def _linea_item(item: dict) -> str:
    """Genera la linea de un item del comprobante."""
    return (
        f"item|{item['unidad']}|{item['codigo']}|{item['descripcion']}|"
        f"{item['cantidad']}|{item['precio_sin_igv']:.8f}|"
        f"{item['precio_con_igv']:.8f}||{item['subtotal_sin_igv']:.8f}|"
        f"{item['afectacion_igv']}|{item['igv']:.8f}|{item['total']:.8f}|false||"
        f"{item['unspsc']}|||||"
    )


def generar_txt(comprobante: dict, ruc: str, razon_social: str) -> tuple[str, str]:
    """
    Genera el contenido TXT del comprobante.
    Retorna (nombre_archivo, contenido).
    Lanza GeneracionError si algo falla.
    """
    nombre = f"{ruc}-02-{comprobante['serie']}-{str(comprobante['numero']).zfill(8)}.txt"
    try:
        lineas  = _cabecera(comprobante, comprobante["totales"], comprobante["cliente"])
        lineas += [_linea_item(item) for item in comprobante["items"]]
        return nombre, "\n".join(lineas)
    except Exception as e:
        raise GeneracionError(nombre, e) from e


def guardar_txt(nombre: str, contenido: str, carpeta_salida: str) -> Path:
    """
    Guarda el TXT en disco.
    Lanza GeneracionError si no se puede escribir.
    """
    try:
        ruta = Path(carpeta_salida) / nombre
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(contenido, encoding="latin-1")
        return ruta
    except Exception as e:
        raise GeneracionError(nombre, e) from e
