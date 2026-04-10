# CLAUDE.md — DisateQ Bridge™

Proyecto: DisateQ Bridge™ — Motor de integración para facturación electrónica.
Conecta cualquier sistema legacy (FoxPro, ERP, Excel, SQL) con SUNAT
vía APIFAS, sin necesidad de migrar o reemplazar el sistema existente.
Organización: DISATEQ

## Ecosistema DisateQ

| Componente             | Rol                                      |
|------------------------|------------------------------------------|
| DisateQ Bridge™        | Motor local de integración (este repo)   |
| BridgeAPI              | API local FastAPI (supervisión/dashboard)|
| DisateQ Plataforma CPE | Plataforma web central DisateQ           |

## Estándar base

Sigue todas las reglas de `.standards/CLAUDE.md` sin excepción.
El estándar completo está en `.standards/STANDARD.md`.

## Reglas específicas de DisateQ Bridge™

### Principio rector
El ejecutable nunca se rompe. Cada cambio es aditivo.
El motor principal (readers → normalizer → txt_generator → sender)
no se modifica sin tests previos que confirmen comportamiento idéntico.

### Fuentes de datos (readers/)
- Interfaz abstracta `BaseReader` en `src/readers/base.py`
- Implementaciones: `dbf_reader.py`, `excel_reader.py`, `sql_reader.py`
- El motor NO sabe ni le importa el origen de los datos
- Primer cliente implementado: sistema farmacia FoxPro (DBF)

### Base de datos local (SQLite)
- SQLite en `D:\DisateQ\Bridge\bridge.db`
- Toda tabla incluye: `empresa_id` (multiempresa futuro)
- Sincronización con DisateQ Plataforma CPE via `txt_to_json.py`

### Comprobantes y envío
- Toda operación crítica es offline-first
- Nunca bloquear el flujo por falta de conexión
- TXT se guarda localmente antes de intentar enviar
- Si sin conexión: guardar en `enviados/` pendiente, reintentar automático

### Rutas en producción
- Directorio base: `D:\DisateQ\Bridge\`
- Config: `D:\DisateQ\Bridge\bridge_config.ini`
- Log: `D:\DisateQ\Bridge\bridge.log`
- Salida TXT: `D:\DisateQ\Bridge\enviados\`

### Nomenclatura
- Variables y funciones: snake_case en español
- Clases: PascalCase
- No usar nunca: "FFEE Platform", "CPE DisateQ", "ffee_farmacia" como nombre de producto

### Nombres de producto (SIEMPRE usar estos)
- Motor:         DisateQ Bridge™
- API local:     BridgeAPI
- Plataforma:    DisateQ Plataforma CPE
- Ejecutable:    DisateQBridge.exe
- Config:        bridge_config.ini
- Log:           bridge.log

## Repositorio

- GitHub: https://github.com/DisateQ/ffee-farmacia
- Plataforma: https://github.com/DisateQ/ffee-platform
- Estándar: https://github.com/DisateQ/standards
