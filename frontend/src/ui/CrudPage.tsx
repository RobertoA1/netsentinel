import { useState, type FormEvent, type ReactNode } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Pencil, Plus, Trash2 } from 'lucide-react'
import { api } from '../api/client'
import { useGet } from '../api/hooks'
import type { Page } from '../api/types'
import { useCan } from '../auth/AuthProvider'
import { Button } from './Button'
import { Dialog, ConfirmDialog } from './Dialog'
import { Check, SelectField, TextArea, TextField, Switch } from './Fields'
import { DataState, EmptyState, PageHead, SkeletonRows } from './State'
import { Pagination } from './Pagination'
import { useToast } from './Toast'
import { errMsg } from '../lib/utils'

export interface FieldSpec {
  key: string
  label: string
  type?: 'hidden' | 'text' | 'number' | 'select' | 'checkbox' | 'switch' | 'textarea' | 'password' | 'email'
  options?: { value: string | number; label: string }[]
  required?: boolean
  help?: string
  full?: boolean
  mono?: boolean
  placeholder?: string
  hideOnEdit?: boolean
  onlyOnCreate?: boolean
  validate?: (v: any, form: Record<string, any>) => string | null
}
export interface Column<T> { header: string; cell: (i: T) => ReactNode; num?: boolean }

interface Props<T extends { id: number }> {
  module: string
  path: string
  title: string
  desc: string
  noun: string // "activo"
  nounPlural?: string
  paginated?: boolean
  searchable?: boolean
  columns: Column<T>[]
  fields: FieldSpec[]
  blank: Record<string, any>
  toForm?: (i: T) => Record<string, any>
  toBody?: (f: Record<string, any>, editing: T | null) => unknown
  editable?: boolean
  rowActions?: (i: T) => ReactNode
  extraHeader?: ReactNode
  canDelete?: (i: T) => boolean
  deleteMessage?: (i: T) => string
  filters?: ReactNode
  queryParams?: Record<string, string | number | undefined>
  emptyHelp?: string
  wide?: boolean
  extraForm?: (form: Record<string, any>, set: (k: string, v: any) => void, errs: Record<string, string>) => ReactNode
}

export function CrudPage<T extends { id: number }>(p: Props<T>) {
  const can = useCan(p.module)
  const qc = useQueryClient()
  const toast = useToast()
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  const [search, setSearch] = useState('')
  const [editing, setEditing] = useState<T | null>(null)
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState<Record<string, any>>(p.blank)
  const [errs, setErrs] = useState<Record<string, string>>({})
  const [del, setDel] = useState<T | null>(null)
  const editable = p.editable !== false

  const params = p.paginated ? { page, page_size: pageSize, q: p.searchable ? search : undefined, ...p.queryParams } : { ...p.queryParams }
  const q = useGet<Page<T> | T[]>(p.path, params, { keep: true })
  const items = (d: Page<T> | T[]) => (Array.isArray(d) ? d : d.items)
  const total = (d: Page<T> | T[]) => (Array.isArray(d) ? d.length : d.total)

  const refresh = () => qc.invalidateQueries({ queryKey: [p.path] })
  const save = useMutation({
    mutationFn: (body: unknown) => (editing ? api.put(`${p.path}/${editing.id}`, body) : api.post(p.path, body)),
    onSuccess: () => { toast.ok(editing ? `${cap(p.noun)} actualizado.` : `${cap(p.noun)} creado.`); close(); void refresh() },
    onError: (e) => toast.err(errMsg(e)),
  })
  const remove = useMutation({
    mutationFn: (i: T) => api.del(`${p.path}/${i.id}`),
    onSuccess: () => { toast.ok(`${cap(p.noun)} eliminado.`); setDel(null); void refresh() },
    onError: (e) => { toast.err(errMsg(e)); setDel(null) },
  })

  function openCreate() { setForm(p.blank); setErrs({}); setEditing(null); setCreating(true) }
  function openEdit(i: T) { setForm(p.toForm ? p.toForm(i) : { ...(i as any) }); setErrs({}); setEditing(i); setCreating(true) }
  function close() { setCreating(false); setEditing(null) }
  const set = (k: string, v: any) => setForm((f) => ({ ...f, [k]: v }))

  function submit(e: FormEvent) {
    e.preventDefault()
    const er: Record<string, string> = {}
    for (const f of p.fields) {
      if (f.hideOnEdit && editing) continue
      if (f.onlyOnCreate && editing) continue
      const v = form[f.key]
      if (f.required && (v === '' || v === null || v === undefined)) er[f.key] = 'Este campo es obligatorio.'
      else if (f.validate) { const m = f.validate(v, form); if (m) er[f.key] = m }
    }
    setErrs(er)
    if (Object.keys(er).length) return
    save.mutate(p.toBody ? p.toBody(form, editing) : form)
  }

  const showActions = (editable && can.update) || can.delete || !!p.rowActions

  return (
    <div className="page">
      <PageHead title={p.title} desc={p.desc}>
        {p.extraHeader}
        {can.create && <Button variant="primary" onClick={openCreate}><Plus size={16} /> Nuevo {p.noun}</Button>}
      </PageHead>
      <section className="panel">
        {(p.searchable || p.filters) && (
          <div className="filters">
            {p.searchable && <TextField label="Buscar" className="wide" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1) }} />}
            {p.filters}
          </div>
        )}
        <DataState q={q} skeleton={<SkeletonRows rows={6} h={22} />} isEmpty={(d) => items(d).length === 0}
          empty={<EmptyState title={search ? 'Sin resultados' : `Aún no hay ${p.nounPlural ?? p.noun + 's'}`} action={!search && can.create ? <Button variant="primary" onClick={openCreate}><Plus size={16} /> Nuevo {p.noun}</Button> : undefined}>{search ? 'Pruebe con otra búsqueda.' : p.emptyHelp}</EmptyState>}>
          {(d) => (
            <>
              <div className="table-wrap">
                <table className="t">
                  <thead><tr>{p.columns.map((c) => <th key={c.header} className={c.num ? 'num' : ''}>{c.header}</th>)}{showActions && <th className="num"><span className="sr-only">Acciones</span></th>}</tr></thead>
                  <tbody>
                    {items(d).map((i) => (
                      <tr key={i.id}>
                        {p.columns.map((c) => <td key={c.header} className={c.num ? 'num' : ''}>{c.cell(i)}</td>)}
                        {showActions && (
                          <td className="actions">
                            {p.rowActions?.(i)}
                            {editable && can.update && <Button size="sm" variant="ghost" icon onClick={() => openEdit(i)} aria-label={`Editar ${p.noun}`}><Pencil size={15} /></Button>}
                            {can.delete && (p.canDelete ? p.canDelete(i) : true) && <Button size="sm" variant="ghost" icon onClick={() => setDel(i)} aria-label={`Eliminar ${p.noun}`}><Trash2 size={15} /></Button>}
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {p.paginated && !Array.isArray(d) && <Pagination page={d.page} pageSize={d.page_size} total={total(d)} onPage={setPage} onSize={(s) => { setPageSize(s); setPage(1) }} />}
            </>
          )}
        </DataState>
      </section>

      <Dialog open={creating} onClose={close} title={editing ? `Editar ${p.noun}` : `Nuevo ${p.noun}`} wide={p.wide}
        footer={<><Button onClick={close}>Cancelar</Button><Button variant="primary" type="submit" form="crud-form" loading={save.isPending}>Guardar</Button></>}>
        <form id="crud-form" onSubmit={submit} noValidate>
          <div className="form-grid">
            {p.fields.filter((f) => f.type !== 'hidden' && !(editing && (f.hideOnEdit || f.onlyOnCreate))).map((f) => {
              const common = { label: f.label, help: f.help, error: errs[f.key], className: f.full ? 'full' : undefined }
              const v = form[f.key] ?? ''
              switch (f.type) {
                case 'select': return <SelectField key={f.key} {...common} value={v} onChange={(e) => set(f.key, e.target.value)} options={f.options ?? []} placeholder={f.required ? undefined : '—'} />
                case 'checkbox': return <div key={f.key} className={f.full ? 'full' : undefined}><Check label={f.label} checked={!!form[f.key]} onChange={(c) => set(f.key, c)} /></div>
                case 'switch': return <div key={f.key} className={f.full ? 'full' : undefined}><Switch label={f.label} checked={!!form[f.key]} onChange={(c) => set(f.key, c)} /></div>
                case 'textarea': return <TextArea key={f.key} {...common} value={v} onChange={(e) => set(f.key, e.target.value)} />
                default: return <TextField key={f.key} {...common} mono={f.mono} type={f.type === 'number' ? 'number' : f.type ?? 'text'} placeholder={f.placeholder} value={v} onChange={(e) => set(f.key, f.type === 'number' ? (e.target.value === '' ? '' : Number(e.target.value)) : e.target.value)} autoComplete={f.type === 'password' ? 'new-password' : 'off'} />
              }
            })}
          </div>
          {p.extraForm?.(form, set, errs)}
        </form>
      </Dialog>
      <ConfirmDialog open={!!del} danger title={`Eliminar ${p.noun}`} confirmLabel="Eliminar" busy={remove.isPending}
        message={del ? (p.deleteMessage?.(del) ?? `¿Eliminar este ${p.noun}? Esta acción no se puede deshacer.`) : ''}
        onConfirm={() => del && remove.mutate(del)} onCancel={() => setDel(null)} />
    </div>
  )
}
const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)
