"""
validator_pre_envio.py
======================
Validador de archivos TXT antes de envío a APIFAS — Motor CPE v3.0

Valida que el TXT generado cumpla el formato esperado por APIFAS.
Detecta errores ANTES de enviar, ahorrando tiempo de debugging.

Uso:
    python validator_pre_envio.py archivo.txt
    python validator_pre_envio.py D:\FFEESUNAT\test\B001-1.txt

Autor: Fernando Miguel Tejada Quevedo (@fhertejadaDEV)
Empresa: DisateQ™
Fecha: Abril 2026
"""

import sys
import re
from pathlib import Path
from typing import Tuple, List, Dict


class ValidadorTxtApifas:
    """
    Valida formato TXT para APIFAS.
    
    Formato esperado (5 líneas pipe-separated):
    1. Cabecera comprobante
    2. Cliente
    3. Ítems (pueden ser múltiples, concatenados)
    4. Totales
    5. Pago
    """
    
    # Campos obligatorios por línea
    CAMPOS_OBLIGATORIOS = {
        1: ['TIPO', 'SERIE', 'NUMERO', 'FECHA', 'MONEDA'],
        2: ['CLI_TIPO', 'CLI_NUM', 'CLI_NOMBRE', 'CLI_DIR'],
        3: ['ITEM_COD', 'ITEM_DESC', 'ITEM_CANT', 'ITEM_UND', 'ITEM_PRECIO'],
        4: ['VENTA_GRAVADA', 'VENTA_EXONERADA', 'VENTA_INAFECTA', 
            'VENTA_ICBPER', 'VENTA_IGV', 'VENTA_TOTAL'],
        5: ['PAGO_FORMA', 'PAGO_MONTO']
    }
    
    # Tipos de documento válidos
    TIPOS_DOC_VALIDOS = ['01', '03', '07', '08']  # Factura, Boleta, NC, ND
    
    # Tipos de documento de identidad
    TIPOS_IDENTIDAD_VALIDOS = ['1', '6', '7', '0']  # DNI, RUC, Pasaporte, Otros
    
    def __init__(self, archivo_txt: str):
        """
        Inicializa validador.
        
        Args:
            archivo_txt: Ruta al archivo TXT a validar
        """
        self.archivo = Path(archivo_txt)
        self.errores: List[str] = []
        self.advertencias: List[str] = []
        self.contenido: str = ""
        self.lineas: List[str] = []
        
    def validar(self) -> Tuple[bool, List[str], List[str]]:
        """
        Ejecuta todas las validaciones.
        
        Returns:
            (es_valido, errores, advertencias)
        """
        self.errores = []
        self.advertencias = []
        
        # 1. Validar que el archivo existe
        if not self._validar_archivo_existe():
            return False, self.errores, self.advertencias
        
        # 2. Leer contenido
        if not self._leer_archivo():
            return False, self.errores, self.advertencias
        
        # 3. Validar estructura básica (5 líneas)
        if not self._validar_estructura_basica():
            return False, self.errores, self.advertencias
        
        # 4. Validar línea 1: Cabecera
        self._validar_linea_cabecera()
        
        # 5. Validar línea 2: Cliente
        self._validar_linea_cliente()
        
        # 6. Validar línea 3: Ítems
        self._validar_linea_items()
        
        # 7. Validar línea 4: Totales
        self._validar_linea_totales()
        
        # 8. Validar línea 5: Pago
        self._validar_linea_pago()
        
        # 9. Validaciones cruzadas
        self._validar_calculos()
        
        es_valido = len(self.errores) == 0
        return es_valido, self.errores, self.advertencias
    
    def _validar_archivo_existe(self) -> bool:
        """Verifica que el archivo existe."""
        if not self.archivo.exists():
            self.errores.append(f"❌ Archivo no encontrado: {self.archivo}")
            return False
        
        if not self.archivo.is_file():
            self.errores.append(f"❌ La ruta no es un archivo: {self.archivo}")
            return False
        
        return True
    
    def _leer_archivo(self) -> bool:
        """Lee el contenido del archivo."""
        try:
            self.contenido = self.archivo.read_text(encoding='utf-8')
            self.lineas = self.contenido.strip().split('\n')
            return True
        except Exception as e:
            self.errores.append(f"❌ Error al leer archivo: {e}")
            return False
    
    def _validar_estructura_basica(self) -> bool:
        """Valida que tenga exactamente 5 líneas no vacías."""
        if len(self.lineas) != 5:
            self.errores.append(
                f"❌ Estructura incorrecta: Se esperan 5 líneas, "
                f"se encontraron {len(self.lineas)}"
            )
            return False
        
        for i, linea in enumerate(self.lineas, 1):
            if not linea.strip():
                self.errores.append(f"❌ Línea {i} está vacía")
                return False
        
        return True
    
    def _parsear_linea(self, numero_linea: int) -> Dict[str, str]:
        """
        Parsea una línea en formato KEY|VALUE|KEY|VALUE...
        
        Args:
            numero_linea: Número de línea (1-5)
        
        Returns:
            Dict con pares clave-valor
        """
        linea = self.lineas[numero_linea - 1]
        partes = linea.split('|')
        
        if len(partes) % 2 != 0:
            self.errores.append(
                f"❌ Línea {numero_linea}: Número impar de elementos "
                f"(debe ser KEY|VALUE pares)"
            )
            return {}
        
        datos = {}
        for i in range(0, len(partes), 2):
            key = partes[i].strip()
            value = partes[i + 1].strip() if i + 1 < len(partes) else ""
            datos[key] = value
        
        return datos
    
    def _validar_campos_obligatorios(self, numero_linea: int, datos: Dict[str, str]):
        """Valida que existan todos los campos obligatorios."""
        campos_requeridos = self.CAMPOS_OBLIGATORIOS.get(numero_linea, [])
        
        for campo in campos_requeridos:
            if campo not in datos:
                self.errores.append(
                    f"❌ Línea {numero_linea}: Falta campo obligatorio '{campo}'"
                )
            elif not datos[campo]:
                self.errores.append(
                    f"❌ Línea {numero_linea}: Campo '{campo}' está vacío"
                )
    
    def _validar_linea_cabecera(self):
        """Valida línea 1: Cabecera del comprobante."""
        datos = self._parsear_linea(1)
        if not datos:
            return
        
        self._validar_campos_obligatorios(1, datos)
        
        # Validar tipo de documento
        if 'TIPO' in datos:
            tipo = datos['TIPO']
            if tipo not in self.TIPOS_DOC_VALIDOS:
                self.errores.append(
                    f"❌ Tipo de documento inválido: '{tipo}' "
                    f"(válidos: {', '.join(self.TIPOS_DOC_VALIDOS)})"
                )
        
        # Validar formato de serie
        if 'SERIE' in datos:
            serie = datos['SERIE']
            if not re.match(r'^[FB]\d{3}$', serie):
                self.advertencias.append(
                    f"⚠️  Serie '{serie}' no sigue formato estándar (F001, B001)"
                )
        
        # Validar formato de fecha
        if 'FECHA' in datos:
            fecha = datos['FECHA']
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', fecha):
                self.errores.append(
                    f"❌ Formato de fecha inválido: '{fecha}' "
                    f"(esperado: YYYY-MM-DD)"
                )
        
        # Validar moneda
        if 'MONEDA' in datos:
            moneda = datos['MONEDA']
            if moneda not in ['PEN', 'USD']:
                self.advertencias.append(
                    f"⚠️  Moneda '{moneda}' poco común (típico: PEN, USD)"
                )
    
    def _validar_linea_cliente(self):
        """Valida línea 2: Datos del cliente."""
        datos = self._parsear_linea(2)
        if not datos:
            return
        
        self._validar_campos_obligatorios(2, datos)
        
        # Validar tipo de documento de identidad
        if 'CLI_TIPO' in datos:
            tipo = datos['CLI_TIPO']
            if tipo not in self.TIPOS_IDENTIDAD_VALIDOS:
                self.errores.append(
                    f"❌ Tipo de documento cliente inválido: '{tipo}' "
                    f"(válidos: {', '.join(self.TIPOS_IDENTIDAD_VALIDOS)})"
                )
        
        # Validar RUC (si es tipo 6)
        if 'CLI_TIPO' in datos and datos['CLI_TIPO'] == '6':
            if 'CLI_NUM' in datos:
                ruc = datos['CLI_NUM']
                if not re.match(r'^\d{11}$', ruc):
                    self.errores.append(
                        f"❌ RUC inválido: '{ruc}' (debe tener 11 dígitos)"
                    )
        
        # Validar DNI (si es tipo 1)
        if 'CLI_TIPO' in datos and datos['CLI_TIPO'] == '1':
            if 'CLI_NUM' in datos:
                dni = datos['CLI_NUM']
                if not re.match(r'^\d{8}$', dni):
                    self.errores.append(
                        f"❌ DNI inválido: '{dni}' (debe tener 8 dígitos)"
                    )
    
    def _validar_linea_items(self):
        """Valida línea 3: Ítems del comprobante."""
        datos = self._parsear_linea(3)
        if not datos:
            return
        
        # Los ítems pueden repetirse (concatenados), validar que existan campos base
        campos_base = ['ITEM_COD', 'ITEM_DESC', 'ITEM_CANT', 'ITEM_UND']
        for campo in campos_base:
            if campo not in datos:
                self.errores.append(
                    f"❌ Línea 3: Falta campo obligatorio '{campo}'"
                )
        
        # Validar cantidad numérica
        if 'ITEM_CANT' in datos:
            try:
                cantidad = float(datos['ITEM_CANT'])
                if cantidad <= 0:
                    self.errores.append(
                        f"❌ Cantidad debe ser mayor a 0: {cantidad}"
                    )
            except ValueError:
                self.errores.append(
                    f"❌ Cantidad no numérica: '{datos['ITEM_CANT']}'"
                )
        
        # Validar precio numérico
        if 'ITEM_PRECIO' in datos:
            try:
                precio = float(datos['ITEM_PRECIO'])
                if precio < 0:
                    self.errores.append(
                        f"❌ Precio no puede ser negativo: {precio}"
                    )
            except ValueError:
                self.errores.append(
                    f"❌ Precio no numérico: '{datos['ITEM_PRECIO']}'"
                )
    
    def _validar_linea_totales(self):
        """Valida línea 4: Totales del comprobante."""
        datos = self._parsear_linea(4)
        if not datos:
            return
        
        self._validar_campos_obligatorios(4, datos)
        
        # Validar que todos los totales sean numéricos
        campos_numericos = [
            'VENTA_GRAVADA', 'VENTA_EXONERADA', 'VENTA_INAFECTA',
            'VENTA_ICBPER', 'VENTA_IGV', 'VENTA_TOTAL'
        ]
        
        for campo in campos_numericos:
            if campo in datos:
                try:
                    valor = float(datos[campo])
                    if valor < 0:
                        self.advertencias.append(
                            f"⚠️  {campo} es negativo: {valor}"
                        )
                except ValueError:
                    self.errores.append(
                        f"❌ {campo} no numérico: '{datos[campo]}'"
                    )
    
    def _validar_linea_pago(self):
        """Valida línea 5: Forma de pago."""
        datos = self._parsear_linea(5)
        if not datos:
            return
        
        self._validar_campos_obligatorios(5, datos)
        
        # Validar monto de pago numérico
        if 'PAGO_MONTO' in datos:
            try:
                monto = float(datos['PAGO_MONTO'])
                if monto <= 0:
                    self.errores.append(
                        f"❌ Monto de pago debe ser mayor a 0: {monto}"
                    )
            except ValueError:
                self.errores.append(
                    f"❌ Monto de pago no numérico: '{datos['PAGO_MONTO']}'"
                )
    
    def _validar_calculos(self):
        """Valida cálculos matemáticos (totales, IGV, etc.)."""
        try:
            # Parsear datos necesarios
            totales = self._parsear_linea(4)
            pago = self._parsear_linea(5)
            
            if not totales or not pago:
                return
            
            # Extraer valores numéricos
            gravada = float(totales.get('VENTA_GRAVADA', 0))
            exonerada = float(totales.get('VENTA_EXONERADA', 0))
            inafecta = float(totales.get('VENTA_INAFECTA', 0))
            icbper = float(totales.get('VENTA_ICBPER', 0))
            igv = float(totales.get('VENTA_IGV', 0))
            total = float(totales.get('VENTA_TOTAL', 0))
            pago_monto = float(pago.get('PAGO_MONTO', 0))
            
            # Validar: IGV = gravada * 0.18 (tolerancia 0.05)
            igv_calculado = round(gravada * 0.18, 2)
            if abs(igv - igv_calculado) > 0.05:
                self.advertencias.append(
                    f"⚠️  IGV inconsistente: esperado {igv_calculado}, "
                    f"encontrado {igv}"
                )
            
            # Validar: Total = gravada + exonerada + inafecta + igv + icbper
            total_calculado = round(gravada + exonerada + inafecta + igv + icbper, 2)
            if abs(total - total_calculado) > 0.05:
                self.errores.append(
                    f"❌ Total inconsistente: esperado {total_calculado}, "
                    f"encontrado {total}"
                )
            
            # Validar: Pago = Total
            if abs(pago_monto - total) > 0.01:
                self.advertencias.append(
                    f"⚠️  Monto de pago difiere del total: "
                    f"pago={pago_monto}, total={total}"
                )
            
        except (ValueError, KeyError) as e:
            self.advertencias.append(
                f"⚠️  No se pudo validar cálculos: {e}"
            )
    
    def generar_reporte(self) -> str:
        """
        Genera reporte textual de la validación.
        
        Returns:
            String con el reporte formateado
        """
        lineas = [
            "=" * 70,
            "VALIDACIÓN TXT APIFAS — Motor CPE v3.0",
            "=" * 70,
            f"Archivo: {self.archivo.name}",
            f"Ruta: {self.archivo.absolute()}",
            f"Tamaño: {self.archivo.stat().st_size} bytes",
            "",
        ]
        
        # Resumen
        es_valido = len(self.errores) == 0
        estado = "✅ VÁLIDO" if es_valido else "❌ INVÁLIDO"
        lineas.append(f"Estado: {estado}")
        lineas.append(f"Errores: {len(self.errores)}")
        lineas.append(f"Advertencias: {len(self.advertencias)}")
        lineas.append("")
        
        # Errores
        if self.errores:
            lineas.append("ERRORES CRÍTICOS:")
            lineas.append("-" * 70)
            for error in self.errores:
                lineas.append(error)
            lineas.append("")
        
        # Advertencias
        if self.advertencias:
            lineas.append("ADVERTENCIAS:")
            lineas.append("-" * 70)
            for advertencia in self.advertencias:
                lineas.append(advertencia)
            lineas.append("")
        
        # Contenido del archivo
        lineas.append("CONTENIDO DEL ARCHIVO:")
        lineas.append("-" * 70)
        for i, linea in enumerate(self.lineas, 1):
            lineas.append(f"Línea {i}: {linea[:100]}{'...' if len(linea) > 100 else ''}")
        
        lineas.append("=" * 70)
        
        return "\n".join(lineas)


def main():
    """Función principal."""
    if len(sys.argv) < 2:
        print("Uso: python validator_pre_envio.py <archivo.txt>")
        print("")
        print("Ejemplos:")
        print("  python validator_pre_envio.py B001-1.txt")
        print("  python validator_pre_envio.py D:\\FFEESUNAT\\test\\B001-1.txt")
        sys.exit(1)
    
    archivo = sys.argv[1]
    
    print("Iniciando validación...")
    print("")
    
    validador = ValidadorTxtApifas(archivo)
    es_valido, errores, advertencias = validador.validar()
    
    # Mostrar reporte
    print(validador.generar_reporte())
    
    # Código de salida
    if es_valido:
        print("")
        print("✅ ARCHIVO LISTO PARA ENVÍO A APIFAS")
        sys.exit(0)
    else:
        print("")
        print("❌ CORREGIR ERRORES ANTES DE ENVIAR")
        sys.exit(1)


if __name__ == "__main__":
    main()
