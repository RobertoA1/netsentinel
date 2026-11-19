import { useEffect, useState, type FormEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import { useGet } from '../api/hooks'
import type { DetectionSettings, RetentionSettings } from '../api/types'
import { useCan } from '../auth/AuthProvider'
import { Button } from '../ui/Button'
import { Switch, TextField } from '../ui/Fields'
import { Link } from 'react-router-dom'
import { DataState, PageHead, SkeletonRows } from '../ui/State'
import { useToast } from '../ui/Toast'
import { errMsg } from '../lib/utils'

const nStr = (n: number | undefined) => (n === undefined ? '' : String(n))
const list = (s: string) => s.split(/[,\s]+/).filter(Boolean)

function numErr(v: string, min: number, max: number, int = false): string | null {
  if (v.trim() === '' || Number.isNaN(Number(v))) return 'Ingrese un número.'
  const n = Number(v)
  if (int && !Number.isInteger(n)) return 'Debe ser un número entero.'
  if (n < min || n > max) return `Debe estar entre ${min} y ${max}.`
  return null
}

function DetectionForm({ data, canEdit }: { data: DetectionSettings; canEdit: boolean }) {
  const toast = useToast()
  const qc = useQueryClient()
  const [f, setF] = useState(() => ({
    beacon_min_connections: nStr(data.beacon_min_connections), beacon_max_cv: nStr(data.beacon_max_cv), beacon_min_score: nStr(data.beacon_min_score),
    exfil_zscore: nStr(data.exfil_zscore), exfil_min_mb: nStr(Math.round(data.exfil_min_bytes / 1048576)),
    common_ports: data.common_ports.join(', '), unusual_port_min_connections: nStr(data.unusual_port_min_connections),
    internal_cidrs: data.internal_cidrs.join(', '), detection_window_hours: nStr(data.detection_window_hours),
  }))
  useEffect(() => { /* los valores del servidor se cargan una vez */ }, [])
  const [errs, setErrs] = useState<Record<string, string>>({})
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF((x) => ({ ...x, [k]: e.target.value }))
  const save = useMutation({
    mutationFn: (b: DetectionSettings) => api.put<DetectionSettings>('/settings/detection', b),
    onSuccess: () => { toast.ok('Parámetros de detección guardados.'); void qc.invalidateQueries({ queryKey: ['/settings/detection'] }) },
    onError: (e) => toast.err(errMsg(e)),
  })
  function submit(e: FormEvent) {
    e.preventDefault()
    const er: Record<string, string | null> = {
      beacon_min_connections: numErr(f.beacon_min_connections, 3, 10000, true),
      beacon_max_cv: numErr(f.beacon_max_cv, 0.01, 2),
      beacon_min_score: numErr(f.beacon_min_score, 0, 100),
      exfil_zscore: numErr(f.exfil_zscore, 0.5, 20),
      exfil_min_mb: numErr(f.exfil_min_mb, 0, 1_000_000),
      unusual_port_min_connections: numErr(f.unusual_port_min_connections, 1, 10000, true),
      detection_window_hours: numErr(f.detection_window_hours, 1, 720, true),
      common_ports: list(f.common_ports).every((x) => /^\d+$/.test(x) && +x <= 65535) ? null : 'Use solo puertos entre 0 y 65535, separados por comas.',
      internal_cidrs: list(f.internal_cidrs).length && list(f.internal_cidrs).every((x) => /^(\d{1,3}\.){3}\d{1,3}\/\d{1,2}$/.test(x)) ? null : 'Use redes CIDR como 10.0.0.0/8, separadas por comas.',
    }
    const clean = Object.fromEntries(Object.entries(er).filter(([, v]) => v)) as Record<string, string>
    setErrs(clean)
    if (Object.keys(clean).length) return
    save.mutate({
      beacon_min_connections: +f.beacon_min_connections, beacon_max_cv: +f.beacon_max_cv, beacon_min_score: +f.beacon_min_score,
      exfil_zscore: +f.exfil_zscore, exfil_min_bytes: Math.round(+f.exfil_min_mb * 1048576),
      common_ports: list(f.common_ports).map(Number), unusual_port_min_connections: +f.unusual_port_min_connections,
      internal_cidrs: list(f.internal_cidrs), detection_window_hours: +f.detection_window_hours,
    })
  }
  const dis = !canEdit
  return (
    <form onSubmit={submit} noValidate className="stack" style={{ gap: 16 }}>
      <section className="panel">
        <div className="panel-head"><h2>Beaconing</h2><span className="hint">Conexiones periódicas a un mismo destino</span></div>
        <div className="panel-body form-grid">
          <TextField label="Conexiones mínimas" inputMode="numeric" value={f.beacon_min_connections} onChange={set('beacon_min_connections')} error={errs.beacon_min_connections} disabled={dis} help="Menos conexiones que esto no se evalúan." />
          <TextField label="Variación máxima de intervalos (CV)" inputMode="decimal" value={f.beacon_max_cv} onChange={set('beacon_max_cv')} error={errs.beacon_max_cv} disabled={dis} help="Más bajo = más estricto. 0,25 es un buen punto de partida." />
          <TextField label="Puntaje mínimo para reportar" inputMode="numeric" value={f.beacon_min_score} onChange={set('beacon_min_score')} error={errs.beacon_min_score} disabled={dis} help="De 0 a 100." />
        </div>
      </section>
      <section className="panel">
        <div className="panel-head"><h2>Exfiltración</h2><span className="hint">Envíos de datos fuera de lo habitual</span></div>
        <div className="panel-body form-grid">
          <TextField label="Desviaciones sobre la línea base (z-score)" inputMode="decimal" value={f.exfil_zscore} onChange={set('exfil_zscore')} error={errs.exfil_zscore} disabled={dis} help="Cuántas desviaciones por encima de lo normal se considera anómalo." />
          <TextField label="Volumen mínimo (MB)" inputMode="numeric" value={f.exfil_min_mb} onChange={set('exfil_min_mb')} error={errs.exfil_min_mb} disabled={dis} help="Envíos menores a este tamaño se ignoran." />
        </div>
      </section>
      <section className="panel">
        <div className="panel-head"><h2>Puertos y red</h2></div>
        <div className="panel-body form-grid">
          <TextField label="Puertos comunes" className="full" mono value={f.common_ports} onChange={set('common_ports')} error={errs.common_ports} disabled={dis} help="Tráfico por otros puertos puede marcarse como inusual." />
          <TextField label="Conexiones mínimas para puerto inusual" inputMode="numeric" value={f.unusual_port_min_connections} onChange={set('unusual_port_min_connections')} error={errs.unusual_port_min_connections} disabled={dis} />
          <TextField label="Ventana de detección (horas)" inputMode="numeric" value={f.detection_window_hours} onChange={set('detection_window_hours')} error={errs.detection_window_hours} disabled={dis} />
          <TextField label="Redes internas (CIDR)" className="full" mono value={f.internal_cidrs} onChange={set('internal_cidrs')} error={errs.internal_cidrs} disabled={dis} help="Define qué es 'interno' y qué es 'afuera'." />
        </div>
      </section>
      {canEdit && <div><Button variant="primary" type="submit" loading={save.isPending}>Guardar parámetros</Button></div>}
    </form>
  )
}

function RetentionForm({ data, canEdit }: { data: RetentionSettings; canEdit: boolean }) {
  const toast = useToast()
  const qc = useQueryClient()
  const [f, setF] = useState({ logs_days: nStr(data.logs_days), findings_days: nStr(data.findings_days), audit_days: nStr(data.audit_days) })
  const [errs, setErrs] = useState<Record<string, string>>({})
  const save = useMutation({
    mutationFn: (b: RetentionSettings) => api.put<RetentionSettings>('/settings/retention', b),
    onSuccess: () => { toast.ok('Retención guardada.'); void qc.invalidateQueries({ queryKey: ['/settings/retention'] }) },
    onError: (e) => toast.err(errMsg(e)),
  })
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF((x) => ({ ...x, [k]: e.target.value }))
  function submit(e: FormEvent) {
    e.preventDefault()
    const er = Object.fromEntries(Object.entries({ logs_days: numErr(f.logs_days, 1, 3650, true), findings_days: numErr(f.findings_days, 1, 3650, true), audit_days: numErr(f.audit_days, 30, 3650, true) }).filter(([, v]) => v)) as Record<string, string>
    setErrs(er)
    if (Object.keys(er).length) return
    save.mutate({ logs_days: +f.logs_days, findings_days: +f.findings_days, audit_days: +f.audit_days })
  }
  return (
    <form onSubmit={submit} noValidate className="panel">
      <div className="panel-head"><h2>Retención de datos</h2><span className="hint">Pasado este plazo, los datos se eliminan automáticamente</span></div>
      <div className="panel-body form-grid">
        <TextField label="Registros (días)" inputMode="numeric" value={f.logs_days} onChange={set('logs_days')} error={errs.logs_days} disabled={!canEdit} />
        <TextField label="Hallazgos (días)" inputMode="numeric" value={f.findings_days} onChange={set('findings_days')} error={errs.findings_days} disabled={!canEdit} />
        <TextField label="Bitácora de auditoría (días)" inputMode="numeric" value={f.audit_days} onChange={set('audit_days')} error={errs.audit_days} disabled={!canEdit} help="Mínimo 30 días. Consulte la política de su organización." />
        {canEdit && <div className="full"><Button variant="primary" type="submit" loading={save.isPending}>Guardar retención</Button></div>}
      </div>
    </form>
  )
}

function MlToggle({ canEdit }: { canEdit: boolean }) {
  const q = useGet<{ model: { name: string } | null; pipeline_enabled: boolean }>('/ml/inference/active', undefined, { retry: false })
  const toast = useToast()
  const qc = useQueryClient()
  const sw = useMutation({ mutationFn: (enabled: boolean) => api.put('/ml/inference/pipeline', { enabled }), onSuccess: () => { toast.ok('Ajuste guardado.'); void qc.invalidateQueries({ queryKey: ['/ml/inference/active'] }) }, onError: (e) => toast.err(errMsg(e)) })
  if (q.isError || !q.data) return null
  return (
    <section className="panel" aria-label="Modelo de aprendizaje automático">
      <div className="panel-head"><h2>Aprendizaje automático en el pipeline</h2><span className="hint">Opcional; apagado por defecto</span></div>
      <div className="panel-body stack">
        <Switch label="Enriquecer los hallazgos nuevos con la predicción del modelo ML (y pasarla al motor IA como contexto)" checked={q.data.pipeline_enabled} disabled={!canEdit || !q.data.model || sw.isPending} onChange={(v) => sw.mutate(v)} />
        <p className="small muted">{q.data.model ? <>Modelo activo: <b>{q.data.model.name}</b>. </> : <>No hay modelo activo: promueva uno desde <Link to="/ml/evaluacion">Evaluación</Link>. </>}La detección determinista no cambia; el resultado ML se agrega a la evidencia y se separa visualmente de los hechos.</p>
      </div>
    </section>
  )
}

export default function Detection() {
  const can = useCan('detection')
  const d = useGet<DetectionSettings>('/settings/detection')
  const r = useGet<RetentionSettings>('/settings/retention', undefined, { retry: false })
  return (
    <div className="page" style={{ maxWidth: 980 }}>
      <PageHead title="Detección" desc="Umbrales que deciden qué comportamiento se reporta como hallazgo. Los cambios aplican a la próxima ejecución de detección." />
      <DataState q={d} skeleton={<div className="panel"><SkeletonRows rows={8} /></div>}>{(data) => <DetectionForm data={data} canEdit={can.update} />}</DataState>
      <div style={{ height: 16 }} />
      <MlToggle canEdit={can.update} />
      <div style={{ height: 16 }} />
      {r.isError ? null : <DataState q={r} skeleton={<div className="panel"><SkeletonRows rows={3} /></div>}>{(data) => <RetentionForm data={data} canEdit={can.update} />}</DataState>}
    </div>
  )
}
