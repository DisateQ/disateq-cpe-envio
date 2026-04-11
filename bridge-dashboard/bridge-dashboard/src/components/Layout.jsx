/**
 * Layout.jsx
 * Shell principal — sidebar + topbar + área de contenido
 */

import React, { useState, useEffect } from 'react'
import { ConnDot } from './ui.jsx'
import { getStatus } from '../lib/api.js'

const NAV = [
  { id: 'dashboard',     label: 'Dashboard',      icon: IconDashboard  },
  { id: 'comprobantes',  label: 'Comprobantes',   icon: IconTable      },
  { id: 'log',           label: 'Log auditoría',  icon: IconLog        },
  { id: 'config',        label: 'Configuración',  icon: IconConfig     },
]

export default function Layout({ page, onNavigate, children }) {
  const [apifasOnline, setApifasOnline] = useState(null)
  const [motorInfo,    setMotorInfo]    = useState(null)
  const [clock,        setClock]        = useState('')

  // Reloj
  useEffect(() => {
    const tick = () => {
      const n = new Date()
      setClock(n.toLocaleTimeString('es-PE', { hour12: false }))
    }
    tick()
    const t = setInterval(tick, 1000)
    return () => clearInterval(t)
  }, [])

  // Polling de status cada 15s
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await getStatus()
        setApifasOnline(data.apifas?.online ?? false)
        setMotorInfo(data.motor)
      } catch {
        setApifasOnline(false)
      }
    }
    fetchStatus()
    const t = setInterval(fetchStatus, 15_000)
    return () => clearInterval(t)
  }, [])

  return (
    <div style={{ display: 'flex', height: '100vh', background: 'var(--bg)', overflow: 'hidden' }}>

      {/* ── SIDEBAR ── */}
      <aside style={{
        width: 'var(--sidebar-w)', flexShrink: 0,
        background: 'var(--surface)',
        borderRight: '0.5px solid var(--border2)',
        display: 'flex', flexDirection: 'column',
      }}>
        {/* Logo */}
        <div style={{
          height: 'var(--topbar-h)',
          borderBottom: '0.5px solid var(--border)',
          display: 'flex', alignItems: 'center', gap: 10,
          padding: '0 16px', flexShrink: 0,
        }}>
          <LogoMark />
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--ink)', letterSpacing: '-0.2px' }}>
              Bridge™
            </div>
            <div style={{ fontSize: 10, fontFamily: 'var(--mono)', color: 'var(--ink3)' }}>
              v2.0 · CPE
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav style={{ flex: 1, padding: '10px 8px', overflowY: 'auto' }}>
          {NAV.map(item => (
            <NavItem key={item.id} item={item} active={page === item.id} onClick={() => onNavigate(item.id)} />
          ))}
        </nav>

        {/* Motor info */}
        <div style={{
          padding: '12px 14px',
          borderTop: '0.5px solid var(--border)',
          fontSize: 10, fontFamily: 'var(--mono)', color: 'var(--ink3)',
        }}>
          {motorInfo ? (
            <>
              <div style={{ color: 'var(--ink2)', fontWeight: 500, marginBottom: 2, fontSize: 11 }}>
                {motorInfo.razon_social || '—'}
              </div>
              <div>RUC {motorInfo.ruc || '—'}</div>
              <div style={{ marginTop: 2 }}>{motorInfo.modalidad} · {motorInfo.modo}</div>
            </>
          ) : (
            <div>Conectando...</div>
          )}
        </div>
      </aside>

      {/* ── MAIN ── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

        {/* Topbar */}
        <header style={{
          height: 'var(--topbar-h)', flexShrink: 0,
          background: 'var(--surface)',
          borderBottom: '0.5px solid var(--border2)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '0 20px',
        }}>
          <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--ink)' }}>
            {NAV.find(n => n.id === page)?.label ?? 'Dashboard'}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            {/* Badge APIFAS */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: 5,
              fontSize: 10, fontFamily: 'var(--mono)',
              padding: '4px 9px', borderRadius: 20,
              border: '0.5px solid var(--border2)',
              background: 'var(--surface2)',
              color: 'var(--ink2)',
            }}>
              <ConnDot online={apifasOnline} />
              {apifasOnline === null ? 'comprobando...' : apifasOnline ? 'APIFAS online' : 'APIFAS offline'}
            </div>
            {/* Reloj */}
            <span style={{ fontSize: 11, fontFamily: 'var(--mono)', color: 'var(--ink3)' }}>
              {clock}
            </span>
          </div>
        </header>

        {/* Contenido */}
        <main style={{ flex: 1, overflowY: 'auto', padding: 20 }}>
          {children}
        </main>

        {/* Status bar */}
        <footer style={{
          height: 28, flexShrink: 0,
          background: 'var(--surface)',
          borderTop: '0.5px solid var(--border2)',
          display: 'flex', alignItems: 'center',
          padding: '0 20px', gap: 20,
          fontSize: 10, fontFamily: 'var(--mono)', color: 'var(--ink3)',
        }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <ConnDot online={apifasOnline} />
            motor activo
          </span>
          <span>bridge_api :8765</span>
          {motorInfo && <span>{motorInfo.ruc}</span>}
        </footer>
      </div>
    </div>
  )
}

function NavItem({ item, active, onClick }) {
  const Icon = item.icon
  return (
    <button onClick={onClick} style={{
      width: '100%', display: 'flex', alignItems: 'center', gap: 9,
      padding: '8px 10px', borderRadius: 'var(--radius-sm)',
      border: 'none', cursor: 'pointer',
      background: active ? 'var(--surface3)' : 'transparent',
      color: active ? 'var(--ink)' : 'var(--ink3)',
      fontSize: 13, fontWeight: active ? 500 : 400,
      fontFamily: 'var(--sans)',
      transition: 'background 0.12s, color 0.12s',
      marginBottom: 2,
    }}>
      <Icon size={15} />
      {item.label}
    </button>
  )
}

// ── Íconos SVG inline ─────────────────────────────────────

function LogoMark() {
  return (
    <div style={{
      width: 28, height: 28, borderRadius: 6,
      background: 'var(--ink)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
    }}>
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <rect x="1" y="1" width="5" height="5" rx="1" fill="white" opacity="0.9"/>
        <rect x="8" y="1" width="5" height="5" rx="1" fill="white" opacity="0.55"/>
        <rect x="1" y="8" width="5" height="5" rx="1" fill="white" opacity="0.55"/>
        <rect x="8" y="8" width="5" height="5" rx="1" fill="white" opacity="0.25"/>
      </svg>
    </div>
  )
}

function IconDashboard({ size = 16 }) {
  return <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.3">
    <rect x="1" y="1" width="6" height="6" rx="1"/>
    <rect x="9" y="1" width="6" height="6" rx="1"/>
    <rect x="1" y="9" width="6" height="6" rx="1"/>
    <rect x="9" y="9" width="6" height="6" rx="1"/>
  </svg>
}

function IconTable({ size = 16 }) {
  return <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.3">
    <rect x="1" y="1" width="14" height="14" rx="2"/>
    <line x1="1" y1="5" x2="15" y2="5"/>
    <line x1="6" y1="5" x2="6" y2="15"/>
  </svg>
}

function IconLog({ size = 16 }) {
  return <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.3">
    <path d="M2 4h12M2 8h8M2 12h10"/>
  </svg>
}

function IconConfig({ size = 16 }) {
  return <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.3">
    <circle cx="8" cy="8" r="2.5"/>
    <path d="M8 1v2M8 13v2M1 8h2M13 8h2M3.05 3.05l1.41 1.41M11.54 11.54l1.41 1.41M3.05 12.95l1.41-1.41M11.54 4.46l1.41-1.41"/>
  </svg>
}
