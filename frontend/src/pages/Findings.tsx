import { useNavigate } from 'react-router-dom'
import { X } from 'lucide-react'
import { useGet } from '../api/hooks'
import type { Finding, Page } from '../api/types'
import { useFilters } from '../lib/useFilters'
import { DataState, EmptyState, PageHead, SkeletonRows } from '../ui/State'
import { Button } from '../ui/Button'
import { Check, SelectField, TextField } from '../ui/Fields'
import { TimeFilter } from '../ui/TimeFilter'
import { Pagination } from '../ui/Pagination'
import { SeverityBadge } from '../ui/Gauge'
import { StatusBadge, VerdictBadge } from '../ui/Badges'
import { num, useFmt } from '../lib/format'
import { FINDING_TYPE_LABEL, SEVERITIES, SEVERITY_LABEL, STATUS_LABEL } from '../lib/labels'

export default function Findings() {
  const F = useFilters({ range: '30d', is_noise: 'false' })
  const fmt = useFmt()
  const nav = useNavigate()
  const v = F.values
  const q = useGet<Page<Finding>>('/findings', { ...F.params, sort: '-last_seen' }, { keep: true })
  const sf = (k: string) => (e: { target: { value: string } }) => F.set({ [k]: e.target.value })
  const showNoise = v.is_noise !== 'false'
  const active = ['q', 'finding_type', 'severity', 'status', 'src_ip', 'dst_ip', 'from', 'to'].some((k) => v[k]) || showNoise

  return (
    <div className="page">
      <PageHead title="Hallazgos" desc="Comportamientos sospechosos detectados. Cada uno trae su evidencia y una explicación en lenguaje llano." />
      <section className="panel">
        <div className="filters" role="search" aria-label="Filtros de hallazgos">
          <TextField label="Buscar" className="wide" value={v.q || ''} onChange={sf('q')} placeholder="Título, IP…" />
          <SelectField label="Tipo" value={v.finding_type || ''} onChange={sf('finding_type')} placeholder="Todos" options={Object.entries(FINDING_TYPE_LABEL).map(([value, label]) => ({ value, label }))} />
          <SelectField label="Severidad" value={v.severity || ''} onChange={sf('severity')} placeholder="Todas" options={SEVERITIES.map((s) => ({ value: s, label: SEVERITY_LABEL[s] }))} />
          <SelectField label="Estado" value={v.status || ''} onChange={sf('status')} placeholder="Todos" options={Object.entries(STATUS_LABEL).map(([value, label]) => ({ value, label }))} />
          <TextField label="IP origen" mono value={v.src_ip || ''} onChange={sf('src_ip')} />
          <TimeFilter values={v} set={F.set} />
          <div className="field"><span className="label">&nbsp;</span><Check label="Mostrar ruido filtrado" checked={showNoise} onChange={(c) => F.set({ is_noise: c ? 'all' : 'false' })} /></div>
          {active && <Button variant="ghost" onClick={() => F.reset()}><X size={15} /> Restablecer</Button>}
        </div>
        <DataState q={q} skeleton={<SkeletonRows rows={8} h={22} />} isEmpty={(d) => d.items.length === 0}
          empty={<EmptyState title="No hay hallazgos con estos filtros">{showNoise ? 'Pruebe ampliando el rango.' : 'Si espera ver más, active "Mostrar ruido filtrado" o amplíe el rango.'}</EmptyState>}>
          {(d) => (
            <>
              <div className="table-wrap">
                <table className="t">
                  <thead><tr><th>Severidad</th><th>Hallazgo</th><th>Tipo</th><th>Estado</th><th>Análisis IA</th><th className="num">Puntaje</th><th className="num">Veces</th><th>Último</th><th>Asignado</th></tr></thead>
                  <tbody>
                    {d.items.map((f) => (
                      <tr key={f.id} className="clickable" onClick={() => nav(`/findings/${f.id}`)} style={f.is_noise ? { opacity: 0.72 } : undefined}>
                        <td><SeverityBadge severity={f.severity} /></td>
                        <td style={{ maxWidth: 380, minWidth: 240 }}>
                          <a href={`/findings/${f.id}`} onClick={(e) => { e.preventDefault(); e.stopPropagation(); nav(`/findings/${f.id}`) }} className="cell-main" style={{ color: 'inherit', textDecoration: 'none' }}>{f.title}</a>
                          <div className="small muted mono">{f.src_ip ?? '—'}{f.dst_ip ? ` → ${f.dst_ip}${f.dst_port ? ':' + f.dst_port : ''}` : ''}</div>
                        </td>
                        <td>{FINDING_TYPE_LABEL[f.finding_type]}</td>
                        <td><StatusBadge status={f.status} /></td>
                        <td>{f.is_noise ? <span className="badge">Ruido</span> : <VerdictBadge verdict={f.llm_verdict} />}</td>
                        <td className="num">{f.score.toFixed(0)}</td>
                        <td className="num">{num(f.occurrences)}</td>
                        <td className="nowrap">{fmt.short(f.last_seen)}</td>
                        <td>{f.assigned_to?.full_name ?? <span className="muted">Sin asignar</span>}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination page={d.page} pageSize={d.page_size} total={d.total} onPage={(p) => F.set({ page: p }, true)} onSize={(s) => F.set({ page_size: s })} />
            </>
          )}
        </DataState>
      </section>
    </div>
  )
}
