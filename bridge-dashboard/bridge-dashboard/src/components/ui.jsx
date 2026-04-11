/**
 * ui.jsx
 * Componentes base del design system — DisateQ Bridge™
 */

import React from 'react'

// ── Badge de estado ───────────────────────────────────────
const BADGE_STYLES = {
  enviado:   { bg: 'var(--green-bg)',  color: 'var(--green)',  label: 'enviado'   },
  error:     { bg: 'var(--red-bg)',    color: 'var(--red)',    label: 'error'     },
  pendiente: { bg: 'var(--amber-bg)',  color: 'var(--amber)',  label: 'pendiente' },
  repetido:  { bg: 'var(--blue-bg)',   color: 'var(--blue)',   label: 'repetido'  },
  info:      { bg: 'var(--blue-bg)',   color: 'var(--blue)',   label: 'info'      },
  warn:      { bg: 'var(--amber-bg)',  color: 'var(--amber)',  label: 'warn'      },
}

export function Badge({ estado, style }) {
  const s = BADGE_STYLES[estado] || BADGE_STYLES.pendiente
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      fontSize: 10, fontFamily: 'var(--mono)', fontWeight: 500,
      padding: '3px 7px', borderRadius: 4, letterSpacing: '0.3px',
      background: s.bg, color: s.color,
      ...style,
    }}>
      {s.label}
    </span>
  )
}

// ── Tipo de comprobante ───────────────────────────────────
export function TipoPill({ tipo }) {
  const isF  = tipo === 'F'
  const isNC = tipo === 'NC'
  return (
    <span style={{
      fontSize: 9, fontFamily: 'var(--mono)', fontWeight: 500,
      padding: '2px 6px', borderRadius: 3, letterSpacing: '0.5px',
      background: isF  ? 'var(--blue-bg)'  :
                  isNC ? 'var(--amber-bg)' : 'var(--surface3)',
      color: isF  ? 'var(--blue)'  :
             isNC ? 'var(--amber)' : 'var(--ink3)',
    }}>
      {isF ? 'FACTURA' : isNC ? 'NOTA CRÉD.' : 'BOLETA'}
    </span>
  )
}

// ── Dot de conexión ───────────────────────────────────────
export function ConnDot({ online }) {
  return (
    <span style={{
      display: 'inline-block',
      width: 7, height: 7, borderRadius: '50%',
      background: online ? 'var(--green-mid)' : 'var(--red-mid)',
      boxShadow: online
        ? '0 0 0 2px var(--green-bg)'
        : '0 0 0 2px var(--red-bg)',
      flexShrink: 0,
    }} />
  )
}

// ── Tarjeta KPI ───────────────────────────────────────────
export function KpiCard({ label, value, sub, accentColor, delay = 0 }) {
  return (
    <div className="fade-up" style={{
      animationDelay: `${delay}ms`,
      background: 'var(--surface)',
      border: '0.5px solid var(--border2)',
      borderRadius: 'var(--radius-md)',
      padding: '14px 16px',
      position: 'relative', overflow: 'hidden',
    }}>
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 3,
        background: accentColor,
      }} />
      <div style={{ fontSize: 10, color: 'var(--ink3)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 6 }}>
        {label}
      </div>
      <div style={{ fontSize: 26, fontWeight: 500, fontFamily: 'var(--mono)', color: 'var(--ink)', letterSpacing: '-1px', lineHeight: 1 }}>
        {value}
      </div>
      {sub && (
        <div style={{ fontSize: 11, color: 'var(--ink3)', marginTop: 5, fontFamily: 'var(--mono)' }}>
          {sub}
        </div>
      )}
    </div>
  )
}

// ── Panel con header ──────────────────────────────────────
export function Panel({ title, actions, children, style }) {
  return (
    <div style={{
      background: 'var(--surface)',
      border: '0.5px solid var(--border2)',
      borderRadius: 'var(--radius-md)',
      overflow: 'hidden',
      ...style,
    }}>
      {(title || actions) && (
        <div style={{
          padding: '11px 16px',
          borderBottom: '0.5px solid var(--border)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          {title && (
            <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--ink)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              {title}
            </span>
          )}
          {actions && <div style={{ display: 'flex', gap: 6 }}>{actions}</div>}
        </div>
      )}
      {children}
    </div>
  )
}

// ── Botón ─────────────────────────────────────────────────
export function Btn({ children, onClick, variant = 'ghost', disabled, style }) {
  const base = {
    fontSize: 11, fontFamily: 'var(--sans)', fontWeight: 500,
    padding: '5px 11px', borderRadius: 'var(--radius-sm)',
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.5 : 1,
    transition: 'background 0.12s, color 0.12s',
    border: '0.5px solid var(--border2)',
    background: 'transparent', color: 'var(--ink2)',
  }
  const variants = {
    ghost:   {},
    primary: { background: 'var(--ink)', color: 'var(--surface)', border: 'none' },
    danger:  { borderColor: 'var(--red-mid)', color: 'var(--red)' },
    warning: { borderColor: 'var(--amber-mid)', color: 'var(--amber)' },
  }
  return (
    <button onClick={onClick} disabled={disabled}
      style={{ ...base, ...variants[variant], ...style }}>
      {children}
    </button>
  )
}

// ── Filtros de pestaña ────────────────────────────────────
export function FilterBar({ options, active, onChange }) {
  return (
    <div style={{ display: 'flex', gap: 4, padding: '8px 16px', borderBottom: '0.5px solid var(--border)', flexWrap: 'wrap' }}>
      {options.map(opt => (
        <button key={opt.value}
          onClick={() => onChange(opt.value)}
          style={{
            fontSize: 11, fontFamily: 'var(--sans)',
            padding: '4px 10px', borderRadius: 20,
            border: '0.5px solid var(--border2)',
            background: active === opt.value ? 'var(--ink)' : 'transparent',
            color:      active === opt.value ? 'var(--surface)' : 'var(--ink2)',
            cursor: 'pointer', transition: 'background 0.12s, color 0.12s',
            whiteSpace: 'nowrap',
          }}>
          {opt.label}
        </button>
      ))}
    </div>
  )
}

// ── Skeleton loader ───────────────────────────────────────
export function Skeleton({ w = '100%', h = 16, style }) {
  return (
    <div style={{
      width: w, height: h, borderRadius: 4,
      background: 'var(--surface3)',
      animation: 'pulse 1.4s ease-in-out infinite',
      ...style,
    }} />
  )
}

// ── Estado vacío ──────────────────────────────────────────
export function Empty({ message = 'Sin resultados' }) {
  return (
    <div style={{ padding: '40px 20px', textAlign: 'center', color: 'var(--ink3)', fontSize: 12 }}>
      {message}
    </div>
  )
}

// ── Error inline ──────────────────────────────────────────
export function InlineError({ message }) {
  if (!message) return null
  return (
    <div style={{
      padding: '10px 16px', fontSize: 12,
      color: 'var(--red)', background: 'var(--red-bg)',
      borderRadius: 'var(--radius-sm)',
    }}>
      ⚠ {message}
    </div>
  )
}
