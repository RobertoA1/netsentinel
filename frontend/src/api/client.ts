// Cliente fetch tipado con refresh automático (una sola vez ante 401).
const BASE = '/api/v1'
const ACCESS = 'ns-access'
const REFRESH = 'ns-refresh'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

function read(k: string): string | null {
  try { return localStorage.getItem(k) } catch { return null }
}
function write(k: string, v: string | null) {
  try { if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, v) } catch { /* sin almacenamiento */ }
}

export const tokens = {
  get access() { return read(ACCESS) },
  get refresh() { return read(REFRESH) },
  set(a: string, r: string) { write(ACCESS, a); write(REFRESH, r) },
  clear() { write(ACCESS, null); write(REFRESH, null) },
}

type UnauthorizedHandler = () => void
let onUnauthorized: UnauthorizedHandler = () => {}
export function setUnauthorizedHandler(h: UnauthorizedHandler) { onUnauthorized = h }

let realFetch: typeof fetch = (...a) => fetch(...a)
export function setFetchImpl(f: typeof fetch) { realFetch = f }

let refreshing: Promise<boolean> | null = null
async function doRefresh(): Promise<boolean> {
  const rt = tokens.refresh
  if (!rt) return false
  try {
    const res = await realFetch(`${BASE}/auth/refresh`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: rt }),
    })
    if (!res.ok) return false
    const data = await res.json()
    tokens.set(data.access_token, data.refresh_token)
    return true
  } catch { return false }
}

export type Params = Record<string, string | number | boolean | null | undefined>
export function qs(params?: Params): string {
  if (!params) return ''
  const u = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === '') continue
    u.set(k, String(v))
  }
  const s = u.toString()
  return s ? `?${s}` : ''
}

async function errorOf(res: Response): Promise<ApiError> {
  let msg = `Error ${res.status}`
  try {
    const j = await res.json()
    if (typeof j?.detail === 'string') msg = j.detail
    else if (Array.isArray(j?.detail)) msg = j.detail.map((d: any) => d.msg ?? '').filter(Boolean).join('; ') || msg
  } catch { /* cuerpo no JSON */ }
  return new ApiError(res.status, msg)
}

async function raw(path: string, init: RequestInit & { auth?: boolean } = {}): Promise<Response> {
  const { auth = true, ...rest } = init
  const doFetch = () => {
    const headers = new Headers(rest.headers)
    if (rest.body && !(rest.body instanceof FormData) && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json')
    }
    const at = tokens.access
    if (auth && at) headers.set('Authorization', `Bearer ${at}`)
    return realFetch(`${BASE}${path}`, { ...rest, headers })
  }
  let res = await doFetch()
  if (res.status === 401 && auth && !path.startsWith('/auth/login') && !path.startsWith('/auth/refresh')) {
    refreshing ??= doRefresh().finally(() => { refreshing = null })
    if (await refreshing) res = await doFetch()
    if (res.status === 401) { tokens.clear(); onUnauthorized() }
  }
  if (!res.ok) throw await errorOf(res)
  return res
}

async function json<T>(path: string, init?: RequestInit & { auth?: boolean }): Promise<T> {
  const res = await raw(path, init)
  if (res.status === 204) return undefined as T
  const text = await res.text()
  return (text ? JSON.parse(text) : undefined) as T
}

const body = (b: unknown) => (b === undefined ? undefined : JSON.stringify(b))

export const api = {
  get: <T>(path: string, params?: Params) => json<T>(path + qs(params)),
  post: <T>(path: string, b?: unknown, opts?: { auth?: boolean }) => json<T>(path, { method: 'POST', body: body(b), ...opts }),
  put: <T>(path: string, b?: unknown) => json<T>(path, { method: 'PUT', body: body(b) }),
  patch: <T>(path: string, b?: unknown) => json<T>(path, { method: 'PATCH', body: body(b) }),
  del: <T = void>(path: string) => json<T>(path, { method: 'DELETE' }),
  upload: <T>(path: string, form: FormData) => json<T>(path, { method: 'POST', body: form }),
  /** Descarga de binario respetando Content-Disposition. */
  async download(path: string, b: unknown): Promise<{ blob: Blob; filename: string }> {
    const res = await raw(path, { method: 'POST', body: body(b) })
    const cd = res.headers.get('Content-Disposition') ?? ''
    const m = /filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i.exec(cd)
    const filename = m ? decodeURIComponent((m[1] ?? m[2]).trim()) : 'reporte'
    return { blob: await res.blob(), filename }
  },
}

/** Envío sin bloqueo para cierre de pestaña: keepalive. */
export function sendBeacon(path: string, payload: unknown) {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const at = tokens.access
  if (at) headers.Authorization = `Bearer ${at}`
  try {
    void realFetch(`${BASE}${path}`, { method: 'POST', headers, body: JSON.stringify(payload), keepalive: true }).catch(() => {})
  } catch { /* nada */ }
}
