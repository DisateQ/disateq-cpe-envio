# Carpeta dist/ - Distribución de Producto Final

Esta carpeta contiene los **productos finales listos para distribución** a clientes.

## 📁 Estructura

```
dist/
├── windows/                   # Ejecutables Windows (.exe)
│   └── MotorCPE_DisateQ_v3.0.0.exe
│
└── installers/               # Paquetes instaladores completos
    └── MotorCPE_v3.0.0_Instalador_2026-04-20.zip
```

---

## 🎯 Contenido de los Instaladores

Cada instalador ZIP incluye:

- ✅ **Ejecutable** - MotorCPE_DisateQ_vX.X.X.exe
- ✅ **Clave pública** - disateq_public.pem
- ✅ **Configuración ejemplo** - config/motor_config.ejemplo.yaml
- ✅ **README cliente** - Instrucciones de instalación
- ✅ **Script instalador** - INSTALAR.bat (Windows)
- ✅ **Carpetas trabajo** - config/, logs/, output/, backup/

**NO incluye:**
- ❌ Código fuente (.py)
- ❌ Clave privada DisateQ
- ❌ Licencia (se genera por separado para cada cliente)

---

## 🚀 Proceso de Distribución

### 1. Compilar Producto
```powershell
cd "D:\DisateQ\Motor CPE"
.\compilar_producto_final.ps1
```

### 2. Enviar a Cliente
- Enviar: `instaladores/MotorCPE_vX.X.X_Instalador_YYYY-MM-DD.zip`
- Cliente ejecuta: `INSTALAR.bat`

### 3. Generar Licencia
```powershell
cd licenses
python crear_licencia_cliente.py
```
- Ingresar datos del cliente
- Enviar: `disateq_motor.lic`

### 4. Cliente Activa
- Cliente coloca `disateq_motor.lic` en carpeta instalación
- Ejecuta: `MotorCPE_DisateQ_vX.X.X.exe`

---

## 📝 Versionado

Formato: `MAJOR.MINOR.PATCH`

- **MAJOR** - Cambios incompatibles (v3.0.0)
- **MINOR** - Nuevas funcionalidades compatibles (v3.1.0)
- **PATCH** - Correcciones de bugs (v3.0.1)

---

## 🔐 Seguridad

### ✅ Incluir en dist/:
- Ejecutables compilados
- Clave pública (.pem)
- Documentación cliente

### ❌ NUNCA incluir:
- Código fuente Python (.py)
- Clave privada DisateQ (disateq_private.pem)
- Licencias de clientes (.lic) - se generan aparte

---

## 📊 Tamaños Típicos

- **Ejecutable**: ~15-25 MB
- **Instalador ZIP**: ~20-30 MB

---

## 🛠️ Compilación Técnica

**Herramienta**: PyInstaller
**Modo**: --onefile (ejecutable único)
**Plataforma**: Windows x64
**Python**: 3.10+

**Dependencias incluidas**:
- cryptography (licencias RSA)
- openpyxl (Excel)
- dbfread (FoxPro)
- pyodbc (SQL)
- PyYAML (configs)
- requests (HTTP)

---

## 📞 Contacto

**DisateQ™**
- Email: soporte@disateq.com
- GitHub: privado

---

© 2026 DisateQ™ | Motor CPE v3.0
