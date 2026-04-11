/**
 * api.js
 * Cliente HTTP para BridgeAPI DisateQ Bridge™
 * Todas las llamadas van a /api/* que Vite proxea a http://localhost:8765
 */

const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

// ── Status ────────────────────────────────────────────────
export const getStatus = () => request('/status')

// ── Comprobantes ──────────────────────────────────────────
export const getComprobantes = (params = {}) => {
  const q = new URLSearchParams()
  if (params.fecha)   q.set('fecha',  params.fecha)
  if (params.estado)  q.set('estado', params.estado)
  if (params.limite)  q.set('limite', params.limite)
  if (params.offset)  q.set('offset', params.offset)
  return request(`/comprobantes${q.toString() ? '?' + q : ''}`)
}

export const getComprobante = (id) => request(`/comprobantes/${id}`)

export const getEnviosComprobante = (id) => request(`/comprobantes/${id}/envios`)

export const reenviarComprobante = (id) =>
  request(`/comprobantes/${id}/reenviar`, { method: 'POST' })

// ── Log ───────────────────────────────────────────────────
export const getLog = (params = {}) => {
  const q = new URLSearchParams()
  if (params.limite) q.set('limite', params.limite)
  if (params.nivel)  q.set('nivel',  params.nivel)
  return request(`/log${q.toString() ? '?' + q : ''}`)
}

// ── Config ────────────────────────────────────────────────
export const getConfig = () => request('/config')

export const updateConfig = (clave, valor) =>
  request(`/config/${clave}`, {
    method: 'PUT',
    body: JSON.stringify({ valor }),
  })
