import { useAuth } from '../auth/AuthProvider'

const LOCALE = 'es-PE'
export const DEFAULT_TZ = 'America/Lima'

const nf = new Intl.NumberFormat(LOCALE)
const nf1 = new Intl.NumberFormat(LOCALE, { maximumFractionDigits: 1 })
const nf2 = new Intl.NumberFormat(LOCALE, { maximumFractionDigits: 2 })

export const num = (n: number | null | undefined) => (n == null ? '—' : nf.format(n))
export const dec = (n: number | null | undefined, d = 1) => (n == null ? '—' : d === 1 ? nf1.format(n) : d === 2 ? nf2.format(n) : n.toFixed(d))
export const pct = (n: number | null | undefined, d = 0) => (n == null ? '—' : `${new Intl.NumberFormat(LOCALE, { maximumFractionDigits: d }).format(n)} %`)
export const ratioPct = (r: number | null | undefined, d = 0) => (r == null ? '—' : pct(r * 100, d))

export function bytes(n: number | null | undefined): string {
  if (n == null) return '—'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let v = Math.abs(n), i = 0
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i++ }
  const s = i === 0 ? nf.format(Math.round(v)) : new Intl.NumberFormat(LOCALE, { maximumFractionDigits: v >= 100 ? 0 : 1 }).format(v)
  return `${n < 0 ? '-' : ''}${s} ${units[i]}`
}

export function duration(sec: number | null | undefined): string {
  if (sec == null) return '—'
  if (sec < 1) return `${Math.round(sec * 1000)} ms`
  if (sec < 60) return `${dec(sec, 1)} s`
  const m = Math.floor(sec / 60), s = Math.round(sec % 60)
  if (m < 60) return s ? `${m} min ${s} s` : `${m} min`
  const h = Math.floor(m / 60), mm = m % 60
  if (h < 24) return mm ? `${h} h ${mm} min` : `${h} h`
  const d = Math.floor(h / 24), hh = h % 24
  return hh ? `${d} d ${hh} h` : `${d} d`
}

export function dateFmt(tz: string) {
  const full = new Intl.DateTimeFormat(LOCALE, { timeZone: tz, day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
  const short = new Intl.DateTimeFormat(LOCALE, { timeZone: tz, day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', hour12: false })
  const day = new Intl.DateTimeFormat(LOCALE, { timeZone: tz, day: '2-digit', month: 'short', year: 'numeric' })
  const hm = new Intl.DateTimeFormat(LOCALE, { timeZone: tz, hour: '2-digit', minute: '2-digit', hour12: false })
  const dm = new Intl.DateTimeFormat(LOCALE, { timeZone: tz, day: '2-digit', month: 'short' })
  const parse = (s: string | null | undefined) => (s ? new Date(s) : null)
  return {
    dt: (s: string | null | undefined) => { const d = parse(s); return d ? full.format(d) : '—' },
    short: (s: string | null | undefined) => { const d = parse(s); return d ? short.format(d) : '—' },
    day: (s: string | null | undefined) => { const d = parse(s); return d ? day.format(d) : '—' },
    hm: (s: string | number) => hm.format(new Date(s)),
    dm: (s: string | number) => dm.format(new Date(s)),
    ago: (s: string | null | undefined) => relative(s),
  }
}

export function relative(s: string | null | undefined): string {
  if (!s) return 'nunca'
  const diff = (Date.now() - new Date(s).getTime()) / 1000
  if (diff < 0) return 'ahora'
  if (diff < 45) return 'hace unos segundos'
  if (diff < 3600) return `hace ${Math.round(diff / 60)} min`
  if (diff < 86400) return `hace ${Math.round(diff / 3600)} h`
  return `hace ${Math.round(diff / 86400)} d`
}

export function useFmt() {
  const { user } = useAuth()
  const tz = user?.profile.timezone || DEFAULT_TZ
  return { tz, ...dateFmt(tz) }
}

/** Convierte una fecha local (input date) a ISO UTC inicio/fin de día en la zona dada (aproximación por offset). */
export function dayBoundIso(dateStr: string, end: boolean, tz: string): string {
  const base = new Date(`${dateStr}T${end ? '23:59:59' : '00:00:00'}Z`)
  // offset de la zona en esa fecha
  const parts = new Intl.DateTimeFormat('en-US', { timeZone: tz, timeZoneName: 'longOffset' }).formatToParts(base)
  const off = parts.find((p) => p.type === 'timeZoneName')?.value ?? 'GMT'
  const m = /GMT([+-])(\d{2}):?(\d{2})?/.exec(off)
  const mins = m ? (m[1] === '-' ? -1 : 1) * (Number(m[2]) * 60 + Number(m[3] ?? 0)) : 0
  return new Date(base.getTime() - mins * 60000).toISOString()
}
