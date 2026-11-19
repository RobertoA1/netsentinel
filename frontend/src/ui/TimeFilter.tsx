import { Field } from './Fields'

/** Rango rápido o fechas personalizadas. */
export function TimeFilter({ values, set }: { values: Record<string, string>; set: (p: Record<string, string | null>) => void }) {
  const custom = !!(values.from || values.to)
  return (
    <>
      <Field label="Rango">
        {(p) => (
          <select className="select" {...p} value={custom ? 'custom' : values.range || ''}
            onChange={(e) => {
              const v = e.target.value
              if (v === 'custom') set({ range: null, from: new Date(Date.now() - 7 * 864e5).toISOString().slice(0, 10), to: new Date().toISOString().slice(0, 10) })
              else set({ range: v || null, from: null, to: null })
            }}>
            <option value="">Todo</option>
            <option value="1h">Última hora</option>
            <option value="24h">Últimas 24 h</option>
            <option value="7d">Últimos 7 días</option>
            <option value="30d">Últimos 30 días</option>
            <option value="custom">Personalizado…</option>
          </select>
        )}
      </Field>
      {custom && (
        <>
          <Field label="Desde" className="narrow">{(p) => <input className="input" type="date" {...p} value={values.from || ''} onChange={(e) => set({ from: e.target.value || null })} style={{ width: 150 }} />}</Field>
          <Field label="Hasta" className="narrow">{(p) => <input className="input" type="date" {...p} value={values.to || ''} onChange={(e) => set({ to: e.target.value || null })} style={{ width: 150 }} />}</Field>
        </>
      )}
    </>
  )
}
