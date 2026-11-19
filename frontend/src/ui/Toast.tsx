import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'

interface T { id: number; msg: string; kind: 'ok' | 'err' }
const Ctx = createContext<{ ok: (m: string) => void; err: (m: string) => void } | null>(null)
let seq = 0

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<T[]>([])
  const push = useCallback((msg: string, kind: T['kind']) => {
    const id = ++seq
    setItems((x) => [...x, { id, msg, kind }])
    setTimeout(() => setItems((x) => x.filter((i) => i.id !== id)), kind === 'err' ? 7000 : 4000)
  }, [])
  const api = useMemo(() => ({ ok: (m: string) => push(m, 'ok'), err: (m: string) => push(m, 'err') }), [push])
  return (
    <Ctx.Provider value={api}>
      {children}
      <div className="toasts" role="status" aria-live="polite">
        {items.map((t) => <div key={t.id} className={`toast ${t.kind === 'err' ? 'err' : ''}`}>{t.msg}</div>)}
      </div>
    </Ctx.Provider>
  )
}
export function useToast() {
  const c = useContext(Ctx)
  if (!c) throw new Error('useToast fuera de ToastProvider')
  return c
}
