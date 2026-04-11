/**
 * Dashboard.jsx
 * Página principal — KPIs del día + gráfico de envíos + actividad reciente
 * Datos reales desde BridgeAPI con polling cada 10s
 */

import React, { useMemo } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts'
import { useApi } from '../hooks/useApi.js'
import { getStatus, getLog } from '../lib/api.js'
import { KpiCard, Panel, Skeleton, InlineError } from '../components/ui.jsx'

// Genera datos de envíos por hora desde los eventos del log
function buildHourData(logItems) {
  const byHour = {}
  for (let h = 7; h <= 21; h++) byHour[h] = { enviados: 0, errores: 0 }

  logItems.forEach(ev => {
    if (!ev.created_at) return
    const h = new Date(ev.created_at).getHours()
    if (h < 7 || h > 21) return
    if (ev.tipo_evento === 'envio_ok' || ev.tipo_evento === 'reenvio_ok') byHour[h].enviados++
    if (ev.nivel === 'error') byHour[h].errores++
  })

  return Object.entries(byHour).map(([h, v]) => ({
    hora: String(h).padStart(2, '0'),
    ...v,
  }))
}

function fmt(n) { return n?.toLocaleString('es-PE') ?? '—' }
function fmtMonto(n) {
  if (n == null) return '—'
  return 'S/ ' + n.toLocaleString('es-PE', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

const NIVEL_COLOR = { info: 'var(--green-mid)', warn: 'var(--amber-mid)', error: 'var(--red-mid)' }

export default function Dashboard() {
  const { data: status, loading: lStatus, error: eStatus } =
    useApi(getStatus, { pollMs: 10_000 })

  const { data: logData, loading: lLog } =
    useApi(() => getLog({ limite: 200 }), { pollMs: 15_000 })

  const stats    = status?.stats_hoy
  const motorRUC = status?.motor?.ruc

  const hourData = useMemo(
    () => buildHourData(logData?.items ?? []),
    [logData]
  )

  const recentEvents = useMemo(
    () => (logData?.items ?? []).slice(0, 8),
    [logData]
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

      {eStatus && <InlineError message={`Sin conexión con BridgeAPI — ${eStatus}`} />}

      {/* ── KPIs ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0,1fr))', gap: 10 }}>
        <KpiCard
          label="Enviados hoy"
          value={lStatus ? '···' : fmt(stats?.enviados)}
          sub={stats ? `monto S/ ${(stats.total_monto ?? 0).toLocaleString('es-PE', { minimumFractionDigits: 0 })}` : ''}
          accentColor="var(--green-mid)"
          delay={0}
        />
        <KpiCard
          label="Errores"
          value={lStatus ? '···' : fmt(stats?.errores)}
          sub="revisar bandeja"
          accentColor="var(--red-mid)"
          delay={60}
        />
        <KpiCard
          label="Pendientes"
          value={lStatus ? '···' : fmt(stats?.pendientes)}
          sub="próx. ciclo 5 min"
          accentColor="var(--amber-mid)"
          delay={120}
        />
        <KpiCard
          label="Monto total"
          value={lStatus ? '···' : fmtMonto(stats?.total_monto)}
          sub={stats?.fecha ?? ''}
          accentColor="var(--blue-mid)"
          delay={180}
          style={{ fontSize: 20 }}
        />
      </div>

      {/* ── Gráfico + Actividad ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 14 }}>

        {/* Gráfico */}
        <Panel title="Envíos por hora">
          <div style={{ padding: '16px 16px 12px' }}>
            {lLog ? (
              <Skeleton h={160} />
            ) : (
              <ResponsiveContainer width="100%" height={160}>
                <BarChart data={hourData} barGap={2} barSize={14}
                  margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
                  <XAxis dataKey="hora" tick={{ fontSize: 10, fontFamily: 'var(--mono)', fill: 'var(--ink3)' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fontFamily: 'var(--mono)', fill: 'var(--ink3)' }} axisLine={false} tickLine={false} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ background: 'var(--surface)', border: '0.5px solid var(--border2)', borderRadius: 8, fontSize: 11, fontFamily: 'var(--mono)' }}
                    labelStyle={{ color: 'var(--ink2)' }}
                    cursor={{ fill: 'var(--surface3)' }}
                  />
                  <Bar dataKey="enviados" name="Enviados" fill="var(--green-mid)" radius={[3,3,0,0]} />
                  <Bar dataKey="errores"  name="Errores"  fill="var(--red-mid)"   radius={[3,3,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
            {/* Leyenda manual */}
            <div style={{ display: 'flex', gap: 14, marginTop: 8 }}>
              {[['var(--green-mid)', 'Enviados'], ['var(--red-mid)', 'Errores']].map(([color, label]) => (
                <span key={label} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 10, fontFamily: 'var(--mono)', color: 'var(--ink3)' }}>
                  <span style={{ width: 8, height: 8, borderRadius: 2, background: color, display: 'inline-block' }} />
                  {label}
                </span>
              ))}
            </div>
          </div>
        </Panel>

        {/* Actividad reciente */}
        <Panel title="Actividad reciente">
          <div style={{ overflowY: 'auto', maxHeight: 220 }}>
            {lLog ? (
              Array.from({ length: 5 }).map((_, i) => (
                <div key={i} style={{ padding: '10px 14px', borderBottom: '0.5px solid var(--border)' }}>
                  <Skeleton h={12} style={{ marginBottom: 4 }} />
                  <Skeleton h={10} w="60%" />
                </div>
              ))
            ) : recentEvents.length === 0 ? (
              <div style={{ padding: 20, textAlign: 'center', fontSize: 11, color: 'var(--ink3)' }}>
                Sin actividad hoy
              </div>
            ) : (
              recentEvents.map((ev, i) => (
                <div key={i} style={{
                  padding: '9px 14px',
                  borderBottom: '0.5px solid var(--border)',
                  display: 'flex', gap: 9, alignItems: 'flex-start',
                }}>
                  <span style={{
                    width: 7, height: 7, borderRadius: '50%', flexShrink: 0, marginTop: 4,
                    background: NIVEL_COLOR[ev.nivel] ?? 'var(--ink3)',
                  }} />
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--ink2)', lineHeight: 1.4 }}>
                      {ev.mensaje}
                    </div>
                    <div style={{ fontSize: 10, fontFamily: 'var(--mono)', color: 'var(--ink3)', marginTop: 2 }}>
                      {ev.created_at ? new Date(ev.created_at).toLocaleTimeString('es-PE', { hour12: false }) : ''}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </Panel>
      </div>

      {/* ── Info motor ── */}
      {status?.motor && (
        <Panel title="Motor CPE">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 0 }}>
            {[
              ['RUC',        status.motor.ruc],
              ['Razón social', status.motor.razon_social],
              ['Modalidad',  status.motor.modalidad],
              ['Modo',       status.motor.modo],
              ['Ruta DBF',   status.motor.ruta_dbf],
              ['APIFAS',     status.apifas?.online ? '✓ online' : '✗ offline'],
            ].map(([lbl, val]) => (
              <div key={lbl} style={{ padding: '10px 16px', borderBottom: '0.5px solid var(--border)', borderRight: '0.5px solid var(--border)' }}>
                <div style={{ fontSize: 10, color: 'var(--ink3)', marginBottom: 3, textTransform: 'uppercase', letterSpacing: '0.4px' }}>{lbl}</div>
                <div style={{ fontSize: 12, fontFamily: 'var(--mono)', color: 'var(--ink)', wordBreak: 'break-all' }}>{val || '—'}</div>
              </div>
            ))}
          </div>
        </Panel>
      )}
    </div>
  )
}
