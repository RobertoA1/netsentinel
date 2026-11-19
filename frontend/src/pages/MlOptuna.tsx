import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Ban, ArrowRight, FlaskConical, SlidersHorizontal, Trash2 } from 'lucide-react'
import { api } from '../api/client'
import { useGet } from '../api/hooks'
import { useCan } from '../auth/AuthProvider'
import { Button } from '../ui/Button'
import { Dialog } from '../ui/Dialog'
import { SelectField, TextField } from '../ui/Fields'
import { DataState, EmptyState, ErrorState, PageHead, SkeletonRows } from '../ui/State'
import { useToast } from '../ui/Toast'
import { duration, useFmt } from '../lib/format'
import { errMsg } from '../lib/utils'
import { SpecGrid, fmtVal, type Spec } from '../ml/figures'
import { Bar, DatasetPicker, Kv, Notice, StatusBadge, isActive, useJob, useJobLog } from '../ml/common'
import { SpaceEditor, diffOverrides, overridesValid, type Overrides } from '../ml/SpaceEditor'
import { METRIC_LABEL, MODEL_LABEL, type MlJob, type ModelSpace, type Page } from '../ml/types'

interface Options { samplers: string[]; pruners: string[]; metrics: string[]; max_trials: number; models: ModelSpace[]; notes: Record<string, string> }
interface Trial { number: number; state: string; state_es: string; value: number | null; params: Record<string, unknown>; duration_s: number | null }
interface Summary { n_trials: number; n_complete: number; n_pruned: number; n_running: number; best_value: number | null; best_number: number | null; best_params: Record<string, unknown> }
interface Detail extends MlJob { trials: Trial[]; summary: Summary | null; space: { name: string }[] }
const SAMPLERS: Record<string, string> = { tpe: 'TPE (bayesiano)', random: 'Aleatorio', cmaes: 'CMA-ES' }
const PRUNERS: Record<string, string> = { median: 'Mediana', hyperband: 'Hyperband', none: 'Sin poda' }

export default function MlOptuna() {
  const can = useCan('ml_optuna')
  const [sp, setSp] = useSearchParams()
  const id = Number(sp.get('study')) || null
  const list = useGet<Page<MlJob & { best_value: number | null }>>('/ml/optuna/studies', { page_size: 30 }, { refetchInterval: 5000 })
  const [open, setOpen] = useState(false)
  return (
    <div className="page">
      <PageHead title="Optimización con Optuna" desc="Busque hiperparámetros con estudios persistidos en PostgreSQL. Los resultados se dibujan desde datos del servidor y se pueden llevar a Entrenamiento.">
        {can.create && <Button variant="primary" onClick={() => setOpen(true)}><FlaskConical size={15} /> Nuevo estudio</Button>}
      </PageHead>
      <section className="panel" aria-label="Estudios">
        <DataState q={list} skeleton={<SkeletonRows rows={3} />} isEmpty={(d) => d.items.length === 0} empty={<EmptyState title="Aún no hay estudios">{can.create ? 'Cree uno con «Nuevo estudio».' : 'Un usuario con permiso de creación puede lanzar el primero.'}</EmptyState>}>
          {(d) => (
            <div className="table-wrap"><table className="t"><thead><tr><th>#</th><th>Estudio</th><th>Estado</th><th className="num">Mejor valor</th><th>Muestreador / poda</th></tr></thead>
              <tbody>{d.items.map((j) => <tr key={j.id} className={`clickable${id === j.id ? ' sel' : ''}`} tabIndex={0} onClick={() => setSp({ study: String(j.id) })} onKeyDown={(e) => { if (e.key === 'Enter') setSp({ study: String(j.id) }) }}>
                <td className="num">{j.id}</td><td className="cell-main">{j.name}</td><td><StatusBadge s={j.status} /></td><td className="num">{fmtVal(j.best_value, 4)}</td><td>{SAMPLERS[j.params.sampler]} / {PRUNERS[j.params.pruner]}</td></tr>)}</tbody></table></div>)}
        </DataState>
      </section>
      {id && <StudyView id={id} canCancel={can.execute} canDelete={can.delete} canTrain={true} onDeleted={() => setSp({})} />}
      {open && <NewStudy onClose={() => setOpen(false)} onCreated={(j) => { setOpen(false); setSp({ study: String(j.id) }) }} />}
    </div>
  )
}

function NewStudy({ onClose, onCreated }: { onClose: () => void; onCreated: (j: MlJob) => void }) {
  const toast = useToast()
  const qc = useQueryClient()
  const opts = useGet<Options>('/ml/optuna/options')
  const [vid, setVid] = useState<number | null>(null)
  const [model, setModel] = useState('random_forest')
  const [over, setOver] = useState<Record<string, Overrides>>({})
  const [f, setF] = useState({ n_trials: '30', timeout: '', sampler: 'tpe', pruner: 'median', metric: 'pr_auc', seed: '42', n_folds: '3' })
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF((x) => ({ ...x, [k]: e.target.value }))
  const ms = opts.data?.models.find((m) => m.model === model)
  const max = opts.data?.max_trials ?? 300
  const nt = Number(f.n_trials)
  const e1 = !Number.isInteger(nt) || nt < 1 || nt > max ? `Entre 1 y ${max}.` : null
  const nf = Number(f.n_folds)
  const e2 = !Number.isInteger(nf) || nf < 2 || nf > 10 ? 'Entre 2 y 10.' : null
  const e3 = f.timeout && (!Number.isInteger(Number(f.timeout)) || Number(f.timeout) < 1 || Number(f.timeout) > 240) ? 'Entre 1 y 240 min.' : null
  const ok = !!vid && !e1 && !e2 && !e3 && !!ms && overridesValid(ms, over[model] ?? {})
  const mut = useMutation({
    mutationFn: () => api.post<MlJob>('/ml/optuna/studies', { dataset_version_id: vid, model_type: model, space: ms && over[model] ? diffOverrides(ms, over[model]) : null, n_trials: nt, timeout_s: f.timeout ? Number(f.timeout) * 60 : undefined, sampler: f.sampler, pruner: f.pruner, metric: f.metric, seed: Number(f.seed), n_folds: nf }),
    onSuccess: (j) => { toast.ok(`Estudio #${j.id} en cola.`); void qc.invalidateQueries({ queryKey: ['/ml/optuna/studies'] }); onCreated(j) }, onError: (e) => toast.err(errMsg(e)),
  })
  const [showSpace, setShowSpace] = useState(false)
  return (
    <Dialog open onClose={onClose} wide title="Nuevo estudio de Optuna" footer={<><Button onClick={onClose}>Cancelar</Button><Button variant="primary" disabled={!ok} loading={mut.isPending} onClick={() => mut.mutate()}>Lanzar estudio</Button></>}>
      <DataState q={opts} skeleton={<SkeletonRows rows={5} />}>
        {(o) => (
          <div className="stack">
            <div className="form-grid">
              <DatasetPicker value={vid} onChange={setVid} help="El estudio usa solo la partición de Desarrollo, con validación cruzada agrupada." />
              <SelectField label="Modelo" value={model} onChange={(e) => { setModel(e.target.value); setShowSpace(false) }} options={o.models.map((m) => ({ value: m.model, label: MODEL_LABEL[m.model] ?? m.label }))} />
              <SelectField label="Métrica" value={f.metric} onChange={set('metric')} options={o.metrics.map((m) => ({ value: m, label: METRIC_LABEL[m] ?? m }))} help={o.notes.direction} />
              <TextField label="Trials" inputMode="numeric" value={f.n_trials} onChange={set('n_trials')} error={e1} />
              <TextField label="Tiempo máximo (min, opcional)" inputMode="numeric" value={f.timeout} onChange={set('timeout')} error={e3} />
              <SelectField label="Muestreador" value={f.sampler} onChange={set('sampler')} options={o.samplers.map((s) => ({ value: s, label: SAMPLERS[s] ?? s }))} help={f.sampler === 'cmaes' ? o.notes.cmaes : undefined} />
              <SelectField label="Podador" value={f.pruner} onChange={set('pruner')} options={o.pruners.map((s) => ({ value: s, label: PRUNERS[s] ?? s }))} />
              <TextField label="Pliegues de validación" inputMode="numeric" value={f.n_folds} onChange={set('n_folds')} error={e2} />
              <TextField label="Semilla" inputMode="numeric" value={f.seed} onChange={set('seed')} />
            </div>
            <div><Button size="sm" onClick={() => setShowSpace((s) => !s)}><SlidersHorizontal size={13} /> {showSpace ? 'Ocultar rangos' : 'Editar rangos'}{over[model] ? ' (editados)' : ''}</Button></div>
            {showSpace && ms && <SpaceEditor space={ms} value={over[model] ?? {}} onChange={(v) => setOver((x) => ({ ...x, [model]: v }))} />}
          </div>)}
      </DataState>
    </Dialog>
  )
}

function StudyView({ id, canCancel, canDelete, canTrain, onDeleted }: { id: number; canCancel: boolean; canDelete: boolean; canTrain: boolean; onDeleted: () => void }) {
  const toast = useToast()
  const qc = useQueryClient()
  const nav = useNavigate()
  const f = useFmt()
  const job = useJob(id)
  const active = isActive(job.data?.status)
  const d = useGet<Detail>(`/ml/optuna/studies/${id}`, undefined, { refetchInterval: active ? 3000 : false })
  const viz = useGet<{ figures: Spec[]; summary: Summary }>(`/ml/optuna/studies/${id}/viz`, undefined, { refetchInterval: active ? 10_000 : false, retry: false })
  const log = useJobLog(id, active)
  const cancel = useMutation({ mutationFn: () => api.post(`/ml/training/jobs/${id}/cancel`), onSuccess: () => { toast.ok('Cancelación solicitada.'); void qc.invalidateQueries({ queryKey: ['/ml/job', id] }) }, onError: (e) => toast.err(errMsg(e)) })
  const del = useMutation({ mutationFn: () => api.del(`/ml/optuna/studies/${id}`), onSuccess: () => { toast.ok('Estudio eliminado.'); void qc.invalidateQueries({ queryKey: ['/ml/optuna/studies'] }); onDeleted() }, onError: (e) => toast.err(errMsg(e)) })
  useEffect(() => { if (job.data && !active) void qc.invalidateQueries({ queryKey: [`/ml/optuna/studies/${id}`] }) }, [job.data, active, id, qc])
  if (d.isPending) return <section className="panel"><SkeletonRows rows={5} /></section>
  if (d.isError) return <section className="panel"><ErrorState error={d.error} onRetry={() => d.refetch()} /></section>
  const s = d.data
  const st = job.data?.status ?? s.status
  const pr = (job.data ?? s).progress ?? {}
  const total = s.params.n_trials as number
  const done = s.summary ? s.summary.n_complete + s.summary.n_pruned : 0
  const hasBest = !!s.summary?.best_value && Object.keys(s.summary.best_params).length > 0
  return (
    <div className="stack" style={{ gap: 16 }}>
      <section className="panel" aria-label={`Estudio ${id}`} aria-live="polite">
        <div className="panel-head"><h2>Estudio #{id} <StatusBadge s={st} /></h2>
          <span className="row" style={{ gap: 6 }}>
            {canCancel && active && <Button size="sm" onClick={() => cancel.mutate()} loading={cancel.isPending} disabled={st === 'cancel_requested'}><Ban size={14} /> Cancelar</Button>}
            {canTrain && hasBest && <Button size="sm" variant="primary" onClick={() => nav(`/ml/entrenamiento?study=${id}`)}>Usar estos hiperparámetros <ArrowRight size={14} /></Button>}
            {canDelete && !active && <Button size="sm" variant="danger" onClick={() => { if (window.confirm('¿Eliminar este estudio y sus trials? No se puede deshacer.')) del.mutate() }} loading={del.isPending}><Trash2 size={14} /> Eliminar</Button>}
          </span></div>
        <div className="panel-body stack">
          <p className="small muted">{s.name}</p>
          {st === 'failed' && <Notice kind="block"><b>El estudio falló.</b> <span className="mono">{s.error}</span></Notice>}
          <div><div className="row between small"><span>{done} de {total} trials{s.summary?.n_running ? ` · ${s.summary.n_running} en curso` : ''}</span><span className="muted">{active && pr.eta_s ? `quedan ~${duration(pr.eta_s)}` : ''}</span></div><Bar value={total ? done / total : 0} label="Progreso del estudio" /></div>
          <div className="form-grid" style={{ alignItems: 'start' }}>
            <Kv rows={[['Modelo', MODEL_LABEL[s.params.model_type]], ['Métrica', METRIC_LABEL[s.params.metric] ?? s.params.metric], ['Muestreador', SAMPLERS[s.params.sampler]], ['Podador', PRUNERS[s.params.pruner]], ['Semilla', s.seed], ['Pliegues', s.params.n_folds], ['Inicio', f.dt(s.started_at)]]} />
            <Kv rows={[['Mejor valor', s.summary?.best_value != null ? fmtVal(s.summary.best_value, 4) : '—'], ['Mejor trial', s.summary?.best_number != null ? `#${s.summary.best_number}` : '—'], ['Completos / podados', s.summary ? `${s.summary.n_complete} / ${s.summary.n_pruned}` : '—'], ['Mejores hiperparámetros', hasBest ? <span className="mono" style={{ fontSize: 12 }}>{fmtVal(s.summary!.best_params, 4)}</span> : '—']]} />
          </div>
          {hasBest && <p className="small muted">«Usar estos hiperparámetros» abre <Link to={`/ml/entrenamiento?study=${id}`}>Entrenamiento</Link> con los rangos acotados alrededor del mejor trial; allí se entrena con validación anidada completa.</p>}
          <details><summary className="small" style={{ cursor: 'pointer' }}>Registro</summary><pre className="mllog" tabIndex={0}>{log.data?.text?.split('\n').slice(-40).join('\n') || 'Sin registro todavía.'}</pre></details>
        </div>
      </section>
      <section className="panel" aria-label="Trials">
        <div className="panel-head"><h3>Trials{active ? ' (en vivo)' : ''}</h3><span className="hint">Los últimos {Math.min(s.trials.length, 300)}</span></div>
        {s.trials.length === 0 ? <EmptyState title="Aún no hay trials">El estudio se está preparando.</EmptyState> : (
          <div className="table-wrap" style={{ maxHeight: 340, overflow: 'auto' }}><table className="t"><thead><tr><th className="num">#</th><th>Estado</th><th className="num">{METRIC_LABEL[s.params.metric]}</th><th className="num">Duración</th><th>Hiperparámetros</th></tr></thead>
            <tbody>{[...s.trials].reverse().map((t) => <tr key={t.number} className={t.number === s.summary?.best_number ? 'sel' : undefined}><td className="num">{t.number}</td><td><span className={`badge ${t.state === 'complete' ? 'ok' : t.state === 'running' ? 'accent' : t.state === 'pruned' ? 'high' : 'crit'}`}>{t.state_es}</span></td><td className="num">{fmtVal(t.value, 4)}</td><td className="num">{t.duration_s != null ? duration(t.duration_s) : '—'}</td><td className="mono" style={{ fontSize: 12, whiteSpace: 'normal' }}>{fmtVal(t.params, 4)}</td></tr>)}</tbody></table></div>)}
      </section>
      {viz.isSuccess && viz.data.figures.length > 0 && <SpecGrid specs={viz.data.figures} module="ml_optuna" />}
      {viz.isError && !active && <p className="small muted">Aún no hay suficientes trials completados para dibujar los gráficos.</p>}
    </div>
  )
}
