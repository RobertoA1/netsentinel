import { useRef, useState, type FormEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Database, Play, ScanSearch, Upload } from 'lucide-react'
import { api } from '../api/client'
import { useGet } from '../api/hooks'
import type { DetectResult, IngestRun, IngestStatus, Page, Source } from '../api/types'
import { useCan } from '../auth/AuthProvider'
import { Button } from '../ui/Button'
import { Check, Field, SelectField } from '../ui/Fields'
import { Pagination } from '../ui/Pagination'
import { DataState, EmptyState, PageHead, SkeletonRows } from '../ui/State'
import { useToast } from '../ui/Toast'
import { duration, num, relative, useFmt } from '../lib/format'
import { FORMAT_LABEL } from '../lib/labels'
import { errMsg } from '../lib/utils'

const TRIGGER: Record<IngestRun['trigger'], string> = { n8n: 'Automática (n8n)', upload: 'Archivo subido', manual: 'Manual', dataset: 'Dataset demo' }
const STATUS: Record<IngestRun['status'], [string, string]> = { running: ['En curso', 'accent'], success: ['Correcta', 'ok'], error: ['Con error', 'crit'] }

export default function Ingestion() {
  const can = useCan('ingestion')
  const fmt = useFmt()
  const toast = useToast()
  const qc = useQueryClient()
  const status = useGet<IngestStatus>('/ingest/status', undefined, { refetchInterval: 10_000 })
  const [page, setPage] = useState(1)
  const runs = useGet<Page<IngestRun>>('/ingest/runs', { page, page_size: 15, sort: '-started_at' }, { keep: true, refetchInterval: (q) => ((q.state.data as Page<IngestRun> | undefined)?.items.some((r) => r.status === 'running') ? 3000 : false) })
  const sources = useGet<Page<Source> | Source[]>('/sources', undefined, { retry: false })
  const srcList = (Array.isArray(sources.data) ? sources.data : sources.data?.items ?? []).filter((s) => s.enabled)

  const [sourceId, setSourceId] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [runDet, setRunDet] = useState(true)
  const [uploadErr, setUploadErr] = useState<string | null>(null)
  const [last, setLast] = useState<IngestRun | null>(null)
  const [lastDet, setLastDet] = useState<DetectResult | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const done = (msg: string) => { toast.ok(msg); void qc.invalidateQueries() }

  const upload = useMutation({
    mutationFn: () => { const fd = new FormData(); fd.append('file', file!); fd.append('source_id', sourceId); fd.append('run_detection', String(runDet)); return api.upload<IngestRun>('/ingest/upload', fd) },
    onSuccess: (r) => { setLast(r); setFile(null); if (fileRef.current) fileRef.current.value = ''; done(`Archivo procesado: ${num(r.logs_inserted)} registros nuevos.`) },
    onError: (e) => toast.err(errMsg(e)),
  })
  const runIngest = useMutation({
    mutationFn: () => api.post<IngestRun>('/ingest/run', sourceId ? { source_id: Number(sourceId) } : {}),
    onSuccess: (r) => { setLast(r); done(`Ingesta completada: ${num(r.logs_inserted)} registros nuevos.`) },
    onError: (e) => toast.err(errMsg(e)),
  })
  const detect = useMutation({
    mutationFn: () => api.post<DetectResult>('/detect/run', {}),
    onSuccess: (r) => { setLastDet(r); done(`Detección completada: ${r.findings_created} nuevos, ${r.findings_noise} ruido.`) },
    onError: (e) => toast.err(errMsg(e)),
  })
  const dataset = useMutation({
    mutationFn: () => api.post<IngestRun>('/ingest/dataset', { rebase_time: true }),
    onSuccess: (r) => { setLast(r); done('Dataset de demostración cargado.') },
    onError: (e) => toast.err(errMsg(e)),
  })

  function submit(e: FormEvent) {
    e.preventDefault()
    if (!sourceId) { setUploadErr('Elija la fuente del archivo.'); return }
    if (!file) { setUploadErr('Elija un archivo de logs.'); return }
    setUploadErr(null); upload.mutate()
  }
  const src = srcList.find((s) => String(s.id) === sourceId)

  return (
    <div className="page">
      <PageHead title="Ingesta" desc="Cargue logs, ejecute la detección y revise el historial de ejecuciones." />

      <div className="grid">
        <section className="panel span-7" aria-labelledby="up">
          <div className="panel-head"><h2 id="up">Subir archivo de logs</h2></div>
          {can.execute ? (
            <form className="panel-body stack" onSubmit={submit} noValidate>
              <SelectField label="Fuente" value={sourceId} onChange={(e) => setSourceId(e.target.value)} placeholder="Elija una fuente…" options={srcList.map((s) => ({ value: s.id, label: `${s.name} · ${FORMAT_LABEL[s.format]}` }))}
                help={srcList.length === 0 ? 'No hay fuentes activas. Cree una en el módulo Fuentes.' : src ? `Se interpretará como ${FORMAT_LABEL[src.format]}.` : undefined} />
              <Field label="Archivo" error={uploadErr && !file ? uploadErr : null}>
                {(p) => <input ref={fileRef} className="input" type="file" {...p} onChange={(e) => setFile(e.target.files?.[0] ?? null)} accept=".log,.txt,.json,.jsonl,.csv,.binetflow,.gz" />}
              </Field>
              {uploadErr && file && <p className="small" role="alert" style={{ color: 'var(--crit-ink)' }}>{uploadErr}</p>}
              <Check label="Ejecutar la detección al terminar" checked={runDet} onChange={setRunDet} />
              <div><Button variant="primary" type="submit" loading={upload.isPending}><Upload size={15} /> Subir y procesar</Button></div>
              {upload.isPending && <p className="small muted" role="status">Procesando el archivo; los archivos grandes pueden tardar varios minutos.</p>}
            </form>
          ) : <div className="panel-body"><p className="muted">Su rol no permite cargar logs.</p></div>}
        </section>

        <section className="panel span-5" aria-labelledby="est">
          <div className="panel-head"><h2 id="est">Estado</h2></div>
          <DataState q={status} skeleton={<SkeletonRows rows={4} />}>
            {(s) => (
              <div className="panel-body stack">
                <dl className="dl">
                  <dt>Última ejecución</dt><dd>{s.last_run ? <>{relative(s.last_run.started_at)} <span className={`badge ${STATUS[s.last_run.status][1]}`}>{STATUS[s.last_run.status][0]}</span></> : 'Ninguna'}</dd>
                  <dt>Archivos pendientes</dt><dd>{num(s.pending_files)}</dd>
                  <dt>Dataset de demo</dt><dd>{s.dataset_available ? (s.dataset_loaded ? 'Disponible, ya cargado' : 'Disponible') : 'No encontrado en el servidor'}</dd>
                </dl>
                {can.execute && (
                  <div className="row">
                    <Button onClick={() => runIngest.mutate()} loading={runIngest.isPending} title="Lee los archivos nuevos de la carpeta de ingesta y luego ejecuta la detección"><Play size={15} /> Ejecutar ingesta</Button>
                    <Button onClick={() => detect.mutate()} loading={detect.isPending}><ScanSearch size={15} /> Ejecutar detección</Button>
                    {s.dataset_available && <Button onClick={() => dataset.mutate()} loading={dataset.isPending}><Database size={15} /> {s.dataset_loaded ? 'Recargar dataset de demo' : 'Cargar dataset de demo'}</Button>}
                  </div>
                )}
              </div>
            )}
          </DataState>
        </section>
      </div>

      {(last || lastDet) && (
        <div className="banner ok" role="status" style={{ marginBottom: 16 }}>
          <div>
            {last && <div><b>Última acción:</b> {num(last.lines_read)} líneas leídas, {num(last.logs_inserted)} registros nuevos, {num(last.parse_errors)} con error de formato, {num(last.findings_created)} hallazgos nuevos ({num(last.findings_noise)} ruido).</div>}
            {lastDet && <div><b>Detección:</b> {lastDet.findings_created} nuevos, {lastDet.findings_updated} actualizados, {lastDet.findings_noise} ruido, en {duration(lastDet.duration_ms / 1000)}.</div>}
          </div>
        </div>
      )}

      <section className="panel" aria-labelledby="hist">
        <div className="panel-head"><h2 id="hist">Historial de ejecuciones</h2></div>
        <DataState q={runs} skeleton={<SkeletonRows rows={6} />} isEmpty={(d) => d.items.length === 0} empty={<EmptyState title="Sin ejecuciones todavía">Cuando suba un archivo o ejecute la ingesta, el resultado aparecerá aquí.</EmptyState>}>
          {(d) => (
            <>
              <div className="table-wrap">
                <table className="t">
                  <thead><tr><th>Inicio</th><th>Origen</th><th>Fuente / archivo</th><th>Estado</th><th className="num">Líneas</th><th className="num">Registros</th><th className="num">Errores</th><th className="num">Hallazgos</th><th className="num">Ruido</th><th className="num">Duración</th></tr></thead>
                  <tbody>{d.items.map((r) => (
                    <tr key={r.id}>
                      <td className="nowrap">{fmt.dt(r.started_at)}</td><td>{TRIGGER[r.trigger]}</td>
                      <td>{r.source_name ?? '—'}{r.filename && <div className="small muted mono">{r.filename}</div>}</td>
                      <td><span className={`badge ${STATUS[r.status][1]}`}>{STATUS[r.status][0]}</span>{r.error && <div className="small" style={{ color: 'var(--crit-ink)', maxWidth: 280 }}>{r.error}</div>}</td>
                      <td className="num">{num(r.lines_read)}</td><td className="num">{num(r.logs_inserted)}</td>
                      <td className="num" style={r.parse_errors ? { color: 'var(--high-ink)' } : undefined}>{num(r.parse_errors)}</td>
                      <td className="num">{num(r.findings_created)}</td><td className="num muted">{num(r.findings_noise)}</td>
                      <td className="num">{r.finished_at ? duration((new Date(r.finished_at).getTime() - new Date(r.started_at).getTime()) / 1000) : '—'}</td>
                    </tr>))}</tbody>
                </table>
              </div>
              <Pagination page={d.page} pageSize={d.page_size} total={d.total} onPage={setPage} />
            </>
          )}
        </DataState>
      </section>
    </div>
  )
}
