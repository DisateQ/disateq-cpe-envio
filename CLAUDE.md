# CLAUDE.md — FFEE Farmacia

Proyecto: Sistema de gestión para farmacias — cliente
del FFEE Platform. Módulo de punto de venta, stock
e integración con la plataforma CPE.
Organización: DISATEQ

## Estándar base

Sigue todas las reglas de `.standards/CLAUDE.md` sin excepción.
El estándar completo está en `.standards/STANDARD.md`.

## Reglas específicas de FFEE Farmacia

### Base de datos local (SQLite)
- Usar SQLite para operación offline en el POS
- UUID generado en la aplicación como TEXT
- Toda tabla incluye: `empresa_id`, `local_id`, `nodo_id`
- Sincronización con servidor via `outbox_events`

### Ventas y comprobantes
- Toda venta genera un UUID interno antes de enviarse
- El correlativo (serie-número) se genera localmente
- Si hay conexión: enviar inmediatamente al FFEE Platform
- Si no hay conexión: guardar en outbox local, enviar después
- Nunca bloquear la venta por falta de conexión

### Stock
- Fuente de verdad: servidor local FFEE Platform
- Descuento de stock: inmediato en local, reconciliación posterior
- Permitir stock negativo con registro de advertencia

### Sincronización
- Outbox local para todas las operaciones críticas
- Reintentos automáticos cada 5 minutos
- Conflictos resueltos por timestamp del servidor

### Stack tecnológico
- Backend: PHP 8.x
- Base de datos local: SQLite
- Base de datos servidor: PostgreSQL (via FFEE Platform)
- Interfaz: adaptada para pantalla táctil y teclado

### Nomenclatura
- Usar snake_case en español
- Ejemplos: `ventas`, `items_venta`, `productos`,
  `clientes`, `movimientos_stock`

## Repositorio

- GitHub: https://github.com/DisateQ/ffee-farmacia
- Plataforma: https://github.com/DisateQ/ffee-platform
- Estándar: https://github.com/DisateQ/standards