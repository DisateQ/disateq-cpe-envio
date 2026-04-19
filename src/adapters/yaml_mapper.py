"""
yaml_mapper.py
==============
Motor de mapeo YAML — Motor CPE DisateQ™ v3.0

Lee configuración YAML y transforma datos origen → contrato _CPE.
Soporta transformaciones, valores por defecto, campos calculados.
"""

import yaml
import re
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
from decimal import Decimal


class YamlMapper:
    """
    Motor de transformación basado en configuración YAML.
    
    Soporta:
    - Mapeo directo de campos
    - Valores por defecto
    - Transformaciones (map, strip, upper, to_date, etc.)
    - Campos calculados
    - Validaciones
    """
    
    def __init__(self, yaml_path: str):
        """Carga configuración YAML de mapeo."""
        self.config = self._load_yaml(yaml_path)
        self.source_config = self.config.get('source', {})
        self.comprobante_map = self.config.get('comprobante', {})
        self.cliente_map = self.config.get('cliente', {})
        self.items_map = self.config.get('items', {})
        self.business_rules = self.config.get('business_rules', {})
        self.validations = self.config.get('validations', [])
    
    def _load_yaml(self, yaml_path: str) -> Dict:
        """Carga y parsea archivo YAML."""
        path = Path(yaml_path)
        if not path.exists():
            raise FileNotFoundError(f"Archivo YAML no encontrado: {yaml_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def map_comprobante(self, source_data: Dict) -> Dict:
        """Mapea datos del comprobante (cabecera)."""
        result = {}
        
        for target_field, config in self.comprobante_map.items():
            value = self._map_field(source_data, config)
            result[target_field] = value
        
        return result
    
    def map_cliente(self, source_data: Dict) -> Dict:
        """Mapea datos del cliente."""
        result = {}
        
        for target_field, config in self.cliente_map.items():
            value = self._map_field(source_data, config)
            result[target_field] = value
        
        return result
    
    def map_items(self, source_items: list) -> list:
        """Mapea lista de ítems."""
        result = []
        
        fields_config = self.items_map.get('fields', {})
        
        for source_item in source_items:
            # Aplicar reglas de negocio (ignorar si)
            if self._should_ignore(source_item):
                continue
            
            mapped_item = {}
            for target_field, config in fields_config.items():
                value = self._map_field(source_item, config, context=mapped_item)
                mapped_item[target_field] = value
            
            result.append(mapped_item)
        
        return result
    
    def _map_field(self, source_data: Dict, config: Any, context: Dict = None) -> Any:
        """
        Mapea un campo individual aplicando transformaciones.
        
        Args:
            source_data: Datos origen
            config: Configuración del campo (puede ser dict o string directo)
            context: Contexto actual (para campos calculados)
        """
        # Si config es string directo, usar como nombre de campo
        if isinstance(config, str):
            config = {'field': config}
        
        # Valor por defecto
        default = config.get('default')
        
        # Campo calculado
        if 'calculated' in config:
            return self._eval_calculated(config['calculated'], source_data, context or {})
        
        # Campo normal
        field_name = config.get('field')
        if not field_name:
            return default
        
        # Obtener valor del source
        value = source_data.get(field_name)
        
        # Si es None o vacío, usar default
        if value is None or value == '':
            return default
        
        # Aplicar transformaciones
        transform = config.get('transform')
        if transform:
            value = self._apply_transform(value, transform, source_data)
        
        return value
    
    def _apply_transform(self, value: Any, transform: str, source_data: Dict) -> Any:
        """
        Aplica transformación al valor.
        
        Transformaciones soportadas:
        - strip()
        - upper()
        - lower()
        - int()
        - float()
        - to_date('formato')
        - map({'A': 'X', 'B': 'Y'})
        - get('campo_alternativo', default)
        """
        # map({'A': 'X', 'B': 'Y'})
        if transform.startswith('map('):
            mapping = eval(transform[4:-1])  # Extraer el dict
            return mapping.get(value, value)
        
        # to_date('%d/%m/%Y')
        if transform.startswith('to_date('):
            fmt = transform[9:-2]  # Extraer el formato
            try:
                if isinstance(value, str):
                    dt = datetime.strptime(value, fmt)
                    return dt.strftime('%Y-%m-%d')
            except:
                return value
        
        # get('campo_alternativo', default)
        if transform.startswith('get('):
            parts = transform[4:-1].split(',')
            alt_field = parts[0].strip().strip("'\"")
            alt_default = parts[1].strip().strip("'\"") if len(parts) > 1 else None
            return source_data.get(alt_field, alt_default)
        
        # Transformaciones simples
        transforms = {
            'strip()': lambda v: v.strip() if isinstance(v, str) else v,
            'upper()': lambda v: v.upper() if isinstance(v, str) else v,
            'lower()': lambda v: v.lower() if isinstance(v, str) else v,
            'int()': lambda v: int(float(v)) if v else 0,
            'float()': lambda v: float(v) if v else 0.0,
        }
        
        if transform in transforms:
            return transforms[transform](value)
        
        # Transformación compleja (eval seguro)
        # Ejemplo: "float() if float() > 0 else get('CANTIDAD_MENOR', 1)"
        if 'if' in transform or 'else' in transform:
            # Contexto seguro para eval
            safe_context = {
                'value': value,
                'float': float,
                'int': int,
                'str': str,
                'get': lambda f, d=None: source_data.get(f, d),
            }
            try:
                return eval(transform.replace('float()', 'float(value)'), safe_context)
            except:
                return value
        
        return value
    
    def _eval_calculated(self, expression: str, source_data: Dict, context: Dict) -> Any:
        """
        Evalúa campo calculado.
        
        Ejemplo: "precio_unitario / 1.18 if afectacion_igv == '10' else precio_unitario"
        """
        safe_context = {
            **source_data,
            **context,
            'Decimal': Decimal,
        }
        
        try:
            return eval(expression, {"__builtins__": {}}, safe_context)
        except Exception as e:
            print(f"Error evaluando campo calculado '{expression}': {e}")
            return None
    
    def _should_ignore(self, source_item: Dict) -> bool:
        """Verifica si el registro debe ignorarse según reglas de negocio."""
        ignore_rules = self.business_rules.get('ignore_if', [])
        
        for rule in ignore_rules:
            field = rule.get('field')
            equals = rule.get('equals')
            
            if source_item.get(field) == equals:
                return True
        
        return False
    
    def validate(self, comprobante: Dict) -> tuple[bool, list]:
        """
        Valida comprobante mapeado.
        
        Returns:
            (es_valido, lista_errores)
        """
        errores = []
        
        for validation in self.validations:
            check = validation.get('check')
            error_msg = validation.get('error')
            
            # Contexto para eval
            context = {
                **comprobante,
                'len': len,
                'abs': abs,
            }
            
            try:
                result = eval(check, {"__builtins__": {}}, context)
                if not result:
                    errores.append(error_msg)
            except Exception as e:
                errores.append(f"Error en validación '{check}': {e}")
        
        return len(errores) == 0, errores


def load_mapping(yaml_path: str) -> YamlMapper:
    """
    Carga configuración de mapeo desde YAML.
    
    Usage:
        mapper = load_mapping('mappings/cliente_farmacia.yaml')
        comprobante = mapper.map_comprobante(source_data)
        cliente = mapper.map_cliente(source_data)
        items = mapper.map_items(source_items)
        
        valid, errors = mapper.validate({
            'total': comprobante['total'],
            'gravada': totales['gravada'],
            ...
        })
    """
    return YamlMapper(yaml_path)
