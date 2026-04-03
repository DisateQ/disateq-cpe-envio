"""
main.py
=======
Entrada principal CPE DisateQ(tm).

Modos:
  (sin args)    -> Interfaz grafica
  --once        -> Procesa pendientes y termina (Tarea Programada)
  --config      -> Abre configuracion (requiere PIN)
  --reporte     -> Genera reporte de correlativos
  --modo legacy/json/ffee -> Fuerza modo de operacion
"""

import sys
import argparse
import logging
from pathlib import Path

from config import leer_config, config_completa


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


def main():
    parser = argparse.ArgumentParser(
        description="CPE DisateQ\u2122 \u2014 @fhertejada\u2122 \u00b7 DisateQ\u2122")
    parser.add_argument("--once",    action="store_true")
    parser.add_argument("--config",  action="store_true")
    parser.add_argument("--reporte", action="store_true")
    parser.add_argument("--modo",    choices=["legacy", "json", "ffee"])
    args = parser.parse_args()

    cfg = leer_config()

    salida   = cfg.get("RUTAS", "salida_txt", fallback=r"D:\FFEESUNAT\CPE DisateQ")
    log_file = str(Path(salida) / "cpe_disateq.log")
    Path(salida).mkdir(parents=True, exist_ok=True)
    init_logging(log_file)

    log = logging.getLogger(__name__)
    log.info("CPE DisateQ\u2122 iniciado \u2014 @fhertejada\u2122 \u00b7 DisateQ\u2122")

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

    # Primera ejecucion: sin PIN configurado aun
    if not config_completa(cfg):
        log.info("Primera ejecucion \u2014 abriendo configuracion inicial")
        import tkinter as tk
        from tkinter import messagebox
        from config_wizard import abrir_wizard
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(
            "Configuracion inicial",
            "Bienvenido a CPE DisateQ\u2122.\n\nComplete la configuracion para continuar.\n"
            "Defina un PIN de 4 digitos que protegera el acceso a esta ventana."
        )
        abrir_wizard(root, cfg, callback=lambda: root.quit(), primer_arranque=True)
        root.mainloop()
        cfg = leer_config()
        if not config_completa(cfg):
            log.error("Configuracion incompleta. Saliendo.")
            return

    if args.reporte:
        from report import generar_reporte
        rpt = generar_reporte(Path(salida))
        print(rpt.read_text(encoding="utf-8"))
        return

    if args.once:
        from monitor import Monitor
        log.info("Modo: ejecucion puntual (--once)")
        Monitor(cfg)._ciclo()
        return

    from gui import iniciar_gui
    from monitor import Monitor
    from report import generar_reporte
    iniciar_gui(cfg, Monitor, generar_reporte)


if __name__ == "__main__":
    main()
