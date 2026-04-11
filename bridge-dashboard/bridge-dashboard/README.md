# DisateQ Bridge™ — Dashboard

Dashboard React + Vite que consume BridgeAPI en `http://localhost:8765`.

## Estructura

```
bridge-dashboard/
├── index.html
├── vite.config.js        ← proxy /api → localhost:8765
├── package.json
└── src/
    ├── main.jsx
    ├── App.jsx            ← router (4 páginas)
    ├── index.css          ← tokens de diseño (light + dark)
    ├── lib/
    │   └── api.js         ← cliente HTTP hacia BridgeAPI
    ├── hooks/
    │   └── useApi.js      ← hook con polling + useAction
    ├── components/
    │   ├── ui.jsx         ← Badge, KpiCard, Panel, Btn, etc.
    │   └── Layout.jsx     ← sidebar + topbar + statusbar
    └── pages/
        ├── Dashboard.jsx  ← KPIs + gráfico recharts + actividad
        ├── Comprobantes.jsx ← tabla paginada + modal + reenvío
        ├── Log.jsx        ← auditoría con filtros por nivel
        └── Config.jsx     ← config Bridge (editable) + motor (solo lectura)
```

## Arranque

```bash
# 1. Tener BridgeAPI corriendo en :8765
uvicorn bridge_api:app --host 0.0.0.0 --port 8765 --reload

# 2. Instalar dependencias
cd bridge-dashboard
npm install

# 3. Dev server (proxy automático hacia :8765)
npm run dev
# → http://localhost:5173
```

## Build de producción

```bash
npm run build
# Genera dist/ — servir con cualquier servidor estático
```

## Polling

| Componente     | Intervalo |
|----------------|-----------|
| Status (topbar)| 15 s      |
| Dashboard KPIs | 10 s      |
| Log actividad  | 15 s      |
| Comprobantes   | 20 s      |
| Log página     | 20 s      |

## Dependencias

- React 18
- Vite 5
- Recharts (gráfico de barras)
- Sin UI kit externo — design system propio con CSS variables
