# DisateQ Bridge™ — Motor de integración para facturación electrónica

Permite que sistemas de ventas legacy (FoxPro, ERP, Excel, SQL) puedan generar,
validar y enviar comprobantes electrónicos a SUNAT de forma automática, sin
necesidad de migrar o reemplazar el sistema existente.

**Desarrollado por:** DISATEQ
**Autor:** @fhertejada™
**Versión:** v2.0.0

---

## Descripción

DisateQ Bridge™ actúa como conector entre cualquier sistema legacy y la
infraestructura de facturación electrónica de DISATEQ. Lee los datos del
sistema origen, normaliza, genera el TXT en formato APIFAS, valida y envía
a SUNAT vía OSE/PSE o SEE directo.

Soporta tres modos de operación para migración gradual sin interrumpir
las operaciones del cliente.

### Ecosistema DisateQ

```
DisateQ Bridge™       ← Motor local (este repo)
BridgeAPI             ← API local de supervisión (FastAPI)
DisateQ Plataforma CPE ← Plataforma web central
```

### Fuentes de datos soportadas

| Fuente        | Estado      | Módulo                    |
|---------------|-------------|---------------------------|
| DBF (FoxPro)  | Operativo   | `src/readers/dbf_reader.py`  |
| Excel (.xlsx) | Operativo   | `src/readers/excel_reader.py`|
| SQL           | Preparado   | `src/readers/sql_reader.py`  |

### Flujo de operación

**Operativo:** Sistema origen → DisateQ Bridge™ → TXT → Valida → APIFAS (OSE/PSE o SEE SUNAT)

**Futuro (DisateQ Plataforma CPE):**
TXT guardados → `txt_to_json.py` → DisateQ Plataforma CPE (`api.disateq.com/v1/cpe`)

---

## Arquitectura

```
Sistema legacy (DBF / Excel / SQL / API)
              ↓
     readers/ (BaseReader)
              ↓
    DisateQ Bridge™ .exe
              ↓
    Normalizer  ──→  TXT Generator
                           ↓
                      Validador TXT
                           ↓
                      Sender (APIFAS)
                      OSE/PSE o SEE SUNAT
                           ↓
                      TXT guardado en enviados/
                           ↓
                [FUTURO] txt_to_json.py
                           ↓
                [FUTURO] DisateQ Plataforma CPE
                     api.disateq.com/v1/cpe
```

---

## Estructura del proyecto

```
ffee-farmacia/
├── README.md
├── CLAUDE.md                     ← Contexto para Claude Code
├── compilar.bat                  ← Compila a .exe + paquete instalador
├── INSTALAR.bat                  ← Instalador para equipos de clientes
├── requirements.txt
├── src/
│   ├── main.py                   ← Entrada principal
│   ├── config.py                 ← Gestión de configuración
│   ├── config_wizard.py          ← Asistente de configuración (PIN)
│   ├── readers/                  ← Capa abstracta multi-fuente
│   │   ├── base.py               ← Interfaz BaseReader
│   │   ├── dbf_reader.py         ← Lector DBF (FoxPro)
│   │   ├── excel_reader.py       ← Lector Excel (.xlsx)
│   │   └── sql_reader.py         ← Lector SQL (stub)
│   ├── normalizer.py             ← Estructura interna + correcciones
│   ├── txt_generator.py          ← Generador TXT (modo legacy)
│   ├── txt_validator.py          ← Validación completa del TXT
│   ├── json_generator.py         ← Generador JSON (modos json/bridge)
│   ├── txt_to_json.py            ← Conversor TXT → DisateQ Plataforma CPE
│   ├── sender.py                 ← Envío a APIFAS
│   ├── monitor.py                ← Orquestador del ciclo de envío
│   ├── correlativo_store.py      ← Control de correlativos procesados
│   ├── report.py                 ← Reportes y control de correlativos
│   ├── status_dia.py             ← Reporte de status diario
│   ├── simulacion.py             ← Simulación sin enviar (dry-run)
│   ├── exceptions.py             ← Jerarquía de excepciones tipadas
│   └── gui.py                    ← Interfaz gráfica (Tkinter)
├── bridge_api/                   ← BridgeAPI (FastAPI) — supervisión
│   ├── main.py
│   ├── routers/
│   └── schemas.py
├── db/                           ← SQLite historial local
│   ├── database.py
│   └── models.py
├── dashboard/                    ← Frontend React (DisateQ Bridge Dashboard)
└── tests/
    ├── test_generator.py
    └── samples/
```

---

## Requisitos

- Windows 10 o superior
- Python 3.10+ (solo para desarrollo/compilación)
- Sistema legacy instalado con acceso a datos
- Carpeta `D:\DisateQ\Bridge\` (se crea automáticamente)

### Dependencias Python

```
requests
dbfread
openpyxl
tkinter (incluido en Python estándar)
fastapi
uvicorn
sqlalchemy
pyinstaller (solo para compilar)
```

---

## Instalación en cliente

### Opción A — Paquete instalador (recomendado)

1. Compilar en Windows con `compilar.bat` → genera `dist\DisateQBridge_Instalador.zip`
2. Copiar el ZIP al equipo del cliente y descomprimir
3. Clic derecho en `INSTALAR.bat` → **Ejecutar como administrador**
4. Al abrirse DisateQ Bridge™ por primera vez, completar:
   - Razón social y RUC
   - Serie (ej: B001)
   - Modalidad: **OSE / PSE** o **SEE SUNAT**
   - **Último correlativo enviado** — para no reenviar históricos
   - **PIN de 4 dígitos** — protege el acceso a la configuración

### Opción B — Desde código fuente (desarrollo)

```bash
git clone https://github.com/DisateQ/ffee-farmacia.git
cd ffee-farmacia
pip install -r requirements.txt
python src/main.py
```

---

## Configuración

El archivo `bridge_config.ini` se genera en `D:\DisateQ\Bridge\` durante la primera ejecución.

```ini
[EMPRESA]
RUC          = 10405206710
RAZON_SOCIAL = EMPRESA SAC
SERIE        = B001

[ENVIO]
MODALIDAD    = SUNAT
MODO         = legacy
URL_ENVIO    = https://apifas.disateq.com/produccion_text.php
URL_ANULACION = https://apifas.disateq.com/produccion_anular.php

[RUTAS]
DATA_SOURCE  = C:\Sistemas\data
SALIDA_TXT   = D:\DisateQ\Bridge

[SEGURIDAD]
PIN          = 1234

[CORRELATIVO]
B001         = 0
```

### Endpoints APIFAS

| Modalidad   | Operación  | URL                                                    |
|-------------|------------|--------------------------------------------------------|
| OSE / PSE   | Envío      | https://apifas.disateq.com/ose_produccion.php          |
| OSE / PSE   | Anulación  | https://apifas.disateq.com/ose_anular.php              |
| SEE SUNAT   | Envío      | https://apifas.disateq.com/produccion_text.php         |
| SEE SUNAT   | Anulación  | https://apifas.disateq.com/produccion_anular.php       |
| Plataforma  | Envío      | https://api.disateq.com/v1/cpe (futuro)                |

---

## Uso

### Interfaz gráfica

```
DisateQBridge.exe
```

### Línea de comandos

```bash
DisateQBridge.exe --once        # Procesar pendientes y terminar
DisateQBridge.exe --config      # Abrir configuración (requiere PIN)
DisateQBridge.exe --reporte     # Generar reporte de correlativos
DisateQBridge.exe --modo legacy # Forzar modo TXT
DisateQBridge.exe --modo json   # Forzar modo JSON
```

---

## Modos de operación

| Modo     | Descripción                                                      |
|----------|------------------------------------------------------------------|
| `legacy` | Genera TXT → envía a APIFAS → guarda en `enviados/`             |
| `json`   | Genera JSON → envía a APIFAS (formato alternativo)              |
| `bridge` | Genera TXT + convierte a JSON → envía a DisateQ Plataforma CPE  |

---

## Powered by DisateQ Bridge™ — @fhertejada™
