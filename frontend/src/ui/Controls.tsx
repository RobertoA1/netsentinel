import type { RangeKey } from '../api/types'
import { RANGE_LABEL } from '../lib/labels'

export function Segmented<T extends string>({ value, onChange, options, label }: { value: T; onChange: (v: T) => void; options: { value: T; label: string }[]; label: string }) {
  return (
    <div className="seg" role="group" aria-label={label}>
      {options.map((o) => (
        <button key={o.value} type="button" aria-pressed={value === o.value} onClick={() => onChange(o.value)}>{o.label}</button>
      ))}
    </div>
  )
}
export function RangeSelect({ value, onChange }: { value: RangeKey; onChange: (v: RangeKey) => void }) {
  const opts = (['1h', '24h', '7d', '30d'] as RangeKey[]).map((v) => ({ value: v, label: v === '1h' ? '1 h' : v === '24h' ? '24 h' : v === '7d' ? '7 d' : '30 d' }))
  return <Segmented label={`Rango de tiempo: ${RANGE_LABEL[value]}`} value={value} onChange={onChange} options={opts} />
}
export function Tabs<T extends string>({ value, onChange, tabs }: { value: T; onChange: (v: T) => void; tabs: { value: T; label: string }[] }) {
  return (
    <div className="tabs" role="tablist">
      {tabs.map((t) => (
        <button key={t.value} role="tab" aria-selected={value === t.value} onClick={() => onChange(t.value)}>{t.label}</button>
      ))}
    </div>
  )
}
