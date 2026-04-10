# CPE FAS Farmacias — DisateQ™

**Conector de Facturación Electrónica para Sistema FAS**

- **Versión:** v1.0.0 (Abril 2026)
- **Desarrollado por:** DisateQ™
- **Autor:** @fhertejada
- **Repositorio:** fhertejadaDEV/cpe-fas-farmacias
- **Plataforma destino:** plataforma-ffee (api.disateq.com/v1/)

---

## DESCRIPCIÓN

Herramienta de envío automático de Comprobantes de Pago
Electrónicos (CPE) para el sistema de farmacia FAS (FoxPro/DBF).

Lee directamente los archivos DBF del sistema FAS, normaliza
la información, genera los comprobantes en el formato correcto
y los envía a SUNAT via APIFAS (API DisateQ™).

Actúa como conector entre el sistema de farmacia legacy
(FoxPro/DBF) y la infraestructura de facturación electrónica
de DisateQ™. Soporta tres modos de operación que permiten
una migración gradual sin interrumpir las operaciones del cliente.

---

## FLUJO DE OPERACIÓN

### Actual (operativo)
- Lee DBF → Normaliza → Genera TXT → Valida → Envía a APIFAS
- OSE/PSE (Operador.pe) o SEE SUNAT según configuración cliente

### Futuro (integración plataforma-ffee)
- TXT guardados → Convierte a JSON → Envía a api.disateq.com/v1/cpe
- La conversión opera sobre archivos en enviados\ sin re-leer DBF

---

## ARQUITECTURA

Sistema FAS FoxPro (DBF)
    ↓
cpe_disateq.exe
    ↓
Lee DBF → Normalizer → TXT Generator
(enviosffee                    ↓
 detalleventa             Validador TXT
 productox)                    ↓
                          Sender (APIFAS)
                          OSE/PSE o SEE SUNAT
                               ↓
                          TXT guardado en enviados\
                               ↓
                     [FUTURO] JSON Generator
                               ↓
                     [FUTURO] api.disateq.com/v1/cpe

---

## STACK TECNOLÓGICO

- Lenguaje: Python 3.10+
- Distribución: PyInstaller → ejecutable Windows .exe
- Interfaz: Tkinter (GUI) + CLI
- Lectura DBF: dbfread
- HTTP: requests
- SO cliente: Windows 10 o superior

---

## ESTRUCTURA DEL PROYECTO

cpe-fas-farmacias/
- docs/ — Documentación técnica
- src/
  - main.py — Entrada principal
  - config.py — Gestión de configuración
  - config_wizard.py — Asistente configuración (protegido PIN)
  - dbf_reader.py — Lectura robusta DBF (maneja campos nulos)
  - normalizer.py — Estructura interna + correcciones FoxPro
  - txt_generator.py — Generador TXT (modo legacy)
  - json_generator.py — Generador JSON (modos json/ffee)
  - sender.py — Envío a APIFAS
  - monitor.py — Monitoreo y ciclos automáticos
  - correlativo_store.py — Registro local correlativos procesados
  - report.py — Reportes y control correlativos
  - gui.py — Interfaz gráfica
- tests/
  - test_generator.py
  - samples/
- dist/ — Ejecutable compilado
- build/ — Archivos compilación
- compilar.bat — Compilar a .exe + armar instalador
- INSTALAR.bat — Instalador para equipos clientes
- requirements.txt

---

## ARCHIVOS DBF DEL SISTEMA FAS

Ubicación: C:\Sistemas\data\

| Archivo | Uso |
|---|---|
| enviosffee.dbf | Registro comprobantes (FLAG_ENVIO=2 pendiente, FLAG_ENVIO=3 enviado) |
| detalleventa.dbf | Detalle ítems por comprobante |
| productox.dbf | Catálogo con descripciones y códigos UNSPSC |

### Campos clave — enviosffee.dbf

| Campo | Descripción |
|---|---|
| FILE_ENVIO | Nombre TXT: {RUC}-02-{SERIE}-{NUMERO}.txt |
| FECHA_DOCU | Fecha de emisión |
| TIPO_FACTU | B = boleta, F = factura |
| SERIE_FACT | Serie: 001, 002, etc. |
| NUMERO_FAC | Correlativo numérico |
| FLAG_ENVIO | 2 = pendiente, 3 = enviado |

### Campos clave — detalleventa.dbf

| Campo | Descripción |
|---|---|
| CODIGO_PRO | Código interno del producto |
| CANTIDAD_P | Cantidad en unidad mayor |
| TABLETA_PE | Cantidad unidad menor (usar si CANTIDAD_P = 0) |
| PRECIO_UNI | Precio unidad mayor con IGV |
| PRECIO_FRA | Precio fracción con IGV |
| MONTO_PEDI | Subtotal sin IGV |
| IGV_PEDIDO | IGV del ítem |
| REAL_PEDID | Total con IGV |
| PRODUCTO_E | 1 = exonerado IGV |
| ICBPER | 1 = impuesto bolsas plásticas |
| FLAG_ANULA | 1 = anulado (ignorar) |
| FORMA_FACT | 1 = contado, 2 = crédito |

---

## ENDPOINTS APIFAS

| Modalidad | Operación | URL |
|---|---|---|
| OSE / PSE | Envío | https://apifas.disateq.com/ose_produccion.php |
| OSE / PSE | Anulación | https://apifas.disateq.com/ose_anular.php |
| SEE SUNAT | Envío | https://apifas.disateq.com/produccion_text.php |
| SEE SUNAT | Anulación | https://apifas.disateq.com/produccion_anular.php |
| FFEE Platform | Envío | https://api.disateq.com/v1/cpe (futuro) |

---

## INSTALACIÓN EN CLIENTE

### Opción A — Paquete instalador (recomendado)
1. Compilar en Windows con compilar.bat
2. Genera dist\CPE_DisateQ_Instalador.zip
3. Copiar ZIP al equipo del cliente y descomprimir
4. Clic derecho en INSTALAR.bat → Ejecutar como administrador
5. Al abrirse por primera vez completar:
   - Razón social y RUC
   - Serie (ej: B001)
   - Modalidad: OSE/PSE o SEE SUNAT
   - Último correlativo enviado a SUNAT
   - PIN de 4 dígitos (protege configuración)

INSTALAR.bat hace automáticamente:
- Crea D:\FFEESUNAT\CPE DisateQ\ con subcarpetas enviados\ y errores\
- Copia el ejecutable
- Registra tarea programada (cada 5 min, como SYSTEM)
- Crea acceso directo en escritorio público

### Opción B — Desde código fuente (desarrollo)
1. git clone https://github.com/fhertejadaDEV/cpe-fas-farmacias
2. cd cpe-fas-farmacias
3. pip install -r requirements.txt
4. python src/main.py

---

## CONFIGURACIÓN

Archivo ffee_config.ini generado en D:\FFEESUNAT\CPE DisateQ\

Secciones:

EMPRESA
- RUC
- RAZON_SOCIAL
- SERIE

ENVIO
- MODALIDAD (SUNAT o OSE)
- MODO (legacy, json, ffee)
- URL_ENVIO
- URL_ANULACION

RUTAS
- DATA_DBF = C:\Sistemas\data
- SALIDA_TXT = D:\FFEESUNAT\CPE DisateQ

SEGURIDAD
- PIN = (4 dígitos)

CORRELATIVO
- B001 = (último número enviado)

---

## USO

### Interfaz gráfica
- Ejecutar cpe_disateq.exe

### Línea de comandos
- --once → Procesar pendientes y terminar (Tarea Programada)
- --config → Abrir configuración (requiere PIN)
- --reporte → Generar reporte de correlativos
- --modo legacy → Forzar modo TXT
- --modo json → Forzar modo JSON

---

## CICLOS DE ENVÍO

| Tipo | Frecuencia | Lote máximo |
|---|---|---|
| Facturas (serie F) | Inmediato al detectar | 20 por ciclo |
| Boletas (serie B) | Cada 5 minutos | 20 por ciclo |
| Manual ("Enviar ahora") | Inmediato, fuerza boletas | 20 por ciclo |

---

## CONTROL DE CORRELATIVOS

Al instalar en cliente con historial previo el técnico ingresa
el último número de boleta/factura ya enviado a SUNAT.

CPE DisateQ guarda ese valor en procesados.json y:
- Ignora todos los comprobantes con número ≤ al correlativo indicado
- Registra automáticamente cada envío exitoso
- Compacta el registro: si se enviaron 23168, 23169, 23170
  guarda hasta: 23170

Esto evita reenvíos de históricos sin modificar el DBF del
sistema FAS.

---

## CORRECCIONES SOBRE SISTEMA FAS ORIGINAL

| Problema | Corrección |
|---|---|
| Afectación IGV siempre 1 | Verifica PRODUCTO_E e ICBPER por ítem |
| Exonerados suman a gravada | Calcula total_gravada y total_exonerada por separado |
| ICBPER en total_gratuita | Usa total_impuestos_bolsas |
| Forma de pago vacía | Lee FORMA_FACT: 1=Contado, 2=Crédito |
| Descripción solo código | Cruza con productox.DESCRIPCIO + PRESENTA_P |
| UNSPSC hardcodeado | Lee productox.CODIGO_UNS |
| Campos fecha nulos (bytes \x00) | _SafeFieldParser maneja sin excepción |

---

## REQUISITOS

### Cliente (producción)
- Windows 10 o superior
- Sistema FAS instalado en C:\Sistemas\
- Carpeta D:\FFEESUNAT\CPE DisateQ\ (se crea automáticamente)

### Desarrollo
- Python 3.10+
- pip install -r requirements.txt

### Dependencias Python
- requests
- dbfread
- tkinter (incluido en Python estándar)
- pyinstaller (solo para compilar)

---

## COMPILAR

Doble clic en compilar.bat
Genera: dist\cpe_disateq.exe + dist\CPE_DisateQ_Instalador.zip

---

## TESTS

Ejecutar desde terminal:
python -m pytest tests/ -v

---

## ROADMAP

Completado:
- Lectura robusta DBF (campos nulos, fechas inválidas)
- Generador TXT corregido (modo legacy)
- Generador JSON normalizado
- Interfaz gráfica CPE DisateQ™
- Configuración protegida con PIN
- Control de correlativos — evita reenvíos históricos
- Lotes de envío — no satura APIFAS
- Instalador de un clic para clientes

Pendiente:
- Modo ffee — integración con plataforma-ffee (api.disateq.com/v1/cpe)
- Soporte notas de crédito/débito automáticas
- Resumen diario de boletas (RC) para SEE SUNAT
- Notificaciones WhatsApp de errores
- Marcar FLAG_ENVIO=3 en DBF tras envío exitoso
- Adaptador DBF directo → JSON sin pasar por TXT

---

## INTEGRACIÓN CON PLATAFORMA FFEE

Este proyecto es el conector entre el sistema FAS y
la Plataforma FFEE DisateQ™.

Flujo de integración futuro:
- cpe-fas-farmacias lee DBF y normaliza
- Envía JSON directamente a api.disateq.com/v1/cpe
- Plataforma FFEE procesa y envía a SUNAT/OSE
- Respuesta regresa al conector
- Conector actualiza FLAG_ENVIO en DBF

Referencia: repo plataforma-ffee

---

## CHANGELOG

### v1.0.0 (Abril 2026)
- Versión operativa con clientes reales
- Soporte OSE/PSE (Operador.pe) y SEE SUNAT
- Interfaz gráfica + CLI
- Instalador automatizado
- Control de correlativos
- Correcciones sobre sistema FAS original

Próximo: v1.1 — integración directa con plataforma-ffee

---

## LICENCIA

Producto propietario — DisateQ™
Todos los derechos reservados.