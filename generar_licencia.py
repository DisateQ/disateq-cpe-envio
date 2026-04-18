"""
generar_licencia.py
===================
Herramienta DisateQ — Generador de licencias CPE DisateQ™

Uso:
    python generar_licencia.py

Solicita el fingerprint del cliente y genera el archivo disateq.lic
listo para entregar.
"""

import json
import base64
import hashlib
from datetime import date
from pathlib import Path

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding


PRIVATE_KEY_FILE = r"D:\DATA\disateq_private.pem"
SALIDA = "disateq.lic"


def cargar_llave_privada():
    ruta = Path(PRIVATE_KEY_FILE)
    if not ruta.exists():
        raise FileNotFoundError(
            f"Llave privada no encontrada en {PRIVATE_KEY_FILE}\n"
            "Copie disateq_private.pem a esa ubicacion."
        )
    return serialization.load_pem_private_key(
        ruta.read_bytes(),
        password=None
    )


def generar_licencia(fingerprint: str, cliente: str, ruc: str) -> dict:
    private_key = cargar_llave_privada()

    payload = json.dumps({
        "fingerprint": fingerprint,
        "cliente":     cliente,
        "ruc":         ruc,
        "producto":    "CPE DisateQ Motor v1",
        "emitida":     date.today().isoformat(),
    }, ensure_ascii=False)

    firma = private_key.sign(
        payload.encode(),
        padding.PKCS1v15(),
        hashes.SHA256()
    )

    lic = {
        "fingerprint": fingerprint,
        "payload":     payload,
        "firma":       base64.b64encode(firma).decode(),
    }

    ruta_lic = Path(SALIDA)
    ruta_lic.write_text(json.dumps(lic, indent=2), encoding="utf-8")
    print(f"\n✅ Licencia generada: {ruta_lic.resolve()}")
    print(f"   Cliente    : {cliente}")
    print(f"   RUC        : {ruc}")
    print(f"   Fingerprint: {fingerprint}")
    print(f"   Emitida    : {date.today().isoformat()}")
    print(f"\n   Entregar al cliente: {SALIDA}")
    print(f"   Destino en cliente : D:\\FFEESUNAT\\CPE DisateQ\\disateq.lic")
    return lic


if __name__ == "__main__":
    print()
    print("  =============================================")
    print("    DisateQ — Generador de Licencias CPE")
    print("  =============================================")
    print()
    fingerprint = input("  Fingerprint del cliente : ").strip().upper()
    cliente     = input("  Razon social            : ").strip()
    ruc         = input("  RUC                     : ").strip()
    print()
    generar_licencia(fingerprint, cliente, ruc)