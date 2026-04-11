/**
 * useApi.js
 * Hook genérico para llamadas a BridgeAPI con:
 *   - Estado loading / error / data
 *   - Polling automático configurable
 *   - Refresco manual con refetch()
 */

import { useState, useEffect, useCallback, useRef } from 'react'

/**
 * @param {Function} fetcher  - función que retorna Promise (de lib/api.js)
 * @param {Object}   options
 *   @param {number}  options.pollMs    - ms entre polls. 0 = sin polling
 *   @param {boolean} options.immediate - ejecutar al montar (default: true)
 *   @param {Array}   options.deps      - deps adicionales que disparan refetch
 */
export function useApi(fetcher, { pollMs = 0, immediate = true, deps = [] } = {}) {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(immediate)
  const [error,   setError]   = useState(null)
  const timerRef  = useRef(null)
  const mountedRef = useRef(true)

  const fetch_ = useCallback(async () => {
    if (!mountedRef.current) return
    setLoading(true)
    setError(null)
    try {
      const result = await fetcher()
      if (mountedRef.current) {
        setData(result)
        setError(null)
      }
    } catch (e) {
      if (mountedRef.current) setError(e.message)
    } finally {
      if (mountedRef.current) setLoading(false)
    }
  }, [fetcher])         // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    mountedRef.current = true
    if (immediate) fetch_()
    if (pollMs > 0) {
      timerRef.current = setInterval(fetch_, pollMs)
    }
    return () => {
      mountedRef.current = false
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [pollMs, immediate, ...deps])   // eslint-disable-line react-hooks/exhaustive-deps

  return { data, loading, error, refetch: fetch_ }
}

/**
 * Variante para acciones manuales (reenviar, etc.)
 * Retorna [execute, { loading, error, data }]
 */
export function useAction(action) {
  const [state, setState] = useState({ loading: false, error: null, data: null })

  const execute = useCallback(async (...args) => {
    setState({ loading: true, error: null, data: null })
    try {
      const result = await action(...args)
      setState({ loading: false, error: null, data: result })
      return result
    } catch (e) {
      setState({ loading: false, error: e.message, data: null })
      throw e
    }
  }, [action])

  return [execute, state]
}
