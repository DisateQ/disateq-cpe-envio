/**
 * Config.jsx
 * Configuración del Bridge + motor (lectura + edición de claves editables)
 */

import React, { useState } from 'react'
import { useApi, useAction } from '../hooks/useApi.js'
import { getConfig, updateConfig } from '../lib/api.js'
import { Panel, Btn, InlineError, Skeleton } from '../components/ui.jsx'

// Claves del Bridge que el usuario puede editar desde el dashboard
const EDITABLES = new Set([
  'watcher_activo',
  'watcher_intervalo',
  'log_nivel',
  'max_registros_log',
])

export default function Config() {
  const { data, loading, error, refetch } = useApi(getConfig)
  const [editando, setEditando] = useState(null)   // { clave, valor }
  const [saved,    setSaved]    = useState(null)   // clave recién guardada

  const [guardar, { loading: lGuardar, error: eGuardar }] =
    useAction(({ clave, valor }) => updateConfig(clave, valor))

  async function handleGuardar() {
    if (!editando) return
    await guardar(editando)
    setSaved(editando.clave)
    setEditando(null)
    refetch()
    setTimeout(() => setSaved(null), 2500)
  }

  const bridgeCfg = data?.bridge ?? {}
  const motorCfg  = data?.motor  ?? {}

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {error && <InlineError message={error} />}

      {/* Bridge config */}
      <Panel title="Configuración Bridge" actions={
        <Btn onClick={refetch} disabled={loading}>{loading ? '···' : '↻'}</Btn>
      }>
        {loading
          ? Array.from({ length: 6 }).map((_, i) => (
              <div key={i} style={{ padding: '10px 16px', borderBottom: '0.5px solid var(--border)' }}>
                <Skeleton h={12} />
              </div>
            ))
          : Object.entries(bridgeCfg).map(([clave, valor]) => {
              const isEditable = EDITABLES.has(clave)
              const justSaved  = saved === clave
              return (
                <div key={clave} style={{
                  padding: '10px 16px', borderBottom: '0.5px solid var(--border)',
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
                }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 10, color: 'var(--ink3)', textTransform: 'uppercase', letterSpacing: '0.4px', marginBottom: 2 }}>
                      {clave}
                    </div>
                    {editando?.clave === clave ? (
                      <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                        <input
                          autoFocus
                          value={editando.valor}
                          onChange={e => setEditando({ ...editando, valor: e.target.value })}
                          onKeyDown={e => { if (e.key === 'Enter') handleGuardar(); if (e.key === 'Escape') setEditando(null); }}
                          style={{
                            fontSize: 12, fontFamily: 'var(--mono)',
                            padding: '4px 8px', borderRadius: 5,
                            border: '0.5px solid var(--border2)',
                            background: 'var(--surface2)', color: 'var(--ink)',
                            width: 200,
                          }}
                        />
                        <Btn variant="primary" onClick={handleGuardar} disabled={lGuardar} style={{ fontSize: 10 }}>
                          {lGuardar ? '···' : 'Guardar'}
                        </Btn>
                        <Btn onClick={() => setEditando(null)} style={{ fontSize: 10 }}>Cancelar</Btn>
                      </div>
                    ) : (
                      <div style={{ fontSize: 12, fontFamily: 'var(--mono)', color: justSaved ? 'var(--green)' : 'var(--ink)' }}>
                        {justSaved ? '✓ guardado' : valor}
                      </div>
                    )}
                  </div>
                  {isEditable && editando?.clave !== clave && (
                    <Btn onClick={() => setEditando({ clave, valor })} style={{ fontSize: 10 }}>
                      Editar
                    </Btn>
                  )}
                </div>
              )
            })
        }
        {eGuardar && <InlineError message={eGuardar} />}
      </Panel>

      {/* Motor config (solo lectura) */}
      <Panel title="Configuración motor (ffee_config.ini)">
        <div style={{ padding: '8px 16px 4px', fontSize: 11, color: 'var(--ink3)' }}>
          Solo lectura — editar directamente en D:\FFEESUNAT\CPE DisateQ\ffee_config.ini
        </div>
        {loading
          ? Array.from({ length: 4 }).map((_, i) => (
              <div key={i} style={{ padding: '10px 16px', borderBottom: '0.5px solid var(--border)' }}>
                <Skeleton h={12} />
              </div>
            ))
          : Object.entries(motorCfg).map(([clave, valor]) => (
              <div key={clave} style={{
                padding: '9px 16px', borderBottom: '0.5px solid var(--border)',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              }}>
                <span style={{ fontSize: 10, color: 'var(--ink3)', fontFamily: 'var(--mono)', textTransform: 'uppercase', letterSpacing: '0.3px' }}>
                  {clave}
                </span>
                <span style={{ fontSize: 11, fontFamily: 'var(--mono)', color: 'var(--ink2)', maxWidth: 300, textAlign: 'right', wordBreak: 'break-all' }}>
                  {valor || '—'}
                </span>
              </div>
            ))
        }
      </Panel>
    </div>
  )
}
