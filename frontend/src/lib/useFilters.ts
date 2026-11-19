import { useCallback, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import type { Params } from '../api/client'
import { dayBoundIso, DEFAULT_TZ } from './format'
import { useAuth } from '../auth/AuthProvider'

/** Filtros en la URL (compartibles y con retorno del navegador). Cambiar un filtro vuelve a la página 1. */
export function useFilters(defaults: Record<string, string> = {}) {
  const [sp, setSp] = useSearchParams()
  const { user } = useAuth()
  const tz = user?.profile.timezone || DEFAULT_TZ

  const values = useMemo(() => {
    const o: Record<string, string> = { ...defaults }
    sp.forEach((v, k) => { o[k] = v })
    return o
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sp])

  const set = useCallback((patch: Record<string, string | number | null | undefined>, keepPage = false) => {
    setSp((prev) => {
      const n = new URLSearchParams(prev)
      for (const [k, v] of Object.entries(patch)) {
        if (v === null || v === undefined || v === '') n.delete(k); else n.set(k, String(v))
      }
      if (!keepPage && !('page' in patch)) n.delete('page')
      return n
    }, { replace: true })
  }, [setSp])

  const page = Number(values.page || 1)
  const pageSize = Number(values.page_size || 25)

  /** Parámetros listos para la API (rango o fechas, paginación, resto de filtros). */
  const params = useMemo((): Params => {
    const p: Params = {}
    for (const [k, v] of Object.entries(values)) {
      if (k === 'from' || k === 'to' || k === 'range') continue
      if (v !== '') p[k] = v
    }
    if (values.from || values.to) {
      if (values.from) p.date_from = dayBoundIso(values.from, false, tz)
      if (values.to) p.date_to = dayBoundIso(values.to, true, tz)
    } else if (values.range) p.range = values.range
    p.page = page; p.page_size = pageSize
    return p
  }, [values, page, pageSize, tz])

  return { values, set, page, pageSize, params, reset: () => setSp({}, { replace: true }) }
}
