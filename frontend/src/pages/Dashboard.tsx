import { useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowDownRight, ArrowUpRight, Database, ShieldCheck, TriangleAlert, Upload } from 'lucide-react'
import { api } from '../api/client'
import { useGet } from '../api/hooks'
import type { DashboardSummary, Finding, FlowRow, Health, IngestStatus, RangeKey, Severity, Talker, TopDestination, TopPort, TrafficPoint } from '../api/types'
import { useAuth, useCan } from '../auth/AuthProvider'
import { Button } from '../ui/Button'
import { RangeSelect, Segmented } from '../ui/Controls'
import { DataState, EmptyState, ErrorState, PageHead, Skeleton, SkeletonRows } from '../ui/State'
import { Gauge, SeverityBadge } from '../ui/Gauge'
import { useToast } from '../ui/Toast'
import { bytes, num, ratioPct, useFmt, relative } from '../lib/format'
import { FINDING_TYPE_LABEL, RANGE_LABEL, SEVERITIES, SEVERITY_LABEL } from '../lib/labels'
import { RealNoiseChart, TrafficChart } from '../charts/Charts'
import { FlowSankey } from '../charts/Flows'
import { errMsg } from '../lib/utils'

function loadRange(): RangeKey {
  try { const v = localStorage.getItem('ns-range'); if (v === '1h' || v === '24h' || v === '7d' || v === '30d') return v } catch { /* nada */ }
  return '24h'
}

function Panel({ title, hint, right, span, children, flush = true }: { title: string; hint?: string; right?: ReactNode; span: string; children: ReactNode; flush?: boolean }) {
  return (
    <section className={`panel ${span}`} aria-label={title}>
      <div className="panel-head">
        <div><h2>{title}</h2>{hint && <div className="hint">{hint}</div>}</div>
        {right}
      </div>
      <div className={`panel-body${flush ? ' flush' : ''}`}>{children}</div>
    </section>
  )
}

function Delta({ v, badWhenUp }: { v: number | undefined; badWhenUp?: boolean }) {
  if (v == null) return <span className="delta flat">&nbsp;</span>
  if (Math.abs(v) < 0.05) return <span className="delta flat">sin cambio</span>
  const up = v > 0
  const cls = badWhenUp === undefined ? 'flat' : up === badWhenUp ? 'up-bad' : 'up-good'
  const Icon = up ? ArrowUpRight : ArrowDownRight
  return <span className={`delta ${cls}`}><Icon size={13} aria-hidden />{up ? '+' : ''}{v.toFixed(1).replace('.', ',')} %<span className="sr-only"> frente al período anterior</span></span>
}

export default function Dashboard() {
  const [range, setRangeS] = useState<RangeKey>(loadRange)
  const setRange = (r: RangeKey) => { setRangeS(r); try { localStorage.setItem('ns-range', r) } catch { /* nada */ } }
  const p = { range }
  const summary = useGet<DashboardSummary>('/dashboard/summary', p, { keep: true })
  const can = useCan('ingestion')

  const empty = summary.data && summary.data.total_logs === 0

  return (
    <div className="page">
      <PageHead title="Panel" desc={`Actividad de red en las últimas ${RANGE_LABEL[range].toLowerCase()}.`}>
        <RangeSelect value={range} onChange={setRange} />
      </PageHead>
      {summary.isError ? (
        <div className="panel"><ErrorState error={summary.error} onRetry={() => summary.refetch()} /></div>
      ) : summary.isPending ? (
        <div className="panel"><SkeletonRows rows={5} h={22} /></div>
      ) : empty ? (
        <NoData canExec={can.execute} canView={can.view} />
      ) : (
        <>
          <Verdict s={summary.data!} range={range} />
          <div className="grid">
            <TopTalkers range={range} />
            <RecentFindings range={range} />
          </div>
          <div className="grid">
            <Panel title="Tráfico" hint="Bytes de salida y entrada; abajo, conexiones bloqueadas" span="span-7" flush={false}>
              <Traffic p={p} />
            </Panel>
            <Panel title="Hallazgos reales y ruido filtrado" hint="Lo que la IA y las reglas descartaron no se pierde: sigue consultable" span="span-5" flush={false}>
              <RealNoise p={p} />
            </Panel>
          </div>
          <div className="grid">
            <TopDest p={p} />
            <TopPorts p={p} />
            <Breakdown p={p} />
          </div>
          <Panel title="Flujos origen → destino" hint="Los 18 flujos con más volumen; el grosor es proporcional a los bytes" span="span-12 grid-pad" flush={false}>
            <Flows p={p} />
          </Panel>
        </>
      )}
    </div>
  )
}

function NoData({ canExec, canView }: { canExec: boolean; canView: boolean }) {
  const st = useGet<IngestStatus>('/ingest/status', undefined, { enabled: canView, retry: false })
  const qc = useQueryClient()
  const toast = useToast()
  const demo = useMutation({
    mutationFn: () => api.post('/ingest/dataset', { rebase_time: true }),
    onSuccess: () => { toast.ok('Dataset de demostración cargado.'); void qc.invalidateQueries() },
    onError: (e) => toast.err(errMsg(e)),
  })
  return (
    <section className="panel">
      <EmptyState title="Aún no hay datos de red para mostrar" icon={<Database size={30} aria-hidden />}
        action={
          <div className="row" style={{ justifyContent: 'center' }}>
            {canExec && st.data?.dataset_available && <Button variant="primary" loading={demo.isPending} onClick={() => demo.mutate()}>Cargar dataset de demostración</Button>}
            {canView && <Link className="btn" to="/ingestion"><Upload size={16} /> Subir un archivo de logs</Link>}
          </div>
        }>
        <ol className="state-steps">
          <li>Cargue el dataset de demostración para explorar el panel con datos de ejemplo, o suba un archivo de logs de su firewall (OPNsense), de Suricata o un flujo CTU-13.</li>
          <li>Ejecute la detección: NetSentinel buscará beaconing, exfiltración y puertos inusuales.</li>
          <li>Vuelva aquí: verá en segundos si hay algo que atender.</li>
        </ol>
        {!canExec && !canView && <p>Pida a un administrador que cargue datos.</p>}
        {canView && st.data && !st.data.dataset_available && <p className="small">No se encontró el dataset de demostración en el servidor.</p>}
      </EmptyState>
    </section>
  )
}

function Verdict({ s, range }: { s: DashboardSummary; range: RangeKey }) {
  const sev = useGet<{ severity: Severity; count: number }[]>('/dashboard/findings-by-severity', { range })
  const health = useGet<Health>('/health', undefined, { retry: false })
  const f = useFmt()
  const worst: Severity | null = sev.data ? SEVERITIES.find((x) => (sev.data!.find((r) => r.severity === x)?.count ?? 0) > 0) ?? null : null
  const open = s.open_findings
  const headline = open === 0 ? 'Nada que atender ahora' : `${num(open)} ${open === 1 ? 'hallazgo' : 'hallazgos'} por atender`
  return (
    <section className="panel" style={{ marginBottom: 16 }} aria-label="Resumen">
      <div className="verdict">
        <div className="verdict-main">
          {open === 0 ? <ShieldCheck size={36} color="var(--ok)" aria-hidden /> : <Gauge severity={worst ?? 'info'} large />}
          <div>
            <h2>{headline}</h2>
            <p>
              {open === 0
                ? 'No hay hallazgos reales sin resolver en este rango.'
                : <>{s.critical_findings > 0 ? <><b style={{ color: 'var(--crit-ink)' }}>{num(s.critical_findings)} {s.critical_findings === 1 ? 'crítico' : 'críticos'}</b>. </> : 'Ninguno crítico. '}
                  {num(s.noise_filtered)} descartados como ruido ({ratioPct(s.noise_ratio)}). <Link to="/findings">Revisar hallazgos</Link></>}
            </p>
          </div>
        </div>
        <div className="verdict-side">
          <div><Database size={15} aria-hidden /> <span className="muted">Última ingesta</span> <b title={f.dt(s.last_ingest_at)}>{relative(s.last_ingest_at)}</b></div>
          <div>
            <span className={`dot ${health.data ? (health.data.llm ? 'ok' : 'warn') : ''}`} />
            <span className="muted">Motor IA</span> <b>{health.data ? (health.data.llm ? 'Activo' : 'Sin respuesta: se usa explicación por plantilla') : '—'}</b>
          </div>
          <div><TriangleAlert size={15} aria-hidden /> <span className="muted">Alertas sin acusar</span> <b>{num(s.alerts_unacknowledged)}</b></div>
        </div>
      </div>
      <dl className="kpis" style={{ margin: 0 }}>
        <div className="kpi"><dt>Registros</dt><dd>{num(s.total_logs)}</dd><Delta v={s.deltas.total_logs} /></div>
        <div className="kpi"><dt>Salida de datos</dt><dd>{bytes(s.total_bytes_out)}</dd><span className="delta flat">entrada {bytes(s.total_bytes_in)}</span></div>
        <div className="kpi"><dt>Equipos / destinos</dt><dd>{num(s.unique_sources)} <span className="muted" style={{ fontWeight: 400 }}>/</span> {num(s.unique_destinations)}</dd><Delta v={s.deltas.unique_destinations} /></div>
        <div className="kpi"><dt>Conexiones bloqueadas</dt><dd>{num(s.blocked_connections)}</dd><Delta v={s.deltas.blocked_connections} badWhenUp /></div>
        <div className="kpi"><dt>Hallazgos abiertos</dt><dd>{num(s.open_findings)}</dd><Delta v={s.deltas.open_findings} badWhenUp /></div>
        <div className="kpi"><dt>Ruido filtrado</dt><dd>{num(s.noise_filtered)}</dd><span className="delta flat">{ratioPct(s.noise_ratio)} del total</span></div>
      </dl>
    </section>
  )
}

function TopTalkers({ range }: { range: RangeKey }) {
  const [metric, setMetric] = useState<'bytes' | 'connections' | 'destinations'>('bytes')
  const q = useGet<Talker[]>('/dashboard/top-talkers', { range, metric, limit: 10, direction: 'outbound' }, { keep: true })
  const val = (t: Talker) => (metric === 'bytes' ? t.bytes_out : metric === 'connections' ? t.connections : t.unique_destinations)
  const fmt = (t: Talker) => (metric === 'bytes' ? bytes(t.bytes_out) : num(val(t)))
  const sub = (t: Talker) => (metric === 'bytes' ? `${num(t.connections)} conexiones · ${num(t.unique_destinations)} destinos` : metric === 'connections' ? `${bytes(t.bytes_out)} salida · ${num(t.unique_destinations)} destinos` : `${num(t.connections)} conexiones · ${bytes(t.bytes_out)} salida`)
  return (
    <Panel title="Top talkers" hint="Equipos que más tráfico generan hacia afuera" span="span-7"
      right={<Segmented label="Ordenar por" value={metric} onChange={setMetric} options={[{ value: 'bytes', label: 'Bytes' }, { value: 'connections', label: 'Conexiones' }, { value: 'destinations', label: 'Destinos' }]} />}>
      <DataState q={q} isEmpty={(d) => d.length === 0} empty={<EmptyState title="Sin tráfico saliente en este rango" />}>
        {(rows) => {
          const max = Math.max(...rows.map(val), 1)
          return (
            <ol className="bar-list" aria-label="Top talkers">
              {rows.map((t) => (
                <li key={t.ip} className="bar-row">
                  <div className="bar-label">
                    <Link className="a" to={`/logs?src_ip=${t.ip}`}>{t.ip}</Link>
                    <span className="b">{t.hostname || 'sin nombre'}{t.findings > 0 && <> · <b style={{ color: 'var(--crit-ink)' }}>{t.findings} {t.findings === 1 ? 'hallazgo' : 'hallazgos'}</b></>}</span>
                  </div>
                  <div className="bar-track" aria-hidden><div className={`bar-fill${t.findings > 0 ? ' crit' : ''}`} style={{ width: `${(val(t) / max) * 100}%` }} /></div>
                  <div className="bar-val">{fmt(t)}<small>{sub(t)}</small></div>
                </li>
              ))}
            </ol>
          )
        }}
      </DataState>
    </Panel>
  )
}

function RecentFindings({ range }: { range: RangeKey }) {
  const q = useGet<Finding[]>('/dashboard/recent-findings', { range, limit: 8 })
  const f = useFmt()
  return (
    <Panel title="Hallazgos recientes" hint="Sin ruido filtrado" span="span-5" right={<Link className="small" to="/findings">Ver todos</Link>}>
      <DataState q={q} isEmpty={(d) => d.length === 0} empty={<EmptyState title="Sin hallazgos reales" icon={<ShieldCheck size={26} aria-hidden />}>No se detectó nada que requiera atención en este rango.</EmptyState>}>
        {(rows) => (
          <ul className="recent">
            {rows.map((r) => (
              <li key={r.id}>
                <Link to={`/findings/${r.id}`}>
                  <Gauge severity={r.severity} />
                  <span className="t">{r.title}</span>
                  <span className="m"><SeverityBadge severity={r.severity} /> <span>{FINDING_TYPE_LABEL[r.finding_type]}</span> <span>{f.short(r.last_seen)}</span></span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </DataState>
    </Panel>
  )
}

const Chartish = ({ h = 280 }: { h?: number }) => <div style={{ padding: 16 }}><Skeleton h={h} /></div>

function Traffic({ p }: { p: { range: RangeKey } }) {
  const q = useGet<TrafficPoint[]>('/dashboard/traffic-timeseries', { ...p, bucket: 'auto' }, { keep: true })
  return (
    <DataState q={q} isEmpty={(d) => d.length === 0} skeleton={<Chartish />} empty={<EmptyState title="Sin tráfico en este rango" />}>
      {(d) => (
        <>
          <div className="legend" style={{ marginBottom: 8 }}>
            <span><i style={{ background: 'var(--c-out)' }} />Salida</span>
            <span><i style={{ background: 'var(--c-in)' }} />Entrada</span>
            <span><i style={{ background: 'var(--c-blk)' }} />Conexiones bloqueadas</span>
          </div>
          <TrafficChart data={d} />
        </>
      )}
    </DataState>
  )
}
function RealNoise({ p }: { p: { range: RangeKey } }) {
  const q = useGet<{ ts: string; real: number; noise: number }[]>('/dashboard/findings-timeseries', p, { keep: true })
  return (
    <DataState q={q} isEmpty={(d) => d.length === 0} skeleton={<Chartish h={210} />} empty={<EmptyState title="Sin hallazgos en este rango" />}>
      {(d) => (
        <>
          <div className="legend" style={{ marginBottom: 8 }}>
            <span><i style={{ background: 'var(--crit)' }} />Reales</span>
            <span><i style={{ background: 'var(--line-strong)' }} />Ruido filtrado</span>
          </div>
          <RealNoiseChart data={d} />
        </>
      )}
    </DataState>
  )
}

function TopDest({ p }: { p: { range: RangeKey } }) {
  const q = useGet<TopDestination[]>('/dashboard/top-destinations', { ...p, limit: 8 })
  return (
    <Panel title="Top destinos" hint="Los de lista negra se marcan" span="span-4 t6">
      <DataState q={q} isEmpty={(d) => d.length === 0} empty={<EmptyState title="Sin destinos" />}>
        {(rows) => {
          const max = Math.max(...rows.map((r) => r.bytes), 1)
          return (
            <ol className="bar-list">
              {rows.map((r) => (
                <li key={r.ip} className="bar-row" style={{ gridTemplateColumns: 'minmax(0,1.3fr) minmax(0,1fr) auto' }}>
                  <div className="bar-label">
                    <Link className="a" to={`/logs?dst_ip=${r.ip}`}>{r.ip}</Link>
                    <span className="b">{r.in_denylist ? <span className="badge crit">Lista negra</span> : `${num(r.unique_sources)} ${r.unique_sources === 1 ? 'equipo' : 'equipos'}`}</span>
                  </div>
                  <div className="bar-track" aria-hidden><div className={`bar-fill${r.in_denylist ? ' crit' : ''}`} style={{ width: `${(r.bytes / max) * 100}%` }} /></div>
                  <div className="bar-val" style={{ minWidth: 60 }}>{bytes(r.bytes)}</div>
                </li>
              ))}
            </ol>
          )
        }}
      </DataState>
    </Panel>
  )
}
function TopPorts({ p }: { p: { range: RangeKey } }) {
  const q = useGet<TopPort[]>('/dashboard/top-ports', { ...p, limit: 8 })
  return (
    <Panel title="Top puertos" hint="Los inusuales para su red se marcan" span="span-4 t6">
      <DataState q={q} isEmpty={(d) => d.length === 0} empty={<EmptyState title="Sin puertos" />}>
        {(rows) => {
          const max = Math.max(...rows.map((r) => r.connections), 1)
          return (
            <ol className="bar-list">
              {rows.map((r) => (
                <li key={`${r.proto}${r.port}`} className="bar-row" style={{ gridTemplateColumns: 'minmax(0,1.3fr) minmax(0,1fr) auto' }}>
                  <div className="bar-label">
                    <Link className="a" to={`/logs?dst_port=${r.port}`}>{r.port}/{r.proto}</Link>
                    <span className="b">{r.unusual ? <span className="badge high">Inusual</span> : r.service || 'sin servicio conocido'}</span>
                  </div>
                  <div className="bar-track" aria-hidden><div className={`bar-fill${r.unusual ? ' crit' : ''}`} style={{ width: `${(r.connections / max) * 100}%` }} /></div>
                  <div className="bar-val" style={{ minWidth: 60 }}>{num(r.connections)}</div>
                </li>
              ))}
            </ol>
          )
        }}
      </DataState>
    </Panel>
  )
}
function Breakdown({ p }: { p: { range: RangeKey } }) {
  const sev = useGet<{ severity: Severity; count: number }[]>('/dashboard/findings-by-severity', p)
  const typ = useGet<{ finding_type: keyof typeof FINDING_TYPE_LABEL; count: number; noise: number }[]>('/dashboard/findings-by-type', p)
  return (
    <Panel title="Hallazgos por severidad y tipo" span="span-4 t6">
      <DataState q={sev} skeleton={<SkeletonRows rows={5} />}>
        {(rows) => {
          const by = new Map(rows.map((r) => [r.severity, r.count]))
          const max = Math.max(...rows.map((r) => r.count), 1)
          return (
            <ul className="bar-list" aria-label="Por severidad">
              {SEVERITIES.map((s) => (
                <li key={s} className="bar-row" style={{ gridTemplateColumns: '110px minmax(0,1fr) 36px', padding: '6px 16px' }}>
                  <span className="row" style={{ gap: 6 }}><Gauge severity={s} /> {SEVERITY_LABEL[s]}</span>
                  <div className="bar-track" aria-hidden><div className="bar-fill" style={{ width: `${((by.get(s) ?? 0) / max) * 100}%`, background: `var(--${s === 'critical' ? 'crit' : s === 'medium' ? 'med' : s})` }} /></div>
                  <span className="bar-val" style={{ minWidth: 0 }}>{num(by.get(s) ?? 0)}</span>
                </li>
              ))}
            </ul>
          )
        }}
      </DataState>
      <div style={{ borderTop: '1px solid var(--line)' }}>
        <DataState q={typ} skeleton={<SkeletonRows rows={4} />} isEmpty={(d) => d.length === 0}>
          {(rows) => (
            <table className="t">
              <thead><tr><th>Tipo</th><th className="num">Reales</th><th className="num">Ruido</th></tr></thead>
              <tbody>
                {rows.map((r) => <tr key={r.finding_type}><td>{FINDING_TYPE_LABEL[r.finding_type]}</td><td className="num">{num(r.count)}</td><td className="num muted">{num(r.noise)}</td></tr>)}
              </tbody>
            </table>
          )}
        </DataState>
      </div>
    </Panel>
  )
}
function Flows({ p }: { p: { range: RangeKey } }) {
  const q = useGet<FlowRow[]>('/dashboard/flows', { ...p, limit: 30 })
  useAuth()
  return (
    <DataState q={q} isEmpty={(d) => d.length === 0} skeleton={<Chartish />} empty={<EmptyState title="Sin flujos en este rango" />}>
      {(rows) => <FlowSankey rows={[...rows].sort((a, b) => b.bytes - a.bytes)} />}
    </DataState>
  )
}
