import { useMemo, useState } from 'react'
import type { FlowRow } from '../api/types'
import { bytes, num } from '../lib/format'

/** Sankey de dos columnas (origen → destino) en SVG; el ancho del flujo es proporcional a los bytes. */
export function FlowSankey({ rows }: { rows: FlowRow[] }) {
  const [hover, setHover] = useState<number | null>(null)
  const layout = useMemo(() => {
    const top = rows.slice(0, 18)
    const agg = (key: 'src_ip' | 'dst_ip') => {
      const m = new Map<string, number>()
      top.forEach((r) => m.set(r[key], (m.get(r[key]) ?? 0) + r.bytes))
      return [...m.entries()].sort((a, b) => b[1] - a[1])
    }
    const srcs = agg('src_ip'), dsts = agg('dst_ip')
    const MIN = 20, K = 90, gap = 10
    const place = (list: [string, number][]) => {
      let y = 0
      const pos = new Map<string, { y: number; h: number; used: number; tot: number }>()
      list.forEach(([k, v]) => { const h = MIN + Math.sqrt(v / list[0][1]) * K; pos.set(k, { y, h, used: 0, tot: v }); y += h + gap })
      return { pos, end: y - gap }
    }
    const S = place(srcs), D = place(dsts)
    const sp = S.pos, dp = D.pos
    const H = Math.max(S.end, D.end, 200)
    const links = top.map((r, i) => {
      const a = sp.get(r.src_ip)!, b = dp.get(r.dst_ip)!
      const lh = Math.max(2, Math.min((r.bytes / a.tot) * a.h, (r.bytes / b.tot) * b.h))
      const y0 = a.y + a.used + lh / 2, y1 = b.y + b.used + lh / 2
      a.used += lh; b.used += lh
      return { ...r, i, y0, y1, lh }
    })
    return { sp, dp, links, H }
  }, [rows])

  const W = 760, L = 150, R = W - 190
  return (
    <div style={{ overflowX: 'auto' }}>
      <svg className="flow-svg" viewBox={`0 0 ${W} ${layout.H + 8}`} width="100%" style={{ minWidth: 560 }} role="img" aria-label="Flujos de tráfico desde equipos de origen hacia destinos, ordenados por volumen">
        {layout.links.map((l) => {
          const d = `M${L},${l.y0} C${(L + R) / 2},${l.y0} ${(L + R) / 2},${l.y1} ${R},${l.y1}`
          return (
            <path key={l.i} d={d} fill="none" stroke="var(--c-out)" strokeWidth={l.lh}
              opacity={hover === null ? 0.28 : hover === l.i ? 0.7 : 0.1}
              onMouseEnter={() => setHover(l.i)} onMouseLeave={() => setHover(null)}>
              <title>{`${l.src_ip} → ${l.dst_ip}:${l.dst_port} · ${bytes(l.bytes)} · ${num(l.connections)} conexiones`}</title>
            </path>
          )
        })}
        {[...layout.sp.entries()].map(([ip, p]) => (
          <g key={ip}>
            <rect x={L - 6} y={p.y} width={6} height={p.h} fill="var(--ink-2)" />
            <text x={L - 12} y={p.y + p.h / 2 + 4} textAnchor="end">{ip}</text>
          </g>
        ))}
        {[...layout.dp.entries()].map(([ip, p]) => (
          <g key={ip}>
            <rect x={R} y={p.y} width={6} height={p.h} fill="var(--ink-2)" />
            <text x={R + 12} y={p.y + p.h / 2 + 4}>{ip}</text>
          </g>
        ))}
      </svg>
    </div>
  )
}
