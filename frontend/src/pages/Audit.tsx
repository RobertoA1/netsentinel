import { useState } from 'react'
import { X } from 'lucide-react'
import { useGet } from '../api/hooks'
import type { AuditEvent, AuditSummary, ModuleSession, Page, User } from '../api/types'
import { useFilters } from '../lib/useFilters'
import { useCan } from '../auth/AuthProvider'
import { Button } from '../ui/Button'
import { Tabs } from '../ui/Controls'
import { SelectField, TextField } from '../ui/Fields'
import { TimeFilter } from '../ui/TimeFilter'
import { Pagination } from '../ui/Pagination'
import { Dialog } from '../ui/Dialog'
import { DataState, EmptyState, PageHead, SkeletonRows } from '../ui/State'
import { duration, num, useFmt } from '../lib/format'
import { EVENT_LABEL, MODULES, moduleLabel } from '../lib/labels'

type Tab = 'events' | 'sessions' | 'summary'
const EXIT: Record<string, string> = { navigation: 'Cambió de módulo', logout: 'Cerró sesión', timeout: 'Sesión expirada', close: 'Cerró la pestaña' }

export default function Audit() {
  const [tab, setTab] = useState<Tab>('events')
  const F = useFilters({ range: '7d' })
  const can = useCan('users')
  const users = useGet<Page<User>>('/users', { page_size: 100 }, { enabled: can.view, retry: false })
  const v = F.values
  const common = (
    <>
      {users.data && <SelectField label="Usuario" value={v.user_id || ''} onChange={(e) => F.set({ user_id: e.target.value })} placeholder="Todos" options={users.data.items.map((u) => ({ value: u.id, label: u.full_name }))} />}
      <SelectField label="Módulo" value={v.module || ''} onChange={(e) => F.set({ module: e.target.value })} placeholder="Todos" options={Object.entries(MODULES).map(([value, m]) => ({ value, label: m.label }))} />
    </>
  )
  const clear = (v.user_id || v.module || v.event_type || v.q) && <Button variant="ghost" onClick={() => F.set({ user_id: null, module: null, event_type: null, q: null })}><X size={15} /> Limpiar</Button>
  return (
    <div className="page">
      <PageHead title="Bitácora" desc="Registro de solo lectura de quién hizo qué y en qué módulo estuvo. No puede editarse ni borrarse." />
      <Tabs value={tab} onChange={setTab} tabs={[{ value: 'events', label: 'Eventos' }, { value: 'sessions', label: 'Sesiones de módulo' }, { value: 'summary', label: 'Resumen' }]} />
      <section className="panel">
        <div className="filters" role="search" aria-label="Filtros de bitácora">
          {tab !== 'summary' && common}
          {tab === 'events' && (
            <>
              <SelectField label="Tipo de evento" value={v.event_type || ''} onChange={(e) => F.set({ event_type: e.target.value })} placeholder="Todos" options={Object.entries(EVENT_LABEL).map(([value, label]) => ({ value, label }))} />
              <TextField label="Texto" className="wide" value={v.q || ''} onChange={(e) => F.set({ q: e.target.value })} placeholder="Descripción, IP…" />
            </>
          )}
          <TimeFilter values={v} set={F.set} />
          {tab !== 'summary' && clear}
        </div>
        {tab === 'events' && <Events F={F} />}
        {tab === 'sessions' && <Sessions F={F} />}
        {tab === 'summary' && <Summary F={F} />}
      </section>
    </div>
  )
}
type FF = ReturnType<typeof useFilters>

function Events({ F }: { F: FF }) {
  const fmt = useFmt()
  const [sel, setSel] = useState<AuditEvent | null>(null)
  const q = useGet<Page<AuditEvent>>('/audit/events', { ...F.params, sort: '-ts' }, { keep: true })
  return (
    <DataState q={q} skeleton={<SkeletonRows rows={10} h={20} />} isEmpty={(d) => d.items.length === 0} empty={<EmptyState title="Sin eventos para estos filtros" />}>
      {(d) => (
        <>
          <div className="table-wrap">
            <table className="t">
              <thead><tr><th>Fecha</th><th>Usuario</th><th>Evento</th><th>Módulo</th><th>Descripción</th><th>IP</th></tr></thead>
              <tbody>{d.items.map((e) => (
                <tr key={e.id} className="clickable" onClick={() => setSel(e)} tabIndex={0} onKeyDown={(k) => { if (k.key === 'Enter') setSel(e) }}>
                  <td className="nowrap">{fmt.dt(e.ts)}</td><td className="cell-main">{e.username || '—'}</td>
                  <td><span className={`badge ${e.event_type === 'login_failed' ? 'crit' : e.event_type === 'delete' ? 'high' : e.event_type === 'export' || e.event_type === 'execute' ? 'accent' : ''}`}>{EVENT_LABEL[e.event_type]}</span></td>
                  <td>{moduleLabel(e.module)}</td><td style={{ maxWidth: 420 }}>{e.description}</td><td className="mono small">{e.ip}</td>
                </tr>))}</tbody>
            </table>
          </div>
          <Pagination page={d.page} pageSize={d.page_size} total={d.total} onPage={(p) => F.set({ page: p }, true)} onSize={(s) => F.set({ page_size: s })} />
          <Dialog open={!!sel} onClose={() => setSel(null)} title="Detalle del evento" drawer>
            {sel && (
              <div className="stack">
                <dl className="dl">
                  <dt>Fecha</dt><dd>{fmt.dt(sel.ts)}</dd><dt>Usuario</dt><dd>{sel.username}</dd><dt>Evento</dt><dd>{EVENT_LABEL[sel.event_type]}</dd>
                  <dt>Módulo</dt><dd>{moduleLabel(sel.module)}</dd>
                  {sel.entity && <><dt>Entidad</dt><dd>{sel.entity} {sel.entity_id != null && `#${sel.entity_id}`}</dd></>}
                  <dt>Descripción</dt><dd>{sel.description}</dd><dt>IP</dt><dd className="mono">{sel.ip}</dd><dt>Navegador</dt><dd className="small">{sel.user_agent}</dd>
                </dl>
                {sel.details && Object.keys(sel.details).length > 0 && <div><h3 style={{ marginBottom: 6 }}>Detalles</h3><pre className="mono-block" tabIndex={0}>{JSON.stringify(sel.details, null, 2)}</pre></div>}
              </div>
            )}
          </Dialog>
        </>
      )}
    </DataState>
  )
}

function Sessions({ F }: { F: FF }) {
  const fmt = useFmt()
  const q = useGet<Page<ModuleSession>>('/audit/module-sessions', { ...F.params, sort: '-entered_at' }, { keep: true })
  return (
    <DataState q={q} skeleton={<SkeletonRows rows={10} h={20} />} isEmpty={(d) => d.items.length === 0} empty={<EmptyState title="Sin sesiones de módulo para estos filtros" />}>
      {(d) => (
        <>
          <div className="table-wrap">
            <table className="t">
              <thead><tr><th>Usuario</th><th>Módulo</th><th>Entró</th><th>Salió</th><th className="num">Duración</th><th>Motivo de salida</th><th>IP</th></tr></thead>
              <tbody>{d.items.map((s) => (
                <tr key={s.id}>
                  <td className="cell-main">{s.username}</td><td>{moduleLabel(s.module)}</td><td className="nowrap">{fmt.dt(s.entered_at)}</td>
                  <td className="nowrap">{s.exited_at ? fmt.dt(s.exited_at) : <span className="badge accent">En curso</span>}</td>
                  <td className="num">{duration(s.duration_seconds)}</td><td>{s.exit_reason ? EXIT[s.exit_reason] : '—'}</td><td className="mono small">{s.ip}</td>
                </tr>))}</tbody>
            </table>
          </div>
          <Pagination page={d.page} pageSize={d.page_size} total={d.total} onPage={(p) => F.set({ page: p }, true)} onSize={(s) => F.set({ page_size: s })} />
        </>
      )}
    </DataState>
  )
}

function Summary({ F }: { F: FF }) {
  const fmt = useFmt()
  const q = useGet<AuditSummary>('/audit/summary', { ...F.params, page: undefined, page_size: undefined }, { keep: true })
  return (
    <DataState q={q} skeleton={<SkeletonRows rows={8} />} isEmpty={(d) => d.by_module.length + d.by_user.length + d.by_event_type.length === 0} empty={<EmptyState title="Sin actividad en este rango" />}>
      {(s) => {
        const maxT = Math.max(...s.by_module.map((m) => m.total_seconds), 1)
        const maxE = Math.max(...s.by_event_type.map((m) => m.count), 1)
        return (
          <div className="grid" style={{ padding: 16, marginBottom: 0 }}>
            <section className="span-6" aria-label="Tiempo por módulo">
              <h3 style={{ marginBottom: 8 }}>Tiempo por módulo</h3>
              <ol className="bar-list" style={{ border: '1px solid var(--line)', borderRadius: 8 }}>
                {s.by_module.map((m) => (
                  <li key={m.module} className="bar-row" style={{ gridTemplateColumns: '110px minmax(0,1fr) 110px' }}>
                    <span className="cell-main">{moduleLabel(m.module)}</span>
                    <div className="bar-track" aria-hidden><div className="bar-fill" style={{ width: `${(m.total_seconds / maxT) * 100}%` }} /></div>
                    <span className="bar-val">{duration(m.total_seconds)}<small>{num(m.visits)} {m.visits === 1 ? 'visita' : 'visitas'}</small></span>
                  </li>
                ))}
              </ol>
            </section>
            <section className="span-6" aria-label="Eventos por tipo">
              <h3 style={{ marginBottom: 8 }}>Eventos por tipo</h3>
              <ol className="bar-list" style={{ border: '1px solid var(--line)', borderRadius: 8 }}>
                {s.by_event_type.map((m) => (
                  <li key={m.event_type} className="bar-row" style={{ gridTemplateColumns: '150px minmax(0,1fr) 60px' }}>
                    <span>{EVENT_LABEL[m.event_type as keyof typeof EVENT_LABEL] ?? m.event_type}</span>
                    <div className="bar-track" aria-hidden><div className="bar-fill in" style={{ width: `${(m.count / maxE) * 100}%` }} /></div>
                    <span className="bar-val" style={{ minWidth: 0 }}>{num(m.count)}</span>
                  </li>
                ))}
              </ol>
            </section>
            <section className="span-12" aria-label="Actividad por usuario">
              <h3 style={{ marginBottom: 8 }}>Actividad por usuario</h3>
              <div className="table-wrap" style={{ border: '1px solid var(--line)', borderRadius: 8 }}>
                <table className="t">
                  <thead><tr><th>Usuario</th><th className="num">Visitas a módulos</th><th className="num">Tiempo total</th><th>Última actividad</th></tr></thead>
                  <tbody>{s.by_user.map((u) => <tr key={u.username}><td className="cell-main">{u.username}</td><td className="num">{num(u.visits)}</td><td className="num">{duration(u.total_seconds)}</td><td>{fmt.dt(u.last_seen)}</td></tr>)}</tbody>
                </table>
              </div>
            </section>
          </div>
        )
      }}
    </DataState>
  )
}
