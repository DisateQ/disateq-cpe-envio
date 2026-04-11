"""
limpiar_repo.py
Limpieza del repo disateq-cpe-envio:
  1. Mueve rc_diario.py y txt_to_json.py a .archive/
  2. Mueve whatsapp_notifier.py a .archive/
  3. Limpia monitor.py: elimina imports y uso de rc_diario y whatsapp_notifier
Ejecutar desde: D:\DATA\_Proyectos_\disateq\disateq-cpe-envio
"""
from pathlib import Path
import shutil

BASE    = Path(__file__).parent
SRC     = BASE / "src"
ARCHIVE = BASE / ".archive"
ARCHIVE.mkdir(exist_ok=True)


def archivar(nombre):
    origen = SRC / nombre
    if origen.exists():
        shutil.copy(origen, ARCHIVE / nombre)
        origen.unlink()
        print(f"[ARCHIVADO] src/{nombre} → .archive/{nombre}")
    else:
        print(f"[~] No encontrado: src/{nombre}")


def patch_monitor():
    ruta = SRC / "monitor.py"
    if not ruta.exists():
        print("[!] monitor.py no encontrado")
        return

    contenido = ruta.read_text(encoding="utf-8")
    original  = contenido

    CAMBIOS = [
        # Eliminar import rc_diario
        (
            "from rc_diario          import procesar_rc_diario\n",
            "",
        ),
        # Eliminar import whatsapp_notifier
        (
            "from whatsapp_notifier  import WhatsAppNotifier\n",
            "",
        ),
        # Eliminar instancia _wa en __init__
        (
            "        self._wa             = WhatsAppNotifier(cfg)\n",
            "",
        ),
        # Eliminar self._wa.registrar_exito()
        (
            "        self._wa.registrar_exito()\n",
            "",
        ),
        # Eliminar self._wa.registrar_error en RespuestaError
        (
            "            self._wa.registrar_error(nombre, e.respuesta)\n",
            "",
        ),
        # Eliminar self._wa.registrar_error en EnvioError
        (
            "            self._wa.registrar_error(nombre, str(e))\n",
            "",
        ),
        # Eliminar bloque RC diario SEE SUNAT completo
        (
            "            # RC diario SEE SUNAT (solo si modalidad es SUNAT)\n"
            "            if self.cfg.get(\"ENVIO\", \"modalidad\", fallback=\"\").upper() == \"SUNAT\":\n"
            "                try:\n"
            "                    ruc_e  = self.cfg.get(\"EMPRESA\", \"ruc\", fallback=\"\")\n"
            "                    rs_e   = self.cfg.get(\"EMPRESA\", \"razon_social\", fallback=\"\")\n"
            "                    url_rc = self.cfg.get(\"ENVIO\", \"url_rc\", fallback=\"\")\n"
            "                    ok_rc, msg_rc = procesar_rc_diario(salida, ruc_e, rs_e, url_rc)\n"
            "                    self._log(\n"
            "                        f\"RC diario: {msg_rc}\",\n"
            "                        \"info\" if ok_rc else \"warn\",\n"
            "                    )\n"
            "                except Exception as e_rc:\n"
            "                    self._log(f\"RC diario error: {e_rc}\", \"warn\")\n",
            "",
        ),
    ]

    for buscar, poner in CAMBIOS:
        if buscar in contenido:
            contenido = contenido.replace(buscar, poner, 1)
            print(f"[OK] monitor.py — eliminado: {buscar[:60].strip()!r}")
        else:
            print(f"[~] Ya limpio o no encontrado: {buscar[:60].strip()!r}")

    if contenido != original:
        shutil.copy(ruta, str(ruta) + ".bak4")
        ruta.write_text(contenido, encoding="utf-8")
        print("[OK] monitor.py guardado")
    else:
        print("[~] monitor.py sin cambios")


print("\n=== Limpieza del repo disateq-cpe-envio ===\n")

# 1 — Archivar módulos eliminados del roadmap
archivar("rc_diario.py")
archivar("whatsapp_notifier.py")
archivar("txt_to_json.py")

print()

# 2 — Limpiar monitor.py
patch_monitor()

print("\n=== Listo ===\n")
print("Archivos movidos a .archive/ (no eliminados — por seguridad)")
print("Verificar con: git status")
