import { useState } from 'react'
import { X } from 'lucide-react'
import { useGet } from '../api/hooks'
import type { FirewallLog, Page } from '../api/types'
import { useFilters } from '../lib/useFilters'
import { PageHead, DataState, EmptyState, SkeletonRows } from '../ui/State'
import { Button } from '../ui/Button'
import { SelectField, TextField } from '../ui/Fields'
import { TimeFilter } from '../ui/TimeFilter'
import { Pagination } from '../ui/Pagination'
import { Dialog } from '../ui/Dialog'
import { ActionBadge } from '../ui/Badges'
import { bytes, num, duration, useFmt } from '../lib/format'
import { ACTION_LABEL, DIRECTION_LABEL, LOG_TYPE_LABEL } from '../lib/labels'
import type { Source } from '../api/types'

export default function Logs() {
  const F = useFilters({ range: '24h' })
  const fmt = useFmt()
  const [sel, setSel] = useState<number | null>(null)
  const q = useGet<Page<FirewallLog>>('/logs', { ...F.params, sort: '-ts' }, { keep: true })
  const sources = useGet<Page<Source> | Source[]>('/sources', undefined, { retry: false })
  const srcList = Array.isArray(sources.data) ? sources.data : sources.data?.items ?? []
  const v = F.values
  const sf = (k: string) => (e: { target: { value: string } }) => F.set({ [k]: e.target.value })
  const active = ['q', 'src_ip', 'dst_ip', 'dst_port', 'proto', 'action', 'log_type', 'direction', 'source_id', 'from', 'to'].some((k) => v[k])
  const selected = q.data?.items.find((l) => l.id === sel)

  return (
    <div className="page">
      <PageHead title="Registros" desc="Eventos de firewall, IDS y flujos ingeridos. Filtre para encontrar una conexión concreta." />
      <section className="panel">
        <div className="filters" role="search" aria-label="Filtros de registros">
          <TextField label="Texto" className="wide" value={v.q || ''} onChange={sf('q')} placeholder="IP, firma, categoría…" />
          <TextField label="IP origen" mono value={v.src_ip || ''} onChange={sf('src_ip')} />
          <TextField label="IP destino" mono value={v.dst_ip || ''} onChange={sf('dst_ip')} />
          <TextField label="Puerto destino" className="narrow" inputMode="numeric" value={v.dst_port || ''} onChange={sf('dst_port')} />
          <SelectField label="Protocolo" className="narrow" value={v.proto || ''} onChange={sf('proto')} placeholder="Todos" options={['tcp', 'udp', 'icmp'].map((x) => ({ value: x, label: x.toUpperCase() }))} />
          <SelectField label="Acción" value={v.action || ''} onChange={sf('action')} placeholder="Todas" options={Object.entries(ACTION_LABEL).map(([value, label]) => ({ value, label }))} />
          <SelectField label="Tipo" value={v.log_type || ''} onChange={sf('log_type')} placeholder="Todos" options={Object.entries(LOG_TYPE_LABEL).map(([value, label]) => ({ value, label }))} />
          <SelectField label="Dirección" value={v.direction || ''} onChange={sf('direction')} placeholder="Todas" options={Object.entries(DIRECTION_LABEL).map(([value, label]) => ({ value, label }))} />
          {srcList.length > 0 && <SelectField label="Fuente" value={v.source_id || ''} onChange={sf('source_id')} placeholder="Todas" options={srcList.map((s) => ({ value: s.id, label: s.name }))} />}
          <TimeFilter values={v} set={F.set} />
          {active && <Button variant="ghost" onClick={() => F.set({ q: null, src_ip: null, dst_ip: null, dst_port: null, proto: null, action: null, log_type: null, direction: null, source_id: null, from: null, to: null })}><X size={15} /> Limpiar</Button>}
        </div>
        <DataState q={q} skeleton={<SkeletonRows rows={10} h={20} />} isEmpty={(d) => d.items.length === 0}
          empty={<EmptyState title="Ningún registro coincide">{active ? 'Pruebe quitando algún filtro o ampliando el rango.' : 'Aún no se han ingerido registros.'}</EmptyState>}>
          {(d) => (
            <>
              <div className="table-wrap">
                <table className="t">
                  <thead><tr>
                    <th>Fecha</th><th>Acción</th><th>Origen</th><th>Destino</th><th>Proto</th><th>Dirección</th>
                    <th className="num">Salida</th><th className="num">Entrada</th><th>Detalle</th>
                  </tr></thead>
                  <tbody>
                    {d.items.map((l) => (
                      <tr key={l.id} className={`clickable${sel === l.id ? ' sel' : ''}`} onClick={() => setSel(l.id)}>
                        <td className="nowrap">{fmt.dt(l.ts)}</td>
                        <td><ActionBadge action={l.action} /></td>
                        <td className="mono nowrap">{l.src_ip}{l.src_port ? `:${l.src_port}` : ''}</td>
                        <td className="mono nowrap">{l.dst_ip}{l.dst_port ? `:${l.dst_port}` : ''}</td>
                        <td>{l.proto?.toUpperCase()}</td>
                        <td>{DIRECTION_LABEL[l.direction]}</td>
                        <td className="num">{bytes(l.bytes_out)}</td>
                        <td className="num">{bytes(l.bytes_in)}</td>
                        <td className="truncate" style={{ maxWidth: 240 }}>
                          <button className="btn sm ghost" onClick={(e) => { e.stopPropagation(); setSel(l.id) }} aria-label={`Ver detalle del registro ${l.id}`}>
                            {l.signature || LOG_TYPE_LABEL[l.log_type]}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination page={d.page} pageSize={d.page_size} total={d.total} onPage={(p) => F.set({ page: p }, true)} onSize={(s) => F.set({ page_size: s })} />
            </>
          )}
        </DataState>
      </section>
      <LogDrawer log={selected} onClose={() => setSel(null)} />
    </div>
  )
}

export function LogDrawer({ log, onClose }: { log: FirewallLog | undefined; onClose: () => void }) {
  const fmt = useFmt()
  return (
    <Dialog open={!!log} onClose={onClose} title="Detalle del registro" drawer>
      {log && (
        <div className="stack">
          <dl className="dl">
            <dt>Fecha</dt><dd>{fmt.dt(log.ts)}</dd>
            <dt>Fuente</dt><dd>{log.source_name} · {LOG_TYPE_LABEL[log.log_type]}</dd>
            <dt>Acción</dt><dd><ActionBadge action={log.action} /></dd>
            <dt>Origen</dt><dd className="mono">{log.src_ip}{log.src_port ? `:${log.src_port}` : ''}</dd>
            <dt>Destino</dt><dd className="mono">{log.dst_ip}{log.dst_port ? `:${log.dst_port}` : ''}</dd>
            <dt>Protocolo</dt><dd>{log.proto?.toUpperCase()}</dd>
            <dt>Dirección</dt><dd>{DIRECTION_LABEL[log.direction]}</dd>
            <dt>Bytes</dt><dd>{bytes(log.bytes_out)} salida · {bytes(log.bytes_in)} entrada</dd>
            <dt>Paquetes</dt><dd>{num(log.packets)}</dd>
            <dt>Duración</dt><dd>{duration(log.duration)}</dd>
            {log.signature && <><dt>Firma IDS</dt><dd>{log.signature} <span className="muted">(#{log.signature_id})</span></dd></>}
            {log.category && <><dt>Categoría</dt><dd>{log.category}</dd></>}
            {log.label && <><dt>Etiqueta</dt><dd>{log.label}</dd></>}
          </dl>
          <div>
            <h3 style={{ marginBottom: 6 }}>Registro original</h3>
            <pre className="mono-block" tabIndex={0}>{JSON.stringify(log.raw, null, 2)}</pre>
          </div>
        </div>
      )}
    </Dialog>
  )
}

