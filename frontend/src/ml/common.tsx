import { useState, type ReactNode } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Ban, CheckCircle2, CircleAlert, Clock, Loader2, RotateCcw } from 'lucide-react'
import { api } from '../api/client'
import { SelectField } from '../ui/Fields'
import { duration, num } from '../lib/format'
import { useGet } from '../api/hooks'
import { type Dataset, type MlJob, STATUS_LABEL, type JobStatus } from './types'

export const ACTIVE: JobStatus[] = ['queued', 'running', 'cancel_requested']
export const isActive = (s?: JobStatus) => !!s && ACTIVE.includes(s)

export function StatusBadge({ s }: { s: JobStatus }) {
  const cls = s === 'succeeded' ? 'ok' : s === 'failed' ? 'crit' : s === 'running' ? 'accent' : s === 'cancelled' ? 'outline' : s === 'cancel_requested' ? 'high' : ''
  const Icon = s === 'succeeded' ? CheckCircle2 : s === 'failed' ? CircleAlert : s === 'running' ? Loader2 : s === 'cancelled' || s === 'cancel_requested' ? Ban : Clock
  return <span className={`badge ${cls}`}><Icon size={12} className={s === 'running' ? 'spin' : undefined} aria-hidden />{STATUS_LABEL[s]}</span>
}

/** Sondeo corto (3 s) del trabajo mientras está activo; al recargar la página se retoma desde la base de datos. */
export function useJob(id: number | null | undefined) {
  return useQuery<MlJob>({
    queryKey: ['/ml/job', id],
    queryFn: () => api.get<MlJob>(`/ml/training/jobs/${id}`),
    enabled: !!id,
    refetchInterval: (q) => (isActive(q.state.data?.status) || !q.state.data ? 3000 : false),
    refetchIntervalInBackground: false,
  })
}
export function useJobLog(id: number | null | undefined, active: boolean) {
  return useQuery<{ text: string }>({
    queryKey: ['/ml/joblog', id], enabled: !!id,
    queryFn: () => api.get(`/ml/training/jobs/${id}/log`, { since: 0 }),
    refetchInterval: active ? 4000 : false,
  })
}

export function Bar({ value, label }: { value: number; label?: string }) {
  const p = Math.max(0, Math.min(1, value))
  return <div className="mlbar" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(p * 100)} aria-label={label ?? 'Progreso'}><i style={{ width: `${p * 100}%` }} /></div>
}

export function useDatasets() { return useGet<Dataset[]>('/ml/data/datasets') }

export function DatasetPicker({ value, onChange, label = 'Versión de dataset', help }: { value: number | null; onChange: (v: number) => void; label?: string; help?: string }) {
  const q = useDatasets()
  const opts = (q.data ?? []).map((d) => ({ value: d.current_version_id, label: `${d.name} · v${d.current_version} · ${d.meta.unit === 'window' ? 'ventanas' : 'flujos'} · grupo ${GROUP_ES[d.meta.group_key]}` }))
  return <SelectField label={label} help={help} value={value ?? ''} onChange={(e) => onChange(Number(e.target.value))} placeholder={q.isPending ? 'Cargando…' : opts.length ? 'Elija un dataset' : 'No hay datasets registrados'} options={opts} />
}
export const GROUP_ES: Record<string, string> = { src_ip: 'host origen', src_dst: 'par origen-destino', time_block: 'bloque temporal' }

export function JobTable({ jobs, current, onPick }: { jobs: MlJob[]; current: number | null; onPick: (id: number) => void }) {
  return (
    <div className="table-wrap">
      <table className="t">
        <thead><tr><th>#</th><th>Trabajo</th><th>Estado</th><th className="num">Duración</th></tr></thead>
        <tbody>{jobs.map((j) => (
          <tr key={j.id} className={`clickable${current === j.id ? ' sel' : ''}`} onClick={() => onPick(j.id)} tabIndex={0} onKeyDown={(e) => { if (e.key === 'Enter') onPick(j.id) }} aria-label={`Trabajo ${j.id}`}>
            <td className="num">{j.id}</td><td className="cell-main" style={{ maxWidth: 360, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={j.name}>{j.name}</td>
            <td><StatusBadge s={j.status} /></td>
            <td className="num">{j.started_at ? duration(((j.finished_at ? new Date(j.finished_at).getTime() : Date.now()) - new Date(j.started_at).getTime()) / 1000) : '—'}</td>
          </tr>))}</tbody>
      </table>
    </div>
  )
}

export function Notice({ kind = 'warn', children }: { kind?: 'warn' | 'block'; children: ReactNode }) {
  return <div className={kind === 'block' ? 'mlblock' : 'mlwarn'} role={kind === 'block' ? 'alert' : 'note'}>{children}</div>
}

export function Kv({ rows }: { rows: [string, ReactNode][] }) {
  return <dl className="mlkv">{rows.map(([k, v]) => <div key={k} style={{ display: 'contents' }}><dt>{k}</dt><dd>{v}</dd></div>)}</dl>
}

export function useInvalidate() {
  const qc = useQueryClient()
  return (...keys: string[]) => keys.forEach((k) => void qc.invalidateQueries({ queryKey: [k] }))
}

export { num, RotateCcw, useState }
