# CPE DisateQ™ — Envío de Facturación Electrónica

Herramienta de envío automático de Comprobantes de Pago Electrónicos (CPE) para el sistema de farmacia FoxPro. Lee directamente los archivos DBF del sistema, genera los comprobantes en el formato correcto y los envía a SUNAT vía **APIFAS** (API para DisateQ).

**Desarrollado por:** DISATEQ  
**Autor:** @fhertejada™  
**Versión:** v1.0.0

---

## Descripción

Este producto actúa como conector entre el sistema de farmacia legacy (FoxPro/DBF) y la infraestructura de facturación electrónica de DISATEQ. Soporta tres modos de operación que permiten una migración gradual sin interrumpir las operaciones del cliente.

### Flujo de operación

**Hoy:** Lee DBF → Genera TXT → Valida → Envía a APIFAS (OSE/PSE o SEE SUNAT)

**Futuro:** Los TXT enviados se convierten a JSON para FFEE Platform DisateQ™ usando `txt_to_json.py`. La conversión opera sobre los archivos ya guardados en `enviados\` — sin re-leer el DBF.

---

## Arquitectura

```
Sistema farmacia FoxPro (DBF)
         ↓
    cpe_disateq.exe
         ↓
    Lee DBF  ──→  Normalizer  ──→  TXT Generator
    (enviosffee                          ↓
     detalleventa                   Validador TXT
     productox)                          ↓
                                    Sender (APIFAS)
                                    OSE/PSE o SEE SUNAT
                                         ↓
                                    TXT guardado en enviados/
                                         ↓
                               [FUTURO] txt_to_json.py
                                         ↓
                               [FUTURO] FFEE Platform DisateQ™
                                    api.disateq.com/v1/cpe
```

**Flujo actual (operativo):**
DBF → Normalizar → Generar TXT → Validar → Enviar a APIFAS → Guardar en `enviados\`

**Flujo futuro (FFEE Platform):**
TXT guardados → Convertir a JSON (`txt_to_json.py`) → Enviar a FFEE Platform DisateQ™

---

## Estructura del proyecto

```
ffee-farmacia/
├── README.md
├── compilar.bat              ← Compilar a .exe + armar paquete instalador
├── INSTALAR.bat              ← Instalador para equipos de clientes
├── requirements.txt
├── src/
│   ├── main.py               ← Entrada principal
│   ├── config.py             ← Gestión de configuración
│   ├── config_wizard.py      ← Asistente de configuración (protegido con PIN)
│   ├── dbf_reader.py         ← Lectura robusta de DBF (maneja campos nulos)
│   ├── normalizer.py         ← Estructura interna + correcciones FoxPro
│   ├── txt_generator.py      ← Generador TXT (modo legacy)
│   ├── json_generator.py     ← Generador JSON (modos json/ffee)
│   ├── sender.py             ← Envío a APIFAS
│   ├── monitor.py            ← Monitoreo y ciclos automáticos
│   ├── correlativo_store.py  ← Registro local de correlativos procesados
│   ├── report.py             ← Reportes y control de correlativos
│   └── gui.py                ← Interfaz gráfica
└── tests/
    ├── test_generator.py
    └── samples/
```

---

## Requisitos

- Windows 10 o superior
- Python 3.10+ (solo para desarrollo/compilación)
- Sistema de farmacia instalado en `C:\Sistemas\`
- Carpeta `D:\FFEESUNAT\CPE DisateQ\` (se crea automáticamente)

### Dependencias Python

```
requests
dbfread
tkinter (incluido en Python estándar)
pyinstaller (solo para compilar)
```

---

## Instalación en cliente

### Opción A — Paquete instalador (recomendado)

1. Compilar en Windows con `compilar.bat` → genera `dist\CPE_DisateQ_Instalador.zip`
2. Copiar el ZIP al equipo del cliente y descomprimir
3. Clic derecho en `INSTALAR.bat` → **Ejecutar como administrador**
4. Al abrirse CPE DisateQ por primera vez, completar:
   - Razón social y RUC
   - Serie (ej: B001)
   - Modalidad: **OSE / PSE** o **SEE SUNAT**
   - **Último correlativo enviado** — número de la última boleta ya enviada a SUNAT (para no reenviar históricos)
   - **PIN de 4 dígitos** — protege el acceso a la configuración

`INSTALAR.bat` hace automáticamente:
- Crea `D:\FFEESUNAT\CPE DisateQ\` con subcarpetas `enviados\` y `errores\`
- Copia el ejecutable
- Registra tarea programada (cada 5 min, como SYSTEM)
- Crea acceso directo en el escritorio público

### Opción B — Desde código fuente (desarrollo)

```bash
git clone https://github.com/DisateQ/ffee-farmacia.git
cd ffee-farmacia
pip install -r requirements.txt
python src/main.py
```

---

## Configuración

El archivo `ffee_config.ini` se genera en `D:\FFEESUNAT\CPE DisateQ\` durante la primera ejecución.

```ini
[EMPRESA]
RUC          = 10405206710
RAZON_SOCIAL = FARMACIA DEL PUEBLO S.A.C.
SERIE        = B001

[ENVIO]
MODALIDAD    = SUNAT
MODO         = legacy
URL_ENVIO    = https://apifas.disateq.com/produccion_text.php
URL_ANULACION = https://apifas.disateq.com/produccion_anular.php

[RUTAS]
DATA_DBF     = C:\Sistemas\data
SALIDA_TXT   = D:\FFEESUNAT\CPE DisateQ

[SEGURIDAD]
PIN          = 1234

[CORRELATIVO]
B001         = 23168
```

### Endpoints APIFAS

| Modalidad | Operación | URL |
|---|---|---|
| OSE / PSE | Envío | https://apifas.disateq.com/ose_produccion.php |
| OSE / PSE | Anulación | https://apifas.disateq.com/ose_anular.php |
| SEE SUNAT | Envío | https://apifas.disateq.com/produccion_text.php |
| SEE SUNAT | Anulación | https://apifas.disateq.com/produccion_anular.php |
| FFEE Platform | Envío | https://api.disateq.com/v1/cpe (futuro) |

---

## Uso

### Interfaz gráfica

```
cpe_disateq.exe
```

### Línea de comandos

```bash
cpe_disateq.exe --once        # Procesar pendientes y terminar (Tarea Programada)
cpe_disateq.exe --config      # Abrir configuración (requiere PIN)
cpe_disateq.exe --reporte     # Generar reporte de correlativos
cpe_disateq.exe --modo legacy # Forzar modo TXT
cpe_disateq.exe --modo json   # Forzar modo JSON
```

---

## DBF del sistema farmacia

El sistema lee los siguientes archivos desde `C:\Sistemas\data\`:

| Archivo | Uso |
|---|---|
| `enviosffee.dbf` | Registro de comprobantes (`FLAG_ENVIO=2` → pendiente, `FLAG_ENVIO=3` → enviado) |
| `detalleventa.dbf` | Detalle de ítems por comprobante |
| `productox.dbf` | Catálogo con descripciones y códigos UNSPSC |

### Campos clave — enviosffee.dbf

| Campo | Descripción |
|---|---|
| `FILE_ENVIO` | Nombre del TXT a generar: `{RUC}-02-{SERIE}-{NUMERO}.txt` |
| `FECHA_DOCU` | Fecha de emisión |
| `TIPO_FACTU` | `B` = boleta, `F` = factura |
| `SERIE_FACT` | Serie: `001`, `002`, etc. |
| `NUMERO_FAC` | Correlativo numérico |
| `FLAG_ENVIO` | `2` = pendiente, `3` = enviado |

### Campos clave — detalleventa.dbf

| Campo | Descripción |
|---|---|
| `CODIGO_PRO` | Código interno del producto |
| `CANTIDAD_P` | Cantidad en unidad mayor |
| `TABLETA_PE` | Cantidad en unidad menor (usar si CANTIDAD_P = 0) |
| `PRECIO_UNI` | Precio unidad mayor con IGV |
| `PRECIO_FRA` | Precio fracción con IGV |
| `MONTO_PEDI` | Subtotal sin IGV |
| `IGV_PEDIDO` | IGV del ítem |
| `REAL_PEDID` | Total con IGV |
| `PRODUCTO_E` | `1` = exonerado IGV |
| `ICBPER` | `1` = impuesto bolsas plásticas |
| `FLAG_ANULA` | `1` = anulado (ignorar) |
| `FORMA_FACT` | `1` = contado, `2` = crédito |

---

## Control de correlativos

Al instalar en un cliente con historial previo, el técnico debe ingresar el **último número de boleta/factura ya enviado** a SUNAT. CPE DisateQ guarda ese valor en `procesados.json` y:

- Ignora todos los comprobantes con número ≤ al correlativo indicado
- Registra automáticamente cada envío exitoso
- Compacta el registro: si se enviaron 23168, 23169, 23170... guarda `hasta: 23170`

Esto evita reenvíos de históricos sin modificar el DBF del sistema FoxPro.

---

## Correcciones sobre el sistema original

El generador corrige los siguientes problemas del código FoxPro original (`infoose.scx`):

| Problema | Corrección |
|---|---|
| Afectación IGV siempre `1` | Verifica `PRODUCTO_E` e `ICBPER` por ítem |
| Exonerados suman a gravada | Calcula `total_gravada` y `total_exonerada` por separado |
| ICBPER en `total_gratuita` | Usa `total_impuestos_bolsas` |
| Forma de pago vacía | Lee `FORMA_FACT`: `1`=Contado, `2`=Crédito |
| Descripción solo código | Cruza con `productox.DESCRIPCIO + PRESENTA_P` |
| UNSPSC hardcodeado | Lee `productox.CODIGO_UNS` |
| Campos fecha nulos (bytes `\x00`) | `_SafeFieldParser` maneja sin excepción |

---

## Ciclos de envío

| Tipo | Frecuencia | Lote máximo |
|---|---|---|
| Facturas (serie F) | Inmediato al detectar | 20 por ciclo |
| Boletas (serie B) | Cada 5 minutos | 20 por ciclo |
| Manual ("Enviar ahora") | Inmediato, fuerza boletas también | 20 por ciclo |

---

## Compilar

```bash
# Doble clic en compilar.bat
# Genera: dist\cpe_disateq.exe + dist\CPE_DisateQ_Instalador.zip
```

---

## Tests

```bash
python -m pytest tests/ -v
```

---

## Roadmap

- [x] Lectura robusta de DBF (campos nulos, fechas inválidas)
- [x] Generador TXT corregido (modo legacy)
- [x] Generador JSON normalizado
- [x] Interfaz gráfica — CPE DisateQ™
- [x] Configuración protegida con PIN
- [x] Control de correlativos — evita reenvíos históricos
- [x] Lotes de envío — no satura APIFAS
- [x] Instalador de un clic para clientes
- [ ] Modo `ffee` — integración con FFEE Platform
- [ ] Soporte notas de crédito/débito automáticas
- [ ] Resumen diario de boletas (RC) para SEE SUNAT
- [ ] Notificaciones WhatsApp de errores
- [ ] Marcar FLAG_ENVIO=3 en DBF tras envío exitoso

---

## Licencia

Producto propietario — DISATEQ. Todos los derechos reservados.
