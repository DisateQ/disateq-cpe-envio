"""
crear_licencia_cliente.py
=========================
Genera licencias firmadas para clientes — Motor CPE DisateQ™ v3.0

Requiere:
- disateq_private.pem (clave privada DisateQ)

Genera:
- disateq_motor.lic (archivo de licencia firmado para cliente)

Autor: Fernando Hernán Tejada (@fhertejada™)
"""

from validador_licencias import LicenseGenerator
from pathlib import Path
from datetime import datetime


def main():
    print("\n" + "="*70)
    print("  Generador de Licencias DisateQ™")
    print("  Motor CPE v3.0")
    print("="*70 + "\n")
    
    # Verificar que existe clave privada
    private_key_path = Path("disateq_private.pem")
    if not private_key_path.exists():
        print("❌ Error: No se encuentra disateq_private.pem")
        print("   Debe generar el par de claves primero con:")
        print("   python generar_claves_disateq.py\n")
        return
    
    print("📝 Ingrese datos del cliente:\n")
    
    # Recopilar datos
    client_name = input("Nombre cliente: ").strip()
    if not client_name:
        print("\n❌ Nombre de cliente es obligatorio\n")
        return
    
    client_ruc = input("RUC cliente (11 dígitos): ").strip()
    if not client_ruc or len(client_ruc) != 11:
        print("\n❌ RUC debe tener 11 dígitos\n")
        return
    
    try:
        expiry_days = int(input("Días de validez (ej: 365): ").strip() or "365")
    except ValueError:
        print("\n❌ Días debe ser un número\n")
        return
    
    try:
        max_docs_input = input("Máx documentos/mes (Enter = ilimitado): ").strip()
        max_docs = int(max_docs_input) if max_docs_input else 999999
    except ValueError:
        print("\n❌ Máx documentos debe ser un número\n")
        return
    
    # Confirmar
    max_docs_display = "ilimitado" if max_docs >= 999999 else str(max_docs)
    
    print("\n" + "-"*70)
    print("RESUMEN DE LICENCIA:")
    print("-"*70)
    print(f"Cliente: {client_name}")
    print(f"RUC: {client_ruc}")
    print(f"Validez: {expiry_days} días")
    print(f"Máx docs/mes: {max_docs_display}")
    print("-"*70 + "\n")
    
    confirmar = input("¿Generar licencia? (si/no): ").strip().lower()
    if confirmar not in ['si', 's', 'yes', 'y']:
        print("\n❌ Operación cancelada\n")
        return
    
    # Generar licencia
    print("\n🔐 Generando licencia firmada...\n")
    
    try:
        license_data = LicenseGenerator.create_license(
            client_name=client_name,
            client_ruc=client_ruc,
            expiry_days=expiry_days,
            max_docs_month=max_docs,
            private_key_path=private_key_path,
            output_path=Path("disateq_motor.lic")
        )
        
        print("\n" + "="*70)
        print("✅ Licencia generada exitosamente")
        print("="*70 + "\n")
        
        print("📁 Archivo generado:")
        print(f"   {Path.cwd() / 'disateq_motor.lic'}\n")
        
        print("📤 Entregar al cliente:")
        print("   1. disateq_motor.lic (este archivo)")
        print("   2. disateq_public.pem (clave pública)")
        print("   3. Motor CPE v3.0 (.exe o instalador)\n")
        
        print("💾 Los archivos deben estar en el mismo directorio que el Motor\n")
    
    except Exception as e:
        print(f"\n❌ Error generando licencia: {e}\n")


if __name__ == '__main__':
    main()
