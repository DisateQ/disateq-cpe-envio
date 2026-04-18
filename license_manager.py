"""
license_manager.py
==================
Verificacion de licencia local firmada — CPE DisateQ™

Flujo:
  1. Al arrancar, lee D:\FFEESUNAT\CPE DisateQ\disateq.lic
  2. Verifica que la firma sea de DisateQ (llave publica embebida)
  3. Verifica que el fingerprint del .lic coincida con este hardware
  4. Si todo OK → arranca
  5. Si falla → muestra error y cierra

El fingerprint se genera desde:
  - Serial del disco C:
  - MAC address de la red principal
  - Nombre del equipo
"""

import hashlib
import json
import base64
import socket
import logging
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)

# ── Llave pública DisateQ (embebida en el .exe) ───────────────
_PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAmw+Z3xxg7G8oiy5C0yr2
exS7JTtzPWleGPhR0g6sC4z7tbRSUL8q7NV46cenq8NbC63GnsAl7/pVsThRzzd5
PaAcZtzDOdMH/jrIM9z+C41L9iLh9C9C75RhjRkXi4gBJfhx0cwDLVQEQAKk5aia
xRIcM+1zdxZxs8iE5qcLMi/eYKWcncYRqSaPG/3Vj+1EXLxB5w2e47kBJAh5NiRL
cofe6phtqDIoGL7TBIKbZmK+C7i3Mz5NGF0m+eDJHPDiJ3V+/ppbjWv2+o7UlnTu
GXr6MsHASu+j8POKVKVnVbhHKLcQ2AXi84uXgJ1omn3tH2HWtw6Xuo/tHRE6HpC3
eQIDAQAB
-----END PUBLIC KEY-----"""

LIC_FILE = r"D:\FFEESUNAT\CPE DisateQ\disateq.lic"


# ── Fingerprint de hardware ───────────────────────────────────

def _serial_disco() -> str:
    try:
        result = subprocess.check_output(
            "wmic diskdrive get SerialNumber",
            shell=True, stderr=subprocess.DEVNULL
        ).decode(errors="ignore")
        lines = [l.strip() for l in result.splitlines() if l.strip() and l.strip() != "SerialNumber"]
        return lines[0] if lines else "NODISK"
    except Exception:
        return "NODISK"


def _mac_address() -> str:
    try:
        import uuid
        mac = uuid.getnode()
        return ':'.join(f'{(mac >> i) & 0xff:02x}' for i in range(40, -1, -8))
    except Exception:
        return "NOMAC"


def _nombre_equipo() -> str:
    try:
        return socket.gethostname().upper()
    except Exception:
        return "NOHOST"


def generar_fingerprint() -> str:
    """
    Genera el fingerprint único de este hardware.
    Retorna string de 16 caracteres hexadecimales.
    """
    serial = _serial_disco()
    mac    = _mac_address()
    host   = _nombre_equipo()
    raw    = f"{serial}|{mac}|{host}|DISATEQ_CPE_V2"
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16].upper()
    return f"{digest[:4]}-{digest[4:8]}-{digest[8:12]}-{digest[12:16]}"


# ── Verificación de licencia ──────────────────────────────────

class LicenciaError(Exception):
    pass


def verificar_licencia() -> dict:
    """
    Verifica la licencia del motor.
    Retorna dict con datos de la licencia si es válida.
    Lanza LicenciaError con mensaje descriptivo si no es válida.
    """
    try:
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.primitives.asymmetric import padding
    except ImportError:
        raise LicenciaError(
            "Componente de seguridad no encontrado.\n"
            "Contacte a DisateQ: soporte@disateq.com"
        )

    # 1 — Verificar que existe el archivo .lic
    ruta_lic = Path(LIC_FILE)
    if not ruta_lic.exists():
        raise LicenciaError(
            "Licencia no encontrada.\n\n"
            "Para activar CPE DisateQ™ contacte a:\n"
            "DisateQ  |  soporte@disateq.com"
        )

    # 2 — Leer y parsear el .lic
    try:
        datos_lic = json.loads(ruta_lic.read_text(encoding="utf-8"))
        fingerprint_lic = datos_lic["fingerprint"]
        firma_b64       = datos_lic["firma"]
        payload_str     = datos_lic["payload"]
    except Exception:
        raise LicenciaError(
            "Archivo de licencia corrupto o inválido.\n"
            "Contacte a DisateQ para reactivar."
        )

    # 3 — Verificar firma criptográfica
    try:
        public_key = serialization.load_pem_public_key(_PUBLIC_KEY_PEM.encode())
        firma      = base64.b64decode(firma_b64)
        public_key.verify(
            firma,
            payload_str.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
    except Exception:
        raise LicenciaError(
            "Licencia inválida o modificada.\n"
            "Contacte a DisateQ para reactivar."
        )

    # 4 — Verificar fingerprint de hardware
    fingerprint_actual = generar_fingerprint()
    if fingerprint_lic != fingerprint_actual:
        raise LicenciaError(
            f"Esta licencia no corresponde a este equipo.\n\n"
            f"Licencia para: {fingerprint_lic}\n"
            f"Este equipo:   {fingerprint_actual}\n\n"
            f"Contacte a DisateQ para transferir la licencia."
        )

    log.info(f"Licencia verificada OK — {fingerprint_actual}")
    return json.loads(payload_str)


def mostrar_fingerprint(fp: str):
    """
    Muestra el fingerprint en una ventana con campo copiable.
    El usuario puede seleccionar y copiar el código fácilmente.
    """
    import tkinter as tk

    win = tk.Tk()
    win.title("CPE DisateQ\u2122 \u2014 Fingerprint del equipo")
    win.geometry("420x220")
    win.resizable(False, False)
    win.configure(bg="#f0f0f0")

    tk.Frame(win, bg="#1a3a5c").pack(fill="x")
    tk.Label(win, text="  CPE DisateQ\u2122  \u2014  Fingerprint del equipo",
             font=("Segoe UI", 11, "bold"), bg="#1a3a5c", fg="white",
             pady=8).pack(fill="x")

    tk.Label(win,
             text="Envíe este código a DisateQ para activar su licencia:",
             font=("Segoe UI", 9), bg="#f0f0f0", fg="#546e7a").pack(pady=(16, 6))

    fr = tk.Frame(win, bg="#f0f0f0")
    fr.pack(pady=4)
    var = tk.StringVar(value=fp)
    entry = tk.Entry(fr, textvariable=var, font=("Consolas", 16, "bold"),
                     width=20, justify="center", relief="solid", bd=1,
                     state="readonly", readonlybackground="#ffffff",
                     fg="#1a3a5c")
    entry.pack(side="left", padx=(0, 6))

    def copiar():
        win.clipboard_clear()
        win.clipboard_append(fp)
        btn_copiar.config(text="¡Copiado!", bg="#2e7d32")
        win.after(2000, lambda: btn_copiar.config(text="Copiar", bg="#1565c0"))

    btn_copiar = tk.Button(fr, text="Copiar", command=copiar,
                           font=("Segoe UI", 9, "bold"),
                           bg="#1565c0", fg="white",
                           relief="flat", padx=10, pady=6,
                           cursor="hand2", bd=0)
    btn_copiar.pack(side="left")

    tk.Label(win, text="soporte@disateq.com  |  www.disateq.com",
             font=("Segoe UI", 8), bg="#f0f0f0", fg="#9e9e9e").pack(pady=(12, 0))

    tk.Button(win, text="Cerrar", command=win.destroy,
              font=("Segoe UI", 9), bg="#546e7a", fg="white",
              relief="flat", padx=14, pady=5,
              cursor="hand2", bd=0).pack(pady=8)

    win.mainloop()


def mostrar_error_licencia(mensaje: str):
    """Muestra ventana de error de licencia y cierra la app."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "CPE DisateQ™ — Licencia requerida",
            f"{mensaje}\n\nwww.disateq.com"
        )
        root.destroy()
    except Exception:
        print(f"ERROR LICENCIA: {mensaje}")


if __name__ == "__main__":
    fp = generar_fingerprint()
    mostrar_fingerprint(fp)
