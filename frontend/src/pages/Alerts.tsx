import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckCheck } from 'lucide-react'
import { api } from '../api/client'
import { useGet } from '../api/hooks'
import type { Alert, AlertRule, Page, Severity } from '../api/types'
import { useCan } from '../auth/AuthProvider'
import { Button } from '../ui/Button'
import { Tabs } from '../ui/Controls'
import { CrudPage } from '../ui/CrudPage'
import { DataState, EmptyState, PageHead, SkeletonRows } from '../ui/State'
import { Pagination } from '../ui/Pagination'
import { SeverityBadge } from '../ui/Gauge'
import { SelectField, Check, TextField } from '../ui/Fields'
import { TimeFilter } from '../ui/TimeFilter'
import { ConfirmDialog } from '../ui/Dialog'
import { useToast } from '../ui/Toast'
import { useFilters } from '../lib/useFilters'
import { useFmt } from '../lib/format'
import { CHANNEL_LABEL, FINDING_TYPE_LABEL, SEVERITIES, SEVERITY_LABEL } from '../lib/labels'
import { errMsg } from '../lib/utils'

function Inbox() {
  const can = useCan('alerts')
  const F = useFilters({ range: '7d', acknowledged: 'false' })
  const fmt = useFmt()
  const toast = useToast()
  const qc = useQueryClient()
  const [picked, setPicked] = useState<Set<number>>(new Set())
  const [confirmAll, setConfirmAll] = useState(false)
  const v = F.values
  const q = useGet<Page<Alert>>('/alerts', { ...F.params, sort: '-created_at' }, { keep: true })
  const refresh = () => { void qc.invalidateQueries({ queryKey: ['/alerts'] }); void qc.invalidateQueries({ queryKey: ['/alerts/unread-count'] }); void qc.invalidateQueries({ queryKey: ['/dashboard/summary'] }) }

  const ack = useMutation({
    mutationFn: async (ids: number[]) => { for (const id of ids) await api.post(`/alerts/${id}/ack`) },
    onSuccess: (_d, ids) => { toast.ok(ids.length === 1 ? 'Alerta acusada.' : `${ids.length} alertas acusadas.`); setPicked(new Set()); refresh() },
    onError: (e) => { toast.err(errMsg(e)); refresh() },
  })
  const ackAll = useMutation({
    mutationFn: () => api.post<{ acknowledged: number }>('/alerts/ack-all'),
    onSuccess: (r) => { toast.ok(`${r.acknowledged} alertas acusadas.`); setConfirmAll(false); setPicked(new Set()); refresh() },
    onError: (e) => { toast.err(errMsg(e)); setConfirmAll(false) },
  })

  const toggle = (id: number) => setPicked((s) => { const n = new Set(s); if (n.has(id)) n.delete(id); else n.add(id); return n })

  return (
    <section className="panel">
      <div className="filters" role="search">
        <SelectField label="Estado" value={v.acknowledged || ''} onChange={(e) => F.set({ acknowledged: e.target.value })} placeholder="Todas" options={[{ value: 'false', label: 'Sin acusar' }, { value: 'true', label: 'Acusadas' }]} />
        <SelectField label="Severidad" value={v.severity || ''} onChange={(e) => F.set({ severity: e.target.value })} placeholder="Todas" options={SEVERITIES.map((s) => ({ value: s, label: SEVERITY_LABEL[s] }))} />
        <TimeFilter values={v} set={F.set} />
        <div className="spacer" />
        {can.update && (
          <>
            <Button disabled={picked.size === 0} loading={ack.isPending} onClick={() => ack.mutate([...picked])}><CheckCheck size={15} /> Acusar seleccionadas ({picked.size})</Button>
            <Button onClick={() => setConfirmAll(true)}>Acusar todas</Button>
          </>
        )}
      </div>
      <DataState q={q} skeleton={<SkeletonRows rows={8} h={22} />} isEmpty={(d) => d.items.length === 0}
        empty={<EmptyState title={v.acknowledged === 'false' ? 'Bandeja al día' : 'No hay alertas'}>{v.acknowledged === 'false' ? 'No tiene alertas pendientes de acuse.' : 'Ninguna alerta coincide con los filtros.'}</EmptyState>}>
        {(d) => {
          const pending = d.items.filter((a) => !a.acknowledged_at)
          const allPicked = pending.length > 0 && pending.every((a) => picked.has(a.id))
          return (
            <>
              <div className="table-wrap">
                <table className="t">
                  <thead><tr>
                    {can.update && <th style={{ width: 36 }}><input type="checkbox" aria-label="Seleccionar todas las pendientes de esta página" checked={allPicked} disabled={pending.length === 0} onChange={(e) => setPicked(e.target.checked ? new Set(pending.map((a) => a.id)) : new Set())} /></th>}
                    <th>Severidad</th><th>Alerta</th><th>Canal</th><th>Fecha</th><th>Estado</th>{can.update && <th />}
                  </tr></thead>
                  <tbody>
                    {d.items.map((a) => (
                      <tr key={a.id} style={a.acknowledged_at ? { opacity: 0.7 } : undefined}>
                        {can.update && <td>{!a.acknowledged_at && <input type="checkbox" checked={picked.has(a.id)} onChange={() => toggle(a.id)} aria-label={`Seleccionar alerta ${a.id}`} />}</td>}
                        <td><SeverityBadge severity={a.severity as Severity} /></td>
                        <td style={{ maxWidth: 460 }}>
                          <Link className="cell-main" to={`/findings/${a.finding_id}`} style={{ color: 'inherit' }}>{a.title}</Link>
                          <div className="small muted">{a.message}</div>
                        </td>
                        <td>{CHANNEL_LABEL[a.channel]}{!a.delivered && a.channel !== 'in_app' && <span className="badge med" style={{ marginLeft: 6 }}>Pendiente de envío</span>}</td>
                        <td className="nowrap">{fmt.dt(a.created_at)}</td>
                        <td>{a.acknowledged_at ? <span className="small muted">Acusada {fmt.short(a.acknowledged_at)}{a.acknowledged_by ? ` por ${typeof a.acknowledged_by === 'string' ? a.acknowledged_by : a.acknowledged_by.full_name}` : ''}</span> : <span className="badge crit">Sin acusar</span>}</td>
                        {can.update && <td className="actions">{!a.acknowledged_at && <Button size="sm" onClick={() => ack.mutate([a.id])} disabled={ack.isPending}>Acusar</Button>}</td>}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination page={d.page} pageSize={d.page_size} total={d.total} onPage={(p) => F.set({ page: p }, true)} onSize={(s) => F.set({ page_size: s })} />
            </>
          )
        }}
      </DataState>
      <ConfirmDialog open={confirmAll} title="Acusar todas las alertas" message="Se marcarán como acusadas todas las alertas pendientes, incluidas las de otras páginas y filtros." confirmLabel="Acusar todas" busy={ackAll.isPending} onConfirm={() => ackAll.mutate()} onCancel={() => setConfirmAll(false)} />
    </section>
  )
}

function Rules() {
  return (
    <CrudPage<AlertRule>
      module="alerts" path="/alert-rules" noun="regla" title="" desc=""
      emptyHelp="Sin reglas no se generan alertas. Cree una para recibir aviso de los hallazgos importantes."
      blank={{ name: '', enabled: true, min_severity: 'high', finding_types: [], channels: ['in_app'], webhook_url: '', email_to: '', include_noise: false }}
      toBody={(f) => ({ ...f, webhook_url: f.channels.includes('webhook') ? f.webhook_url || null : null, email_to: f.channels.includes('email') ? f.email_to || null : null })}
      columns={[
        { header: 'Regla', cell: (r) => <span className="cell-main">{r.name}</span> },
        { header: 'Estado', cell: (r) => <span className={`badge ${r.enabled ? 'ok' : ''}`}>{r.enabled ? 'Activa' : 'Pausada'}</span> },
        { header: 'Desde severidad', cell: (r) => <SeverityBadge severity={r.min_severity} /> },
        { header: 'Tipos', cell: (r) => r.finding_types.length ? r.finding_types.map((t) => FINDING_TYPE_LABEL[t]).join(', ') : 'Todos' },
        { header: 'Canales', cell: (r) => r.channels.map((c) => CHANNEL_LABEL[c]).join(', ') },
      ]}
      fields={[
        { key: 'name', label: 'Nombre de la regla', required: true, full: true },
        { key: 'min_severity', label: 'Alertar desde severidad', type: 'select', required: true, options: SEVERITIES.map((s) => ({ value: s, label: SEVERITY_LABEL[s] })) },
        { key: 'enabled', label: 'Regla activa', type: 'switch' },
        { key: 'channels', label: 'Canales', type: 'hidden', validate: (v) => (v.length ? null : 'Elija al menos un canal de entrega.') },
        { key: 'include_noise', label: 'Incluir hallazgos marcados como ruido', type: 'checkbox', full: true },
      ]}
      extraForm={(form, set, errs) => (
        <div className="stack" style={{ marginTop: 14 }}>
          <fieldset style={{ border: '1px solid var(--line)', borderRadius: 6, padding: '8px 14px 12px' }}>
            <legend className="small" style={{ fontWeight: 600, padding: '0 6px' }}>Tipos de hallazgo (vacío = todos)</legend>
            <div className="row" style={{ gap: 14 }}>
              {Object.entries(FINDING_TYPE_LABEL).map(([k, l]) => (
                <Check key={k} label={l} checked={form.finding_types.includes(k)} onChange={(c) => set('finding_types', c ? [...form.finding_types, k] : form.finding_types.filter((x: string) => x !== k))} />
              ))}
            </div>
          </fieldset>
          <fieldset style={{ border: '1px solid var(--line)', borderRadius: 6, padding: '8px 14px 12px' }}>
            <legend className="small" style={{ fontWeight: 600, padding: '0 6px' }}>Canales de entrega</legend>
            <div className="row" style={{ gap: 14 }}>
              {Object.entries(CHANNEL_LABEL).map(([k, l]) => (
                <Check key={k} label={l} checked={form.channels.includes(k)} onChange={(c) => set('channels', c ? [...form.channels, k] : form.channels.filter((x: string) => x !== k))} />
              ))}
            </div>
            {form.channels.includes('webhook') && <div style={{ marginTop: 10 }}><TextField label="URL del webhook" type="url" mono value={form.webhook_url ?? ''} onChange={(e) => set('webhook_url', e.target.value)} placeholder="https://" /></div>}
            {form.channels.includes('email') && <div style={{ marginTop: 10 }}><TextField label="Enviar correo a" type="email" value={form.email_to ?? ''} onChange={(e) => set('email_to', e.target.value)} /></div>}
          </fieldset>
          {errs.channels && <p className="small" role="alert" style={{ color: 'var(--crit-ink)' }}>{errs.channels}</p>}
        </div>
      )}
    />
  )
}

export default function Alerts() {
  const can = useCan('alerts')
  const [tab, setTab] = useState<'inbox' | 'rules'>('inbox')
  return (
    <div className="page">
      <PageHead title="Alertas" desc="Avisos generados por las reglas cuando aparece un hallazgo relevante. Acúselas cuando las haya revisado." />
      <Tabs value={tab} onChange={setTab} tabs={[{ value: 'inbox', label: 'Bandeja' }, { value: 'rules', label: 'Reglas de alerta' }]} />
      {tab === 'inbox' ? <Inbox /> : can.view ? <div className="rules-embed"><Rules /></div> : null}
    </div>
  )
}
