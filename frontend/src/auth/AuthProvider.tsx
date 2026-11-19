import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { api, tokens, setUnauthorizedHandler } from '../api/client'
import type { LoginResponse, UserMe } from '../api/types'
import { moduleAudit } from '../audit/tracker'

interface AuthCtx {
  user: UserMe | null
  loading: boolean
  login: (username: string, password: string) => Promise<UserMe>
  logout: () => Promise<void>
  setUser: (u: UserMe) => void
  reload: () => Promise<void>
  can: (perm: string) => boolean
}
const Ctx = createContext<AuthCtx | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient()
  const [user, setUserState] = useState<UserMe | null>(null)
  const [loading, setLoading] = useState<boolean>(!!tokens.access)

  const clear = useCallback(() => {
    moduleAudit.reset()
    tokens.clear()
    setUserState(null)
    qc.clear()
  }, [qc])

  useEffect(() => { setUnauthorizedHandler(clear) }, [clear])

  useEffect(() => {
    if (!tokens.access) return
    api.get<UserMe>('/auth/me').then(setUserState).catch(() => tokens.clear()).finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (username: string, password: string) => {
    const r = await api.post<LoginResponse>('/auth/login', { username, password }, { auth: false })
    tokens.set(r.access_token, r.refresh_token)
    qc.clear()
    setUserState(r.user)
    return r.user
  }, [qc])

  const logout = useCallback(async () => {
    moduleAudit.exit('logout')
    try { await api.post('/auth/logout') } catch { /* la sesión local se cierra igual */ }
    clear()
  }, [clear])

  const reload = useCallback(async () => {
    setUserState(await api.get<UserMe>('/auth/me'))
  }, [])

  const perms = useMemo(() => new Set(user?.permissions ?? []), [user])
  const can = useCallback((p: string) => perms.has(p), [perms])

  const value = useMemo(() => ({ user, loading, login, logout, setUser: setUserState, reload, can }), [user, loading, login, logout, reload, can])
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useAuth() {
  const c = useContext(Ctx)
  if (!c) throw new Error('useAuth fuera de AuthProvider')
  return c
}

/** Atajo: permisos de un módulo. */
export function useCan(module: string) {
  const { can } = useAuth()
  return {
    view: can(`${module}:view`), create: can(`${module}:create`), update: can(`${module}:update`),
    delete: can(`${module}:delete`), export: can(`${module}:export`), execute: can(`${module}:execute`),
  }
}
