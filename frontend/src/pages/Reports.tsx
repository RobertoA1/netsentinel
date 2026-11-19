import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Download, FileSpreadsheet, FileText, FileType } from 'lucide-react'
import { api } from '../api/client'
import { useGet } from '../api/hooks'
import type { Page, ReportCatalogItem, ReportFormat, ReportHistoryItem } from '../api/types'
import { useCan } from '../auth/AuthProvider'
import { Button } from '../ui/Button'
import { Dialog } from '../ui/Dialog'
import { Field, SelectField } from '../ui/Fields'
import { Pagination } from '../ui/Pagination'
import { DataState, EmptyState, PageHead, SkeletonRows } from '../ui/State'
import { Tabs } from '../ui/Controls'
import { useToast } from '../ui/Toast'
import { bytes, dayBoundIso, useFmt } from '../lib/format'
import { download, errMsg } from '../lib/utils'
import type { Dataset, MlJob, MlModel, Page as MlPage } from '../ml/types'
import { MODEL_LABEL } from '../ml/types'

const FMT_LABEL: Record<ReportFormat, string> = { pdf: 'PDF', docx: 'Word (.docx)', xlsx: 'Excel (.xlsx)' }
const FmtIcon = ({ f }: { f: ReportFormat }) => (f === 'xlsx' ? <FileSpreadsheet size={14} /> : f === 'docx' ? <FileType size={14} /> : <FileText size={14} />)
const iso = (d: Date) => d.toISOString().slice(0, 10)

export default function Reports() {
  const can = useCan('reports')
  const [tab, setTab] = useState<'catalog' | 'history'>('catalog')
  return (
    <div className="page">
      <PageHead title="Reportes" desc="Documentos para operar y para rendir cuentas. Elija el período y el formato; la descarga queda registrada en la bitácora." />
      <Tabs value={tab} onChange={setTab} tabs={[{ value: 'catalog', label: 'Catálogo' }, { value: 'history', label: 'Historial' }]} />
      {tab === 'catalog' ? <Catalog canExport={can.export} /> : <History />}
    </div>
  )
}

function Catalog({ canExport }: { canExport: boolean }) {
  const q = useGet<ReportCatalogItem[]>('/reports/catalog')
  const [pick, setPick] = useState<ReportCatalogItem | null>(null)
  return (
    <DataState q={q} skeleton={<div className="panel"><SkeletonRows rows={6} /></div>} isEmpty={(d) => d.length === 0} empty={<div className="panel"><EmptyState title="No hay reportes disponibles" /></div>}>
      {(items) => (
        <div className="stack" style={{ gap: 16 }}>
          {([['operational', 'Operacionales', 'Para el trabajo diario del analista.'], ['management', 'De gestión', 'Para gerencia: tendencias, métricas de respuesta y riesgo.'], ['ml', 'Laboratorio ML', 'Datos, entrenamiento, evaluación, explicabilidad, inferencia y ficha del modelo. Las figuras se incrustan a 600 DPI.']] as const).map(([cat, title, hint]) => {
            const list = items.filter((i) => i.category === cat)
            if (!list.length) return null
            return (
              <section className="panel" key={cat} aria-label={title}>
                <div className="panel-head"><h2>{title}</h2><span className="hint">{hint}</span></div>
                <div className="reports-grid" style={{ borderTop: 0 }}>
                  {list.map((r) => (
                    <div className="report-item" key={r.code}>
                      <h3>{r.name}</h3>
                      <p>{r.description}</p>
                      <div className="row between">
                        <span className="row" style={{ gap: 4 }}>{r.formats.map((f) => <span key={f} className="badge outline"><FmtIcon f={f} />{f.toUpperCase()}</span>)}</span>
                        {canExport && <Button size="sm" variant="primary" onClick={() => setPick(r)}><Download size={14} /> Generar</Button>}
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )
          })}
          {!canExport && <p className="small muted">Su rol no incluye exportar reportes.</p>}
          {pick && <GenerateDialog item={pick} onClose={() => setPick(null)} />}
        </div>
      )}
    </DataState>
  )
}

function GenerateDialog({ item, onClose }: { item: ReportCatalogItem; onClose: () => void }) {
  const f = useFmt()
  const toast = useToast()
  const qc = useQueryClient()
  const today = new Date()
  const [from, setFrom] = useState(iso(new Date(today.getTime() - 7 * 864e5)))
  const [to, setTo] = useState(iso(today))
  const [fmt, setFmt] = useState<ReportFormat>(item.formats[0] ?? 'pdf')
  const err = from > to ? 'La fecha inicial debe ser anterior o igual a la final.' : null
  const need = item.params ?? []
  const [pv, setPv] = useState<Record<string, string>>({})
  const ds = useGet<Dataset[]>('/ml/data/datasets', undefined, { enabled: need.includes('dataset_version_id') })
  const jobs = useGet<MlPage<MlJob>>('/ml/training/jobs', { kind: 'train', page_size: 50 }, { enabled: need.includes('job_id') })
  const models = useGet<MlModel[]>('/ml/evaluation/models', undefined, { enabled: need.includes('model_id') })
  const missing = need.some((k) => !pv[k])
  const gen = useMutation({
    mutationFn: () => api.download('/reports/generate', { report_code: item.code, format: fmt, date_from: dayBoundIso(from, false, f.tz), date_to: dayBoundIso(to, true, f.tz), params: Object.fromEntries(need.map((k) => [k, Number(pv[k])])) }),
    onSuccess: ({ blob, filename }) => { download(blob, filename); toast.ok(`Reporte descargado: ${filename}`); void qc.invalidateQueries({ queryKey: ['/reports/history'] }); onClose() },
    onError: (e) => toast.err(errMsg(e)),
  })
  const preset = (days: number) => { setFrom(iso(new Date(Date.now() - days * 864e5))); setTo(iso(new Date())) }
  return (
    <Dialog open onClose={onClose} title={item.name}
      footer={<><Button onClick={onClose}>Cancelar</Button><Button variant="primary" disabled={!!err || missing} loading={gen.isPending} onClick={() => gen.mutate()}><Download size={15} /> Generar y descargar</Button></>}>
      <div className="stack">
        <p className="muted">{item.description}</p>
        {need.includes('dataset_version_id') && <SelectField label="Versión de dataset" value={pv.dataset_version_id ?? ''} onChange={(e) => setPv((x) => ({ ...x, dataset_version_id: e.target.value }))} placeholder={ds.isPending ? 'Cargando…' : 'Elija un dataset'} options={(ds.data ?? []).map((d) => ({ value: d.current_version_id, label: `${d.name} · v${d.current_version}` }))} />}
        {need.includes('job_id') && <SelectField label="Trabajo de entrenamiento" value={pv.job_id ?? ''} onChange={(e) => setPv((x) => ({ ...x, job_id: e.target.value }))} placeholder={jobs.isPending ? 'Cargando…' : 'Elija un trabajo terminado'} options={(jobs.data?.items ?? []).filter((j) => j.status === 'succeeded').map((j) => ({ value: j.id, label: `#${j.id} · ${j.name}` }))} />}
        {need.includes('model_id') && <SelectField label="Modelo" value={pv.model_id ?? ''} onChange={(e) => setPv((x) => ({ ...x, model_id: e.target.value }))} placeholder={models.isPending ? 'Cargando…' : 'Elija un modelo'} options={(models.data ?? []).filter((m) => !m.is_baseline).map((m) => ({ value: m.id, label: `${MODEL_LABEL[m.model_type] ?? m.model_type} · #${m.id}${m.is_active ? ' (activo)' : ''}` }))} />}
        <div className="row">{[['Hoy', 1], ['7 días', 7], ['30 días', 30], ['90 días', 90]].map(([l, d]) => <Button key={l} size="sm" onClick={() => preset(d as number)}>{l}</Button>)}</div>
        <div className="form-grid">
          <Field label="Desde">{(p) => <input className="input" type="date" {...p} value={from} onChange={(e) => setFrom(e.target.value)} />}</Field>
          <Field label="Hasta" error={err}>{(p) => <input className="input" type="date" {...p} value={to} onChange={(e) => setTo(e.target.value)} />}</Field>
        </div>
        <SelectField label="Formato" value={fmt} onChange={(e) => setFmt(e.target.value as ReportFormat)} options={item.formats.map((x) => ({ value: x, label: FMT_LABEL[x] }))} />
        {gen.isPending && <p className="small muted" role="status">Generando el reporte; puede tardar unos segundos…</p>}
      </div>
    </Dialog>
  )
}

function History() {
  const [page, setPage] = useState(1)
  const f = useFmt()
  const q = useGet<Page<ReportHistoryItem>>('/reports/history', { page, page_size: 25 }, { keep: true })
  return (
    <section className="panel">
      <DataState q={q} skeleton={<SkeletonRows rows={6} />} isEmpty={(d) => d.items.length === 0} empty={<EmptyState title="Aún no se generaron reportes">Los reportes que genere aparecerán aquí.</EmptyState>}>
        {(d) => (
          <>
            <div className="table-wrap">
              <table className="t">
                <thead><tr><th>Reporte</th><th>Formato</th><th>Período</th><th>Generado por</th><th>Fecha</th><th className="num">Tamaño</th></tr></thead>
                <tbody>{d.items.map((r) => (
                  <tr key={r.id}>
                    <td className="cell-main">{r.report_name}</td><td><span className="badge outline">{r.format.toUpperCase()}</span></td>
                    <td className="nowrap">{f.day(r.date_from)} – {f.day(r.date_to)}</td><td>{r.generated_by}</td><td className="nowrap">{f.dt(r.generated_at)}</td><td className="num">{bytes(r.size_bytes)}</td>
                  </tr>))}</tbody>
              </table>
            </div>
            <Pagination page={d.page} pageSize={d.page_size} total={d.total} onPage={setPage} />
          </>
        )}
      </DataState>
    </section>
  )
}
