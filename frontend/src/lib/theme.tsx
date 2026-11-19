import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'

export type ThemePref = 'system' | 'light' | 'dark'
const KEY = 'ns-theme'
const Ctx = createContext<{ pref: ThemePref; setPref: (t: ThemePref) => void; resolved: 'light' | 'dark' } | null>(null)

function initial(): ThemePref {
  try { const v = localStorage.getItem(KEY); if (v === 'light' || v === 'dark' || v === 'system') return v } catch { /* nada */ }
  return 'system'
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [pref, setPrefState] = useState<ThemePref>(initial)
  const [sys, setSys] = useState(() => window.matchMedia('(prefers-color-scheme: dark)').matches)

  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const h = (e: MediaQueryListEvent) => setSys(e.matches)
    mq.addEventListener('change', h)
    return () => mq.removeEventListener('change', h)
  }, [])

  const resolved = pref === 'system' ? (sys ? 'dark' : 'light') : pref
  useEffect(() => {
    document.documentElement.dataset.theme = resolved
    document.documentElement.style.colorScheme = resolved
  }, [resolved])

  const setPref = useCallback((t: ThemePref) => {
    setPrefState(t)
    try { localStorage.setItem(KEY, t) } catch { /* nada */ }
  }, [])

  const value = useMemo(() => ({ pref, setPref, resolved }), [pref, setPref, resolved])
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useTheme() {
  const c = useContext(Ctx)
  if (!c) throw new Error('useTheme fuera de ThemeProvider')
  return c
}
