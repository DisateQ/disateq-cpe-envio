"""
main.py
=======
Motor CPE DisateQ™ v3.0 — Punto de entrada principal

Flujo:
    1. Validar licencia offline (RSA)
    2. Cargar configuración YAML
    3. Conectar a fuente de datos
    4. Procesar comprobantes pendientes
    5. Enviar a SUNAT (legacy o direct)

Autor: Fernando Hernán Tejada (@fhertejada™)
Empresa: DisateQ™
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

# Agregar src/ al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Validador de licencias (ahora en licenses/)
sys.path.insert(0, str(Path(__file__).parent / "licenses"))
from validador_licencias import LicenseValidator


def banner():
    """Muestra banner del Motor CPE."""
    print("\n" + "="*70)
    print("  Motor CPE DisateQ™ v3.0")
    print("  Comprobantes de Pago Electrónicos — Envío SUNAT")
    print("  © 2026 DisateQ™ | @fhertejada™")
    print("="*70 + "\n")


def validar_licencia() -> bool:
    """
    Valida licencia antes de ejecutar el Motor.
    
    Returns:
        True si licencia válida, False caso contrario
    """
    print("🔐 Validando licencia...")
    
    try:
        # Auto-detecta ubicación (C:\Program Files o desarrollo)
        validator = LicenseValidator()
        valida, mensaje, datos = validator.validate()
        
        if valida:
            print(f"✅ {mensaje}")
            print(f"   Cliente: {datos['client_name']}")
            print(f"   RUC: {datos['client_ruc']}")
            print(f"   Vencimiento: {datos['expiry_date'][:10]}")
            print()
            return True
        else:
            print(f"\n❌ {mensaje}")
            print(f"\nPara renovar su licencia, contacte a:")
            print(f"   DisateQ™ — soporte@disateq.com")
            print(f"   WhatsApp: +51 999 999 999\n")
            return False
    
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print(f"\nAsegúrese de tener los archivos:")
        print(f"   - disateq_motor.lic")
        print(f"   - disateq_public.pem")
        print(f"\nContacte a DisateQ™ para obtener su licencia.\n")
        return False
    
    except Exception as e:
        print(f"\n❌ Error inesperado validando licencia: {e}\n")
        return False


def cargar_configuracion(config_path: Optional[Path] = None) -> dict:
    """
    Carga configuración del Motor desde YAML.
    
    Args:
        config_path: Ruta al archivo de configuración.
                     Por defecto: D:\\FFEESUNAT\\CPE DisateQ\\config\\motor_config.yaml
    
    Returns:
        Dict con configuración cargada
    """
    if config_path is None:
        # Buscar en carpeta de datos (D:)
        config_path = Path(r"D:\FFEESUNAT\CPE DisateQ\config\motor_config.yaml")
        
        # Si no existe, buscar relativo al ejecutable (desarrollo)
        if not config_path.exists():
            config_path = Path(__file__).parent / "config" / "motor_config.yaml"
    
    print(f"📄 Cargando configuración: {config_path}")
    
    # TODO: Implementar carga YAML real
    # Por ahora, retornar config por defecto
    config = {
        'modo': 'legacy',  # 'legacy' o 'direct'
        'fuente': {
            'tipo': 'xlsx',  # 'xlsx', 'dbf', 'sql'
            'archivo': 'ventas.xlsx',  # o string conexión SQL
        },
        'envio': {
            'url': 'https://apifas.disateq.com/produccion_text.php',
            'usuario': '',
            'token': '',
        }
    }
    
    print(f"   Modo: {config['modo']}")
    print(f"   Fuente: {config['fuente']['tipo']}")
    print()
    
    return config


def procesar_comprobantes(config: dict):
    """
    Procesa comprobantes pendientes según configuración.
    
    Args:
        config: Dict con configuración del Motor
    """
    print("🔄 Iniciando procesamiento de comprobantes...\n")
    
    # TODO: Implementar lógica real
    # 1. Instanciar adaptador según config['fuente']['tipo']
    # 2. Conectar a fuente
    # 3. Leer comprobantes pendientes
    # 4. Para cada comprobante:
    #    - Normalizar
    #    - Enviar a SUNAT
    #    - Marcar como enviado
    # 5. Desconectar
    
    print("⚠️  Lógica de procesamiento pendiente de implementar")
    print("   Este es el punto de integración con adaptadores\n")


def main():
    """Función principal del Motor CPE."""
    banner()
    
    # PASO 1: Validar licencia (crítico)
    if not validar_licencia():
        print("⛔ Motor detenido por licencia inválida\n")
        return 1
    
    # PASO 2: Cargar configuración
    try:
        config = cargar_configuracion()
    except Exception as e:
        print(f"❌ Error cargando configuración: {e}\n")
        return 1
    
    # PASO 3: Procesar comprobantes
    try:
        procesar_comprobantes(config)
    except KeyboardInterrupt:
        print("\n\n⚠️  Procesamiento interrumpido por usuario\n")
        return 0
    except Exception as e:
        print(f"\n❌ Error en procesamiento: {e}\n")
        return 1
    
    # Finalización exitosa
    print("✅ Procesamiento completado exitosamente\n")
    return 0


if __name__ == '__main__':
    sys.exit(main())
