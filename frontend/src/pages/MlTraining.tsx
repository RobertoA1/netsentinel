import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Ban, Play, RotateCcw, SlidersHorizontal } from 'lucide-react'
import { api } from '../api/client'
import { useGet } from '../api/hooks'
import { useCan } from '../auth/AuthProvider'
import { Button } from '../ui/Button'
import { Dialog } from '../ui/Dialog'
import { Check, SelectField, TextField } from '../ui/Fields'
import { DataState, EmptyState, ErrorState, PageHead, SkeletonRows } from '../ui/State'
import { useToast } from '../ui/Toast'
import { duration, num, useFmt } from '../lib/format'
import { errMsg } from '../lib/utils'
import { SpecGrid, fmtVal, type Spec } from '../ml/figures'
import { Bar, DatasetPicker, JobTable, Kv, Notice, StatusBadge, isActive, useDatasets, useJob, useJobLog } from '../ml/common'
import { SpaceEditor, diffOverrides, narrowAround, overridesValid, type Overrides } from '../ml/SpaceEditor'
import { METRIC_LABEL, MODEL_LABEL, type MlJob, type ModelSpace, type Page, type Validation } from '../ml/types'

interface Spaces { models: ModelSpace[]; metrics: string[]; max_trials: number; protocol: Record<string, string | number> }
interface Analysis { figures: Spec[]; tables: Spec[]; runs: { run_id: number; model_type: string; duration_s: number; summary: any; final_params: Record<string, unknown>; test_metrics: Record<string, number> }[] }
const MODEL_ORDER = ['dummy', 'logreg', 'random_forest', 'hist_gb', 'xgboost']

export default function MlTraining() {
  const can = useCan('ml_training')
  const [sp, setSp] = useSearchParams()
  const jobId = Number(sp.get('job')) || null
  const jobs = useGet<Page<MlJob>>('/ml/training/jobs', { kind: 'train', page_size: 30 }, { refetchInterval: 5000 })
  const pick = (id: number) => { const n = new URLSearchParams(sp); n.set('job', String(id)); setSp(n) }
  return (
    <div className="page">
      <PageHead title="Entrenamiento" desc="Validación cruzada anidada 5×3 por grupos (la búsqueda de hiperparámetros solo ve los pliegues internos), modelo final con umbral y calibración en Validación, y una única evaluación en Prueba." />
      {can.execute && <NewTraining onLaunched={pick} />}
      <section className="panel" aria-label="Trabajos de entrenamiento">
        <div className="panel-head"><h2>Trabajos</h2><span className="hint">Se actualiza solo mientras hay trabajos activos</span></div>
        <DataState q={jobs} skeleton={<SkeletonRows rows={3} />} isEmpty={(d) => d.items.length === 0} empty={<EmptyState title="Aún no hay entrenamientos">Configure uno arriba. Corre en segundo plano en el servicio ml-worker; puede cerrar la página y volver.</EmptyState>}>
          {(d) => <JobTable jobs={d.items} current={jobId} onPick={pick} />}
        </DataState>
      </section>
      {jobId ? <Monitor id={jobId} canRun={can.execute} /> : null}
    </div>
  )
}

/* ------------------------------------------------------------------------------------------ formulario */
function NewTraining({ onLaunched }: { onLaunched: (id: number) => void }) {
  const toast = useToast()
  const qc = useQueryClient()
  const [sp] = useSearchParams()
  const studyId = Number(sp.get('study')) || null
  const spaces = useGet<Spaces>('/ml/training/spaces')
  const datasets = useDatasets()
  const [vid, setVid] = useState<number | null>(null)
  const [sel, setSel] = useState<Record<string, boolean>>({ dummy: true, logreg: true, random_forest: false, hist_gb: false, xgboost: false })
  const [over, setOver] = useState<Record<string, Overrides>>({})
  const [edit, setEdit] = useState<string | null>(null)
  const [f, setF] = useState({ n_trials: '20', metric: 'pr_auc', sampler: 'tpe', pruner: 'median', seed: '42', time_limit: '' })
  const [fromStudy, setFromStudy] = useState<number | null>(null)
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF((x) => ({ ...x, [k]: e.target.value }))

  useEffect(() => { if (vid === null && datasets.data?.length) setVid(datasets.data[0].current_version_id) }, [datasets.data, vid])

  // «Usar estos hiperparámetros»: llega desde Optuna con ?study=ID y acota los rangos alrededor del mejor trial.
  const best = useGet<{ job_id: number; model_type: string; best_params: Record<string, unknown>; dataset_version_id: number }>(`/ml/optuna/studies/${studyId}/best`, undefined, { enabled: !!studyId, retry: false })
  useEffect(() => {
    if (!best.data || !spaces.data || fromStudy === best.data.job_id) return
    const ms = spaces.data.models.find((m) => m.model === best.data!.model_type)
    if (!ms) return
    setFromStudy(best.data.job_id)
    setSel({ dummy: true, logreg: false, random_forest: false, hist_gb: false, xgboost: false, [best.data.model_type]: true })
    setOver({ [best.data.model_type]: narrowAround(ms, best.data.best_params) })
    setVid(best.data.dataset_version_id)
    setEdit(best.data.model_type)
  }, [best.data, spaces.data, fromStudy])

  const val = useGet<Validation>(`/ml/data/versions/${vid}/validation`, undefined, { enabled: !!vid, staleTime: 60_000 })
  const chosen = val.data?.keys[val.data.chosen]
  const blocked = !!chosen && !chosen.viable
  const nTrials = Number(f.n_trials)
  const errTrials = !Number.isInteger(nTrials) || nTrials < 1 || nTrials > (spaces.data?.max_trials ?? 300) ? `Entre 1 y ${spaces.data?.max_trials ?? 300}.` : null
  const chosenModels = MODEL_ORDER.filter((m) => sel[m])
  const spaceOf = (m: string) => spaces.data?.models.find((x) => x.model === m)
  const okSpaces = chosenModels.every((m) => { const s = spaceOf(m); return !s || !over[m] || overridesValid(s, over[m]) })
  const go = useMutation({
    mutationFn: () => api.post<MlJob>('/ml/training/jobs', {
      dataset_version_id: vid, metric: f.metric, n_trials: nTrials, sampler: f.sampler, pruner: f.pruner, seed: Number(f.seed), from_study: fromStudy,
      time_limit_s: f.time_limit ? Number(f.time_limit) * 60 : undefined,
      models: chosenModels.map((m) => ({ type: m, space: spaceOf(m) && over[m] ? diffOverrides(spaceOf(m)!, over[m]) : null })),
    }),
    onSuccess: (j) => { toast.ok(`Entrenamiento #${j.id} en cola.`); void qc.invalidateQueries({ queryKey: ['/ml/training/jobs'] }); onLaunched(j.id) },
    onError: (e) => toast.err(errMsg(e)),
  })
  const sm = edit ? spaceOf(edit) : null
  return (
    <section className="panel" aria-label="Nuevo entrenamiento">
      <div className="panel-head"><h2>Nuevo entrenamiento</h2><span className="hint">Protocolo fijo: partición 70/15/15 por grupos · CV anidada 5 externos × 3 internos · Optuna solo en pliegues internos</span></div>
      <DataState q={spaces} skeleton={<SkeletonRows rows={4} />}>
        {() => (
          <div className="panel-body stack" style={{ gap: 16 }}>
            {fromStudy && <Notice>Rangos acotados alrededor del mejor trial del estudio #{fromStudy}. Revíselos con «Editar espacio» antes de lanzar.</Notice>}
            <div className="form-grid">
              <DatasetPicker value={vid} onChange={setVid} help="Define unidad (flujo o ventana) y agrupación; ambas se guardan con el modelo." />
              <SelectField label="Métrica objetivo de la búsqueda" value={f.metric} onChange={set('metric')} options={(spaces.data?.metrics ?? []).map((m) => ({ value: m, label: METRIC_LABEL[m] ?? m }))} help="PR-AUC es la más informativa con clases desbalanceadas." />
              <TextField label="Trials por búsqueda" inputMode="numeric" value={f.n_trials} onChange={set('n_trials')} error={errTrials} help="Hay una búsqueda por pliegue externo y otra final." />
              <SelectField label="Muestreador" value={f.sampler} onChange={set('sampler')} options={[{ value: 'tpe', label: 'TPE (bayesiano)' }, { value: 'random', label: 'Aleatorio' }, { value: 'cmaes', label: 'CMA-ES' }]} />
              <SelectField label="Podador" value={f.pruner} onChange={set('pruner')} options={[{ value: 'median', label: 'Mediana' }, { value: 'hyperband', label: 'Hyperband' }, { value: 'none', label: 'Sin poda' }]} />
              <TextField label="Semilla" inputMode="numeric" value={f.seed} onChange={set('seed')} help="Con la misma semilla y datos, el resultado se reproduce." />
              <TextField label="Límite de tiempo (min, opcional)" inputMode="numeric" value={f.time_limit} onChange={set('time_limit')} help="Por defecto 120 min. El trabajo se detiene al cumplirse." />
            </div>
            {vid && val.isPending && <p className="small muted" role="status">Validando la agrupación del dataset…</p>}
            {val.isError && <ErrorState error={val.error} />}
            {blocked && chosen && (
              <Notice kind="block"><b>Entrenamiento bloqueado por la validación de grupos.</b> {chosen.blocking[0]} {val.data?.recommended && <>Recomendación: usar «{val.data.recommended === 'time_block' ? 'bloque temporal' : val.data.recommended}»{val.data.recommended_block_seconds ? ` de ${val.data.recommended_block_seconds} s` : ''} desde <Link to="/ml/datos">Datos</Link>.</>}</Notice>
            )}
            <fieldset style={{ border: 0, padding: 0, margin: 0 }}>
              <legend className="small" style={{ fontWeight: 600, marginBottom: 6 }}>Modelos a entrenar</legend>
              <div className="mlmodels">
                {MODEL_ORDER.map((m) => (
                  <div key={m} className={`mrow${sel[m] ? ' on' : ''}`}>
                    <Check checked={!!sel[m]} onChange={(v) => setSel((s) => ({ ...s, [m]: v }))} label={`${MODEL_LABEL[m]}${m === 'dummy' ? ' (línea base obligatoria para comparar)' : ''}${over[m] ? ' · espacio editado' : ''}`} />
                    {m !== 'dummy' && <Button size="sm" variant="ghost" onClick={() => setEdit(m)} disabled={!spaceOf(m)}><SlidersHorizontal size={13} /> Editar espacio</Button>}
                  </div>))}
              </div>
            </fieldset>
            <div className="row"><Button variant="primary" loading={go.isPending} disabled={blocked || !vid || !chosenModels.length || !!errTrials || !okSpaces || !Number.isInteger(Number(f.seed))} onClick={() => go.mutate()}><Play size={15} /> Lanzar entrenamiento</Button>
              <span className="small muted">{chosenModels.length} modelo(s) · ~{num(chosenModels.filter((m) => m !== 'dummy').length * 6 * (Number.isFinite(nTrials) ? nTrials : 0))} trials en total</span></div>
          </div>
        )}
      </DataState>
      {sm && edit && (
        <Dialog open onClose={() => setEdit(null)} wide title={`Espacio de búsqueda · ${sm.label}`} footer={<><Button onClick={() => { setOver((o) => { const n = { ...o }; delete n[edit]; return n }); setEdit(null) }}>Restablecer</Button><Button variant="primary" disabled={!overridesValid(sm, over[edit] ?? {})} onClick={() => setEdit(null)}>Aceptar</Button></>}>
          <div className="stack">
            <p className="small muted">Los rangos deben quedar dentro del límite duro del servidor. Cada parámetro explica por qué se eligió ese rango.</p>
            <SpaceEditor space={sm} value={over[edit] ?? {}} onChange={(v) => setOver((o) => ({ ...o, [edit]: v }))} />
            {Object.keys(sm.fixed).length > 0 && <p className="small muted">Fijos: {fmtVal(sm.fixed)}</p>}
          </div>
        </Dialog>
      )}
    </section>
  )
}

/* ------------------------------------------------------------------------------------------ monitor */
function Monitor({ id, canRun }: { id: number; canRun: boolean }) {
  const toast = useToast()
  const qc = useQueryClient()
  const q = useJob(id)
  const j = q.data
  const active = isActive(j?.status)
  const log = useJobLog(id, active)
  const analysis = useGet<Analysis>(`/ml/training/jobs/${id}/analysis`, undefined, { refetchInterval: active ? 12_000 : false, retry: false })
  const f = useFmt()
  const cancel = useMutation({ mutationFn: () => api.post(`/ml/training/jobs/${id}/cancel`), onSuccess: () => { toast.ok('Cancelación solicitada.'); void qc.invalidateQueries({ queryKey: ['/ml/job', id] }) }, onError: (e) => toast.err(errMsg(e)) })
  const retry = useMutation({ mutationFn: () => api.post(`/ml/training/jobs/${id}/retry`), onSuccess: () => { toast.ok('Trabajo reencolado.'); void qc.invalidateQueries({ queryKey: ['/ml/job', id] }) }, onError: (e) => toast.err(errMsg(e)) })
  const pr = j?.progress ?? {}
  const frac = pr.units_total ? pr.units_done / pr.units_total : j?.status === 'succeeded' ? 1 : 0
  const logText = log.data?.text ?? ''
  const logLines = useMemo(() => logText.split('\n').slice(-60).join('\n'), [logText])
  if (q.isPending) return <section className="panel"><SkeletonRows rows={5} /></section>
  if (q.isError) return <section className="panel"><ErrorState error={q.error} onRetry={() => q.refetch()} /></section>
  if (!j) return null
  return (
    <div className="stack" style={{ gap: 16 }}>
      <section className="panel" aria-label={`Trabajo ${j.id}`} aria-live="polite">
        <div className="panel-head">
          <h2>Trabajo #{j.id} <StatusBadge s={j.status} /></h2>
          <span className="row" style={{ gap: 6 }}>
            {canRun && active && <Button size="sm" onClick={() => cancel.mutate()} loading={cancel.isPending} disabled={j.status === 'cancel_requested'}><Ban size={14} /> Cancelar</Button>}
            {canRun && (j.status === 'failed' || j.status === 'cancelled') && <Button size="sm" onClick={() => retry.mutate()} loading={retry.isPending}><RotateCcw size={14} /> Reintentar</Button>}
          </span>
        </div>
        <div className="panel-body stack" style={{ gap: 12 }}>
          <p className="small muted" style={{ overflowWrap: 'anywhere' }}>{j.name}</p>
          {j.status === 'failed' && <Notice kind="block"><b>El trabajo falló.</b> <span className="mono" style={{ overflowWrap: 'anywhere' }}>{j.error}</span> Revise el registro de abajo y use «Reintentar».</Notice>}
          {j.status === 'queued' && <p className="small muted" role="status">En cola: el servicio ml-worker lo tomará en unos segundos.</p>}
          <div>
            <div className="row between small"><span>{active || j.status === 'succeeded' ? `${num(pr.units_done ?? 0)} de ${num(pr.units_total ?? 0)} trials` : 'Sin avance'}{pr.current?.model ? ` · ${MODEL_LABEL[pr.current.model] ?? pr.current.model}${typeof pr.current.outer === 'number' ? `, pliegue externo ${pr.current.outer}` : pr.current.outer === 'final' ? ', modelo final' : ''}` : ''}</span><span className="muted">{active && pr.eta_s ? `quedan ~${duration(pr.eta_s)}` : j.finished_at && j.started_at ? `duró ${duration((new Date(j.finished_at).getTime() - new Date(j.started_at).getTime()) / 1000)}` : ''}</span></div>
            <Bar value={frac} label="Progreso del entrenamiento" />
          </div>
          <div className="form-grid" style={{ alignItems: 'start' }}>
            <Kv rows={[['Semilla', j.seed], ['Inicio', f.dt(j.started_at)], ['Fin', f.dt(j.finished_at)], ['Límite de tiempo', j.time_limit_s ? duration(j.time_limit_s) : '—'], ['Intentos', j.attempts], ['Lanzado por', j.created_by]]} />
            <Kv rows={[['Procesos', j.resources?.pid ? `PID ${j.resources.pid}` : '—'], ['CPU', j.resources?.cpu_percent != null ? `${fmtVal(j.resources.cpu_percent, 0)} % (${j.resources.cpu_count} núcleos)` : '—'], ['Memoria', j.resources?.rss_mb != null ? `${fmtVal(j.resources.rss_mb, 0)} MB de ${fmtVal((j.resources.mem_total_mb ?? 0) / 1024, 1)} GB` : '—'], ['Mejor valor visto', pr.best_value != null ? fmtVal(pr.best_value, 4) : '—'], ['Librerías', j.libs ? `scikit-learn ${j.libs['scikit-learn']}, optuna ${j.libs.optuna}, shap ${j.libs.shap}` : '—']]} />
          </div>
          {j.runs && j.runs.length > 0 && (
            <div className="table-wrap"><table className="t">
              <thead><tr><th>Modelo</th><th>Estado</th><th className="num">PR-AUC (CV externa)</th><th className="num">PR-AUC (Prueba)</th><th className="num">Duración</th></tr></thead>
              <tbody>{j.runs.map((r) => <tr key={r.id}><td className="cell-main">{MODEL_LABEL[r.model_type] ?? r.model_type}</td><td>{r.status === 'succeeded' ? <span className="badge ok">Listo</span> : r.status === 'running' ? <span className="badge accent">En curso</span> : <span className="badge">{r.status === 'pending' ? 'Pendiente' : r.status}</span>}</td><td className="num">{fmtVal(r.pr_auc_cv)}</td><td className="num">{fmtVal(r.pr_auc_test)}</td><td className="num">{r.duration_s != null ? duration(r.duration_s) : '—'}</td></tr>)}</tbody>
            </table></div>)}
          <details><summary className="small" style={{ cursor: 'pointer' }}>Registro del trabajo</summary><pre className="mllog" tabIndex={0} aria-label="Registro del trabajo">{logLines || 'Sin registro todavía.'}</pre></details>
        </div>
      </section>
      {analysis.isSuccess && analysis.data.runs.length > 0 && (
        <>
          <section className="panel" aria-label="Hiperparámetros finales">
            <div className="panel-head"><h3>Mejores hiperparámetros del modelo final</h3><span className="hint">Búsqueda sobre todo Desarrollo; umbral y calibración en Validación</span></div>
            <div className="table-wrap"><table className="t"><thead><tr><th>Modelo</th><th>Hiperparámetros</th><th className="num">Prueba: PR-AUC</th><th className="num">Prueba: F1</th></tr></thead>
              <tbody>{analysis.data.runs.map((r) => <tr key={r.run_id}><td className="cell-main">{MODEL_LABEL[r.model_type]}</td><td className="mono" style={{ fontSize: 12, whiteSpace: 'normal' }}>{Object.keys(r.final_params).length ? fmtVal(r.final_params, 4) : '—'}</td><td className="num">{fmtVal(r.test_metrics?.pr_auc)}</td><td className="num">{fmtVal(r.test_metrics?.f1)}</td></tr>)}</tbody></table></div>
          </section>
          <SpecGrid specs={[...analysis.data.figures, ...analysis.data.tables]} module="ml_training" />
          {j.status === 'succeeded' && <p className="small">Siguiente paso: <Link to={`/ml/evaluacion?job=${j.id}`}>evaluar y comparar los modelos de este trabajo</Link>.</p>}
        </>
      )}
    </div>
  )
}
