import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { BadgeCheck, Power } from 'lucide-react'
import { api } from '../api/client'
import { useGet } from '../api/hooks'
import { useCan } from '../auth/AuthProvider'
import { Button } from '../ui/Button'
import { SelectField } from '../ui/Fields'
import { DataState, EmptyState, ErrorState, PageHead, SkeletonRows } from '../ui/State'
import { useToast } from '../ui/Toast'
import { useFmt } from '../lib/format'
import { errMsg } from '../lib/utils'
import { SpecGrid, FigureCard, fmtVal, type FigSpec, type Spec } from '../ml/figures'
import { Notice, StatusBadge, isActive, useJob } from '../ml/common'
import { MODEL_LABEL, type MlJob, type MlModel, type Page } from '../ml/types'

interface EvalOut { id: number; status: string; result: { figures: Spec[]; tables: Spec[]; n_folds: number; test_n: number; prevalence: number; models: { run_id: number; model_id: number; name: string; model_type: string }[] } | null }
interface Confusion { threshold: number; model_threshold: number; metrics: Record<string, number>; figures: FigSpec[]; sweep: { threshold: number[]; precision: number[]; recall: number[]; f1: number[] } }

export default function MlEvaluation() {
  const can = useCan('ml_evaluation')
  const [sp, setSp] = useSearchParams()
  const jobId = Number(sp.get('job')) || null
  const jobs = useGet<Page<MlJob>>('/ml/training/jobs', { kind: 'train', page_size: 50 })
  const done = (jobs.data?.items ?? []).filter((j) => j.status === 'succeeded')
  useEffect(() => { if (!jobId && done.length) setSp({ job: String(done[0].id) }, { replace: true }) }, [jobId, done, setSp])
  return (
    <div className="page">
      <PageHead title="Evaluación y comparación" desc="Rendimiento en validación cruzada externa (media, desviación e IC 95 %) y en Prueba, comparación estadística entre modelos y contra los detectores deterministas de NetSentinel." />
      <DataState q={jobs} skeleton={<div className="panel"><SkeletonRows rows={3} /></div>} isEmpty={() => done.length === 0}
        empty={<div className="panel"><EmptyState title="Todavía no hay entrenamientos terminados">Entrene al menos un modelo y la línea base en <Link to="/ml/entrenamiento">Entrenamiento</Link>.</EmptyState></div>}>
        {() => (
          <div className="stack" style={{ gap: 16 }}>
            <section className="panel"><div className="panel-body">
              <SelectField label="Trabajo de entrenamiento a evaluar" value={jobId ?? ''} onChange={(e) => setSp({ job: e.target.value })} options={done.map((j) => ({ value: j.id, label: `#${j.id} · ${j.name}` }))} />
            </div></section>
            {jobId && <Evaluation jobId={jobId} canPromote={can.update} />}
          </div>
        )}
      </DataState>
    </div>
  )
}

function Evaluation({ jobId, canPromote }: { jobId: number; canPromote: boolean }) {
  const qc = useQueryClient()
  const toast = useToast()
  const [evalId, setEvalId] = useState<number | null>(null)
  const start = useMutation({ mutationFn: () => api.post<MlJob>('/ml/evaluation/evaluations', { job_id: jobId }), onSuccess: (j) => setEvalId(j.id), onError: (e) => toast.err(errMsg(e)) })
  const { mutate: startEval } = start
  useEffect(() => { setEvalId(null); startEval() }, [jobId, startEval])
  const job = useJob(evalId)
  const done = job.data?.status === 'succeeded'
  const ev = useGet<EvalOut>(`/ml/evaluation/evaluations/${evalId}`, undefined, { enabled: !!evalId && done })
  const models = useGet<MlModel[]>('/ml/evaluation/models', undefined, { refetchInterval: 10_000 })
  const mine = (models.data ?? []).filter((m) => m.job_id === jobId)
  const best = useMemo(() => mine.filter((m) => !m.is_baseline).sort((a, b) => (b.metrics.cv.pr_auc?.mean ?? 0) - (a.metrics.cv.pr_auc?.mean ?? 0))[0], [mine])
  const promote = useMutation({ mutationFn: (id: number) => api.post(`/ml/evaluation/models/${id}/promote`), onSuccess: () => { toast.ok('Modelo promovido: es el único activo para inferencia.'); void qc.invalidateQueries({ queryKey: ['/ml/evaluation/models'] }); void qc.invalidateQueries({ queryKey: ['/ml/inference/active'] }) }, onError: (e) => toast.err(errMsg(e)) })
  const deact = useMutation({ mutationFn: () => api.post('/ml/evaluation/models/deactivate'), onSuccess: () => { toast.ok('No queda ningún modelo activo.'); void qc.invalidateQueries({ queryKey: ['/ml/evaluation/models'] }); void qc.invalidateQueries({ queryKey: ['/ml/inference/active'] }) }, onError: (e) => toast.err(errMsg(e)) })
  const f = useFmt()
  const nFolds = ev.data?.result?.n_folds
  return (
    <>
      <section className="panel" aria-label="Modelos del trabajo">
        <div className="panel-head"><h2>Modelos del trabajo #{jobId}</h2><span className="hint">Solo el modelo promovido se usa en inferencia y, si se activa, en el pipeline</span></div>
        <DataState q={models} skeleton={<SkeletonRows rows={3} />} isEmpty={() => mine.length === 0} empty={<EmptyState title="Este trabajo no generó modelos" />}>
          {() => (
            <div className="table-wrap"><table className="t">
              <thead><tr><th>Modelo</th><th className="num">PR-AUC CV (media ± desv.)</th><th className="num">IC 95 % (t)</th><th className="num">PR-AUC Prueba</th><th className="num">F1 Prueba</th><th className="num">Umbral</th><th>Calibración</th><th>Estado</th><th /></tr></thead>
              <tbody>{mine.map((m) => {
                const cv = m.metrics.cv.pr_auc
                return (
                  <tr key={m.id}><td className="cell-main">{MODEL_LABEL[m.model_type] ?? m.model_type}{m.is_baseline && <> <span className="badge outline">línea base</span></>}{best?.id === m.id && <> <span className="badge accent">mejor en CV</span></>}</td>
                    <td className="num">{fmtVal(cv?.mean)} ± {fmtVal(cv?.std)}</td><td className="num">[{fmtVal(cv?.ci_t?.[0])}; {fmtVal(cv?.ci_t?.[1])}]</td>
                    <td className="num">{fmtVal(m.metrics.test.pr_auc)}</td><td className="num">{fmtVal(m.metrics.test.f1)}</td><td className="num">{fmtVal(m.threshold)}</td><td>{m.calibration_method}</td>
                    <td>{m.is_active ? <span className="badge ok"><BadgeCheck size={12} />Activo{m.promoted_by ? ` · ${m.promoted_by}, ${f.day(m.promoted_at)}` : ''}</span> : '—'}</td>
                    <td className="actions">{canPromote && !m.is_baseline && !m.is_active && <Button size="sm" variant="primary" onClick={() => promote.mutate(m.id)} loading={promote.isPending && promote.variables === m.id}>Promover a activo</Button>}
                      {canPromote && m.is_active && <Button size="sm" onClick={() => deact.mutate()} loading={deact.isPending}><Power size={13} /> Desactivar</Button>}</td></tr>)
              })}</tbody>
            </table></div>)}
        </DataState>
      </section>

      {mine.some((m) => !m.is_baseline) && <ConfusionPanel models={mine.filter((m) => !m.is_baseline)} />}

      {nFolds !== undefined && nFolds < 10 && (
        <Notice><b>Poca potencia estadística.</b> Con {nFolds} pliegues, la prueba de Wilcoxon exacta no puede dar un p menor que {fmtVal(2 / 2 ** nFolds, 4)}: ninguna comparación entre pares puede resultar significativa a 0,05 tras la corrección de Holm, aunque los modelos difieran mucho. Lea los tamaños de efecto y los intervalos, no solo el valor p.</Notice>
      )}

      {start.isPending || (evalId && !done && job.data?.status !== 'failed' && job.data?.status !== 'cancelled') ? (
        <section className="panel" role="status"><div className="panel-body"><p className="small muted">Calculando la evaluación estadística ({job.data ? <StatusBadge s={job.data.status} /> : 'en cola'}). Esto puede tardar un minuto: incluye bootstrap por grupos y los detectores deterministas sobre la misma partición de Prueba.</p></div><SkeletonRows rows={4} /></section>
      ) : job.data && isActive(job.data.status) ? null : job.data?.status === 'failed' ? (
        <Notice kind="block">La evaluación falló: <span className="mono">{job.data.error}</span></Notice>
      ) : ev.isError ? <ErrorState error={ev.error} onRetry={() => ev.refetch()} /> : ev.data?.result ? (
        <SpecGrid specs={[...ev.data.result.figures, ...ev.data.result.tables]} module="ml_evaluation" />
      ) : null}
    </>
  )
}

function ConfusionPanel({ models }: { models: MlModel[] }) {
  const [runId, setRunId] = useState(models[0].run_id)
  const [thr, setThr] = useState<number | null>(null)
  const [debounced, setDebounced] = useState<number | null>(null)
  useEffect(() => { const t = setTimeout(() => setDebounced(thr), 200); return () => clearTimeout(t) }, [thr])
  const q = useGet<Confusion>(`/ml/evaluation/runs/${runId}/confusion`, { threshold: debounced ?? undefined }, { keep: true })
  const m = models.find((x) => x.run_id === runId)!
  const t = thr ?? q.data?.threshold ?? m.threshold
  const sweep: FigSpec | null = useMemo(() => q.data ? ({
    id: 'sweep', kind: 'lines', title: `Precisión, exhaustividad y F1 según el umbral — ${MODEL_LABEL[m.model_type]}`,
    note: `Prueba, n = ${q.data.metrics.n} (${q.data.metrics.n_pos} Botnet). La línea punteada marca el umbral elegido en Validación (${fmtVal(m.threshold)}).`,
    data: { series: [{ name: 'Precisión', x: q.data.sweep.threshold, y: q.data.sweep.precision }, { name: 'Exhaustividad', x: q.data.sweep.threshold, y: q.data.sweep.recall }, { name: 'F1', x: q.data.sweep.threshold, y: q.data.sweep.f1, bold: true }], xlabel: 'Umbral de decisión', ylabel: 'Valor', xlim: [0, 1], ylim: [0, 1.02] },
    interpretation: { meaning: [`Con umbral ${fmtVal(t, 2)} se detectan ${fmtVal(q.data.metrics.recall * 100, 1)} % de los flujos Botnet (exhaustividad) y ${fmtVal(q.data.metrics.precision * 100, 1)} % de las alertas son correctas (precisión).`, 'Subir el umbral reduce las falsas alarmas pero deja pasar más botnets; bajarlo hace lo contrario.'], caution: [] },
  }) : null, [q.data, m, t])
  return (
    <section className="panel" aria-label="Matriz de confusión con umbral">
      <div className="panel-head"><h2>Matriz de confusión y umbral</h2><span className="hint">Calculada en Prueba; el umbral por defecto se eligió en Validación</span></div>
      <div className="panel-body stack" style={{ gap: 14 }}>
        <div className="form-grid">
          <SelectField label="Modelo" value={runId} onChange={(e) => { setRunId(Number(e.target.value)); setThr(null) }} options={models.map((x) => ({ value: x.run_id, label: MODEL_LABEL[x.model_type] ?? x.model_type }))} />
          <div className="field"><label htmlFor="thr">Umbral de decisión: {fmtVal(t, 2)}</label>
            <input id="thr" className="mlslider" type="range" min={0} max={1} step={0.01} value={t} onChange={(e) => setThr(Number(e.target.value))} aria-valuetext={`${fmtVal(t, 2)}`} />
            <span className="help">Valor del modelo: {fmtVal(m.threshold)} · <button type="button" className="btn ghost sm" onClick={() => setThr(null)}>Restablecer</button></span></div>
        </div>
        {q.isPending ? <SkeletonRows rows={4} /> : q.isError ? <ErrorState error={q.error} onRetry={() => q.refetch()} /> : (
          <div className="mlgrid">{q.data.figures.map((fg) => <FigureCard key={fg.id} spec={fg} module="ml_evaluation" />)}{sweep && <FigureCard spec={sweep} module="ml_evaluation" wide />}</div>
        )}
      </div>
    </section>
  )
}
