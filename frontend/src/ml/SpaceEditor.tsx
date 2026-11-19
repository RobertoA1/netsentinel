import type { ModelSpace, SpaceParam } from './types'
import { fmtVal } from './figures'

export type Overrides = Record<string, { low?: number; high?: number; choices?: string[] }>

/** Editor de espacio de búsqueda: rangos acotados por límites duros del servidor, cada uno con su justificación. */
export function SpaceEditor({ space, value, onChange, disabled }: { space: ModelSpace; value: Overrides; onChange: (v: Overrides) => void; disabled?: boolean }) {
  const cur = (p: SpaceParam) => ({ low: value[p.name]?.low ?? p.low!, high: value[p.name]?.high ?? p.high!, choices: value[p.name]?.choices ?? p.choices ?? [] })
  const set = (p: SpaceParam, patch: Overrides[string]) => onChange({ ...value, [p.name]: { ...value[p.name], ...patch } })
  return (
    <div className="table-wrap">
      <table className="t">
        <thead><tr><th>Hiperparámetro</th><th>Rango o valores</th><th>Límite duro</th><th>Por qué este rango</th></tr></thead>
        <tbody>{space.params.map((p) => {
          const c = cur(p)
          const lo = Number(c.low), hi = Number(c.high)
          const bad = p.type !== 'categorical' && (Number.isNaN(lo) || Number.isNaN(hi) || lo > hi || lo < p.hard![0] || hi > p.hard![1] || (p.log && lo <= 0))
          return (
            <tr key={p.name}>
              <td className="cell-main mono">{p.name}{p.log && <span className="muted small"> · escala log</span>}</td>
              <td style={{ minWidth: 200 }}>
                {p.type === 'categorical' ? (
                  <div className="row" style={{ gap: 10, flexWrap: 'wrap' }}>{p.hard_choices!.map((ch) => (
                    <label key={ch} className="check"><input type="checkbox" disabled={disabled} checked={c.choices.includes(ch)} onChange={(e) => { const next = e.target.checked ? [...c.choices, ch] : c.choices.filter((x) => x !== ch); if (next.length) set(p, { choices: next }) }} /><span>{ch}</span></label>))}</div>
                ) : (
                  <div className="row" style={{ gap: 6 }}>
                    <input className="input" style={{ width: 90 }} inputMode="decimal" aria-label={`${p.name}: mínimo`} disabled={disabled} value={String(c.low)} aria-invalid={bad || undefined} onChange={(e) => set(p, { low: e.target.value === '' ? NaN : Number(e.target.value) })} />
                    <span className="muted">a</span>
                    <input className="input" style={{ width: 90 }} inputMode="decimal" aria-label={`${p.name}: máximo`} disabled={disabled} value={String(c.high)} aria-invalid={bad || undefined} onChange={(e) => set(p, { high: e.target.value === '' ? NaN : Number(e.target.value) })} />
                  </div>)}
                {bad && <div className="small" style={{ color: 'var(--crit-ink)' }} role="alert">Debe estar dentro de [{fmtVal(p.hard![0])}; {fmtVal(p.hard![1])}].</div>}
              </td>
              <td className="num">{p.type === 'categorical' ? '—' : `[${fmtVal(p.hard![0])}; ${fmtVal(p.hard![1])}]`}</td>
              <td className="small" style={{ whiteSpace: 'normal', maxWidth: 420, color: 'var(--ink-2)' }}>{p.why}</td>
            </tr>)
        })}</tbody>
      </table>
    </div>
  )
}

export function overridesValid(space: ModelSpace, v: Overrides): boolean {
  return space.params.every((p) => {
    if (p.type === 'categorical') return true
    const lo = v[p.name]?.low ?? p.low!, hi = v[p.name]?.high ?? p.high!
    return !(Number.isNaN(lo) || Number.isNaN(hi) || lo > hi || lo < p.hard![0] || hi > p.hard![1] || (p.log && lo <= 0))
  })
}
/** Solo lo que difiere del espacio por defecto. */
export function diffOverrides(space: ModelSpace, v: Overrides): Overrides | null {
  const out: Overrides = {}
  for (const p of space.params) {
    const o = v[p.name]
    if (!o) continue
    if (p.type === 'categorical') { if (o.choices && o.choices.join() !== (p.choices ?? []).join()) out[p.name] = { choices: o.choices } }
    else if ((o.low !== undefined && o.low !== p.low) || (o.high !== undefined && o.high !== p.high)) out[p.name] = { low: o.low ?? p.low, high: o.high ?? p.high }
  }
  return Object.keys(out).length ? out : null
}
/** Acota cada rango alrededor del mejor valor de un estudio (para «Usar estos hiperparámetros»). */
export function narrowAround(space: ModelSpace, best: Record<string, unknown>): Overrides {
  const out: Overrides = {}
  for (const p of space.params) {
    const b = best[p.name]
    if (b === undefined || b === null) continue
    if (p.type === 'categorical') { out[p.name] = { choices: [String(b)] }; continue }
    const v = Number(b), [hl, hh] = p.hard!
    let lo: number, hi: number
    if (p.log && v > 0) { lo = v / 2; hi = v * 2 } else { const span = (p.high! - p.low!) * 0.15; lo = v - span; hi = v + span }
    lo = Math.max(hl, p.log ? Math.max(lo, 1e-12) : lo); hi = Math.min(hh, hi)
    if (p.type === 'int') { lo = Math.floor(lo); hi = Math.ceil(hi) }
    out[p.name] = { low: Number(lo.toPrecision(4)), high: Number(hi.toPrecision(4)) }
  }
  return out
}
