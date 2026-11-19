/* Figuras del Laboratorio ML dibujadas en SVG a partir de la especificación que entrega el backend
   ({kind, title, note, data, interpretation}). La misma especificación la dibuja matplotlib a 600 DPI
   en los reportes y en la exportación PNG/SVG. */
import { useId, useMemo, useState, type ReactNode } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Download } from 'lucide-react'
import { api } from '../api/client'
import { Button } from '../ui/Button'
import { useToast } from '../ui/Toast'
import { download, errMsg } from '../lib/utils'

export interface Interp { meaning: string[]; caution: string[] }
export interface FigSpec { id: string; kind: string; title: string; note: string; data: any; interpretation: Interp }
export interface TableSpec { id: string; kind: 'table'; title: string; note: string; columns: { key: string; label: string }[]; rows: Record<string, any>[]; interpretation: Interp }
export type Spec = FigSpec | TableSpec

const nf3 = new Intl.NumberFormat('es-PE', { maximumFractionDigits: 3 })
const nf0 = new Intl.NumberFormat('es-PE', { maximumFractionDigits: 0 })
export function fmtVal(v: unknown, d = 3): string {
  if (v === null || v === undefined || (typeof v === 'number' && !Number.isFinite(v))) return '—'
  if (typeof v === 'boolean') return v ? 'Sí' : 'No'
  if (typeof v === 'number') return Number.isInteger(v) && Math.abs(v) >= 1000 ? nf0.format(v) : Number.isInteger(v) ? String(v) : new Intl.NumberFormat('es-PE', { maximumFractionDigits: d }).format(v)
  if (Array.isArray(v)) return '[' + v.map((x) => fmtVal(x, d)).join('; ') + ']'
  if (typeof v === 'object') return Object.entries(v as object).map(([k, x]) => `${k}=${fmtVal(x, d)}`).join(', ')
  return String(v)
}
const short = (v: number) => {
  const a = Math.abs(v)
  if (a !== 0 && (a >= 1e9 || a < 0.001)) return v.toExponential(1).replace('.', ',')
  if (a >= 1000) return nf0.format(Math.round(v))
  return nf3.format(Math.round(v * 1000) / 1000)
}

/** Colores de series: tokens del sistema, legibles en claro y oscuro. */
const SERIES = ['var(--c-out)', 'var(--crit)', 'var(--ok)', 'var(--high)', 'var(--ai)', 'var(--c-in)', 'var(--med)', 'var(--low)']
const STATE: Record<string, string> = { complete: 'var(--c-out)', pruned: 'var(--high)', fail: 'var(--crit)', running: 'var(--ok)' }
const STATE_ES: Record<string, string> = { complete: 'Completado', pruned: 'Podado', fail: 'Fallido', running: 'En curso' }

function ticks(lo: number, hi: number, n = 5): number[] {
  if (!(hi > lo)) return [lo]
  const raw = (hi - lo) / n
  const p = 10 ** Math.floor(Math.log10(raw))
  const s = [1, 2, 2.5, 5, 10].find((m) => m * p >= raw)! * p
  const out: number[] = []
  for (let v = Math.ceil(lo / s) * s; v <= hi + s * 1e-9; v += s) out.push(Math.round(v / s) * s)
  return out
}
const clip = (s: string, n: number) => (s.length > n ? s.slice(0, n - 1) + '…' : s)
const W = 640

function Frame({ h, label, children }: { h: number; label: string; children: ReactNode }) {
  return <svg className="mlfig" viewBox={`0 0 ${W} ${h}`} role="img" aria-label={label} width="100%" style={{ maxHeight: h * 1.4 }}>{children}</svg>
}
function Axes({ x0, x1, y0, y1, xt, yt, sx, sy, xl, yl, xf = short, yf = short, grid = true }:
  { x0: number; x1: number; y0: number; y1: number; xt?: number[]; yt?: number[]; sx?: (v: number) => number; sy?: (v: number) => number; xl?: string; yl?: string; xf?: (v: number) => string; yf?: (v: number) => string; grid?: boolean }) {
  return (
    <g className="ax">
      <line x1={x0} x2={x1} y1={y1} y2={y1} className="axl" /><line x1={x0} x2={x0} y1={y0} y2={y1} className="axl" />
      {yt && sy && yt.map((t) => <g key={t}>{grid && <line x1={x0} x2={x1} y1={sy(t)} y2={sy(t)} className="grid" />}<text x={x0 - 6} y={sy(t) + 3.5} textAnchor="end">{yf(t)}</text></g>)}
      {xt && sx && xt.map((t) => <g key={t}>{grid && <line y1={y0} y2={y1} x1={sx(t)} x2={sx(t)} className="grid" />}<text x={sx(t)} y={y1 + 14} textAnchor="middle">{xf(t)}</text></g>)}
      {xl && <text x={(x0 + x1) / 2} y={y1 + 30} textAnchor="middle" className="axt">{xl}</text>}
      {yl && <text transform={`translate(11 ${(y0 + y1) / 2}) rotate(-90)`} textAnchor="middle" className="axt">{yl}</text>}
    </g>
  )
}

function Legend({ items }: { items: { name: string; color: string }[] }) {
  if (items.length < 2) return null
  return <div className="legend" style={{ marginTop: 6 }}>{items.map((i) => <span key={i.name}><i style={{ background: i.color }} />{i.name}</span>)}</div>
}

/* ---------------------------------------------------------------- barras */
function Bars({ d, title }: { d: any; title: string }) {
  const labels: string[] = d.labels.map(String)
  const series: any[] = d.series
  const hor = !!d.horizontal
  const all = series.flatMap((s) => s.values.map((v: number | null, i: number) => [v ?? 0, s.err?.[i] ?? 0] as const))
  const maxV = Math.max(0, ...all.map(([v, e]) => v + e)), minV = Math.min(0, ...all.map(([v, e]) => v - e))
  const tr = (v: number) => (d.log ? Math.log10(Math.max(v, 1e-9)) : v)
  const lo = d.log ? Math.floor(tr(Math.max(1e-9, Math.min(...all.map(([v]) => v).filter((v) => v > 0), 1)))) : minV
  const hi = d.log ? Math.ceil(tr(maxV || 1)) : maxV || 1
  if (hor) {
    const rowH = 22, padL = 150, padR = 16, padT = 8, padB = 36
    const h = padT + padB + labels.length * rowH
    const sx = (v: number) => padL + ((tr(v) - lo) / (hi - lo || 1)) * (W - padL - padR)
    const xt = ticks(lo, hi, 5)
    const gh = (rowH - 6) / series.length
    return (
      <Frame h={h} label={title}>
        <Axes x0={padL} x1={W - padR} y0={padT} y1={h - padB} xt={xt} sx={(v) => sx(d.log ? 10 ** v : v)} xl={d.xlabel ?? d.ylabel} xf={(v) => short(d.log ? 10 ** v : v)} />
        {labels.map((l, i) => (
          <g key={i}>
            <text x={padL - 6} y={padT + i * rowH + rowH / 2 + 3.5} textAnchor="end" className="lbl">{clip(l, 26)}<title>{l}</title></text>
            {series.map((s, k) => {
              const v = s.values[i] ?? 0
              const neg = d.signed && v < 0
              const x0 = sx(0 > lo ? 0 : lo), x1 = sx(v)
              return <g key={k}><rect x={Math.min(x0, x1)} width={Math.abs(x1 - x0)} y={padT + i * rowH + 3 + k * gh} height={Math.max(gh - 1, 2)} fill={d.signed ? (neg ? 'var(--crit)' : 'var(--c-out)') : s.color ?? SERIES[k % SERIES.length]} rx={1.5}><title>{`${l}: ${short(v)}`}</title></rect>
                {s.err?.[i] != null && <line x1={sx(v - s.err[i])} x2={sx(v + s.err[i])} y1={padT + i * rowH + 3 + k * gh + gh / 2} y2={padT + i * rowH + 3 + k * gh + gh / 2} className="err" />}</g>
            })}
          </g>
        ))}
      </Frame>
    )
  }
  const padL = 64, padR = 12, padT = 10, padB = 46, h = 250
  const sy = (v: number) => padT + (1 - (tr(v) - lo) / (hi - lo || 1)) * (h - padT - padB)
  const yt = ticks(lo, hi, 5)
  const bw = (W - padL - padR) / labels.length
  const gw = (bw * 0.78) / series.length
  const rot = labels.length > 7
  return (
    <>
      <Frame h={h + (rot ? 20 : 0)} label={title}>
        <Axes x0={padL} x1={W - padR} y0={padT} y1={h - padB} yt={yt} sy={(v) => sy(d.log ? 10 ** v : v)} yl={d.ylabel} yf={(v) => short(d.log ? 10 ** v : v)} xl={d.xlabel} />
        {labels.map((l, i) => (
          <g key={i}>
            {series.map((s, k) => {
              const v = s.values[i]
              if (v == null) return null
              const x = padL + i * bw + bw * 0.11 + k * gw
              const y0 = sy(Math.max(0, d.log ? 10 ** lo : 0)), y = sy(v)
              return <g key={k}><rect x={x} width={Math.max(gw - 1, 2)} y={Math.min(y, y0)} height={Math.max(Math.abs(y0 - y), 0.5)} fill={d.signed ? (v < 0 ? 'var(--crit)' : 'var(--c-out)') : s.color ?? SERIES[k % SERIES.length]} rx={1.5}><title>{`${l} · ${s.name}: ${short(v)}`}</title></rect>
                {s.err?.[i] != null && <line x1={x + gw / 2} x2={x + gw / 2} y1={sy(v - s.err[i])} y2={sy(v + s.err[i])} className="err" />}</g>
            })}
            <text transform={`translate(${padL + i * bw + bw / 2} ${h - padB + 14}) rotate(${rot ? -35 : 0})`} textAnchor={rot ? 'end' : 'middle'} className="lbl">{clip(l, rot ? 14 : 16)}<title>{l}</title></text>
          </g>
        ))}
      </Frame>
      <Legend items={series.map((s, k) => ({ name: s.name, color: s.color ?? SERIES[k % SERIES.length] }))} />
    </>
  )
}

/* ---------------------------------------------------------------- líneas */
function Lines({ d, title }: { d: any; title: string }) {
  const series: any[] = d.series
  const xs = series.flatMap((s) => s.x as number[]), ys = series.flatMap((s) => [...s.y, ...(s.lo ?? []), ...(s.hi ?? [])] as number[]).filter((v) => v != null && Number.isFinite(v))
  const hl: any[] = d.hlines ?? []
  const [xl0, xl1] = d.xlim ?? [Math.min(...xs), Math.max(...xs)]
  const allY = [...ys, ...hl.map((h) => h.y)]
  const [yl0, yl1] = d.ylim ?? [Math.min(...allY), Math.max(...allY)]
  const padL = 62, padR = 14, padT = 10, padB = 42, h = 270
  const tx = (v: number) => (d.xlog ? Math.log10(Math.max(v, 1e-12)) : v), ty = (v: number) => (d.ylog ? Math.log10(Math.max(v, 1e-12)) : v)
  const a0 = tx(xl0), a1 = tx(xl1) || 1, b0 = ty(yl0), b1 = ty(yl1)
  const sx = (v: number) => padL + ((tx(v) - a0) / (a1 - a0 || 1)) * (W - padL - padR)
  const sy = (v: number) => padT + (1 - (ty(v) - b0) / (b1 - b0 || 1)) * (h - padT - padB)
  const xt = d.xlog ? [] : ticks(xl0, xl1, 6), yt = d.ylog ? [] : ticks(yl0, yl1, 5)
  const path = (x: number[], y: number[]) => x.map((v, i) => `${i ? 'L' : 'M'}${sx(v).toFixed(1)} ${sy(y[i]).toFixed(1)}`).join('')
  return (
    <>
      <Frame h={h} label={title}>
        <Axes x0={padL} x1={W - padR} y0={padT} y1={h - padB} xt={xt} yt={yt} sx={sx} sy={sy} xl={d.xlabel} yl={d.ylabel} />
        {d.diagonal && <line x1={sx(0)} y1={sy(0)} x2={sx(1)} y2={sy(1)} className="ref" />}
        {hl.map((x, i) => <g key={i}><line x1={padL} x2={W - padR} y1={sy(x.y)} y2={sy(x.y)} className="ref" />{x.label && <text x={W - padR - 2} y={sy(x.y) - 4} textAnchor="end" className="lbl">{x.label}</text>}</g>)}
        {series.map((s, k) => {
          const col = s.color ?? SERIES[k % SERIES.length]
          if (s.state || d.mode === 'segments') return <line key={k} x1={sx(s.x[0])} x2={sx(s.x[1])} y1={sy(s.y[0])} y2={sy(s.y[1])} stroke={STATE[s.state ?? 'complete']} strokeWidth={6} strokeLinecap="butt"><title>{`${s.name ?? ''} ${STATE_ES[s.state] ?? ''}`}</title></line>
          if (s.mode === 'markers') return <g key={k}>{s.x.map((v: number, i: number) => <circle key={i} cx={sx(v)} cy={sy(s.y[i])} r={2.6} fill={col} fillOpacity={0.7} />)}</g>
          const mx = s.sizes ? Math.max(...s.sizes) : 1
          return (
            <g key={k}>
              {s.lo && <path d={path(s.x, s.hi) + path([...s.x].reverse(), [...s.lo].reverse()).replace('M', 'L') + 'Z'} fill={col} fillOpacity={0.16} stroke="none" />}
              <path d={path(s.x, s.y)} fill="none" stroke={s.bold ? 'var(--ink)' : s.faint ? 'var(--ink-3)' : col} strokeOpacity={s.faint ? 0.35 : 1} strokeWidth={s.bold ? 2.4 : s.faint ? 0.7 : 1.6} />
              {s.points && s.x.map((v: number, i: number) => <circle key={i} cx={sx(v)} cy={sy(s.y[i])} r={3 + (s.sizes ? 5 * (s.sizes[i] / mx) : 0)} fill={col}><title>{`${s.name}: ${short(s.y[i])}`}</title></circle>)}
            </g>
          )
        })}
      </Frame>
      {d.mode === 'segments' || series.some((s) => s.state) ? <Legend items={Object.entries(STATE_ES).map(([k, v]) => ({ name: v, color: STATE[k] }))} /> : <Legend items={series.filter((s) => !s.faint && s.name).map((s, k) => ({ name: s.name, color: s.bold ? 'var(--ink)' : s.color ?? SERIES[k % SERIES.length] }))} />}
    </>
  )
}

/* ---------------------------------------------------------------- puntos por grupo */
function Dots({ d, title }: { d: any; title: string }) {
  const groups: any[] = d.groups
  const all = groups.flatMap((g) => g.values.filter((v: number | null) => v != null) as number[])
  const lo = Math.min(...all), hi = Math.max(...all), pad = (hi - lo) * 0.1 || 0.05
  const padL = 62, padR = 12, padT = 10, padB = 36, h = 240
  const sy = (v: number) => padT + (1 - (v - (lo - pad)) / (hi - lo + 2 * pad)) * (h - padT - padB)
  const bw = (W - padL - padR) / groups.length
  return (
    <Frame h={h} label={title}>
      <Axes x0={padL} x1={W - padR} y0={padT} y1={h - padB} yt={ticks(lo - pad, hi + pad, 5)} sy={sy} yl={d.ylabel} />
      {groups.map((g, i) => {
        const vals = g.values.filter((v: number | null) => v != null) as number[]
        const m = vals.reduce((a, b) => a + b, 0) / (vals.length || 1), cx = padL + bw * (i + 0.5)
        return (
          <g key={i}>
            {vals.map((v, j) => <circle key={j} cx={cx + (vals.length > 1 ? (j / (vals.length - 1) - 0.5) * 0.3 * bw : 0)} cy={sy(v)} r={4} fill={SERIES[i % SERIES.length]}><title>{`${g.name}: ${short(v)}`}</title></circle>)}
            {vals.length > 0 && <line x1={cx - bw * 0.22} x2={cx + bw * 0.22} y1={sy(m)} y2={sy(m)} stroke="var(--ink)" strokeWidth={2}><title>{`Media ${short(m)}`}</title></line>}
            <text x={cx} y={h - padB + 15} textAnchor="middle" className="lbl">{clip(g.name, 18)}</text>
          </g>
        )
      })}
    </Frame>
  )
}

/* ---------------------------------------------------------------- mapa de calor */
const mix = (t: number, scale: string) => {
  const c = Math.max(0, Math.min(1, t))
  if (scale === 'div') return c < 0.5 ? `color-mix(in oklch, var(--surface) ${Math.round(c * 200)}%, var(--crit))` : `color-mix(in oklch, var(--surface) ${Math.round((1 - c) * 200)}%, var(--c-out))`
  return `color-mix(in oklch, var(--surface) ${Math.round((1 - c) * 100)}%, var(--accent))`
}
function Heatmap({ d, title }: { d: any; title: string }) {
  const rows: string[] = d.rows, cols: string[] = d.cols, vals: (number | null)[][] = d.values
  const flat = vals.flat().filter((v) => v != null) as number[]
  const vmin = d.vmin ?? Math.min(...flat), vmax0 = d.vmax ?? Math.max(...flat), vmax = vmax0 === vmin ? vmin + 1e-9 : vmax0
  const padL = 130, padR = 54, padT = 8, padB = cols.length > 6 ? 70 : 40
  const cw = Math.min(70, (W - padL - padR) / cols.length), ch = Math.min(34, Math.max(16, 300 / rows.length))
  const h = padT + padB + rows.length * ch
  const f = (v: number) => (d.fmt === 'int' ? nf0.format(v) : d.fmt === 'pct' ? `${new Intl.NumberFormat('es-PE', { maximumFractionDigits: 1 }).format(v * 100)} %` : short(v))
  const gid = useId()
  const x1 = padL + cols.length * cw
  return (
    <Frame h={h} label={title}>
      <defs><linearGradient id={gid} x1="0" y1="1" x2="0" y2="0">{[0, 0.25, 0.5, 0.75, 1].map((t) => <stop key={t} offset={`${t * 100}%`} stopColor={mix(t, d.scale)} />)}</linearGradient></defs>
      {rows.map((r, i) => <text key={i} x={padL - 6} y={padT + i * ch + ch / 2 + 3.5} textAnchor="end" className="lbl">{clip(r, 20)}<title>{r}</title></text>)}
      {cols.map((c, j) => <text key={j} transform={`translate(${padL + j * cw + cw / 2} ${padT + rows.length * ch + 13}) rotate(${cols.length > 6 ? -45 : 0})`} textAnchor={cols.length > 6 ? 'end' : 'middle'} className="lbl">{clip(c, 12)}<title>{c}</title></text>)}
      {vals.map((row, i) => row.map((v, j) => v == null ? null : (
        <g key={`${i}-${j}`}>
          <rect x={padL + j * cw} y={padT + i * ch} width={cw - 1} height={ch - 1} fill={mix((v - vmin) / (vmax - vmin), d.scale)} rx={2}><title>{`${rows[i]} · ${cols[j]}: ${f(v)}`}</title></rect>
          {d.annotate && <text x={padL + j * cw + cw / 2} y={padT + i * ch + ch / 2 + 4} textAnchor="middle" className="cell" style={{ fill: (v - vmin) / (vmax - vmin) > 0.55 ? 'var(--on-accent)' : 'var(--ink)' }}>{f(v)}</text>}
        </g>)))}
      <rect x={x1 + 12} y={padT} width={10} height={rows.length * ch} fill={`url(#${gid})`} stroke="var(--line)" />
      <text x={x1 + 26} y={padT + 8} className="lbl">{short(vmax)}</text><text x={x1 + 26} y={padT + rows.length * ch} className="lbl">{short(vmin)}</text>
    </Frame>
  )
}

/* ---------------------------------------------------------------- enjambre SHAP */
function Swarm({ d, title }: { d: any; title: string }) {
  const feats: any[] = d.features
  const xs = feats.flatMap((f) => f.points.map((p: any) => p.x as number))
  const m = Math.max(...xs.map(Math.abs), 1e-6)
  const padL = 170, padR = 40, padT = 8, padB = 38, rowH = 26, h = padT + padB + feats.length * rowH
  const sx = (v: number) => padL + ((v + m) / (2 * m)) * (W - padL - padR)
  const col = (c: number) => `color-mix(in oklch, var(--c-out) ${Math.round((1 - c) * 100)}%, var(--crit))`
  const jit = (i: number, k: number) => (((i * 9301 + k * 49297) % 233280) / 233280 - 0.5) * (rowH - 8)
  const gid = useId()
  return (
    <Frame h={h + 6} label={title}>
      <defs><linearGradient id={gid} x1="0" x2="1"><stop offset="0%" stopColor={col(0)} /><stop offset="100%" stopColor={col(1)} /></linearGradient></defs>
      <Axes x0={padL} x1={W - padR} y0={padT} y1={h - padB} xt={ticks(-m, m, 6)} sx={sx} xl={d.xlabel} />
      <line x1={sx(0)} x2={sx(0)} y1={padT} y2={h - padB} className="ref" />
      {feats.map((f, i) => (
        <g key={i}>
          <text x={padL - 6} y={padT + i * rowH + rowH / 2 + 3.5} textAnchor="end" className="lbl">{clip(f.label ?? f.feature, 28)}<title>{f.label ?? f.feature}</title></text>
          {f.points.map((p: any, k: number) => <circle key={k} cx={sx(p.x)} cy={padT + i * rowH + rowH / 2 + jit(i, k)} r={2.1} fill={col(p.c)} fillOpacity={0.75} />)}
        </g>
      ))}
      <text x={padL} y={h - 4} className="lbl">Valor bajo</text><rect x={padL + 56} y={h - 12} width={80} height={6} fill={`url(#${gid})`} /><text x={padL + 142} y={h - 4} className="lbl">Valor alto</text>
    </Frame>
  )
}

/* ---------------------------------------------------------------- cascada */
function Waterfall({ d, title }: { d: any; title: string }) {
  const items: any[] = d.items, base = d.base ?? 0
  let cur = base
  const segs = items.map((it) => { const a = cur; cur += it.value; return [a, cur] as const })
  const all = [base, ...segs.flat()]
  const lo = Math.min(...all), hi = Math.max(...all), pad = (hi - lo) * 0.08 || 0.1
  const padL = 190, padR = 24, padT = 8, padB = 36, rowH = 24, h = padT + padB + items.length * rowH
  const sx = (v: number) => padL + ((v - (lo - pad)) / (hi - lo + 2 * pad)) * (W - padL - padR)
  return (
    <Frame h={h} label={title}>
      <Axes x0={padL} x1={W - padR} y0={padT} y1={h - padB} xt={ticks(lo - pad, hi + pad, 5)} sx={sx} xl={d.xlabel ?? 'Contribución acumulada'} />
      <line x1={sx(base)} x2={sx(base)} y1={padT} y2={h - padB} className="ref" />
      {items.map((it, i) => {
        const [a, b] = segs[i]
        return (
          <g key={i}>
            <text x={padL - 6} y={padT + i * rowH + rowH / 2 + 3.5} textAnchor="end" className="lbl">{clip(it.label, 32)}<title>{it.label}</title></text>
            <rect x={Math.min(sx(a), sx(b))} width={Math.max(Math.abs(sx(b) - sx(a)), 1.5)} y={padT + i * rowH + 4} height={rowH - 8} rx={1.5} fill={it.value > 0 ? 'var(--crit)' : 'var(--c-out)'}><title>{`${it.label}: ${it.value > 0 ? '+' : ''}${short(it.value)}`}</title></rect>
          </g>
        )
      })}
    </Frame>
  )
}

/* ---------------------------------------------------------------- coordenadas paralelas */
function ParCoords({ d, title }: { d: any; title: string }) {
  const axes: any[] = d.axes, lines: any[] = d.lines
  const vals = lines.map((l) => l.value), vmin = Math.min(...vals), vmax = Math.max(...vals)
  const padL = 30, padR = 30, padT = 22, padB = 30, h = 280
  const gx = (i: number) => padL + (i / Math.max(axes.length - 1, 1)) * (W - padL - padR)
  const sc = (a: any, v: any) => {
    if (v == null) return 0
    if (a.categories) { const i = a.categories.indexOf(v); return i < 0 ? 0 : i / Math.max(a.categories.length - 1, 1) }
    let lo = a.min, hi = a.max, x = v
    if (a.log && lo > 0) { lo = Math.log10(lo); hi = Math.log10(Math.max(hi, a.min * 1.0001)); x = Math.log10(Math.max(v, 1e-12)) }
    return hi > lo ? (x - lo) / (hi - lo) : 0.5
  }
  const gy = (t: number) => padT + (1 - t) * (h - padT - padB)
  const col = (v: number) => `color-mix(in oklch, var(--c-in) ${Math.round((1 - (v - vmin) / (vmax - vmin || 1)) * 100)}%, var(--ok))`
  const sorted = useMemo(() => [...lines].sort((a, b) => a.value - b.value), [lines])
  return (
    <>
      <Frame h={h} label={title}>
        {sorted.map((l, k) => <path key={k} d={axes.map((a, i) => `${i ? 'L' : 'M'}${gx(i).toFixed(1)} ${gy(sc(a, l.values[i])).toFixed(1)}`).join('')} fill="none" stroke={col(l.value)} strokeOpacity={0.6} strokeWidth={1.1}><title>{`${d.objective ?? 'Valor'}: ${short(l.value)}`}</title></path>)}
        {axes.map((a, i) => (
          <g key={i}>
            <line x1={gx(i)} x2={gx(i)} y1={padT} y2={h - padB} stroke="var(--ink-3)" />
            <text x={gx(i)} y={h - padB + 14} textAnchor="middle" className="lbl">{clip(a.name, 14)}</text>
            <text x={gx(i)} y={padT - 7} textAnchor="middle" className="lbl">{a.categories ? clip(String(a.categories[a.categories.length - 1]), 10) : short(a.max)}</text>
            <text x={gx(i)} y={h - padB + 26} textAnchor="middle" className="lbl">{a.categories ? clip(String(a.categories[0]), 10) : short(a.min)}</text>
          </g>
        ))}
      </Frame>
      <div className="legend" style={{ marginTop: 6 }}><span><i style={{ background: col(vmax) }} />Mejor {d.objective ?? 'valor'} ({short(vmax)})</span><span><i style={{ background: col(vmin) }} />Peor ({short(vmin)})</span></div>
    </>
  )
}

export function FigureBody({ spec }: { spec: FigSpec }) {
  const d = spec.data
  switch (spec.kind) {
    case 'bars': return <Bars d={d} title={spec.title} />
    case 'lines': return <Lines d={d} title={spec.title} />
    case 'dots': return <Dots d={d} title={spec.title} />
    case 'heatmap': return <Heatmap d={d} title={spec.title} />
    case 'swarm': return <Swarm d={d} title={spec.title} />
    case 'waterfall': return <Waterfall d={d} title={spec.title} />
    case 'parcoords': return <ParCoords d={d} title={spec.title} />
    default: return <p className="muted small">Tipo de figura no soportado: {spec.kind}</p>
  }
}

/* ---------------------------------------------------------------- tarjeta con nota, interpretación y exportación */
export function Reading({ ip }: { ip: Interp }) {
  if (!ip.meaning.length && !ip.caution.length) return null
  return (
    <div className="reading">
      {ip.meaning.length > 0 && <div><h4>Qué significa</h4><ul>{ip.meaning.map((m, i) => <li key={i}>{m}</li>)}</ul></div>}
      {ip.caution.length > 0 && <div className="caution"><h4>Precaución</h4><ul>{ip.caution.map((m, i) => <li key={i}>{m}</li>)}</ul></div>}
    </div>
  )
}

export function FigureCard({ spec, module = 'ml_evaluation', wide }: { spec: FigSpec; module?: string; wide?: boolean }) {
  const toast = useToast()
  const [busy, setBusy] = useState<string | null>(null)
  const exp = useMutation({
    mutationFn: (format: 'png' | 'svg') => { setBusy(format); return api.download('/ml/figures/export', { spec: { kind: spec.kind, title: spec.title, data: spec.data }, format, module }) },
    onSuccess: ({ blob, filename }) => { download(blob, filename); toast.ok(`Figura exportada: ${filename}`) },
    onError: (e) => toast.err(errMsg(e)),
    onSettled: () => setBusy(null),
  })
  return (
    <figure className={`panel mlcard${wide ? ' wide' : ''}`} aria-label={spec.title}>
      <div className="panel-head">
        <h3>{spec.title}</h3>
        <span className="row" style={{ gap: 4 }}>
          <Button size="sm" variant="ghost" loading={busy === 'png'} onClick={() => exp.mutate('png')} title="Descargar PNG a 600 DPI"><Download size={13} /> PNG 600 DPI</Button>
          <Button size="sm" variant="ghost" loading={busy === 'svg'} onClick={() => exp.mutate('svg')} title="Descargar SVG vectorial"><Download size={13} /> SVG</Button>
        </span>
      </div>
      <div className="panel-body">
        <FigureBody spec={spec} />
        <figcaption className="small muted note">{spec.note}</figcaption>
        <Reading ip={spec.interpretation} />
      </div>
    </figure>
  )
}

export function TableCard({ spec }: { spec: TableSpec }) {
  return (
    <section className="panel mlcard wide" aria-label={spec.title}>
      <div className="panel-head"><h3>{spec.title}</h3></div>
      <div className="table-wrap">
        <table className="t">
          <thead><tr>{spec.columns.map((c, i) => <th key={c.key} className={i ? 'num' : ''}>{c.label}</th>)}</tr></thead>
          <tbody>{spec.rows.map((r, i) => <tr key={i}>{spec.columns.map((c, j) => <td key={c.key} className={j ? 'num' : 'cell-main'} style={j && typeof r[c.key] === 'string' ? { textAlign: 'left', whiteSpace: 'normal' } : undefined}>{fmtVal(r[c.key])}</td>)}</tr>)}</tbody>
        </table>
      </div>
      <div className="panel-body">
        <p className="small muted note">{spec.note}</p>
        <Reading ip={spec.interpretation} />
      </div>
    </section>
  )
}

export function SpecCard({ spec, module, wide }: { spec: Spec; module?: string; wide?: boolean }) {
  return spec.kind === 'table' ? <TableCard spec={spec as TableSpec} /> : <FigureCard spec={spec as FigSpec} module={module} wide={wide} />
}

/** Cuadrícula de figuras y tablas; las tablas ocupan todo el ancho. */
export function SpecGrid({ specs, module }: { specs: (Spec | null | undefined)[]; module?: string }) {
  const list = specs.filter(Boolean) as Spec[]
  return <div className="mlgrid">{list.map((s) => <SpecCard key={s.id} spec={s} module={module} />)}</div>
}
