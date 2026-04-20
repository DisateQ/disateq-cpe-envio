"""
generar_claves_disateq.py
=========================
Genera par de claves RSA-2048 para DisateQ™

Solo ejecutar UNA VEZ para obtener:
- disateq_private.pem (MANTENER SEGURA - DisateQ)
- disateq_public.pem (distribuir con Motor)

Autor: Fernando Hernán Tejada (@fhertejada™)
"""

from validador_licencias import LicenseGenerator
from pathlib import Path


def main():
    print("\n" + "="*70)
    print("  Generador de Claves RSA DisateQ™")
    print("  Motor CPE v3.0")
    print("="*70 + "\n")
    
    print("⚠️  ADVERTENCIA:")
    print("   Este script solo debe ejecutarse UNA VEZ")
    print("   para generar el par de claves maestro de DisateQ™\n")
    
    respuesta = input("¿Continuar? (si/no): ").strip().lower()
    
    if respuesta not in ['si', 's', 'yes', 'y']:
        print("\n❌ Operación cancelada\n")
        return
    
    print("\n🔐 Generando par de claves RSA-2048...\n")
    
    # Generar claves en directorio actual
    LicenseGenerator.generate_keypair(Path.cwd())
    
    print("\n" + "="*70)
    print("✅ Claves generadas exitosamente")
    print("="*70 + "\n")
    
    print("📁 Archivos generados:")
    print(f"   {Path.cwd() / 'disateq_private.pem'}")
    print(f"   {Path.cwd() / 'disateq_public.pem'}\n")
    
    print("⚠️  SEGURIDAD:")
    print("   1. Guardar disateq_private.pem en lugar SEGURO")
    print("   2. NUNCA compartir la clave privada")
    print("   3. Hacer backup de ambas claves")
    print("   4. Distribuir disateq_public.pem con cada instalación del Motor\n")
    
    print("📝 Próximos pasos:")
    print("   1. Copiar disateq_private.pem a carpeta segura DisateQ")
    print("   2. Copiar disateq_public.pem al directorio del Motor")
    print("   3. Usar crear_licencia_cliente.py para generar licencias\n")


if __name__ == '__main__':
    main()
