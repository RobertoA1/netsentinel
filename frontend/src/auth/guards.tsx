import { Navigate, useLocation } from 'react-router-dom'
import type { ReactNode } from 'react'
import { useAuth } from './AuthProvider'
import { Forbidden } from '../pages/Forbidden'

export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  const loc = useLocation()
  if (loading) return <div className="state" role="status">Cargando sesión…</div>
  if (!user) return <Navigate to="/login" replace state={{ from: loc.pathname + loc.search }} />
  if (user.must_change_password && loc.pathname !== '/change-password') return <Navigate to="/change-password" replace />
  return <>{children}</>
}

export function RequirePerm({ perm, children }: { perm: string; children: ReactNode }) {
  const { can } = useAuth()
  if (!can(perm)) return <Forbidden />
  return <>{children}</>
}
