"""
sql_adapter.py
==============
Adaptador SQL Universal — Motor CPE DisateQ™ v3.0

Soporta LEGACY y MODERNO:
- ODBC genérico (FoxPro, Access, etc.)
- SQL Server 2000-2022
- PostgreSQL
- MySQL
- Oracle
- DB2
- Sybase

El mismo código funciona para todos vía YAML config.
"""

from typing import Dict, List, Optional
from pathlib import Path
from .base_adapter import BaseAdapter
from .yaml_mapper import load_mapping


class SQLAdapter(BaseAdapter):
    """
    Adaptador SQL universal.
    
    Soporta múltiples motores SQL mediante connection string.
    Lee configuración de mapeo desde YAML.
    
    Ejemplo YAML:
        source:
          type: sqlserver
          connection: "Driver={SQL Server};Server=localhost;Database=ERP"
          table: VENTAS
          
        source:
          type: odbc
          connection: "Driver={Microsoft Visual FoxPro Driver};SourceDB=C:\\SIS98"
          table: FACTURACION
    """
    
    def __init__(self, mapping_file: str):
        """
        Args:
            mapping_file: Ruta al archivo YAML de configuración
        """
        super().__init__()
        self.mapper = load_mapping(mapping_file)
        self.config = self.mapper.source_config
        
        self.db_type = self.config.get('type', 'odbc')
        self.connection_string = self.config.get('connection')
        self.table_name = self.config.get('table') or self.config.get('path', '').split('/')[-1].split('.')[0]
        self.encoding = self.config.get('encoding', 'utf-8')
        
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Establece conexión según el tipo de base de datos."""
        try:
            import pyodbc
        except ImportError:
            raise RuntimeError(
                "pyodbc no instalado.\n"
                "Ejecutar: pip install pyodbc\n"
                "Para SQL Server también: pip install pyodbc"
            )
        
        try:
            self.conn = pyodbc.connect(self.connection_string)
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            raise RuntimeError(f"Error conectando a base de datos: {e}")
    
    def disconnect(self):
        """Cierra conexión."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def read_pending(self) -> List[Dict]:
        """
        Lee comprobantes pendientes según filtros del YAML.
        
        Returns:
            Lista de dicts con datos de cabecera de comprobantes pendientes
        """
        if not self.conn:
            self.connect()
        
        # Construir query con filtros
        filters = self._build_filters()
        query = f"SELECT * FROM {self.table_name}"
        
        if filters:
            query += f" WHERE {filters}"
        
        self.cursor.execute(query)
        
        # Convertir resultados a lista de dicts
        columns = [column[0] for column in self.cursor.description]
        results = []
        
        for row in self.cursor.fetchall():
            record = dict(zip(columns, row))
            results.append(record)
        
        return results
    
    def read_items(self, comprobante: Dict) -> List[Dict]:
        """
        Lee items/detalle de un comprobante.
        
        Args:
            comprobante: Dict con datos de cabecera
            
        Returns:
            Lista de dicts con items del comprobante
        """
        if not self.conn:
            self.connect()
        
        items_config = self.mapper.items_map
        items_table = items_config.get('source_table', self.table_name + '_detalle')
        relation_fields = items_config.get('relation', {})
        
        # Construir WHERE clause basado en relación
        where_parts = []
        for target_field, source_field in relation_fields.items():
            value = comprobante.get(source_field)
            if isinstance(value, str):
                where_parts.append(f"{target_field} = '{value}'")
            else:
                where_parts.append(f"{target_field} = {value}")
        
        where_clause = " AND ".join(where_parts)
        query = f"SELECT * FROM {items_table} WHERE {where_clause}"
        
        self.cursor.execute(query)
        
        columns = [column[0] for column in self.cursor.description]
        results = []
        
        for row in self.cursor.fetchall():
            record = dict(zip(columns, row))
            results.append(record)
        
        return results
    
    def normalize(self, source_data: Dict, source_items: List[Dict]) -> Dict:
        """
        Normaliza datos origen al formato CPE usando YAML mapper.
        
        Args:
            source_data: Datos de cabecera
            source_items: Lista de items
            
        Returns:
            Dict normalizado listo para generar XML/JSON
        """
        # Mapear comprobante
        comprobante = self.mapper.map_comprobante(source_data)
        
        # Mapear cliente
        cliente = self.mapper.map_cliente(source_data)
        
        # Mapear items
        items = self.mapper.map_items(source_items)
        
        # Calcular totales
        totales = self._calculate_totales(items)
        
        # Construir estructura normalizada
        result = {
            'comprobante': comprobante,
            'cliente': cliente,
            'totales': totales,
            'items': items,
        }
        
        # Validar
        valid, errors = self.mapper.validate({
            **comprobante,
            **totales,
            'items': items,
        })
        
        if not valid:
            raise ValueError(f"Validación fallida: {'; '.join(errors)}")
        
        return result
    
    def _build_filters(self) -> str:
        """Construye cláusula WHERE basada en business_rules del YAML."""
        filter_rules = self.mapper.business_rules.get('filter', [])
        
        if not filter_rules:
            return ""
        
        parts = []
        for rule in filter_rules:
            field = rule.get('field')
            equals = rule.get('equals')
            
            if isinstance(equals, str):
                parts.append(f"{field} = '{equals}'")
            else:
                parts.append(f"{field} = {equals}")
        
        return " AND ".join(parts)
    
    def _calculate_totales(self, items: List[Dict]) -> Dict:
        """
        Calcula totales del comprobante desde los items.
        
        Args:
            items: Lista de items mapeados
            
        Returns:
            Dict con gravada, exonerada, inafecta, igv, total
        """
        from decimal import Decimal
        
        gravada = Decimal('0')
        exonerada = Decimal('0')
        inafecta = Decimal('0')
        igv_total = Decimal('0')
        icbper_total = Decimal('0')
        total = Decimal('0')
        
        for item in items:
            afectacion = item.get('afectacion_igv', '10')
            subtotal = Decimal(str(item.get('subtotal_sin_igv', 0)))
            igv_item = Decimal(str(item.get('igv', 0)))
            total_item = Decimal(str(item.get('total', 0)))
            
            if afectacion == '10':  # Gravado
                gravada += subtotal
                igv_total += igv_item
            elif afectacion == '20':  # Exonerado
                exonerada += total_item
            elif afectacion == '30':  # Inafecto
                inafecta += total_item
            
            total += total_item
        
        return {
            'gravada': float(gravada),
            'exonerada': float(exonerada),
            'inafecta': float(inafecta),
            'igv': float(igv_total),
            'icbper': float(icbper_total),
            'total': float(total),
        }


# Alias para compatibilidad
class ODBCAdapter(SQLAdapter):
    """Alias para legacy ODBC (FoxPro, Access)."""
    pass


class SQLServerAdapter(SQLAdapter):
    """Alias para SQL Server."""
    pass


class PostgreSQLAdapter(SQLAdapter):
    """Alias para PostgreSQL."""
    pass


class MySQLAdapter(SQLAdapter):
    """Alias para MySQL."""
    pass


class OracleAdapter(SQLAdapter):
    """Alias para Oracle."""
    pass
