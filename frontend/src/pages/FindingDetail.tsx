import { useState, type FormEvent, type ReactNode } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Bot, ChevronRight, RefreshCw, Sparkles } from 'lucide-react'
import { api } from '../api/client'
import { useGet } from '../api/hooks'
import type { Finding, FindingStatus, FirewallLog, Page, Severity, User } from '../api/types'
import { useAuth } from '../auth/AuthProvider'
import { Button } from '../ui/Button'
import { Check, SelectField, TextArea } from '../ui/Fields'
import { DataState, EmptyState, PageHead, Skeleton, SkeletonRows } from '../ui/State'
import { SeverityBadge } from '../ui/Gauge'
import { ActionBadge, StatusBadge } from '../ui/Badges'
import { Pagination } from '../ui/Pagination'
import { useToast } from '../ui/Toast'
import { BaselineGauge, IntervalStrip } from '../charts/Charts'
import { bytes, dec, duration, num, ratioPct, useFmt } from '../lib/format'
import { DIRECTION_LABEL, FINDING_TYPE_LABEL, FINDING_TYPE_PLAIN, SEVERITIES, SEVERITY_LABEL, STATUS_LABEL, VERDICT_LABEL } from '../lib/labels'
import { errMsg } from '../lib/utils'
import { LogDrawer } from './Logs'

function Metric({ label, value, unit }: { label: string; value: ReactNode; unit?: string }) {
  return <div className="metric"><dt>{label}</dt><dd>{value}{unit && <> <small>{unit}</small></>}</dd></div>
}

function Evidence({ f }: { f: Finding }) {
  const e = f.evidence as any
  switch (f.finding_type) {
    case 'beaconing': {
      const regular = e.cv <= 0.25
      return (
        <div className="stack">
          <dl className="metrics">
            <Metric label="Conexiones" value={num(e.connections)} />
            <Metric label="Intervalo medio" value={duration(e.mean_interval_s)} />
            <Metric label="Desviación" value={duration(e.stdev_interval_s)} />
            <Metric label="Regularidad (CV)" value={dec(e.cv, 2)} />
            <Metric label="Bytes por conexión" value={bytes(e.mean_bytes)} />
            <Metric label="Duración observada" value={duration(e.duration_h * 3600)} />
          </dl>
          {Array.isArray(e.intervals_sample) && e.intervals_sample.length > 0 && <IntervalStrip samples={e.intervals_sample} mean={e.mean_interval_s} stdev={e.stdev_interval_s} />}
          <p className="small muted">
            El coeficiente de variación (CV) mide cuán parejos son los intervalos: cerca de 0 es un reloj; un uso humano normal es irregular.{' '}
            <b style={{ color: regular ? 'var(--crit-ink)' : 'var(--ink-2)' }}>Aquí CV = {dec(e.cv, 2)}: {regular ? 'muy regular, típico de un programa automático.' : 'moderadamente irregular.'}</b>
            {e.bytes_cv != null && <> Variación del tamaño: {dec(e.bytes_cv, 2)}.</>}
          </p>
        </div>
      )
    }
    case 'exfiltration':
      return (
        <div className="stack">
          <dl className="metrics">
            <Metric label="Datos enviados" value={bytes(e.bytes_out)} />
            <Metric label="Habitual (base)" value={bytes(e.baseline_mean)} />
            <Metric label="Desviaciones (σ)" value={dec(e.zscore, 1)} />
            <Metric label="Salida / entrada" value={`${dec(e.ratio_out_in, 1)}×`} />
          </dl>
          <BaselineGauge value={e.bytes_out} mean={e.baseline_mean} stdev={e.baseline_stdev} zscore={e.zscore} />
          {e.top_destinations?.length > 0 && (
            <table className="t" aria-label="Destinos principales">
              <thead><tr><th>Destino</th><th className="num">Bytes</th><th className="num">Parte del total</th></tr></thead>
              <tbody>{e.top_destinations.map((d: { ip: string; bytes: number }) => (
                <tr key={d.ip}><td><Link className="mono" to={`/logs?dst_ip=${d.ip}`}>{d.ip}</Link></td><td className="num">{bytes(d.bytes)}</td><td className="num">{ratioPct(d.bytes / e.bytes_out)}</td></tr>
              ))}</tbody>
            </table>
          )}
        </div>
      )
    case 'unusual_port':
      return (
        <dl className="metrics">
          <Metric label="Puerto" value={e.port} />
          <Metric label="Servicio" value={e.service || 'desconocido'} />
          <Metric label="Conexiones" value={num(e.connections)} />
          <Metric label="Datos" value={bytes(e.bytes)} />
          <Metric label="Equipos distintos" value={num(e.distinct_sources)} />
          <Metric label="En línea base" value={e.in_baseline ? 'Sí' : 'No'} />
        </dl>
      )
    case 'ids_alert':
      return (
        <dl className="metrics">
          <Metric label="Firma" value={<span style={{ fontSize: '0.9rem' }}>{e.signature}</span>} />
          <Metric label="ID de firma" value={e.signature_id} />
          <Metric label="Categoría" value={<span style={{ fontSize: '0.9rem' }}>{e.category}</span>} />
          <Metric label="Severidad IDS" value={e.ids_severity} unit="(1 = más grave)" />
          <Metric label="Eventos" value={num(e.count)} />
          <Metric label="Orígenes distintos" value={num(e.distinct_sources)} />
        </dl>
      )
    case 'talker_anomaly':
      return (
        <div className="stack">
          <dl className="metrics">
            <Metric label="Métrica" value={<span style={{ fontSize: '0.9rem' }}>{e.metric}</span>} />
            <Metric label="Valor observado" value={num(e.value)} />
            <Metric label="Línea base" value={num(e.baseline_mean)} />
            <Metric label="Desviaciones (σ)" value={dec(e.zscore, 1)} />
            <Metric label="Destinos distintos" value={num(e.unique_destinations)} />
          </dl>
        </div>
      )
    default:
      return <pre className="mono-block">{JSON.stringify(f.evidence, null, 2)}</pre>
  }
}

function AiBox({ f }: { f: Finding }) {
  if (!f.llm_verdict) {
    return (
      <section className="ai-box" aria-label="Explicación por plantilla">
        <div className="ai-head"><Bot size={16} aria-hidden /> Explicación por plantilla <span className="badge outline">Sin interpretación de IA</span></div>
        <div className="ai-body">
          <p>El motor de IA no respondió para este hallazgo, así que la explicación se generó con una plantilla fija a partir de la evidencia. No hay veredicto ni nivel de confianza.</p>
          {f.llm_explanation && <div><h4>Explicación</h4><p>{f.llm_explanation}</p></div>}
          {f.llm_recommendation && <div><h4>Recomendación</h4><p>{f.llm_recommendation}</p></div>}
        </div>
      </section>
    )
  }
  const conf = f.llm_confidence ?? 0
  return (
    <section className="ai-box" aria-label="Interpretación de IA">
      <div className="ai-head">
        <Sparkles size={16} aria-hidden /> Interpretación de IA
        <span className="small" style={{ fontWeight: 400, color: 'var(--ink-3)' }}>Es una opinión del modelo, no un hecho: contraste con la evidencia.</span>
      </div>
      <div className="ai-body">
        <div className="row" style={{ gap: 20 }}>
          <div><h4>Veredicto</h4><span className={`badge ${f.llm_verdict === 'real' ? 'crit' : f.llm_verdict === 'noise' ? '' : 'med'}`}>{VERDICT_LABEL[f.llm_verdict]}</span></div>
          <div><h4>Confianza</h4><span className="conf"><span className="conf-bar"><i style={{ width: `${conf * 100}%` }} /></span>{ratioPct(conf)}</span></div>
          {f.llm_model && <div><h4>Modelo</h4><span className="mono small">{f.llm_model}</span></div>}
        </div>
        {f.llm_explanation && <div><h4>Explicación</h4><p>{f.llm_explanation}</p></div>}
        {f.llm_recommendation && <div><h4>Recomendación</h4><p>{f.llm_recommendation}</p></div>}
      </div>
    </section>
  )
}

function RelatedLogs({ id }: { id: number }) {
  const [page, setPage] = useState(1)
  const [sel, setSel] = useState<number | null>(null)
  const fmt = useFmt()
  const q = useGet<Page<FirewallLog>>(`/findings/${id}/related-logs`, { page, page_size: 10 }, { keep: true })
  return (
    <section className="panel" aria-labelledby="rl">
      <div className="panel-head"><h2 id="rl">Registros relacionados</h2><span className="hint">Las conexiones que originaron este hallazgo</span></div>
      <DataState q={q} skeleton={<SkeletonRows rows={5} />} isEmpty={(d) => d.items.length === 0} empty={<EmptyState title="Sin registros relacionados" />}>
        {(d) => (
          <>
            <div className="table-wrap">
              <table className="t">
                <thead><tr><th>Fecha</th><th>Acción</th><th>Origen</th><th>Destino</th><th>Dirección</th><th className="num">Salida</th></tr></thead>
                <tbody>{d.items.map((l) => (
                  <tr key={l.id} className="clickable" onClick={() => setSel(l.id)} tabIndex={0} onKeyDown={(e) => { if (e.key === 'Enter') setSel(l.id) }}>
                    <td className="nowrap">{fmt.dt(l.ts)}</td><td><ActionBadge action={l.action} /></td>
                    <td className="mono">{l.src_ip}</td><td className="mono">{l.dst_ip}{l.dst_port ? `:${l.dst_port}` : ''}</td>
                    <td>{DIRECTION_LABEL[l.direction]}</td><td className="num">{bytes(l.bytes_out)}</td>
                  </tr>))}</tbody>
              </table>
            </div>
            <Pagination page={d.page} pageSize={d.page_size} total={d.total} onPage={setPage} />
            <LogDrawer log={d.items.find((l) => l.id === sel)} onClose={() => setSel(null)} />
          </>
        )}
      </DataState>
    </section>
  )
}

export default function FindingDetail() {
  const { id } = useParams()
  const { can, user } = useAuth()
  const fmt = useFmt()
  const toast = useToast()
  const qc = useQueryClient()
  const path = `/findings/${id}`
  const q = useGet<Finding>(path)
  const canUpdate = can('findings:update')
  const canRe = can('findings:execute') || canUpdate
  const users = useGet<Page<User>>('/users', { page_size: 100 }, { enabled: canUpdate && can('users:view'), retry: false })
  const [body, setBody] = useState('')

  const patch = useMutation({
    mutationFn: (b: Partial<{ status: FindingStatus; severity: Severity; assigned_to_id: number | null; is_noise: boolean }>) => api.patch<Finding>(path, b),
    onSuccess: (f) => { qc.setQueryData([path, {}], f); void qc.invalidateQueries({ queryKey: ['/findings'] }); toast.ok('Hallazgo actualizado.') },
    onError: (e) => toast.err(errMsg(e)),
  })
  const comment = useMutation({
    mutationFn: (b: string) => api.post<Finding>(`${path}/comments`, { body: b }),
    onSuccess: (f) => { qc.setQueryData([path, {}], f); setBody(''); toast.ok('Comentario agregado.') },
    onError: (e) => toast.err(errMsg(e)),
  })
  const reanalyze = useMutation({
    mutationFn: () => api.post<Finding>(`${path}/reanalyze`),
    onSuccess: (f) => { qc.setQueryData([path, {}], f); toast.ok('Hallazgo reanalizado.') },
    onError: (e) => toast.err(errMsg(e)),
  })

  if (q.isPending) return <div className="page"><Skeleton h={30} w="50%" /><div style={{ height: 16 }} /><SkeletonRows rows={8} h={22} /></div>
  if (q.isError) return <div className="page"><div className="panel"><DataState q={q}>{() => null}</DataState></div></div>
  const f = q.data

  const assignees = new Map<number, string>()
  if (user) assignees.set(user.id, user.full_name)
  if (f.assigned_to) assignees.set(f.assigned_to.id, f.assigned_to.full_name)
  users.data?.items.filter((u) => u.is_active).forEach((u) => assignees.set(u.id, u.full_name))

  function addComment(e: FormEvent) { e.preventDefault(); if (body.trim()) comment.mutate(body.trim()) }

  return (
    <div className="page">
      <nav className="crumbs" aria-label="Ruta"><Link to="/findings">Hallazgos</Link><ChevronRight size={14} aria-hidden /><span>#{f.id}</span></nav>
      <PageHead title={f.title}>
        {canRe && <Button onClick={() => reanalyze.mutate()} loading={reanalyze.isPending}><RefreshCw size={15} /> Reanalizar con IA</Button>}
      </PageHead>
      <div className="row" style={{ marginBottom: 16, marginTop: -8 }}>
        <SeverityBadge severity={f.severity} /> <StatusBadge status={f.status} />
        <span className="badge outline">{FINDING_TYPE_LABEL[f.finding_type]}</span>
        {f.is_noise && <span className="badge">Marcado como ruido</span>}
        <span className="small muted">Puntaje {f.score.toFixed(0)}/100 · visto {num(f.occurrences)} {f.occurrences === 1 ? 'vez' : 'veces'}</span>
      </div>

      <div className="detail-grid">
        <div className="stack" style={{ gap: 16 }}>
          <section className="panel">
            <div className="panel-head"><h2>Qué significa</h2></div>
            <div className="panel-body"><p>{FINDING_TYPE_PLAIN[f.finding_type]}</p></div>
          </section>

          <section className="panel" aria-labelledby="ev">
            <div className="panel-head"><h2 id="ev">Evidencia medida</h2><span className="hint">Cálculo determinista sobre sus logs, sin IA</span></div>
            <div className="panel-body"><Evidence f={f} /></div>
          </section>

          <AiBox f={f} />

          <RelatedLogs id={f.id} />

          <section className="panel" aria-labelledby="cm">
            <div className="panel-head"><h2 id="cm">Comentarios</h2></div>
            <div className="panel-body">
              {f.comments && f.comments.length > 0 ? f.comments.map((c) => (
                <div className="comment" key={c.id}><div className="who">{c.author} <span className="muted" style={{ fontWeight: 400 }}>· {fmt.dt(c.created_at)}</span></div><p>{c.body}</p></div>
              )) : <p className="muted">Aún no hay comentarios.</p>}
              {canUpdate && (
                <form onSubmit={addComment} className="stack" style={{ marginTop: 12 }}>
                  <TextArea label="Agregar comentario" value={body} onChange={(e) => setBody(e.target.value)} placeholder="Qué revisó, qué decidió…" />
                  <div><Button type="submit" variant="primary" disabled={!body.trim()} loading={comment.isPending}>Comentar</Button></div>
                </form>
              )}
            </div>
          </section>
        </div>

        <aside className="stack" style={{ gap: 16 }}>
          <section className="panel" aria-labelledby="gest">
            <div className="panel-head"><h2 id="gest">Gestión</h2></div>
            <div className="panel-body stack">
              <SelectField label="Estado" value={f.status} disabled={!canUpdate || patch.isPending} onChange={(e) => patch.mutate({ status: e.target.value as FindingStatus })} options={Object.entries(STATUS_LABEL).map(([value, label]) => ({ value, label }))} />
              <SelectField label="Severidad" value={f.severity} disabled={!canUpdate || patch.isPending} onChange={(e) => patch.mutate({ severity: e.target.value as Severity })} options={SEVERITIES.map((s) => ({ value: s, label: SEVERITY_LABEL[s] }))} />
              <SelectField label="Asignado a" value={f.assigned_to?.id ?? ''} disabled={!canUpdate || patch.isPending} placeholder="Sin asignar"
                onChange={(e) => patch.mutate({ assigned_to_id: e.target.value ? Number(e.target.value) : null })}
                options={[...assignees].map(([value, label]) => ({ value, label }))} />
              <Check label="Es ruido (no requiere atención)" checked={f.is_noise} disabled={!canUpdate || patch.isPending} onChange={(c) => patch.mutate({ is_noise: c })} />
              {!canUpdate && <p className="small muted">Su rol solo permite consultar este hallazgo.</p>}
            </div>
          </section>
          <section className="panel">
            <div className="panel-head"><h2>Contexto</h2></div>
            <dl className="panel-body dl">
              {f.src_ip && <><dt>Origen</dt><dd><Link className="mono" to={`/logs?src_ip=${f.src_ip}`}>{f.src_ip}</Link></dd></>}
              {f.dst_ip && <><dt>Destino</dt><dd><Link className="mono" to={`/logs?dst_ip=${f.dst_ip}`}>{f.dst_ip}{f.dst_port ? `:${f.dst_port}` : ''}</Link></dd></>}
              {f.proto && <><dt>Protocolo</dt><dd>{f.proto.toUpperCase()}</dd></>}
              <dt>Primera vez</dt><dd>{fmt.dt(f.first_seen)}</dd>
              <dt>Última vez</dt><dd>{fmt.dt(f.last_seen)}</dd>
              {f.window_start && <><dt>Ventana</dt><dd>{fmt.dt(f.window_start)} a {fmt.dt(f.window_end)}</dd></>}
              <dt>Creado</dt><dd>{fmt.dt(f.created_at)}</dd>
            </dl>
          </section>
        </aside>
      </div>
    </div>
  )
}
