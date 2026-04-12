"""
main.py
=======
Entrada principal DisateQ Bridge(tm).

Modos:
  (sin args)    -> Interfaz grafica
  --once        -> Procesa pendientes y termina (Tarea Programada)
  --config      -> Abre configuracion (requiere PIN)
  --reporte     -> Genera reporte de correlativos
  --modalidad OSE|SEE -> Fuerza modalidad de envio
  --modo legacy|json  -> Fuerza modo de generacion
"""

import sys
import argparse
import logging
from pathlib import Path

VERSION = "2.0.0"

# ── Resolver ruta de modulos para PyInstaller ──────────────
def _setup_path():
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
        src  = base / "src"
        if src.exists() and str(src) not in sys.path:
            sys.path.insert(0, str(src))
        if str(base) not in sys.path:
            sys.path.insert(0, str(base))
    else:
        src = Path(__file__).parent
        if str(src) not in sys.path:
            sys.path.insert(0, str(src))

_setup_path()
# ──────────────────────────────────────────────────────────

from config import leer_config, config_completa, label_modalidad
from license_manager import verificar_licencia, mostrar_error_licencia, generar_fingerprint, LicenciaError


def init_logging(log_file: str):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )



def _verificar_instancia_unica() -> bool:
    """
    Verifica que no haya otra instancia de CPE DisateQ corriendo.
    Usa un Mutex de Windows para garantizar instancia unica.
    Retorna True si es la unica instancia, False si ya hay otra corriendo.
    """
    try:
        import ctypes
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "CPEDisateQ_Mutex_v2")
        if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning(
                "CPE DisateQ\u2122",
                "CPE DisateQ\u2122 ya est\u00e1 en ejecuci\u00f3n.\n\n"
                "Revisa la barra de tareas o el \u00e1rea de notificaciones."
            )
            root.destroy()
            return False
        return True
    except Exception:
        return True  # Si falla la verificacion, permitir arranque


def main():
    parser = argparse.ArgumentParser(
        description=f"DisateQ Bridge\u2122 v{VERSION} \u2014 @fhertejada\u2122 \u00b7 DisateQ\u2122")
    parser.add_argument("--once",       action="store_true")
    parser.add_argument("--config",     action="store_true")
    parser.add_argument("--reporte",    action="store_true")
    parser.add_argument("--modalidad",  choices=["OSE", "SEE"])
    parser.add_argument("--modo",       choices=["legacy", "json"])
    parser.add_argument("--fingerprint", action="store_true",
                        help="Muestra el fingerprint de este equipo y termina")
    args = parser.parse_args()

    # Mostrar fingerprint si se solicita
    if args.fingerprint:
        fp = generar_fingerprint()
        from license_manager import mostrar_fingerprint
        mostrar_fingerprint(fp)
        return

    if not _verificar_instancia_unica():
        return

    # Verificar licencia
    try:
        verificar_licencia()
    except LicenciaError as e:
        mostrar_error_licencia(str(e))
        return

    cfg = leer_config()

    salida   = cfg.get("RUTAS", "salida_txt", fallback=r"D:\DisateQ\Bridge")
    log_file = str(Path(salida) / "bridge.log")
    Path(salida).mkdir(parents=True, exist_ok=True)
    init_logging(log_file)

    log = logging.getLogger(__name__)
    log.info(f"DisateQ Bridge\u2122 v{VERSION} iniciado \u2014 @fhertejada\u2122 \u00b7 DisateQ\u2122")

    # Sobrescribir desde argumentos si se pasaron
    if args.modalidad:
        cfg.set("ENVIO", "modalidad", args.modalidad)
    if args.modo:
        cfg.set("ENVIO", "modo", args.modo)

    # --config: abre wizard protegido por PIN
    if args.config:
        import tkinter as tk
        from config_wizard import abrir_wizard
        root = tk.Tk()
        root.withdraw()
        abrir_wizard(root, cfg)
        root.mainloop()
        return

    # Primera ejecucion: sin configuracion completa
    if not config_completa(cfg):
        log.info("Primera ejecucion \u2014 abriendo configuracion inicial")
        import tkinter as tk
        from tkinter import messagebox
        from config_wizard import abrir_wizard
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(
            "Configuracion inicial",
            "Bienvenido a DisateQ Bridge\u2122.\n\n"
            "Complete la configuracion para continuar.\n"
            "Defina un PIN de 4 digitos que protegera el acceso a esta ventana."
        )
        abrir_wizard(root, cfg)
        root.mainloop()
        return

    # --once: sin GUI, para Tarea Programada Windows
    if args.once:
        from monitor import Monitor
        monitor = Monitor(cfg)
        monitor.procesar_una_vez()
        return

    # --reporte
    if args.reporte:
        from report import generar_reporte
        print(generar_reporte(cfg.get("RUTAS", "salida_txt")))
        return

    # Modo normal: GUI
    from gui import iniciar_gui
    from monitor import Monitor
    from report import generar_reporte
    iniciar_gui(cfg, Monitor, generar_reporte)


if __name__ == "__main__":
    main()

