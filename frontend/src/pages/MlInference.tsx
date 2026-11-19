import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Sparkles, TriangleAlert } from 'lucide-react'
import { api } from '../api/client'
import { useGet } from '../api/hooks'
import { useCan } from '../auth/AuthProvider'
import { Button } from '../ui/Button'
import { Segmented } from '../ui/Controls'
import { TextField, SelectField, Switch } from '../ui/Fields'
import { SeverityBadge } from '../ui/Gauge'
import { Pagination } from '../ui/Pagination'
import { DataState, EmptyState, ErrorState, PageHead, SkeletonRows } from '../ui/State'
import { useToast } from '../ui/Toast'
import { useFmt } from '../lib/format'
import { errMsg } from '../lib/utils'
import type { Severity } from '../api/types'
import { FigureCard, Reading, fmtVal, type FigSpec, type Interp } from '../ml/figures'
import { Kv, Notice } from '../ml/common'
import { MODEL_LABEL, type MlModel, type Page } from '../ml/types'

type Kind = 'flow' | 'window' | 'finding' | 'manual'
interface Contribution { feature: string; label: string; shap: number; value: number | string | null }
interface Pred {
  id: number; probability: number; interval: [number, number]; prediction_set: string[]; predicted_class: string; threshold: number
  ambiguous: boolean; ood: { is_ood: boolean; out_of_range?: { feature: string; value: number; lo: number; hi: number }[]; n_out?: number; share?: number }
  severity: Severity; severity_steps: { step: string; text: string; points?: number; level?: string }[]; narrative: string; narrative_source: 'template' | 'llm'
  contributions?: { favor: Contribution[]; contra: Contribution[]; base: number; space: string; all: Contribution[] }
  model?: { id: number; name: string; threshold: number }; interpretation?: Interp; n_scored?: number; share_positive?: number; context?: Record<string, unknown>
  features?: Record<string, unknown>
}
interface Active { model: MlModel | null; pipeline_enabled: boolean }
interface SevCfg { config: Record<string, Record<string, number | string>>; default: Record<string, Record<string, number | string>> }
interface FeatureSpec { numeric: string[]; categorical: string[] }

export default function MlInference() {
  const can = useCan('ml_inference')
  const detCan = useCan('detection')
  const active = useGet<Active>('/ml/inference/active')
  const models = useGet<MlModel[]>('/ml/evaluation/models')
  const list = (models.data ?? []).filter((m) => !m.is_baseline)
  const [mid, setMid] = useState<number | null>(null)
  const [res, setRes] = useState<Pred | null>(null)
  const model = list.find((m) => m.id === (mid ?? active.data?.model?.id ?? list[0]?.id)) ?? null
  return (
    <div className="page">
      <PageHead title="Inferencia" desc="Prediga si un flujo, una ventana host-tiempo, un hallazgo o valores manuales corresponden a tráfico de botnet, con probabilidad calibrada, incertidumbre y explicación de cada factor." />
      <DataState q={models} skeleton={<div className="panel"><SkeletonRows rows={3} /></div>} isEmpty={() => list.length === 0}
        empty={<div className="panel"><EmptyState title="No hay modelos entrenados">Entrene un modelo en <Link to="/ml/entrenamiento">Entrenamiento</Link> y promuévalo en <Link to="/ml/evaluacion">Evaluación</Link>.</EmptyState></div>}>
        {() => (
          <div className="stack" style={{ gap: 16 }}>
            <ActivePanel active={active.data} canToggle={detCan.update} />
            {can.execute ? (
              <div className="mlsplit">
                <section className="panel" aria-label="Nueva predicción">
                  <div className="panel-head"><h2>Nueva predicción</h2></div>
                  <div className="panel-body"><PredictForm models={list} model={model} setModel={setMid} onResult={setRes} /></div>
                </section>
                <div>{res ? <Result p={res} /> : <section className="panel"><EmptyState title="Aún no hay resultado">Elija una entrada y pulse «Predecir». La severidad se muestra paso a paso.</EmptyState></section>}</div>
              </div>
            ) : <p className="small muted">Su rol puede ver el historial pero no ejecutar predicciones.</p>}
            {model && <Uncertainty model={model} />}
            <History onOpen={setRes} />
            <SeverityEditor canEdit={can.update} />
          </div>
        )}
      </DataState>
    </div>
  )
}

function ActivePanel({ active, canToggle }: { active?: Active; canToggle: boolean }) {
  const toast = useToast()
  const qc = useQueryClient()
  const m = active?.model
  const sw = useMutation({ mutationFn: (enabled: boolean) => api.put('/ml/inference/pipeline', { enabled }), onSuccess: () => { toast.ok('Ajuste guardado.'); void qc.invalidateQueries({ queryKey: ['/ml/inference/active'] }) }, onError: (e) => toast.err(errMsg(e)) })
  return (
    <section className="panel" aria-label="Modelo activo">
      <div className="panel-head"><h2>Modelo activo en el pipeline</h2>{m && <span className="hint">Promovido por {m.promoted_by ?? '—'}</span>}</div>
      <div className="panel-body stack">
        {m ? <Kv rows={[['Modelo', `${m.name} (${MODEL_LABEL[m.model_type]})`], ['Unidad', m.unit === 'window' ? `Ventana host-tiempo (${m.window_minutes} min)` : 'Flujo'], ['Umbral', fmtVal(m.threshold)], ['PR-AUC en Prueba', fmtVal(m.metrics.test.pr_auc)]]} />
          : <p className="muted">No hay modelo activo. Promueva uno desde <Link to="/ml/evaluacion">Evaluación</Link> para usarlo en el pipeline.</p>}
        <Switch label="Usar el modelo ML en el pipeline de detección (los hallazgos nuevos reciben evidencia ML y el LLM la usa como contexto)" checked={!!active?.pipeline_enabled} disabled={!canToggle || !m || sw.isPending} onChange={(v) => sw.mutate(v)} />
        {!canToggle && <p className="small muted">Cambiar este ajuste requiere permiso de edición de Detección.</p>}
        <p className="small muted">Apagado por defecto. Con el interruptor apagado, NetSentinel se comporta exactamente como antes.</p>
      </div>
    </section>
  )
}

function PredictForm({ models, model, setModel, onResult }: { models: MlModel[]; model: MlModel | null; setModel: (id: number) => void; onResult: (p: Pred) => void }) {
  const toast = useToast()
  const qc = useQueryClient()
  const [kind, setKind] = useState<Kind>('finding')
  const [v, setV] = useState({ log_id: '', src_ip: '', window_end: '', minutes: '', finding_id: '' })
  const [vals, setVals] = useState<Record<string, string>>({})
  const spec = useGet<FeatureSpec>('/ml/data/feature-spec', { unit: model?.unit ?? 'flow', window_minutes: model?.window_minutes ?? undefined }, { enabled: kind === 'manual' && !!model })
  const mut = useMutation({
    mutationFn: () => {
      const b: Record<string, unknown> = { model_id: model?.id, kind }
      if (kind === 'flow') b.log_id = Number(v.log_id)
      if (kind === 'finding') b.finding_id = Number(v.finding_id)
      if (kind === 'window') { b.src_ip = v.src_ip.trim(); if (v.window_end) b.window_end = new Date(v.window_end).toISOString(); if (v.minutes) b.minutes = Number(v.minutes) }
      if (kind === 'manual') b.values = Object.fromEntries(Object.entries(vals).filter(([, x]) => x !== '').map(([k, x]) => [k, spec.data?.numeric.includes(k) ? Number(x) : x]))
      return api.post<Pred>('/ml/inference/predict', b)
    },
    onSuccess: (p) => { onResult(p); void qc.invalidateQueries({ queryKey: ['/ml/inference/predictions'] }) },
    onError: (e) => toast.err(errMsg(e)),
  })
  const ok = kind === 'flow' ? /^\d+$/.test(v.log_id) : kind === 'finding' ? /^\d+$/.test(v.finding_id) : kind === 'window' ? v.src_ip.trim().length > 6 : Object.values(vals).some((x) => x !== '')
  const set = (k: keyof typeof v) => (e: { target: { value: string } }) => setV((x) => ({ ...x, [k]: e.target.value }))
  function submit(e: FormEvent) { e.preventDefault(); if (ok) mut.mutate() }
  return (
    <form className="stack" onSubmit={submit} noValidate>
      <SelectField label="Modelo" value={model?.id ?? ''} onChange={(e) => setModel(Number(e.target.value))} options={models.map((m) => ({ value: m.id, label: `${MODEL_LABEL[m.model_type]} · #${m.id}${m.is_active ? ' (activo)' : ''}` }))} />
      <Segmented<Kind> label="Tipo de entrada" value={kind} onChange={setKind} options={[{ value: 'finding', label: 'Hallazgo' }, { value: 'flow', label: 'Flujo' }, { value: 'window', label: 'Ventana' }, { value: 'manual', label: 'Manual' }]} />
      {kind === 'finding' && <TextField label="N.º de hallazgo" inputMode="numeric" value={v.finding_id} onChange={set('finding_id')} help="Se puntúan los flujos del hallazgo y se explica el de mayor riesgo; el puntaje determinista entra en la severidad." />}
      {kind === 'flow' && <TextField label="N.º de registro (flujo)" inputMode="numeric" value={v.log_id} onChange={set('log_id')} help="El ID de la fila en Registros." />}
      {kind === 'window' && <>
        <TextField label="IP de origen" mono value={v.src_ip} onChange={set('src_ip')} />
        <div className="form-grid"><TextField label="Fin de la ventana (opcional)" type="datetime-local" value={v.window_end} onChange={set('window_end')} /><TextField label="Minutos (opcional)" inputMode="decimal" value={v.minutes} onChange={set('minutes')} /></div></>}
      {kind === 'manual' && (
        <DataState q={spec} skeleton={<SkeletonRows rows={3} />}>
          {(s) => <div className="form-grid">{[...s.numeric, ...s.categorical].map((c) => <TextField key={c} label={c} mono value={vals[c] ?? ''} onChange={(e) => setVals((x) => ({ ...x, [c]: e.target.value }))} inputMode={s.numeric.includes(c) ? 'decimal' : 'text'} />)}</div>}
        </DataState>)}
      <div><Button type="submit" variant="primary" loading={mut.isPending} disabled={!ok || !model}>Predecir</Button></div>
    </form>
  )
}

function Result({ p }: { p: Pred }) {
  const toast = useToast()
  const [n, setN] = useState<{ narrative: string; source: string } | null>(null)
  useEffect(() => setN(null), [p.id])
  const gen = useMutation({ mutationFn: () => api.post<{ narrative: string; source: string }>(`/ml/inference/predictions/${p.id}/narrative`), onSuccess: setN, onError: (e) => toast.err(errMsg(e)) })
  const wf: FigSpec | null = useMemo(() => p.contributions ? ({
    id: 'local', kind: 'waterfall', title: `Qué factores empujan esta predicción (SHAP local, espacio de ${p.contributions.space})`,
    note: `Predicción #${p.id}. Cada barra es la contribución de una variable al puntaje del modelo; valor base ${fmtVal(p.contributions.base)}.`,
    data: { base: p.contributions.base, items: p.contributions.all.slice(0, 10).map((r) => ({ label: `${r.label} = ${fmtVal(r.value)}`, value: r.shap })), xlabel: 'Contribución acumulada al puntaje' },
    interpretation: { meaning: [p.contributions.favor.length ? `Los factores que más empujan hacia Botnet son: ${p.contributions.favor.slice(0, 3).map((r) => r.label).join(', ')}.` : 'Ninguna variable empuja claramente hacia Botnet.', p.contributions.contra.length ? `Los que más empujan hacia Normal: ${p.contributions.contra.slice(0, 3).map((r) => r.label).join(', ')}.` : ''].filter(Boolean), caution: ['SHAP describe cómo decide el modelo, no causalidad en la red.'] },
  }) : null, [p])
  const text = n?.narrative ?? p.narrative
  const src = n?.source ?? p.narrative_source
  return (
    <div className="stack" style={{ gap: 16 }} aria-live="polite">
      <section className="panel" aria-label="Resultado de la predicción">
        <div className="panel-head"><h2>Resultado #{p.id}</h2><SeverityBadge severity={p.severity} /></div>
        <div className="panel-body stack">
          <div className="mlprob"><span className="big">{fmtVal(p.probability * 100, 1)} %</span><span>probabilidad calibrada de Botnet → <b>{p.predicted_class}</b> (umbral {fmtVal(p.threshold)})</span></div>
          <Kv rows={[['Intervalo conforme', `[${fmtVal(p.interval[0])}; ${fmtVal(p.interval[1])}]`], ['Conjunto de predicción', p.prediction_set.join(' o ') + (p.ambiguous ? ' (ambiguo)' : '')], ...(p.n_scored ? [['Flujos puntuados', `${p.n_scored} (${fmtVal((p.share_positive ?? 0) * 100, 0)} % Botnet); se explica el de mayor riesgo`] as [string, string]] : [])]} />
          {p.ood.is_ood && <Notice kind="warn"><TriangleAlert size={14} aria-hidden style={{ verticalAlign: '-2px' }} /> <b>Fuera de distribución.</b> {p.ood.out_of_range?.length ? `Variables fuera del rango visto en el entrenamiento: ${p.ood.out_of_range.slice(0, 4).map((o) => `${o.feature} = ${fmtVal(o.value)} (rango ${fmtVal(o.lo)} a ${fmtVal(o.hi)})`).join('; ')}.` : ''} La predicción puede no ser fiable; confirme manualmente.</Notice>}
          <div>
            <h3 style={{ marginBottom: 6 }}>Cómo se llegó a la severidad</h3>
            <ol className="mlsteps">{p.severity_steps.map((s, i) => <li key={i}><b>{i + 1}</b><span>{s.text}</span></li>)}</ol>
            {p.interpretation && <Reading ip={p.interpretation} />}
          </div>
        </div>
      </section>
      <section className="ai-box" aria-label="Narrativa">
        <div className="ai-head"><Sparkles size={15} aria-hidden /> {src === 'llm' ? 'Interpretación de IA' : 'Resumen automático (plantilla determinista)'}
          <span style={{ marginLeft: 'auto' }}><Button size="sm" onClick={() => gen.mutate()} loading={gen.isPending}>{src === 'llm' ? 'Regenerar con IA' : 'Generar narrativa con IA'}</Button></span></div>
        <div className="ai-body"><p>{text}</p>{gen.isPending && <p className="small muted" role="status">El modelo de lenguaje local puede tardar unos 30 s en CPU. Solo recibe cifras ya calculadas; si falla, se conserva la plantilla.</p>}
          {n?.source === 'template' && <p className="small muted">El modelo de lenguaje no respondió: se muestra la plantilla determinista.</p>}</div>
      </section>
      {wf && <FigureCard spec={wf} module="ml_inference" wide />}
    </div>
  )
}

function Uncertainty({ model }: { model: MlModel }) {
  const q = useGet<{ reliability: FigSpec; conformal_interpretation: Interp; coverage: Record<string, number | boolean> }>(`/ml/inference/models/${model.id}/uncertainty`, undefined, { retry: false })
  return (
    <section className="panel" aria-label="Incertidumbre y calibración">
      <div className="panel-head"><h2>Incertidumbre y calibración de {MODEL_LABEL[model.model_type]}</h2><span className="hint">Cobertura conforme verificada en Prueba</span></div>
      <DataState q={q} skeleton={<SkeletonRows rows={4} />}>
        {(d) => (
          <div className="panel-body stack">
            <Kv rows={[['Cobertura nominal', fmtVal(Number(d.coverage.nominal) * 100, 0) + ' %'], ['Cobertura observada en Prueba', fmtVal(Number(d.coverage.empirical_set) * 100, 1) + ' %'], ['¿Cumple la nominal?', d.coverage.meets_nominal ? 'Sí' : 'No'], ['Casos de Prueba', fmtVal(d.coverage.n)]]} />
            <Reading ip={d.conformal_interpretation} />
            <FigureCard spec={d.reliability} module="ml_inference" />
          </div>)}
      </DataState>
    </section>
  )
}

function History({ onOpen }: { onOpen: (p: Pred) => void }) {
  const [page, setPage] = useState(1)
  const [sev, setSev] = useState('')
  const f = useFmt()
  const q = useGet<Page<Pred & { ts: string; username: string; input_kind: string; input_ref: string }>>('/ml/inference/predictions', { page, page_size: 10, severity: sev || undefined }, { keep: true })
  return (
    <section className="panel" aria-label="Historial de predicciones">
      <div className="panel-head"><h2>Historial de predicciones</h2>
        <SelectField label="Severidad" value={sev} onChange={(e) => { setSev(e.target.value); setPage(1) }} placeholder="Todas" options={['critical', 'high', 'medium', 'low', 'info'].map((s) => ({ value: s, label: { critical: 'Crítica', high: 'Alta', medium: 'Media', low: 'Baja', info: 'Informativa' }[s]! }))} /></div>
      <DataState q={q} skeleton={<SkeletonRows rows={4} />} isEmpty={(d) => d.items.length === 0} empty={<EmptyState title="Sin predicciones">Las predicciones que ejecute quedan registradas aquí.</EmptyState>}>
        {(d) => (<>
          <div className="table-wrap"><table className="t"><thead><tr><th>#</th><th>Fecha</th><th>Entrada</th><th>Referencia</th><th className="num">Prob.</th><th>Clase</th><th>Severidad</th><th>Usuario</th></tr></thead>
            <tbody>{d.items.map((r) => <tr key={r.id} className="clickable" tabIndex={0} onClick={() => onOpen(r)} onKeyDown={(e) => { if (e.key === 'Enter') onOpen(r) }}><td className="num">{r.id}</td><td className="nowrap">{f.dt(r.ts)}</td><td>{({ flow: 'Flujo', window: 'Ventana', finding: 'Hallazgo', manual: 'Manual' } as Record<string, string>)[r.input_kind]}</td><td className="mono">{r.input_ref}</td><td className="num">{fmtVal(r.probability)}</td><td>{r.predicted_class}</td><td><SeverityBadge severity={r.severity} /></td><td>{r.username}</td></tr>)}</tbody></table></div>
          <Pagination page={d.page} pageSize={d.page_size} total={d.total} onPage={setPage} />
        </>)}
      </DataState>
    </section>
  )
}

function SeverityEditor({ canEdit }: { canEdit: boolean }) {
  const q = useGet<SevCfg>('/ml/inference/severity-config')
  const toast = useToast()
  const qc = useQueryClient()
  const [cfg, setCfg] = useState<SevCfg['config'] | null>(null)
  useEffect(() => { if (q.data && !cfg) setCfg(q.data.config) }, [q.data, cfg])
  const save = useMutation({ mutationFn: (c: object) => api.put('/ml/inference/severity-config', c), onSuccess: () => { toast.ok('Regla de severidad guardada.'); void qc.invalidateQueries({ queryKey: ['/ml/inference/severity-config'] }) }, onError: (e) => toast.err(errMsg(e)) })
  const L: Record<string, [string, Record<string, string>]> = {
    weights: ['Pesos', { probability: 'Probabilidad del modelo', deterministic: 'Puntaje determinista' }],
    thresholds: ['Umbrales de puntos (0–100)', { low: 'Baja desde', medium: 'Media desde', high: 'Alta desde', critical: 'Crítica desde' }],
    uncertainty: ['Penalización por incertidumbre', { interval_width_gt: 'Ancho de intervalo mayor que', penalty_points: 'Puntos que se restan', ambiguous_set_penalty_points: 'Puntos si el conjunto es ambiguo' }],
    asset_bump: ['Sube niveles según criticidad del activo (0–2)', { critical: 'Crítico', high: 'Alto', medium: 'Medio', low: 'Bajo' }],
  }
  return (
    <section className="panel" aria-label="Regla de severidad">
      <div className="panel-head"><h2>Regla de severidad</h2><span className="hint">Probabilidad y puntaje determinista → puntos → umbrales → ajustes; cada predicción muestra los pasos</span></div>
      <DataState q={q} skeleton={<SkeletonRows rows={4} />}>
        {() => cfg && (
          <form className="panel-body stack" onSubmit={(e) => { e.preventDefault(); save.mutate(cfg) }} noValidate>
            <div className="form-grid">{Object.entries(L).flatMap(([g, [title, fields]]) => [<b key={g} className="full small">{title}</b>, ...Object.entries(fields).map(([k, label]) => <TextField key={`${g}.${k}`} label={label} inputMode="decimal" disabled={!canEdit} value={String(cfg[g][k])} onChange={(e) => setCfg((c) => ({ ...c!, [g]: { ...c![g], [k]: e.target.value === '' ? '' : Number(e.target.value) } }))} />)])}
              <SelectField label="Tope si hay variables fuera de distribución" disabled={!canEdit} value={String(cfg.ood_cap)} onChange={(e) => setCfg((c) => ({ ...c!, ood_cap: e.target.value as unknown as Record<string, number | string> } as unknown as SevCfg['config']))} options={['info', 'low', 'medium', 'high', 'critical'].map((s) => ({ value: s, label: { critical: 'Crítica', high: 'Alta', medium: 'Media', low: 'Baja', info: 'Informativa' }[s]! }))} /></div>
            {canEdit && <div className="row"><Button variant="primary" type="submit" loading={save.isPending}>Guardar regla</Button><Button onClick={() => setCfg(q.data!.default)}>Restablecer a los valores por defecto</Button></div>}
          </form>)}
      </DataState>
      {q.isError && <ErrorState error={q.error} />}
    </section>
  )
}
