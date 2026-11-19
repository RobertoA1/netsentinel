import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { TrafficPoint } from '../api/types'
import { bytes, num, useFmt } from '../lib/format'

type TipProps = { active?: boolean; payload?: any[]; label?: string | number; fmtVal: (v: number) => string; fmtLabel: (l: any) => string }
function Tip({ active, payload, label, fmtVal, fmtLabel }: TipProps) {
  if (!active || !payload?.length) return null
  return (
    <div className="chart-tip">
      <b>{fmtLabel(label)}</b>
      {payload.map((p) => (
        <div key={p.dataKey}><span style={{ color: p.color }}>{p.name}</span><span>{fmtVal(p.value)}</span></div>
      ))}
    </div>
  )
}

function useTick(points: { ts: string }[]) {
  const f = useFmt()
  const span = points.length > 1 ? new Date(points[points.length - 1].ts).getTime() - new Date(points[0].ts).getTime() : 0
  const tick = (v: string | number) => (span > 2 * 86400_000 ? f.dm(v) : f.hm(v))
  const full = (v: string | number) => f.short(new Date(v).toISOString())
  return { tick, full }
}

export function TrafficChart({ data }: { data: TrafficPoint[] }) {
  const { tick, full } = useTick(data)
  const pts = data.map((d) => ({ ...d, t: new Date(d.ts).getTime() }))
  const axis = { stroke: 'var(--line-strong)', tickLine: false } as const
  return (
    <div role="img" aria-label="Serie de tráfico: bytes de salida, bytes de entrada y conexiones bloqueadas en el tiempo">
      <ResponsiveContainer width="100%" height={210}>
        <AreaChart data={pts} margin={{ top: 8, right: 8, left: 0, bottom: 0 }} syncId="traffic">
          <CartesianGrid vertical={false} />
          <XAxis dataKey="t" type="number" domain={['dataMin', 'dataMax']} scale="time" tickFormatter={tick} hide {...axis} />
          <YAxis width={58} tickFormatter={(v) => bytes(v)} axisLine={false} tickLine={false} />
          <Tooltip content={<Tip fmtVal={bytes} fmtLabel={full} />} />
          <Area type="monotone" dataKey="bytes_out" name="Salida" stroke="var(--c-out)" fill="var(--c-out)" fillOpacity={0.18} strokeWidth={2} isAnimationActive={false} />
          <Area type="monotone" dataKey="bytes_in" name="Entrada" stroke="var(--c-in)" fill="var(--c-in)" fillOpacity={0.14} strokeWidth={1.5} isAnimationActive={false} />
        </AreaChart>
      </ResponsiveContainer>
      <ResponsiveContainer width="100%" height={70}>
        <BarChart data={pts} margin={{ top: 2, right: 8, left: 0, bottom: 0 }} syncId="traffic">
          <XAxis dataKey="t" type="number" domain={['dataMin', 'dataMax']} scale="time" tickFormatter={tick} {...axis} />
          <YAxis width={58} allowDecimals={false} tickFormatter={(v) => num(v)} axisLine={false} tickLine={false} tickCount={3} />
          <Tooltip content={<Tip fmtVal={(v) => `${num(v)} conexiones`} fmtLabel={full} />} />
          <Bar dataKey="blocked" name="Bloqueadas" fill="var(--c-blk)" isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function RealNoiseChart({ data }: { data: { ts: string; real: number; noise: number }[] }) {
  const { tick, full } = useTick(data)
  const pts = data.map((d) => ({ ...d, t: new Date(d.ts).getTime() }))
  return (
    <div role="img" aria-label="Hallazgos reales y ruido filtrado en el tiempo">
      <ResponsiveContainer width="100%" height={210}>
        <BarChart data={pts} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid vertical={false} />
          <XAxis dataKey="t" tickFormatter={tick} stroke="var(--line-strong)" tickLine={false} minTickGap={24} />
          <YAxis width={34} allowDecimals={false} axisLine={false} tickLine={false} />
          <Tooltip content={<Tip fmtVal={(v) => num(v)} fmtLabel={full} />} />
          <Bar dataKey="real" name="Reales" stackId="a" fill="var(--crit)" isAnimationActive={false} />
          <Bar dataKey="noise" name="Ruido filtrado" stackId="a" fill="var(--line-strong)" isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/** Intervalos entre conexiones consecutivas (s): un punto por intervalo sobre la banda media ± desviación. */
export function IntervalStrip({ samples, mean, stdev }: { samples: number[]; mean: number; stdev: number }) {
  const w = 600, h = 150, padL = 44, padR = 12, padT = 14, padB = 26
  const lo = Math.min(mean * 0.5, ...samples) , hi = Math.max(mean * 1.5, ...samples)
  const y = (v: number) => padT + (1 - (v - lo) / (hi - lo)) * (h - padT - padB)
  const x = (i: number) => padL + (i + 0.5) * ((w - padL - padR) / samples.length)
  return (
    <svg viewBox={`0 0 ${w} ${h}`} width="100%" role="img" aria-label={`Intervalos entre conexiones: media ${mean.toFixed(0)} segundos, desviación ${stdev.toFixed(1)} segundos`} style={{ maxWidth: 720 }}>
      <rect x={padL} y={y(mean + stdev)} width={w - padL - padR} height={Math.max(2, y(mean - stdev) - y(mean + stdev))} fill="var(--accent)" opacity={0.16} />
      <line x1={padL} x2={w - padR} y1={y(mean)} y2={y(mean)} stroke="var(--accent)" strokeDasharray="4 3" />
      <line x1={padL} x2={padL} y1={padT} y2={h - padB} stroke="var(--line-strong)" />
      <line x1={padL} x2={w - padR} y1={h - padB} y2={h - padB} stroke="var(--line-strong)" />
      {[hi, mean, lo].map((t, i) => <text key={i} x={padL - 6} y={y(t) + 4} textAnchor="end" style={{ fontSize: 10, fill: 'var(--ink-3)' }}>{t.toFixed(0)} s</text>)}
      {samples.map((s, i) => <circle key={i} cx={x(i)} cy={y(s)} r={3} fill="var(--c-out)" />)}
      <text x={w - padR} y={y(mean + stdev) - 4} textAnchor="end" style={{ fontSize: 10.5, fill: 'var(--accent)', fontWeight: 600 }}>media ± desviación ({mean.toFixed(0)} ± {stdev.toFixed(1)} s)</text>
      <text x={padL} y={h - 8} style={{ fontSize: 10, fill: 'var(--ink-3)' }}>{samples.length} intervalos consecutivos, del más antiguo al más reciente</text>
    </svg>
  )
}

/** Volumen observado frente a la línea base (media ± desviación). */
export function BaselineGauge({ value, mean, stdev, zscore }: { value: number; mean: number; stdev: number; zscore: number }) {
  const w = 560, h = 92, pad = 16
  const max = Math.max(value, mean + stdev * 3) * 1.08
  const x = (v: number) => pad + (v / max) * (w - pad * 2)
  return (
    <svg viewBox={`0 0 ${w} ${h}`} width="100%" role="img" aria-label={`Volumen ${bytes(value)} frente a línea base ${bytes(mean)}, ${zscore.toFixed(1)} desviaciones`} style={{ maxWidth: 680 }}>
      <rect x={pad} y={38} width={w - pad * 2} height={12} rx={2} fill="var(--surface-3)" />
      <rect x={x(Math.max(0, mean - stdev))} y={38} width={x(mean + stdev) - x(Math.max(0, mean - stdev))} height={12} fill="var(--low)" opacity={0.45} />
      <line x1={x(mean)} x2={x(mean)} y1={30} y2={58} stroke="var(--low-ink)" strokeWidth={2} />
      <text x={x(mean)} y={72} textAnchor="middle" style={{ fontSize: 11, fill: 'var(--ink-2)' }}>base {bytes(mean)}</text>
      <rect x={x(value) - 2} y={22} width={4} height={40} fill="var(--crit)" />
      <text x={Math.min(x(value), w - pad)} y={14} textAnchor={x(value) > w - 100 ? 'end' : 'middle'} style={{ fontSize: 12, fontWeight: 700, fill: 'var(--crit-ink)' }}>{bytes(value)} ({zscore.toFixed(1)}σ)</text>
    </svg>
  )
}
