/**
 * Comprobantes.jsx
 * Bandeja completa — filtros, tabla paginada, modal de detalle y reenvío
 * Datos reales desde BridgeAPI con polling cada 20s
 */

import React, { useState, useCallback } from 'react'
import { useApi, useAction } from '../hooks/useApi.js'
import { getComprobantes, getEnviosComprobante, reenviarComprobante } from '../lib/api.js'
import {
  Panel, Badge, TipoPill, FilterBar, Btn,
  Skeleton, Empty, InlineError,
} from '../components/ui.jsx'

const PAGE_SIZE = 50

const FILTROS = [
  { value: 'todos',     label: 'Todos'       },
  { value: 'enviado',   label: 'Enviados'    },
  { value: 'error',     label: 'Errores'     },
  { value: 'pendiente', label: 'Pendientes'  },
  { value: 'repetido',  label: 'Repetidos'   },
]

function pad8(n) { return String(n).padStart(8, '0') }

export default function Comprobantes() {
  const [filtro,  setFiltro]  = useState('todos')
  const [offset,  setOffset]  = useState(0)
  const [selected, setSelected] = useState(null)  // comprobante seleccionado para modal

  const fetcher = useCallback(
    () => getComprobantes({
      estado:  filtro === 'todos' ? undefined : filtro,
      limite:  PAGE_SIZE,
      offset,
    }),
    [filtro, offset]
  )

  const { data, loading, error, refetch } = useApi(fetcher, {
    pollMs: 20_000,
    deps: [filtro, offset],
  })

  const items = data?.items ?? []
  const total = data?.total ?? 0

  function cambiarFiltro(v) {
    setFiltro(v)
    setOffset(0)
  }

  return (
    <>
      <Panel
        title={`Comprobantes${total ? ` (${total})` : ''}`}
        actions={
          <Btn onClick={refetch} disabled={loading}>
            {loading ? '···' : '↻ Actualizar'}
          </Btn>
        }
      >
        <FilterBar options={FILTROS} active={filtro} onChange={cambiarFiltro} />

        {error && <InlineError message={error} />}

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
            <thead>
              <tr style={{ background: 'var(--surface2)' }}>
                {['Archivo', 'Tipo', 'Cliente', 'Fecha', 'Total', 'Estado', ''].map(h => (
                  <th key={h} style={{
                    padding: '8px 12px', textAlign: h === 'Total' ? 'right' : 'left',
                    fontSize: 10, fontWeight: 500, color: 'var(--ink3)',
                    textTransform: 'uppercase', letterSpacing: '0.5px',
                    borderBottom: '0.5px solid var(--border2)',
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading && items.length === 0
                ? Array.from({ length: 8 }).map((_, i) => (
                    <tr key={i}>
                      {Array.from({ length: 7 }).map((_, j) => (
                        <td key={j} style={{ padding: '10px 12px' }}>
                          <Skeleton h={12} />
                        </td>
                      ))}
                    </tr>
                  ))
                : items.length === 0
                  ? <tr><td colSpan={7}><Empty message="Sin comprobantes para este filtro" /></td></tr>
                  : items.map(comp => (
                      <CompRow
                        key={comp.id}
                        comp={comp}
                        onSelect={() => setSelected(comp)}
                      />
                    ))
              }
            </tbody>
          </table>
        </div>

        {/* Paginación */}
        {total > PAGE_SIZE && (
          <div style={{
            padding: '10px 16px', borderTop: '0.5px solid var(--border)',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            fontSize: 11, color: 'var(--ink3)', fontFamily: 'var(--mono)',
          }}>
            <span>{offset + 1}–{Math.min(offset + PAGE_SIZE, total)} de {total}</span>
            <div style={{ display: 'flex', gap: 6 }}>
              <Btn disabled={offset === 0} onClick={() => setOffset(o => Math.max(0, o - PAGE_SIZE))}>
                ← Anterior
              </Btn>
              <Btn disabled={offset + PAGE_SIZE >= total} onClick={() => setOffset(o => o + PAGE_SIZE)}>
                Siguiente →
              </Btn>
            </div>
          </div>
        )}
      </Panel>

      {/* Modal detalle */}
      {selected && (
        <Modal comp={selected} onClose={() => setSelected(null)} onReenviado={refetch} />
      )}
    </>
  )
}

// ── Fila de tabla ─────────────────────────────────────────
function CompRow({ comp, onSelect }) {
  const nombre_corto = `${comp.serie}-${pad8(comp.numero)}`
  const canReenviar  = comp.estado === 'error' || comp.estado === 'pendiente'

  return (
    <tr style={{
      borderBottom: '0.5px solid var(--border)',
      transition: 'background 0.1s',
      cursor: 'pointer',
    }}
      onMouseEnter={e => e.currentTarget.style.background = 'var(--surface2)'}
      onMouseLeave={e => e.currentTarget.style.background = ''}
    >
      <td style={{ padding: '9px 12px', fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--ink)' }}>
        {nombre_corto}
      </td>
      <td style={{ padding: '9px 12px' }}>
        <TipoPill tipo={comp.tipo_comprobante} />
      </td>
      <td style={{ padding: '9px 12px', color: 'var(--ink3)', fontSize: 11, maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {comp.cliente_denominacion}
      </td>
      <td style={{ padding: '9px 12px', color: 'var(--ink3)', fontSize: 11, fontFamily: 'var(--mono)' }}>
        {comp.fecha_emision}
      </td>
      <td style={{ padding: '9px 12px', textAlign: 'right', fontFamily: 'var(--mono)', fontSize: 12, fontWeight: 500, color: 'var(--ink)' }}>
        S/ {Number(comp.total).toFixed(2)}
      </td>
      <td style={{ padding: '9px 12px' }}>
        <Badge estado={comp.estado} />
      </td>
      <td style={{ padding: '9px 12px' }}>
        <Btn
          onClick={onSelect}
          variant={canReenviar ? 'warning' : 'ghost'}
          style={{ fontSize: 10 }}
        >
          {canReenviar ? 'Reenviar' : 'Ver'}
        </Btn>
      </td>
    </tr>
  )
}

// ── Modal de detalle ──────────────────────────────────────
function Modal({ comp, onClose, onReenviado }) {
  const canReenviar = comp.estado === 'error' || comp.estado === 'pendiente'

  const { data: enviosData, loading: lEnvios } =
    useApi(() => getEnviosComprobante(comp.id))

  const [reenviar, { loading: lReenvio, error: eReenvio }] =
    useAction(useCallback(() => reenviarComprobante(comp.id), [comp.id]))

  async function handleReenviar() {
    try {
      await reenviar()
      onReenviado?.()
      onClose()
    } catch { /* error ya en state */ }
  }

  return (
    /* Overlay faux-viewport */
    <div style={{
      position: 'fixed', inset: 0, zIndex: 200,
      background: 'rgba(0,0,0,0.45)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }} onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="fade-up" style={{
        background: 'var(--surface)',
        border: '0.5px solid var(--border2)',
        borderRadius: 'var(--radius-lg)',
        width: 460, maxWidth: '95vw',
        maxHeight: '85vh', overflow: 'hidden',
        display: 'flex', flexDirection: 'column',
      }}>
        {/* Header */}
        <div style={{
          padding: '13px 18px', borderBottom: '0.5px solid var(--border)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--ink)', fontFamily: 'var(--mono)' }}>
            {comp.serie}-{pad8(comp.numero)}
          </span>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--ink3)', fontSize: 18, lineHeight: 1 }}>
            ×
          </button>
        </div>

        {/* Body */}
        <div style={{ overflowY: 'auto', flex: 1, padding: '4px 0' }}>
          {/* Datos del comprobante */}
          {[
            ['Archivo',        comp.nombre_archivo],
            ['Tipo',           comp.tipo_comprobante === 'F' ? 'Factura' : comp.tipo_comprobante === 'NC' ? 'Nota de crédito' : 'Boleta'],
            ['Fecha emisión',  comp.fecha_emision],
            ['Cliente',        comp.cliente_denominacion],
            ['Nro. documento', comp.cliente_num_doc],
            ['Base gravada',   `S/ ${Number(comp.total_gravada ?? 0).toFixed(2)}`],
            ['IGV',            `S/ ${Number(comp.total_igv ?? 0).toFixed(2)}`],
            ['Total',          `S/ ${Number(comp.total).toFixed(2)}`],
            ['Forma de pago',  comp.forma_pago],
            ['Estado',         null],   // badge especial
            ['Origen',         comp.origen],
          ].map(([lbl, val]) => (
            <div key={lbl} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '8px 18px', borderBottom: '0.5px solid var(--border)',
              fontSize: 12,
            }}>
              <span style={{ color: 'var(--ink3)' }}>{lbl}</span>
              {val === null
                ? <Badge estado={comp.estado} />
                : <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--ink)', fontWeight: 500, textAlign: 'right', maxWidth: 260, wordBreak: 'break-all' }}>{val}</span>
              }
            </div>
          ))}

          {/* Historial de envíos */}
          <div style={{ padding: '10px 18px 4px', fontSize: 10, color: 'var(--ink3)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 600 }}>
            Historial de envíos
          </div>
          {lEnvios ? (
            <div style={{ padding: '8px 18px' }}><Skeleton h={12} /></div>
          ) : enviosData?.envios?.length === 0 ? (
            <div style={{ padding: '8px 18px', fontSize: 11, color: 'var(--ink3)' }}>Sin intentos registrados</div>
          ) : (
            enviosData?.envios?.map((env, i) => (
              <div key={i} style={{
                padding: '8px 18px', borderBottom: '0.5px solid var(--border)',
                display: 'flex', justifyContent: 'space-between', fontSize: 11,
              }}>
                <span style={{ fontFamily: 'var(--mono)', color: 'var(--ink3)' }}>
                  Intento {env.intento} · {env.modalidad} · {env.duracion_ms ?? '—'}ms
                </span>
                <Badge estado={env.resultado === 'enviado' ? 'enviado' : 'error'} />
              </div>
            ))
          )}

          {eReenvio && <InlineError message={eReenvio} />}
        </div>

        {/* Footer */}
        <div style={{
          padding: '11px 18px', borderTop: '0.5px solid var(--border)',
          display: 'flex', gap: 8, justifyContent: 'flex-end',
        }}>
          <Btn onClick={onClose}>Cerrar</Btn>
          {canReenviar && (
            <Btn variant="primary" onClick={handleReenviar} disabled={lReenvio}>
              {lReenvio ? 'Enviando···' : 'Reenviar a APIFAS'}
            </Btn>
          )}
        </div>
      </div>
    </div>
  )
}
