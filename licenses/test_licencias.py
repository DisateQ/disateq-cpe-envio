"""
test_licencias.py
=================
Script de prueba del sistema de licencias RSA

Prueba el flujo completo:
1. Generar par de claves
2. Crear licencia de prueba
3. Validar licencia
4. Probar licencia vencida
5. Probar licencia alterada

Autor: Fernando Hernán Tejada (@fhertejada™)
"""

import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from validador_licencias import LicenseGenerator, LicenseValidator


def test_flujo_completo():
    """Prueba el flujo completo de licencias."""
    print("\n" + "="*70)
    print("  TEST SISTEMA DE LICENCIAS RSA")
    print("  Motor CPE DisateQ™ v3.0")
    print("="*70 + "\n")
    
    # Usar directorio temporal para las pruebas
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # TEST 1: Generar claves
        print("📝 TEST 1: Generando par de claves RSA...")
        try:
            LicenseGenerator.generate_keypair(tmpdir)
            print("   ✅ Claves generadas correctamente\n")
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
            return False
        
        # TEST 2: Crear licencia válida
        print("📝 TEST 2: Creando licencia de prueba (válida 30 días)...")
        try:
            LicenseGenerator.create_license(
                client_name="Cliente de Prueba S.A.C.",
                client_ruc="20123456789",
                expiry_days=30,
                max_docs_month=1000,
                private_key_path=tmpdir / "disateq_private.pem",
                output_path=tmpdir / "disateq_motor.lic"
            )
            print("   ✅ Licencia creada correctamente\n")
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
            return False
        
        # TEST 3: Validar licencia correcta
        print("📝 TEST 3: Validando licencia correcta...")
        try:
            validator = LicenseValidator(tmpdir)
            valida, mensaje, datos = validator.validate()
            
            if valida:
                print(f"   ✅ {mensaje}")
                print(f"      Cliente: {datos['client_name']}")
                print(f"      RUC: {datos['client_ruc']}\n")
            else:
                print(f"   ❌ Validación falló: {mensaje}\n")
                return False
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
            return False
        
        # TEST 4: Licencia vencida
        print("📝 TEST 4: Probando licencia vencida...")
        try:
            # Crear licencia vencida hace 1 día
            LicenseGenerator.create_license(
                client_name="Cliente Vencido S.A.C.",
                client_ruc="20111111111",
                expiry_days=-1,  # Vencida ayer
                max_docs_month=1000,
                private_key_path=tmpdir / "disateq_private.pem",
                output_path=tmpdir / "disateq_motor.lic"
            )
            
            validator = LicenseValidator(tmpdir)
            valida, mensaje, datos = validator.validate()
            
            if not valida and "vencida" in mensaje.lower():
                print(f"   ✅ Detectada correctamente: {mensaje}\n")
            else:
                print(f"   ❌ Debería detectar vencimiento\n")
                return False
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
            return False
        
        # TEST 5: Licencia alterada
        print("📝 TEST 5: Probando licencia alterada (firma inválida)...")
        try:
            # Crear licencia válida
            LicenseGenerator.create_license(
                client_name="Cliente Original S.A.C.",
                client_ruc="20222222222",
                expiry_days=30,
                max_docs_month=1000,
                private_key_path=tmpdir / "disateq_private.pem",
                output_path=tmpdir / "disateq_motor.lic"
            )
            
            # Alterar el archivo (cambiar nombre)
            lic_path = tmpdir / "disateq_motor.lic"
            with open(lic_path, 'r') as f:
                lic_data = json.load(f)
            
            lic_data['data']['client_name'] = "Cliente Hacker S.A.C."  # ⚠️ Alterar
            
            with open(lic_path, 'w') as f:
                json.dump(lic_data, f, indent=2)
            
            # Intentar validar
            validator = LicenseValidator(tmpdir)
            valida, mensaje, datos = validator.validate()
            
            if not valida and "firma" in mensaje.lower():
                print(f"   ✅ Detectada correctamente: {mensaje}\n")
            else:
                print(f"   ❌ Debería detectar firma inválida\n")
                return False
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
            return False
        
        # TEST 6: Archivo faltante
        print("📝 TEST 6: Probando archivo de licencia faltante...")
        try:
            # Eliminar archivo de licencia
            (tmpdir / "disateq_motor.lic").unlink()
            
            validator = LicenseValidator(tmpdir)
            valida, mensaje, datos = validator.validate()
            
            if not valida and "no encontrada" in mensaje.lower():
                print(f"   ✅ Detectada correctamente: {mensaje}\n")
            else:
                print(f"   ❌ Debería detectar archivo faltante\n")
                return False
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
            return False
    
    # Todos los tests pasaron
    print("="*70)
    print("✅ TODOS LOS TESTS PASARON")
    print("="*70 + "\n")
    
    print("🎯 Sistema de licencias funcionando correctamente")
    print("   Listo para integrar en Motor CPE v3.0\n")
    
    return True


if __name__ == '__main__':
    import sys
    exito = test_flujo_completo()
    sys.exit(0 if exito else 1)
