import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Check, Pencil, Plus, Trash2 } from 'lucide-react'
import { api } from '../api/client'
import { useGet } from '../api/hooks'
import type { PermissionModule, Role } from '../api/types'
import { useCan } from '../auth/AuthProvider'
import { Button } from '../ui/Button'
import { ConfirmDialog, Dialog } from '../ui/Dialog'
import { TextArea, TextField } from '../ui/Fields'
import { DataState, EmptyState, PageHead, SkeletonRows } from '../ui/State'
import { useToast } from '../ui/Toast'
import { ACTION_PERM_LABEL } from '../lib/labels'
import { errMsg } from '../lib/utils'
import { num } from '../lib/format'

const ALL_ACTIONS = ['view', 'create', 'update', 'delete', 'export', 'execute']

function Matrix({ mods, value, onChange, readOnly }: { mods: PermissionModule[]; value: Set<string>; onChange?: (s: Set<string>) => void; readOnly?: boolean }) {
  const toggle = (p: string) => { const n = new Set(value); if (n.has(p)) n.delete(p); else n.add(p); onChange?.(n) }
  const toggleRow = (m: PermissionModule) => {
    const all = m.actions.every((a) => value.has(`${m.code}:${a}`))
    const n = new Set(value)
    m.actions.forEach((a) => (all ? n.delete(`${m.code}:${a}`) : n.add(`${m.code}:${a}`)))
    onChange?.(n)
  }
  const toggleCol = (a: string) => {
    const rows = mods.filter((m) => m.actions.includes(a))
    const all = rows.every((m) => value.has(`${m.code}:${a}`))
    const n = new Set(value)
    rows.forEach((m) => (all ? n.delete(`${m.code}:${a}`) : n.add(`${m.code}:${a}`)))
    onChange?.(n)
  }
  return (
    <div className="table-wrap">
      <table className="t matrix">
        <thead>
          <tr>
            <th>Módulo</th>
            {ALL_ACTIONS.map((a) => (
              <th key={a}>{readOnly ? ACTION_PERM_LABEL[a] : <button type="button" className="btn sm ghost" onClick={() => toggleCol(a)} title={`Alternar "${ACTION_PERM_LABEL[a]}" en todos los módulos`}>{ACTION_PERM_LABEL[a]}</button>}</th>
            ))}
            {!readOnly && <th>Todo</th>}
          </tr>
        </thead>
        <tbody>
          {mods.map((m) => (
            <tr key={m.code}>
              <td className="cell-main">{m.label}</td>
              {ALL_ACTIONS.map((a) => {
                const has = m.actions.includes(a)
                const p = `${m.code}:${a}`
                return (
                  <td key={a}>
                    {!has ? <span className="na" aria-label="No aplica">—</span>
                      : readOnly ? (value.has(p)
                        ? <span style={{ color: 'var(--ok)' }} role="img" aria-label={`${m.label}: ${ACTION_PERM_LABEL[a]}, permitido`}><Check size={17} strokeWidth={2.6} /></span>
                        : <span className="muted" role="img" aria-label={`${m.label}: ${ACTION_PERM_LABEL[a]}, no permitido`}>·</span>)
                      : <input type="checkbox" checked={value.has(p)} disabled={readOnly} onChange={() => toggle(p)} aria-label={`${m.label}: ${ACTION_PERM_LABEL[a]}`} />}
                  </td>
                )
              })}
              {!readOnly && <td><input type="checkbox" checked={m.actions.every((a) => value.has(`${m.code}:${a}`))} onChange={() => toggleRow(m)} aria-label={`${m.label}: todos los permisos`} /></td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function Roles() {
  const can = useCan('roles')
  const qc = useQueryClient()
  const toast = useToast()
  const roles = useGet<Role[]>('/roles')
  const perms = useGet<{ modules: PermissionModule[] }>('/permissions')
  const [sel, setSel] = useState<number | null>(null)
  const [editing, setEditing] = useState<Role | 'new' | null>(null)
  const [del, setDel] = useState<Role | null>(null)

  useEffect(() => { if (sel === null && roles.data?.length) setSel(roles.data[0].id) }, [roles.data, sel])
  const role = roles.data?.find((r) => r.id === sel)
  const mods = perms.data?.modules ?? []

  const remove = useMutation({
    mutationFn: (r: Role) => api.del(`/roles/${r.id}`),
    onSuccess: () => { toast.ok('Rol eliminado.'); setDel(null); setSel(null); void qc.invalidateQueries({ queryKey: ['/roles'] }) },
    onError: (e) => { toast.err(errMsg(e)); setDel(null) },
  })

  return (
    <div className="page">
      <PageHead title="Roles" desc="Un rol agrupa permisos por módulo y acción. Los usuarios heredan los de su rol.">
        {can.create && <Button variant="primary" onClick={() => setEditing('new')}><Plus size={16} /> Nuevo rol</Button>}
      </PageHead>
      <div className="grid">
        <section className="panel span-4" aria-label="Lista de roles">
          <DataState q={roles} skeleton={<SkeletonRows rows={4} />} isEmpty={(d) => d.length === 0} empty={<EmptyState title="Sin roles" />}>
            {(rs) => (
              <ul className="recent" style={{ margin: 0 }}>
                {rs.map((r) => (
                  <li key={r.id}>
                    <a href="#" aria-current={r.id === sel ? 'true' : undefined} onClick={(e) => { e.preventDefault(); setSel(r.id) }}
                      style={{ gridTemplateColumns: '1fr', background: r.id === sel ? 'var(--accent-soft)' : undefined }}>
                      <span className="t">{r.name} {r.is_system && <span className="badge outline">Del sistema</span>}</span>
                      <span className="m" style={{ gridColumn: 1 }}>{num(r.user_count)} {r.user_count === 1 ? 'usuario' : 'usuarios'} · {r.permissions.length} permisos</span>
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </DataState>
        </section>
        <section className="panel span-8" aria-label="Permisos del rol">
          {!role ? <SkeletonRows rows={6} /> : (
            <>
              <div className="panel-head">
                <div><h2>{role.name}</h2><div className="hint">{role.description || 'Sin descripción'}</div></div>
                <div className="row">
                  {can.update && <Button onClick={() => setEditing(role)}><Pencil size={15} /> Editar</Button>}
                  {can.delete && role.name !== 'admin' && !role.is_system && <Button onClick={() => setDel(role)}><Trash2 size={15} /> Eliminar</Button>}
                </div>
              </div>
              <DataState q={perms} skeleton={<SkeletonRows rows={8} />}>
                {() => <Matrix mods={mods} value={new Set(role.permissions)} readOnly />}
              </DataState>
            </>
          )}
        </section>
      </div>
      {editing && <RoleDialog role={editing === 'new' ? null : editing} mods={mods} onClose={() => setEditing(null)} onSaved={(r) => { setEditing(null); setSel(r.id) }} />}
      <ConfirmDialog open={!!del} danger title="Eliminar rol" confirmLabel="Eliminar" busy={remove.isPending}
        message={del ? (del.user_count > 0 ? `El rol "${del.name}" tiene ${del.user_count} usuarios asignados; reasígnelos antes de eliminarlo.` : `¿Eliminar el rol "${del.name}"? Esta acción no se puede deshacer.`) : ''}
        onConfirm={() => del && remove.mutate(del)} onCancel={() => setDel(null)} />
    </div>
  )
}

function RoleDialog({ role, mods, onClose, onSaved }: { role: Role | null; mods: PermissionModule[]; onClose: () => void; onSaved: (r: Role) => void }) {
  const qc = useQueryClient()
  const toast = useToast()
  const [name, setName] = useState(role?.name ?? '')
  const [desc, setDesc] = useState(role?.description ?? '')
  const [perms, setPerms] = useState(() => new Set(role?.permissions ?? []))
  const [err, setErr] = useState<string | null>(null)
  const isAdmin = role?.name === 'admin'
  const count = useMemo(() => perms.size, [perms])

  const save = useMutation({
    mutationFn: () => {
      const b = { name: name.trim(), description: desc.trim(), permissions: [...perms] }
      return role ? api.put<Role>(`/roles/${role.id}`, b) : api.post<Role>('/roles', b)
    },
    onSuccess: (r) => { toast.ok('Rol guardado.'); void qc.invalidateQueries({ queryKey: ['/roles'] }); onSaved(r) },
    onError: (e) => toast.err(errMsg(e)),
  })
  function submit(e: FormEvent) {
    e.preventDefault()
    if (!name.trim()) { setErr('Ingrese un nombre para el rol.'); return }
    if (perms.size === 0) { setErr('Seleccione al menos un permiso.'); return }
    setErr(null); save.mutate()
  }
  return (
    <Dialog open wide onClose={onClose} title={role ? `Editar rol: ${role.name}` : 'Nuevo rol'}
      footer={<><Button onClick={onClose}>Cancelar</Button><Button variant="primary" type="submit" form="role-form" loading={save.isPending}>Guardar</Button></>}>
      <form id="role-form" onSubmit={submit} className="stack" noValidate>
        {isAdmin && <div className="banner warn">El rol admin conserva siempre todos los permisos y no puede eliminarse.</div>}
        <div className="form-grid">
          <TextField label="Nombre" value={name} onChange={(e) => setName(e.target.value)} disabled={!!role?.is_system} error={err && !name.trim() ? err : null} />
          <TextArea label="Descripción" value={desc} onChange={(e) => setDesc(e.target.value)} />
        </div>
        <div>
          <div className="row between" style={{ marginBottom: 6 }}><h3>Permisos</h3><span className="small muted">{count} seleccionados</span></div>
          <Matrix mods={mods} value={perms} onChange={setPerms} readOnly={isAdmin} />
          {err && name.trim() && <p className="err small" role="alert" style={{ color: 'var(--crit-ink)', marginTop: 6 }}>{err}</p>}
        </div>
      </form>
    </Dialog>
  )
}
