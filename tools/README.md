# Herramientas — Motor CPE DisateQ™ v3.0

## 🔍 Source Explorer

Herramienta de inspección de fuentes de datos para técnicos instaladores.

---

## Descripción

\source_explorer.py\ examina cualquier fuente de datos (DBF, Excel, SQL, etc.) y muestra su estructura completa: nombres de campos, tipos de datos, longitudes y valores de muestra.

**Propósito:** Facilitar la creación de archivos de mapeo YAML sin tener que adivinar nombres de campos.

---

## Uso

### **Sintaxis Básica**

\\\ash
python tools/source_explorer.py --source <archivo_o_tabla> [opciones]
\\\

### **Opciones**

| Opción | Descripción | Requerido |
|--------|-------------|-----------|
| \--source\ | Archivo o nombre de tabla | ✅ Sí |
| \--connection\ | Connection string (solo SQL) | Para SQL |
| \--verbose\ | Mostrar valores de muestra | No |
| \--output\ | Guardar resultado en archivo | No |
| \--limit\ | Límite de registros a examinar | No (default: 10) |

---

## Ejemplos por Tipo de Fuente

### **1. DBF (FoxPro)**

\\\ash
python tools/source_explorer.py --source C:/Sistemas/data/ventas.dbf --verbose
\\\

**Salida:**
\\\
═══════════════════════════════════════
Source Explorer — DisateQ™
═══════════════════════════════════════

Fuente:  ventas.dbf
Tipo:    DBF (FoxPro)
Ruta:    C:/Sistemas/data/ventas.dbf

Registros encontrados: 1,234
Registros examinados: 10

CAMPOS (15 total):
───────────────────────────────────────

NOMBRE              TIPO    LONG.   VALORES MUESTRA
──────────────────────────────────────────────────
TIPO_DOC            C       1       B, F, B, B, F
SERIE               C       4       001, 001, 002, 001, 003
NUMERO              N       8       123, 124, 45, 125, 67
FECHA               D       8       2024-03-27, 2024-03-27, ...
RUC_CLI             C       11      12345678901, 98765432109, ...
NOMBRE_CLI          C       100     JUAN PEREZ, MARIA GOMEZ, ...
TOTAL_GRAV          N       12,2    100.00, 85.50, 120.00, ...
TOTAL_EXON          N       12,2    0.00, 0.00, 25.00, ...
TOTAL_IGV           N       12,2    18.00, 15.39, 21.60, ...
TOTAL               N       12,2    118.00, 100.89, 166.60, ...
FLAG_ENVIO          N       1       0, 0, 1, 0, 1
FLAG_ANULA          L       1       F, F, F, T, F
OBSERV              M       10      [memo], [memo], ...
CREATED             T       8       2024-03-27 10:30:15, ...
MODIFIED            T       8       2024-03-27 15:45:22, ...

═══════════════════════════════════════
Copie estos nombres EXACTOS a su YAML
═══════════════════════════════════════
\\\

---

### **2. Excel (XLSX)**

\\\ash
python tools/source_explorer.py --source ventas.xlsx --verbose
\\\

**Salida:**
\\\
═══════════════════════════════════════
Source Explorer — DisateQ™
═══════════════════════════════════════

Fuente:  ventas.xlsx
Tipo:    Excel (XLSX)
Sheets:  Ventas, Detalle, _CPE

Examinando sheet: _CPE

COLUMNAS (20 total):
───────────────────────────────────────

NOMBRE                      TIPO       VALORES MUESTRA
──────────────────────────────────────────────────────
tipo_doc                    str        03, 03, 01, 03
serie                       str        B001, B001, F001, B002
numero                      int        123, 124, 45, 125
fecha_emision               date       2024-03-27, 2024-03-27, ...
ruc_cliente                 str        12345678, 87654321, ...
nombre_cliente              str        CLIENTE VARIOS, JUAN LOPEZ, ...
item_codigo                 str        PROD001, PROD002, PROD001, ...
item_descripcion            str        PARACETAMOL 500MG, IBUPROFENO, ...
item_cantidad               float      2.0, 1.0, 10.0, 3.0
item_precio_unitario        float      5.90, 8.50, 1.20, 12.00
item_valor_unitario         float      5.00, 7.20, 1.02, 10.17
item_subtotal_sin_igv       float      10.00, 7.20, 10.20, 30.51
item_igv                    float      1.80, 1.30, 1.84, 5.49
item_total                  float      11.80, 8.50, 12.04, 36.00
item_afectacion_igv         str        10, 10, 10, 20
item_unidad                 str        NIU, NIU, NIU, NIU
item_unspsc                 str        51101500, 51101501, ...
total_gravada               float      10.00, 7.20, 10.20, 0.00
total_exonerada             float      0.00, 0.00, 0.00, 30.51
total_igv                   float      1.80, 1.30, 1.84, 0.00
total                       float      11.80, 8.50, 12.04, 30.51

═══════════════════════════════════════
\\\

---

### **3. SQL Server**

\\\ash
python tools/source_explorer.py \
  --source VEN_CABECERA \
  --connection "Driver={ODBC Driver 17 for SQL Server};Server=SRV01;Database=ERP;UID=cpe_user;PWD=secret" \
  --verbose
\\\

**Salida:**
\\\
═══════════════════════════════════════
Source Explorer — DisateQ™
═══════════════════════════════════════

Fuente:  VEN_CABECERA
Tipo:    SQL Server (via ODBC)
Server:  SRV01
DB:      ERP

Registros totales: 45,678
Registros examinados: 10

COLUMNAS (18 total):
───────────────────────────────────────

NOMBRE                  TIPO            NULL    VALORES MUESTRA
────────────────────────────────────────────────────────────────
ID_DOCUMENTO            int             NO      1, 2, 3, 4, 5
TIPO_COMPROBANTE        varchar(3)      NO      FAC, BOL, BOL, FAC, BOL
SERIE_DOCUMENTO         varchar(4)      NO      F001, B001, B001, F002, B003
NRO_DOCUMENTO           int             NO      123, 456, 457, 78, 234
FECHA_EMISION           date            NO      2024-03-27, 2024-03-27, ...
MONEDA                  char(3)         NO      PEN, PEN, USD, PEN, PEN
TIPO_DOC_CLIENTE        char(1)         SÍ      6, 1, 1, 6, 1
NRO_DOC_CLIENTE         varchar(11)     SÍ      20123456789, 12345678, ...
RAZON_SOCIAL_CLIENTE    varchar(200)    SÍ      EMPRESA SAC, JUAN PEREZ, ...
DIRECCION_CLIENTE       varchar(250)    SÍ      AV EJEMPLO 123, JR LIMA 456, ...
TOTAL_GRAVADA           decimal(12,2)   NO      1000.00, 85.50, 0.00, 2500.00
TOTAL_EXONERADA         decimal(12,2)   NO      0.00, 0.00, 120.00, 0.00
TOTAL_IGV               decimal(12,2)   NO      180.00, 15.39, 0.00, 450.00
TOTAL                   decimal(12,2)   NO      1180.00, 100.89, 120.00, 2950.00
ESTADO_SUNAT            varchar(20)     SÍ      PENDIENTE, ENVIADO, ERROR, ...
MENSAJE_SUNAT           varchar(500)    SÍ      NULL, Aceptado, Error..., ...
ANULADO                 bit             NO      0, 0, 1, 0, 0
FECHA_CREACION          datetime        NO      2024-03-27 08:15:30, ...

═══════════════════════════════════════
SUGERENCIA DE MAPEO YAML:
═══════════════════════════════════════

comprobante:
  tipo_doc:
    field: TIPO_COMPROBANTE
    transform: "map({'FAC': '01', 'BOL': '03'})"
  
  serie:
    field: SERIE_DOCUMENTO
    transform: "strip()"
  
  numero:
    field: NRO_DOCUMENTO
    transform: "int()"

cliente:
  tipo_doc:
    field: TIPO_DOC_CLIENTE
  
  numero_doc:
    field: NRO_DOC_CLIENTE

business_rules:
  filter:
    - field: ESTADO_SUNAT
      equals: 'PENDIENTE'
  
  ignore_if:
    - field: ANULADO
      equals: 1
\\\

---

### **4. PostgreSQL**

\\\ash
python tools/source_explorer.py \
  --source ventas \
  --connection "host=localhost port=5432 dbname=erp user=postgres password=secret" \
  --verbose
\\\

---

### **5. MySQL**

\\\ash
python tools/source_explorer.py \
  --source ventas \
  --connection "host=localhost;user=root;password=secret;database=erp" \
  --verbose
\\\

---

## Guardar Resultado

\\\ash
# Guardar en archivo para documentación
python tools/source_explorer.py \
  --source ventas.dbf \
  --verbose \
  --output analisis_ventas.txt
\\\

---

## Workflow Recomendado

### **Para Técnico Instalador**

1. **Ejecutar explorer:**
   \\\ash
   python tools/source_explorer.py --source <fuente> --verbose > estructura.txt
   \\\

2. **Copiar plantilla YAML:**
   \\\ash
   cp docs/mapping_examples/ejemplo_completo_sql.yaml \
      src/adapters/mappings/cliente_nuevo.yaml
   \\\

3. **Editar YAML con nombres exactos:**
   - Abrir \structura.txt\ generado
   - Copiar nombres de campos **exactamente** como aparecen
   - Pegar en el YAML

4. **Probar mapeo:**
   \\\python
   from adapters.sql_adapter import SQLAdapter
   
   adapter = SQLAdapter('src/adapters/mappings/cliente_nuevo.yaml')
   adapter.connect()
   print(adapter.read_pending())
   \\\

5. **Ajustar transformaciones** según necesidad

---

## Opciones Avanzadas

### **Limitar registros examinados**

\\\ash
python tools/source_explorer.py --source ventas.dbf --limit 100
\\\

### **Solo estructura (sin valores de muestra)**

\\\ash
python tools/source_explorer.py --source ventas.dbf
# (omitir --verbose)
\\\

### **Formato JSON para integración**

\\\ash
python tools/source_explorer.py \
  --source ventas.dbf \
  --format json \
  --output estructura.json
\\\

---

## Troubleshooting

### **Error: "Could not connect to database"**

**Causa:** Connection string incorrecto

**Solución:**
- Verificar sintaxis del connection string
- Probar conexión con cliente GUI primero (DBeaver, SSMS)
- Verificar que el driver ODBC esté instalado

### **Error: "File not found"**

**Causa:** Ruta incorrecta al archivo

**Solución:**
- Usar rutas absolutas: \C:/Sistemas/data/ventas.dbf\
- Verificar que el archivo exista
- Usar barras \/\ en vez de \\\\ en Windows

### **Warning: "Could not decode field"**

**Causa:** Encoding incorrecto en DBF

**Solución:**
El explorer usa \latin-1\ por defecto. Si es otro encoding, modificar en el código.

---

## Código Fuente

El código fuente está en: \	ools/source_explorer.py\

**Funciones principales:**

| Función | Descripción |
|---------|-------------|
| \xplorar_dbf()\ | Examina archivos DBF |
| \xplorar_xlsx()\ | Examina archivos Excel |
| \xplorar_sql()\ | Examina tablas SQL |
| \mostrar_estructura()\ | Formatea y muestra resultados |

---

## Contribuir

¿Encontraste un bug o tienes una mejora?

1. Fork del repo
2. Crear branch: \git checkout -b feature/mejora-explorer\
3. Commit: \git commit -m 'Mejora en explorer'\
4. Push: \git push origin feature/mejora-explorer\
5. Pull Request

---

**DisateQ™** — Motor CPE v3.0
