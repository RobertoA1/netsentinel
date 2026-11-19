import { useMemo, useState, type FormEvent } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Upload } from 'lucide-react'
import { api } from '../api/client'
import { useGet } from '../api/hooks'
import { useCan } from '../auth/AuthProvider'
import { Button } from '../ui/Button'
import { Dialog } from '../ui/Dialog'
import { Field, SelectField, TextArea, TextField } from '../ui/Fields'
import { Tabs } from '../ui/Controls'
import { DataState, EmptyState, PageHead, SkeletonRows } from '../ui/State'
import { useToast } from '../ui/Toast'
import { num, useFmt } from '../lib/format'
import { errMsg } from '../lib/utils'
import { SpecGrid, SpecCard, Reading, type Spec } from '../ml/figures'
import { GROUP_ES, Kv, Notice, useDatasets } from '../ml/common'
import type { Dataset, Summary, Validation } from '../ml/types'

type Tab = 'summary' | 'meta' | 'groups'

export default function MlData() {
  const can = useCan('ml_data')
  const [sp, setSp] = useSearchParams()
  const q = useDatasets()
  const [create, setCreate] = useState(false)
  const sel = Number(sp.get('ds')) || null
  const [tab, setTab] = useState<Tab>('summary')
  const f = useFmt()
  const current = q.data?.find((d) => d.id === sel) ?? q.data?.[0] ?? null
  return (
    <div className="page">
      <PageHead title="Datos del laboratorio" desc="Conjuntos etiquetados para entrenar el clasificador Botnet vs Normal. Los flujos Background se excluyen del entrenamiento y la evaluación porque no tienen verdad conocida.">
        {can.create && <Button variant="primary" onClick={() => setCreate(true)}><Plus size={15} /> Registrar dataset</Button>}
      </PageHead>
      <DataState q={q} skeleton={<div className="panel"><SkeletonRows rows={4} /></div>} isEmpty={(d) => d.length === 0}
        empty={<div className="panel"><EmptyState title="Todavía no hay datasets" icon={<Upload size={28} />} action={can.create ? <Button variant="primary" onClick={() => setCreate(true)}>Registrar el primero</Button> : undefined}>Registre un dataset desde una fuente ya ingerida (CTU-13) o suba un archivo etiquetado. No se descarga nada de Internet.</EmptyState></div>}>
        {(list) => (
          <div className="stack" style={{ gap: 16 }}>
            <section className="panel" aria-label="Datasets registrados">
              <div className="table-wrap">
                <table className="t">
                  <thead><tr><th>Dataset</th><th>Origen</th><th className="num">Flujos únicos</th><th className="num">Duplicados descartados</th><th>Unidad</th><th>Agrupación</th><th className="num">Versión</th><th>Creado</th></tr></thead>
                  <tbody>{list.map((d) => (
                    <tr key={d.id} className={`clickable${current?.id === d.id ? ' sel' : ''}`} tabIndex={0} onClick={() => setSp({ ds: String(d.id) })} onKeyDown={(e) => { if (e.key === 'Enter') setSp({ ds: String(d.id) }) }}>
                      <td className="cell-main">{d.name}</td><td>{d.origin === 'source' ? `Fuente #${d.source_id}` : 'Archivo subido'}</td>
                      <td className="num">{num(d.n_rows)}</td><td className="num">{num(d.n_duplicates_dropped)}</td>
                      <td>{d.meta.unit === 'window' ? `Ventana ${d.meta.window_minutes} min` : 'Flujo'}</td><td>{GROUP_ES[d.meta.group_key]}{d.meta.group_key === 'time_block' ? ` (${d.meta.time_block_seconds} s)` : ''}</td>
                      <td className="num">v{d.current_version}</td><td className="nowrap">{f.day(d.created_at)}</td>
                    </tr>))}</tbody>
                </table>
              </div>
            </section>
            {current && (
              <>
                {current.n_duplicates_dropped > 0 && <Notice>Este origen contiene {num(current.n_duplicates_dropped)} filas repetidas (carga doble). Se descartan al construir la instantánea; la base de datos no se modifica.</Notice>}
                <Tabs value={tab} onChange={setTab} tabs={[{ value: 'summary', label: 'Resumen y estadística' }, { value: 'groups', label: 'Validación de grupos' }, { value: 'meta', label: 'Metadatos y versiones' }]} />
                {tab === 'summary' && <SummaryTab ds={current} />}
                {tab === 'groups' && <GroupsTab ds={current} canEdit={can.update} />}
                {tab === 'meta' && <MetaTab ds={current} canEdit={can.update} />}
              </>
            )}
          </div>
        )}
      </DataState>
      {create && <CreateDialog onClose={() => setCreate(false)} onCreated={(id) => { setSp({ ds: String(id) }); setCreate(false) }} />}
    </div>
  )
}

function SummaryTab({ ds }: { ds: Dataset }) {
  const q = useGet<Summary>(`/ml/data/versions/${ds.current_version_id}/summary`, undefined, { staleTime: 60_000 })
  return (
    <DataState q={q} skeleton={<div className="panel"><SkeletonRows rows={8} /></div>}>
      {(s) => (
        <div className="stack" style={{ gap: 16 }}>
          <div className="panel"><dl className="kpis" style={{ borderTop: 0 }}>
            {[['Elementos etiquetados', s.n_labeled], ['Botnet', s.n_botnet], ['Normal', s.n_normal], ['Excluidos (Background)', s.n_excluded], ['Filas en la instantánea', s.n_rows]].map(([k, v]) => <div className="kpi" key={String(k)}><dt>{k}</dt><dd>{num(v as number)}</dd></div>)}
          </dl></div>
          <SpecGrid specs={[...s.figures, ...s.tables]} module="ml_data" />
        </div>
      )}
    </DataState>
  )
}

function GroupsTab({ ds, canEdit }: { ds: Dataset; canEdit: boolean }) {
  const q = useGet<Validation>(`/ml/data/versions/${ds.current_version_id}/validation`, undefined, { staleTime: 60_000 })
  const toast = useToast()
  const qc = useQueryClient()
  const apply = useMutation({
    mutationFn: (b: object) => api.put(`/ml/data/datasets/${ds.id}`, b),
    onSuccess: () => { toast.ok('Se creó una versión nueva con la agrupación recomendada.'); void qc.invalidateQueries({ queryKey: ['/ml/data/datasets'] }); void qc.invalidateQueries({ queryKey: [`/ml/data/datasets/${ds.id}`] }) },
    onError: (e) => toast.err(errMsg(e)),
  })
  return (
    <DataState q={q} skeleton={<div className="panel"><SkeletonRows rows={8} /></div>}>
      {(v) => {
        const chosen = v.keys[v.chosen]
        return (
          <div className="stack" style={{ gap: 16 }}>
            {!chosen.viable ? (
              <Notice kind="block"><b>Entrenamiento bloqueado.</b> La agrupación elegida («{chosen.label}») no permite 5 pliegues externos × 3 internos sin fuga entre grupos.<ul style={{ margin: '6px 0 0', paddingLeft: 18 }}>{chosen.blocking.slice(0, 4).map((b, i) => <li key={i}>{b}</li>)}</ul></Notice>
            ) : <Notice kind="warn"><b>Agrupación viable:</b> «{chosen.label}»{v.chosen === 'time_block' ? ` (bloques de ${ds.meta.time_block_seconds} s)` : ''} permite 5×3 pliegues. {v.n_hosts_botnet <= 5 && <>Solo {v.n_hosts_botnet} hosts generan tráfico Botnet: agrupar por host no es posible y esta validación es menos exigente.</>}</Notice>}
            <section className="panel">
              <div className="panel-head"><h3>Claves de agrupación comparadas (n = {num(v.n_rows)} elementos etiquetados)</h3>
                {canEdit && v.recommended && v.recommended !== v.chosen && <Button variant="primary" size="sm" loading={apply.isPending} onClick={() => apply.mutate({ note: `Agrupación recomendada por el validador: ${GROUP_ES[v.recommended!]}`, group_key: v.recommended, ...(v.recommended === 'time_block' && v.recommended_block_seconds ? { time_block_seconds: v.recommended_block_seconds } : {}) })}>Aplicar la recomendada ({GROUP_ES[v.recommended]}{v.recommended_block_seconds ? `, ${v.recommended_block_seconds} s` : ''})</Button>}
              </div>
              <div className="table-wrap"><table className="t">
                <thead><tr><th>Clave</th><th>¿Viable para 5×3?</th><th className="num">Grupos Botnet</th><th className="num">Grupos Normal</th><th>Motivo principal</th></tr></thead>
                <tbody>{Object.values(v.keys).map((k) => (
                  <tr key={k.group_key}><td className="cell-main">{k.label}{k.group_key === v.chosen && <> <span className="badge accent">elegida</span></>}{k.group_key === v.recommended && <> <span className="badge ok">recomendada</span></>}</td>
                    <td><span className={`badge ${k.viable ? 'ok' : 'crit'}`}>{k.viable ? 'Sí' : 'No'}</span></td>
                    <td className="num">{k.class_stats ? num(k.class_stats.Botnet.groups) : '—'}</td><td className="num">{k.class_stats ? num(k.class_stats.Normal.groups) : '—'}</td>
                    <td style={{ whiteSpace: 'normal', maxWidth: 520 }}>{k.blocking[0] ?? '—'}</td></tr>))}</tbody>
              </table></div>
              <div className="panel-body"><Reading ip={v.interpretation_global} /></div>
            </section>
            <section className="panel">
              <div className="panel-head"><h3>Tamaños de bloque temporal probados</h3><span className="hint">Se recomienda el mayor viable: menos autocorrelación entre bloques vecinos</span></div>
              <div className="table-wrap"><table className="t">
                <thead><tr><th className="num">Bloque (s)</th><th>Viable</th><th className="num">Grupos Botnet</th><th className="num">Grupos Normal</th><th>Problema</th></tr></thead>
                <tbody>{v.time_block_options.map((o) => <tr key={o.seconds}><td className="num">{o.seconds}</td><td><span className={`badge ${o.viable ? 'ok' : 'crit'}`}>{o.viable ? 'Sí' : 'No'}</span></td><td className="num">{o.groups_botnet}</td><td className="num">{o.groups_normal}</td><td style={{ whiteSpace: 'normal' }}>{o.problem ?? '—'}</td></tr>)}</tbody>
              </table></div>
            </section>
            <SpecCard spec={v.partition_table as Spec} />
          </div>
        )
      }}
    </DataState>
  )
}

function MetaTab({ ds, canEdit }: { ds: Dataset; canEdit: boolean }) {
  const q = useGet<Dataset>(`/ml/data/datasets/${ds.id}`)
  const f = useFmt()
  return (
    <DataState q={q} skeleton={<div className="panel"><SkeletonRows rows={8} /></div>}>
      {(d) => (
        <div className="mlsplit" style={{ gridTemplateColumns: 'minmax(0,1.3fr) minmax(280px,1fr)' }}>
          <MetaForm key={d.current_version_id} ds={d} canEdit={canEdit} />
          <section className="panel" aria-label="Versiones">
            <div className="panel-head"><h3>Versiones (inmutables)</h3><span className="hint">Cada edición crea una nueva</span></div>
            <div className="table-wrap"><table className="t"><thead><tr><th>Versión</th><th>Cambio</th><th>Autor</th><th>Fecha</th><th>Hash</th></tr></thead>
              <tbody>{d.versions?.map((v) => <tr key={v.id}><td className="cell-main">v{v.version}</td><td style={{ whiteSpace: 'normal' }}>{v.change_note || '—'}</td><td>{v.created_by}</td><td className="nowrap">{f.dt(v.created_at)}</td><td className="mono" title={v.content_hash}>{v.content_hash.slice(0, 10)}</td></tr>)}</tbody></table></div>
            <div className="panel-body"><Kv rows={[['SHA-256 de la instantánea', <span className="mono" style={{ fontSize: 11 }}>{d.snapshot_sha256}</span>]]} /></div>
          </section>
        </div>
      )}
    </DataState>
  )
}

function MetaForm({ ds, canEdit }: { ds: Dataset; canEdit: boolean }) {
  const m = ds.meta
  const toast = useToast()
  const qc = useQueryClient()
  const [f, setF] = useState({ name: m.name, description: m.description, provenance: m.provenance, license: m.license, unit: m.unit, window_minutes: String(m.window_minutes), group_key: m.group_key, time_block_seconds: String(m.time_block_seconds), notes: m.notes, note: '' })
  const [lm, setLm] = useState<Record<string, string>>(m.label_map)
  const [showMap, setShowMap] = useState(false)
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF((x) => ({ ...x, [k]: e.target.value }))
  const counts = useMemo(() => { const c = { Botnet: 0, Normal: 0, excluded: 0 } as Record<string, number>; Object.values(lm).forEach((v) => { c[v] = (c[v] ?? 0) + 1 }); return c }, [lm])
  const save = useMutation({
    mutationFn: (b: object) => api.put(`/ml/data/datasets/${ds.id}`, b),
    onSuccess: () => { toast.ok('Se guardó una nueva versión del dataset.'); void qc.invalidateQueries({ queryKey: ['/ml/data/datasets'] }); void qc.invalidateQueries({ queryKey: [`/ml/data/datasets/${ds.id}`] }) },
    onError: (e) => toast.err(errMsg(e)),
  })
  const bad = f.unit === 'window' && f.group_key === 'src_dst' ? 'El par origen-destino no aplica a ventanas host-tiempo.' : null
  function submit(e: FormEvent) {
    e.preventDefault()
    if (bad) return
    save.mutate({ note: f.note || 'Edición de metadatos', name: f.name, description: f.description, provenance: f.provenance, license: f.license, label_map: lm, unit: f.unit, window_minutes: Number(f.window_minutes), group_key: f.group_key, time_block_seconds: Number(f.time_block_seconds), notes: f.notes })
  }
  const dis = !canEdit
  return (
    <form className="panel" onSubmit={submit} noValidate>
      <div className="panel-head"><h3>Metadatos de la versión v{ds.current_version}</h3><span className="hint">Guardar crea la v{ds.current_version + 1}</span></div>
      <div className="panel-body form-grid">
        <TextField label="Nombre" value={f.name} onChange={set('name')} disabled={dis} />
        <SelectField label="Unidad de análisis" value={f.unit} onChange={set('unit')} disabled={dis} options={[{ value: 'flow', label: 'Flujo (una fila por conexión)' }, { value: 'window', label: 'Ventana host-tiempo (por IP origen)' }]} />
        <TextField label="Tamaño de ventana (min)" inputMode="decimal" value={f.window_minutes} onChange={set('window_minutes')} disabled={dis || f.unit !== 'window'} help="Entre 0,25 y 240. Solo aplica a ventanas." />
        <SelectField label="Clave de agrupación" value={f.group_key} onChange={set('group_key')} disabled={dis} error={bad} options={[{ value: 'time_block', label: 'Bloque temporal' }, { value: 'src_dst', label: 'Par origen-destino' }, { value: 'src_ip', label: 'Host origen' }]} />
        <TextField label="Bloque temporal (s)" inputMode="decimal" value={f.time_block_seconds} onChange={set('time_block_seconds')} disabled={dis || f.group_key !== 'time_block'} help="Segundos por bloque; todo el bloque va a una sola partición." />
        <TextArea className="full" label="Descripción" value={f.description} onChange={set('description')} disabled={dis} rows={2} />
        <TextArea className="full" label="Procedencia" value={f.provenance} onChange={set('provenance')} disabled={dis} rows={3} />
        <TextArea className="full" label="Licencia y atribución" value={f.license} onChange={set('license')} disabled={dis} rows={3} />
        <TextArea className="full" label="Notas" value={f.notes} onChange={set('notes')} disabled={dis} rows={2} />
        <div className="full">
          <div className="row between"><b className="small">Mapa de etiquetas: {counts.Botnet} → Botnet, {counts.Normal} → Normal, {counts.excluded} excluidas</b><Button size="sm" onClick={() => setShowMap((s) => !s)}>{showMap ? 'Ocultar' : 'Editar mapa'}</Button></div>
          {showMap && (
            <div className="table-wrap" style={{ maxHeight: 260, overflow: 'auto', marginTop: 8, border: '1px solid var(--line)', borderRadius: 6 }}>
              <table className="t"><thead><tr><th>Etiqueta original</th><th>Clase</th></tr></thead>
                <tbody>{Object.entries(lm).map(([k, v]) => <tr key={k}><td className="mono" style={{ fontSize: 12 }}>{k}</td><td><select className="select" aria-label={`Clase de ${k}`} value={v} disabled={dis} onChange={(e) => setLm((x) => ({ ...x, [k]: e.target.value }))}><option value="Botnet">Botnet</option><option value="Normal">Normal</option><option value="excluded">Excluida (Background)</option></select></td></tr>)}</tbody></table>
            </div>
          )}
        </div>
        {canEdit && <>
          <TextField className="full" label="Motivo del cambio" value={f.note} onChange={set('note')} help="Queda registrado en la versión." />
          <div className="full"><Button variant="primary" type="submit" loading={save.isPending} disabled={!!bad}>Guardar como nueva versión</Button></div>
        </>}
      </div>
    </form>
  )
}

function CreateDialog({ onClose, onCreated }: { onClose: () => void; onCreated: (id: number) => void }) {
  const toast = useToast()
  const qc = useQueryClient()
  const sources = useGet<{ id: number; name: string; format: string; logs: number }[]>('/ml/data/sources')
  const [mode, setMode] = useState<'source' | 'upload'>('source')
  const [name, setName] = useState('')
  const [src, setSrc] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [desc, setDesc] = useState('')
  const done = (d: Dataset) => { toast.ok(`Dataset «${d.name}» registrado (${num(d.n_rows)} filas).`); void qc.invalidateQueries({ queryKey: ['/ml/data/datasets'] }); onCreated(d.id) }
  const mut = useMutation({
    mutationFn: () => {
      if (mode === 'source') return api.post<Dataset>('/ml/data/datasets', { name, source_id: Number(src), description: desc || undefined })
      const fd = new FormData(); fd.append('file', file!); fd.append('name', name); fd.append('description', desc)
      return api.upload<Dataset>('/ml/data/datasets/upload', fd)
    },
    onSuccess: done, onError: (e) => toast.err(errMsg(e)),
  })
  const ok = name.trim().length >= 2 && (mode === 'source' ? !!src : !!file)
  return (
    <Dialog open onClose={onClose} title="Registrar dataset" footer={<><Button onClick={onClose}>Cancelar</Button><Button variant="primary" disabled={!ok} loading={mut.isPending} onClick={() => mut.mutate()}>Registrar</Button></>}>
      <div className="stack">
        <Tabs value={mode} onChange={setMode} tabs={[{ value: 'source', label: 'Desde una fuente ingerida' }, { value: 'upload', label: 'Subir archivo etiquetado' }]} />
        <TextField label="Nombre" value={name} onChange={(e) => setName(e.target.value)} />
        {mode === 'source'
          ? <SelectField label="Fuente" value={src} onChange={(e) => setSrc(e.target.value)} placeholder={sources.isPending ? 'Cargando…' : 'Elija una fuente'} options={(sources.data ?? []).map((s) => ({ value: s.id, label: `${s.name} · ${num(s.logs)} registros` }))} help="Solo fuentes CTU-13 binetflow ya ingeridas, con etiqueta." />
          : <Field label="Archivo (.binetflow, .csv, .txt o .gz)" help="Con columnas de flujo y etiqueta. Se valida el contenido y el tamaño; nunca se ejecuta ni se descarga nada.">{(p) => <input className="input" type="file" accept=".binetflow,.csv,.txt,.gz" {...p} onChange={(e) => setFile(e.target.files?.[0] ?? null)} />}</Field>}
        <TextArea label="Descripción (opcional)" value={desc} onChange={(e) => setDesc(e.target.value)} rows={2} />
      </div>
    </Dialog>
  )
}
