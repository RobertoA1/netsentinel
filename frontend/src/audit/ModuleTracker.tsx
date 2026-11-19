import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthProvider'
import { moduleAudit } from './tracker'
import { moduleOfRoute } from '../lib/labels'

/** Módulo de la ruta (p. ej. /ml/datos → ml_data). Las subpáginas del mismo módulo no generan eventos. */
export function moduleOfPath(pathname: string): string | null {
  return moduleOfRoute(pathname)
}

export function ModuleTracker() {
  const { pathname } = useLocation()
  const { user, can } = useAuth()

  useEffect(() => {
    const m = user ? moduleOfPath(pathname) : null
    moduleAudit.enter(m && can(`${m}:view`) && !user?.must_change_password ? m : null)
  }, [pathname, user, can])

  useEffect(() => {
    const onHide = () => moduleAudit.exit('close')
    const onShow = (e: PageTransitionEvent) => { if (e.persisted) moduleAudit.resume() }
    window.addEventListener('pagehide', onHide)
    window.addEventListener('pageshow', onShow)
    return () => {
      window.removeEventListener('pagehide', onHide)
      window.removeEventListener('pageshow', onShow)
    }
  }, [])

  return null
}
