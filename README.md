# Motor CPE DisateQ™ v3.0

**Motor de Comprobantes de Pago Electrónicos** — Envío directo a SUNAT SEE (UBL 2.1)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-30%20passing-green.svg)](tests/)

---

## 🎯 Características

### ✅ **Envío Directo a SUNAT**
- **SIN middleware de terceros** (APIFAS, Facturador, etc.)
- Genera JSON UBL 2.1 estándar SUNAT
- Firma digital con certificado .PEM
- Lectura automática de CDR (Constancia de Recepción)

### ✅ **Adaptadores Universales**
Compatible con **cualquier sistema origen**:
- **Excel** (XLSX) — DisateQ POS™
- **FoxPro** (DBF) — Sistemas legacy
- **SQL Server** (2000-2022) — ODBC + Nativo
- **PostgreSQL, MySQL, Oracle** — Soporte nativo
- **Access** (MDB/ACCDB) — Vía ODBC

### ✅ **Configuración YAML**
- Mapeo de campos **sin código**
- Transformaciones configurables
- Validaciones de negocio
- Reglas por cliente en archivos separados

---

## 🚀 Inicio Rápido

\\\ash
# Clonar repositorio
git clone git@github.com:DisateQ/disateq-cpe-envio.git
cd disateq-cpe-envio

# Instalar dependencias
pip install -r requirements.txt

# Explorar fuente de datos del cliente
python tools/source_explorer.py --source ventas.dbf

# Configurar mapeo YAML
cp docs/mapping_examples/ejemplo_completo_sql.yaml \\
   src/adapters/mappings/mi_cliente.yaml

# Editar con nombres reales de campos
nano src/adapters/mappings/mi_cliente.yaml

# Probar
python -m pytest tests/ -v
\\\

---

## 📁 Estructura del Proyecto

\\\
disateq-cpe-envio/
├── src/
│   ├── adapters/          # Adaptadores universales
│   │   ├── base_adapter.py
│   │   ├── xlsx_adapter.py    # Excel
│   │   ├── dbf_adapter.py     # FoxPro
│   │   ├── sql_adapter.py     # SQL universal
│   │   ├── yaml_mapper.py     # Motor de mapeo
│   │   └── mappings/          # Configs por cliente
│   ├── normalizer.py      # UBL 2.1 normalización
│   ├── sender.py          # Envío a SUNAT
│   └── signer.py          # Firma digital
├── tools/
│   └── source_explorer.py # Inspección de datos
├── tests/                 # 30 tests
├── docs/                  # Documentación completa
└── requirements.txt
\\\

---

## 🔧 Uso Básico

### **Opción 1: Excel (DisateQ POS™)**

\\\python
from adapters.xlsx_adapter import XlsxAdapter

# Leer desde Excel
adapter = XlsxAdapter('ventas.xlsx')
adapter.connect()

# Obtener pendientes
comprobantes = adapter.read_pending()

for comp in comprobantes:
    items = adapter.read_items(comp)
    cpe = adapter.normalize(comp, items)
    
    # Enviar a SUNAT
    from sender import enviar_cpe
    exito, cdr = enviar_cpe(cpe, 'certificado.pem')
    print(f"CPE {cpe['serie']}-{cpe['numero']}: {exito}")
\\\

### **Opción 2: SQL Server con YAML**

\\\python
from adapters.sql_adapter import SQLAdapter

# Cargar configuración YAML
adapter = SQLAdapter('src/adapters/mappings/cliente_xyz.yaml')
adapter.connect()

# Procesar pendientes
for comp in adapter.read_pending():
    items = adapter.read_items(comp)
    cpe = adapter.normalize(comp, items)
    # ... enviar
\\\

---

## 📚 Documentación

- **[Arquitectura](docs/ARQUITECTURA.md)** — Diseño técnico del sistema
- **[Instalación](docs/INSTALACION.md)** — Guía paso a paso
- **[API Reference](docs/API.md)** — Clases y métodos
- **[Ejemplos](docs/EJEMPLOS.md)** — Casos de uso reales
- **[Guía Técnica](docs/GUIA_TECNICA.md)** — Para instaladores

---

## 🧪 Testing

\\\ash
# Ejecutar todos los tests
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=src --cov-report=html

# Test específico
pytest tests/test_xlsx_adapter.py -v
\\\

**Estado actual:** ✅ 30/30 tests pasando

---

## 🗺️ Roadmap

- [x] Motor CPE base (v2.0)
- [x] XlsxAdapter — POS™ Excel
- [x] DbfAdapter — FoxPro legacy
- [x] SqlAdapter universal
- [x] YamlMapper — Configuración sin código
- [x] source_explorer — Herramienta de inspección
- [ ] Validación JSON vs XSD SUNAT
- [ ] Primer envío real a SUNAT
- [ ] Instaladores profesionales v3.0
- [ ] Plataforma CPE™ + License Server

---

## 🏢 Sistema DisateQ™

Este motor es parte del ecosistema **DisateQ™**:

1. **DisateQ POS™** — Punto de venta Excel (en desarrollo)
2. **Motor CPE™** — Este repositorio ✅
3. **Plataforma CPE™** — Servicio cloud + licencias (próximamente)

---

## 📄 Licencia

**Propietario** — DisateQ™ / @fhertejada™

Todos los derechos reservados. Este software es propiedad de DisateQ™ y no puede ser distribuido, modificado o utilizado sin autorización expresa.

---

## 👨‍💻 Autor

**Fernando Hernán Tejada**  
@fhertejada™ | DisateQ™

---

## 🆘 Soporte

Para soporte técnico o consultas comerciales:
- **Email:** soporte@disateq.com
- **GitHub Issues:** Para bugs y mejoras
- **Documentación:** [docs/](docs/)

---

**DisateQ™** — Soluciones empresariales para facturación electrónica
