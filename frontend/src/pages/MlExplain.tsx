import { useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Play } from 'lucide-react'
import { api } from '../api/client'
import { useGet } from '../api/hooks'
import { useCan } from '../auth/AuthProvider'
import { Button } from '../ui/Button'
import { SelectField } from '../ui/Fields'
import { DataState, EmptyState, ErrorState, PageHead, SkeletonRows } from '../ui/State'
import { useToast } from '../ui/Toast'
import { errMsg } from '../lib/utils'
import { SpecGrid, type Spec } from '../ml/figures'
import { Notice, StatusBadge, isActive, useJob } from '../ml/common'
import { MODEL_LABEL, type MlJob, type MlModel } from '../ml/types'

interface ExplainOut { status: string; id?: number; error?: string; result: { figures: Spec[]; tables: Spec[]; model: string } | null }

export default function MlExplain() {
  const can = useCan('ml_explain')
  const [sp, setSp] = useSearchParams()
  const models = useGet<MlModel[]>('/ml/evaluation/models')
  const list = (models.data ?? []).filter((m) => !m.is_baseline)
  const mid = Number(sp.get('model')) || null
  useEffect(() => { if (!mid && list.length) setSp({ model: String((list.find((m) => m.is_active) ?? list[0]).id) }, { replace: true }) }, [mid, list, setSp])
  return (
    <div className="page">
      <PageHead title="Explicabilidad" desc="Por qué el modelo decide lo que decide: SHAP global y local, importancia por permutación como contraste independiente, mapas de calor, dependencia parcial, oclusión y estabilidad entre pliegues." />
      <DataState q={models} skeleton={<div className="panel"><SkeletonRows rows={3} /></div>} isEmpty={() => list.length === 0}
        empty={<div className="panel"><EmptyState title="No hay modelos para explicar">Entrene y evalúe un modelo en <Link to="/ml/entrenamiento">Entrenamiento</Link>. La línea base trivial no tiene explicaciones.</EmptyState></div>}>
        {() => (
          <div className="stack" style={{ gap: 16 }}>
            <section className="panel"><div className="panel-body">
              <SelectField label="Modelo a explicar" value={mid ?? ''} onChange={(e) => setSp({ model: e.target.value })} options={list.map((m) => ({ value: m.id, label: `${m.name || MODEL_LABEL[m.model_type]} · #${m.id}${m.is_active ? ' (activo)' : ''}` }))} />
            </div></section>
            {mid && <Explanation key={mid} modelId={mid} canRun={can.execute} />}
          </div>
        )}
      </DataState>
    </div>
  )
}

function Explanation({ modelId, canRun }: { modelId: number; canRun: boolean }) {
  const qc = useQueryClient()
  const toast = useToast()
  const latest = useGet<ExplainOut>(`/ml/explain/models/${modelId}`, undefined, { retry: false })
  const jobId = latest.data?.id ?? null
  const live = useJob(jobId && latest.data && isActive(latest.data.status as MlJob['status']) ? jobId : null)
  useEffect(() => { if (live.data?.status === 'succeeded' || live.data?.status === 'failed') void qc.invalidateQueries({ queryKey: [`/ml/explain/models/${modelId}`] }) }, [live.data?.status, modelId, qc])
  const run = useMutation({ mutationFn: (force: boolean) => api.post<MlJob>('/ml/explain/jobs', { model_id: modelId, force }), onSuccess: () => { toast.ok('Explicabilidad en cola.'); void qc.invalidateQueries({ queryKey: [`/ml/explain/models/${modelId}`] }) }, onError: (e) => toast.err(errMsg(e)) })
  const { mutate: startRun, isPending: running, isSuccess: started } = run
  const missing = latest.isSuccess && latest.data.status === 'none'
  useEffect(() => { if (missing && canRun && !running && !started) startRun(false) }, [missing, canRun, running, started, startRun])
  if (latest.isPending) return <section className="panel"><SkeletonRows rows={6} /></section>
  if (latest.isError) return <ErrorState error={latest.error} onRetry={() => latest.refetch()} />
  const d = latest.data
  const status = (live.data?.status ?? d.status) as MlJob['status'] | 'none'
  if (status === 'none') return <EmptyState title="Este modelo aún no se explicó">{canRun ? 'Se está solicitando el cálculo…' : 'Un analista con permiso de ejecución debe solicitar el cálculo.'}</EmptyState>
  if (isActive(status as MlJob['status'])) {
    const pr = live.data?.progress
    return <section className="panel" role="status" aria-live="polite"><div className="panel-head"><h2>Calculando explicaciones <StatusBadge s={status as MlJob['status']} /></h2></div><div className="panel-body"><p className="small muted">{pr?.step ? String(pr.step) : 'SHAP, permutación, mapas de calor, dependencia parcial y oclusión sobre la partición de Validación. Puede tardar varios minutos; puede salir de esta página y volver.'}</p></div><SkeletonRows rows={4} /></section>
  }
  if (status === 'failed') return <Notice kind="block">El cálculo falló: <span className="mono">{live.data?.error ?? d.error}</span>{canRun && <> <Button size="sm" onClick={() => run.mutate(true)}>Reintentar</Button></>}</Notice>
  if (!d.result) return <EmptyState title="Sin resultados" />
  return (
    <div className="stack" style={{ gap: 16 }}>
      <div className="row between"><p className="small muted">Todas las figuras se calcularon sobre datos de Validación; no usan Prueba.</p>{canRun && <Button size="sm" onClick={() => run.mutate(true)} loading={run.isPending}><Play size={13} /> Recalcular</Button>}</div>
      <SpecGrid specs={[...d.result.figures, ...d.result.tables]} module="ml_explain" />
    </div>
  )
}
