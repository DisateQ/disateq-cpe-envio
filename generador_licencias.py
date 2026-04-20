"""
generador_licencias.py
======================
Generador de licencias DisateQ™ — Para técnicos en campo

Requiere:
- firma_disateq.key en mismo directorio
- Password del técnico

Uso:
    python generador_licencias.py

Autor: Fernando Miguel Tejada Quevedo
Empresa: DisateQ™
Fecha: Abril 2026
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
from pathlib import Path
import json
import hashlib
import getpass
import sys

# Importaciones de criptografía
try:
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.backends import default_backend
except ImportError:
    print("ERROR: Instalar cryptography")
    print("pip install cryptography")
    sys.exit(1)


class GeneradorLicencias:
    """GUI para generar licencias DisateQ™."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Generador de Licencias DisateQ™ v3.0")
        self.root.geometry("600x900")
        self.root.resizable(True, True)
        
        # Variables
        self.private_key = None
        self.key_loaded = False
        
        # UI
        self.crear_interfaz()
        
    def crear_interfaz(self):
        """Crea la interfaz gráfica."""
        
        # Frame principal
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        titulo = tk.Label(
            main_frame,
            text="Generador de Licencias",
            font=("Arial", 18, "bold"),
            fg="#2c3e50"
        )
        titulo.pack(pady=(0, 5))
        
        subtitulo = tk.Label(
            main_frame,
            text="DisateQ™ Motor CPE v3.0",
            font=("Arial", 10),
            fg="#7f8c8d"
        )
        subtitulo.pack(pady=(0, 20))
        
        # Separador
        ttk.Separator(main_frame, orient="horizontal").pack(fill=tk.X, pady=10)
        
        # Sección: Clave privada
        key_frame = tk.LabelFrame(main_frame, text="Autenticación", padx=15, pady=15)
        key_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(key_frame, text="Password técnico:", anchor="w").pack(fill=tk.X)
        self.password_entry = tk.Entry(key_frame, show="•", font=("Arial", 10))
        self.password_entry.pack(fill=tk.X, pady=(5, 10))
        
        self.btn_cargar_key = tk.Button(
            key_frame,
            text="🔓 Cargar Clave Privada",
            command=self.cargar_clave_privada,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2"
        )
        self.btn_cargar_key.pack(fill=tk.X)
        
        self.lbl_key_status = tk.Label(
            key_frame,
            text="⚠️  Clave no cargada",
            fg="#e74c3c",
            font=("Arial", 9)
        )
        self.lbl_key_status.pack(pady=(10, 0))
        
        # Sección: Datos de licencia
        datos_frame = tk.LabelFrame(main_frame, text="Datos de Licencia", padx=15, pady=15)
        datos_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Serie
        tk.Label(datos_frame, text="Serie del Motor:", anchor="w").pack(fill=tk.X)
        self.serie_entry = tk.Entry(datos_frame, font=("Courier", 10))
        self.serie_entry.pack(fill=tk.X, pady=(5, 15))
        
        # RUC
        tk.Label(datos_frame, text="RUC Cliente:", anchor="w").pack(fill=tk.X)
        self.ruc_entry = tk.Entry(datos_frame, font=("Arial", 10))
        self.ruc_entry.pack(fill=tk.X, pady=(5, 15))
        
        # Nombre
        tk.Label(datos_frame, text="Nombre Empresa:", anchor="w").pack(fill=tk.X)
        self.nombre_entry = tk.Entry(datos_frame, font=("Arial", 10))
        self.nombre_entry.pack(fill=tk.X, pady=(5, 15))
        
        # Plan
        tk.Label(datos_frame, text="Plan:", anchor="w").pack(fill=tk.X)
        self.plan_var = tk.StringVar(value="basico")
        plan_frame = tk.Frame(datos_frame)
        plan_frame.pack(fill=tk.X, pady=(5, 15))
        
        tk.Radiobutton(
            plan_frame,
            text="Básico",
            variable=self.plan_var,
            value="basico"
        ).pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Radiobutton(
            plan_frame,
            text="Premium",
            variable=self.plan_var,
            value="premium"
        ).pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Radiobutton(
            plan_frame,
            text="Enterprise",
            variable=self.plan_var,
            value="enterprise"
        ).pack(side=tk.LEFT)
        
        # Vigencia
        tk.Label(datos_frame, text="Vigencia (años):", anchor="w").pack(fill=tk.X)
        self.vigencia_var = tk.StringVar(value="1")
        vigencia_frame = tk.Frame(datos_frame)
        vigencia_frame.pack(fill=tk.X, pady=(5, 0))
        
        for años in ["1", "2", "3", "5"]:
            tk.Radiobutton(
                vigencia_frame,
                text=f"{años} año{'s' if años != '1' else ''}",
                variable=self.vigencia_var,
                value=años
            ).pack(side=tk.LEFT, padx=(0, 20))
        
        # Botón generar
        ttk.Separator(main_frame, orient="horizontal").pack(fill=tk.X, pady=15)
        
        self.btn_generar = tk.Button(
            main_frame,
            text="🔑 GENERAR LICENCIA",
            command=self.generar_licencia,
            bg="#27ae60",
            fg="white",
            font=("Arial", 12, "bold"),
            height=2,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.btn_generar.pack(fill=tk.X, pady=(0, 10))
        
        # Info técnico
        info_frame = tk.Frame(main_frame, bg="#ecf0f1", padx=10, pady=10)
        info_frame.pack(fill=tk.X)
        
        info_text = f"Técnico: {getpass.getuser().upper()} | Equipo: {Path.home().parent.name}"
        tk.Label(
            info_frame,
            text=info_text,
            bg="#ecf0f1",
            fg="#7f8c8d",
            font=("Arial", 8)
        ).pack()
    
    def cargar_clave_privada(self):
        """Carga y desencripta la clave privada."""
        password = self.password_entry.get()
        
        if not password:
            messagebox.showerror(
                "Error",
                "Ingresa el password del técnico"
            )
            return
        
        # Buscar archivo de clave
        key_path = Path("firma_disateq.key")
        
        if not key_path.exists():
            # Buscar en ubicaciones comunes
            posibles = [
                Path.cwd() / "firma_disateq.key",
                Path.home() / "DisateQ" / "firma_disateq.key",
                Path("D:/DisateQ/firma_disateq.key"),
            ]
            
            for p in posibles:
                if p.exists():
                    key_path = p
                    break
            else:
                # No encontrado, preguntar
                messagebox.showwarning(
                    "Archivo no encontrado",
                    "Selecciona el archivo firma_disateq.key"
                )
                
                key_file = filedialog.askopenfilename(
                    title="Seleccionar clave privada",
                    filetypes=[("Key files", "*.key"), ("All files", "*.*")]
                )
                
                if not key_file:
                    return
                
                key_path = Path(key_file)
        
        try:
            # Leer y desencriptar clave
            with open(key_path, 'rb') as f:
                key_data = f.read()
            
            self.private_key = serialization.load_pem_private_key(
                key_data,
                password=password.encode(),
                backend=default_backend()
            )
            
            self.key_loaded = True
            
            # Actualizar UI
            self.lbl_key_status.config(
                text="✅ Clave cargada correctamente",
                fg="#27ae60"
            )
            self.btn_cargar_key.config(state=tk.DISABLED)
            self.password_entry.config(state=tk.DISABLED)
            self.btn_generar.config(state=tk.NORMAL)
            
            messagebox.showinfo(
                "Éxito",
                "Clave privada cargada correctamente\n\n"
                "Ahora puedes generar licencias."
            )
            
        except ValueError:
            messagebox.showerror(
                "Error",
                "Password incorrecto"
            )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error al cargar clave:\n{e}"
            )
    
    def validar_datos(self) -> tuple[bool, str]:
        """Valida los datos ingresados."""
        serie = self.serie_entry.get().strip()
        ruc = self.ruc_entry.get().strip()
        nombre = self.nombre_entry.get().strip()
        
        # Validar serie
        if not serie:
            return False, "Ingresa la serie del Motor"
        
        if len(serie) < 10:
            return False, "Serie inválida (muy corta)"
        
        # Validar RUC
        if not ruc:
            return False, "Ingresa el RUC del cliente"
        
        if not ruc.isdigit() or len(ruc) != 11:
            return False, "RUC debe tener 11 dígitos numéricos"
        
        # Validar nombre
        if not nombre:
            return False, "Ingresa el nombre de la empresa"
        
        if len(nombre) < 3:
            return False, "Nombre muy corto"
        
        return True, "OK"
    
    def generar_firma(self, datos: dict) -> str:
        """Genera firma digital de los datos."""
        # Serializar datos
        datos_str = json.dumps(datos, sort_keys=True)
        
        # Firmar con clave privada
        firma = self.private_key.sign(
            datos_str.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # Convertir a hexadecimal
        return firma.hex()
    
    def generar_licencia(self):
        """Genera el archivo de licencia."""
        if not self.key_loaded:
            messagebox.showerror("Error", "Carga primero la clave privada")
            return
        
        # Validar datos
        valido, mensaje = self.validar_datos()
        if not valido:
            messagebox.showerror("Error de Validación", mensaje)
            return
        
        # Confirmar generación
        serie = self.serie_entry.get().strip()
        ruc = self.ruc_entry.get().strip()
        nombre = self.nombre_entry.get().strip()
        plan = self.plan_var.get()
        vigencia_años = int(self.vigencia_var.get())
        
        confirmacion = messagebox.askyesno(
            "Confirmar Generación",
            f"¿Generar licencia con estos datos?\n\n"
            f"Serie: {serie}\n"
            f"RUC: {ruc}\n"
            f"Empresa: {nombre}\n"
            f"Plan: {plan.upper()}\n"
            f"Vigencia: {vigencia_años} año(s)"
        )
        
        if not confirmacion:
            return
        
        try:
            # Calcular fechas
            fecha_activacion = datetime.now()
            fecha_expiracion = fecha_activacion + timedelta(days=365 * vigencia_años)
            
            # Crear estructura de licencia
            licencia = {
                "serie": serie,
                "ruc": ruc,
                "nombre": nombre,
                "plan": plan,
                "activacion": fecha_activacion.strftime("%Y-%m-%d"),
                "expiracion": fecha_expiracion.strftime("%Y-%m-%d"),
                "tecnico": getpass.getuser().upper(),
                "generado": datetime.now().isoformat()
            }
            
            # Generar firma
            firma = self.generar_firma(licencia)
            licencia["firma"] = firma
            
            # Guardar archivo
            nombre_archivo = f"licencia_{ruc}.lic"
            
            archivo_guardado = filedialog.asksaveasfilename(
                title="Guardar licencia",
                defaultextension=".lic",
                initialfile=nombre_archivo,
                filetypes=[("License files", "*.lic"), ("All files", "*.*")]
            )
            
            if not archivo_guardado:
                return
            
            # Escribir archivo
            with open(archivo_guardado, 'w', encoding='utf-8') as f:
                json.dump(licencia, f, indent=2, ensure_ascii=False)
            
            # Registrar en log
            self.registrar_generacion(licencia, archivo_guardado)
            
            # Mostrar éxito
            messagebox.showinfo(
                "✅ Licencia Generada",
                f"Licencia generada exitosamente\n\n"
                f"Archivo: {Path(archivo_guardado).name}\n"
                f"Válida hasta: {fecha_expiracion.strftime('%d/%m/%Y')}\n\n"
                f"Copia este archivo a:\n"
                f"C:\\DisateQ\\Motor CPE\\licencia.lic"
            )
            
            # Limpiar campos
            self.serie_entry.delete(0, tk.END)
            self.ruc_entry.delete(0, tk.END)
            self.nombre_entry.delete(0, tk.END)
            
            # Abrir carpeta
            abrir = messagebox.askyesno(
                "Abrir carpeta",
                "¿Abrir carpeta donde se guardó la licencia?"
            )
            
            if abrir:
                import subprocess
                subprocess.run(['explorer', '/select,', archivo_guardado])
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error al generar licencia:\n{e}"
            )
    
    def registrar_generacion(self, licencia: dict, archivo: str):
        """Registra la licencia generada en log local."""
        log_file = Path("licencias_generadas.log")
        
        registro = {
            "timestamp": datetime.now().isoformat(),
            "ruc": licencia["ruc"],
            "nombre": licencia["nombre"],
            "plan": licencia["plan"],
            "expiracion": licencia["expiracion"],
            "tecnico": licencia["tecnico"],
            "archivo": archivo
        }
        
        try:
            # Leer log existente
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = [json.loads(line) for line in f if line.strip()]
            else:
                logs = []
            
            # Agregar nuevo registro
            logs.append(registro)
            
            # Guardar
            with open(log_file, 'w', encoding='utf-8') as f:
                for log in logs:
                    f.write(json.dumps(log, ensure_ascii=False) + '\n')
        
        except Exception as e:
            print(f"Warning: No se pudo registrar en log: {e}")
    
    def run(self):
        """Ejecuta la aplicación."""
        self.root.mainloop()


if __name__ == "__main__":
    app = GeneradorLicencias()
    app.run()
