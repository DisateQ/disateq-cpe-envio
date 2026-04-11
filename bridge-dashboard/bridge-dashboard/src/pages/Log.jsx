/**
 * Log.jsx
 * Log de auditoría completo con filtros por nivel
 */

import React, { useState, useCallback } from 'react'
import { useApi } from '../hooks/useApi.js'
import { getLog } from '../lib/api.js'
import { Panel, Badge, FilterBar, Skeleton, Empty, InlineError } from '../components/ui.jsx'

const FILTROS = [
  { value: 'todos', label: 'Todos'  },
  { value: 'info',  label: 'Info'   },
  { value: 'warn',  label: 'Warn'   },
  { value: 'error', label: 'Error'  },
]

export default function Log() {
  const [nivel, setNivel] = useState('todos')

  const fetcher = useCallback(
    () => getLog({ limite: 200, nivel: nivel === 'todos' ? undefined : nivel }),
    [nivel]
  )
  const { data, loading, error, refetch } = useApi(fetcher, {
    pollMs: 20_000, deps: [nivel],
  })

  const items = data?.items ?? []

  return (
    <Panel
      title={`Log de auditoría${items.length ? ` (${items.length})` : ''}`}
      actions={
        <button onClick={refetch} style={{
          fontSize: 11, padding: '4px 10px', border: '0.5px solid var(--border2)',
          borderRadius: 6, background: 'transparent', color: 'var(--ink2)', cursor: 'pointer',
        }}>
          {loading ? '···' : '↻'}
        </button>
      }
    >
      <FilterBar options={FILTROS} active={nivel} onChange={v => { setNivel(v) }} />
      {error && <InlineError message={error} />}

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
          <thead>
            <tr style={{ background: 'var(--surface2)' }}>
              {['Timestamp', 'Nivel', 'Evento', 'Mensaje'].map(h => (
                <th key={h} style={{
                  padding: '8px 12px', textAlign: 'left',
                  fontSize: 10, fontWeight: 500, color: 'var(--ink3)',
                  textTransform: 'uppercase', letterSpacing: '0.5px',
                  borderBottom: '0.5px solid var(--border2)',
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading && items.length === 0
              ? Array.from({ length: 10 }).map((_, i) => (
                  <tr key={i}>
                    {[120, 60, 100, '100%'].map((w, j) => (
                      <td key={j} style={{ padding: '10px 12px' }}>
                        <Skeleton h={12} w={typeof w === 'number' ? w : w} />
                      </td>
                    ))}
                  </tr>
                ))
              : items.length === 0
                ? <tr><td colSpan={4}><Empty message="Sin eventos" /></td></tr>
                : items.map((ev, i) => (
                    <tr key={i} style={{ borderBottom: '0.5px solid var(--border)' }}>
                      <td style={{ padding: '8px 12px', fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--ink3)', whiteSpace: 'nowrap' }}>
                        {ev.created_at
                          ? new Date(ev.created_at).toLocaleString('es-PE', { hour12: false })
                          : '—'}
                      </td>
                      <td style={{ padding: '8px 12px' }}>
                        <Badge estado={ev.nivel === 'warn' ? 'pendiente' : ev.nivel === 'error' ? 'error' : 'enviado'} />
                      </td>
                      <td style={{ padding: '8px 12px', fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--ink3)', whiteSpace: 'nowrap' }}>
                        {ev.tipo_evento}
                      </td>
                      <td style={{ padding: '8px 12px', fontSize: 12, color: 'var(--ink2)' }}>
                        {ev.mensaje}
                      </td>
                    </tr>
                  ))
            }
          </tbody>
        </table>
      </div>
    </Panel>
  )
}
