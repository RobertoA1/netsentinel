import { useState, type FormEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { KeyRound, Power } from 'lucide-react'
import { api } from '../api/client'
import { useGet } from '../api/hooks'
import type { Role, User } from '../api/types'
import { useAuth, useCan } from '../auth/AuthProvider'
import { CrudPage } from '../ui/CrudPage'
import { Button } from '../ui/Button'
import { Dialog } from '../ui/Dialog'
import { TextField } from '../ui/Fields'
import { useToast } from '../ui/Toast'
import { validatePassword } from './ChangePassword'
import { useFmt } from '../lib/format'
import { errMsg, initials } from '../lib/utils'

export default function Users() {
  const roles = useGet<Role[]>('/roles', undefined, { retry: false })
  const can = useCan('users')
  const { user: me } = useAuth()
  const fmt = useFmt()
  const toast = useToast()
  const qc = useQueryClient()
  const [reset, setReset] = useState<User | null>(null)
  const [pw, setPw] = useState('')
  const [pwErr, setPwErr] = useState<string | null>(null)

  const toggle = useMutation({
    mutationFn: (u: User) => api.put(`/users/${u.id}`, { username: u.username, email: u.email, full_name: u.full_name, role_id: u.role.id, is_active: !u.is_active, profile: u.profile }),
    onSuccess: (_d, u) => { toast.ok(u.is_active ? 'Usuario desactivado.' : 'Usuario activado.'); void qc.invalidateQueries({ queryKey: ['/users'] }) },
    onError: (e) => toast.err(errMsg(e)),
  })
  const doReset = useMutation({
    mutationFn: (u: User) => api.post(`/users/${u.id}/reset-password`, { new_password: pw }),
    onSuccess: () => { toast.ok('Contraseña restablecida. El usuario deberá cambiarla al ingresar.'); setReset(null); setPw('') },
    onError: (e) => setPwErr(errMsg(e)),
  })
  function submitReset(e: FormEvent) {
    e.preventDefault()
    const m = validatePassword(pw)
    setPwErr(m)
    if (!m && reset) doReset.mutate(reset)
  }

  const roleOpts = (roles.data ?? []).map((r) => ({ value: r.id, label: r.name }))

  return (
    <>
      <CrudPage<User>
        module="users" path="/users" paginated searchable noun="usuario" title="Usuarios"
        desc="Personas con acceso a NetSentinel. El rol define qué módulos ven y qué pueden hacer."
        blank={{ username: '', full_name: '', email: '', password: '', role_id: roleOpts[0]?.value ?? '', is_active: true, job_title: '', department: '', phone: '' }}
        toForm={(u) => ({ username: u.username, full_name: u.full_name, email: u.email, role_id: u.role.id, is_active: u.is_active, job_title: u.profile?.job_title ?? '', department: u.profile?.department ?? '', phone: u.profile?.phone ?? '' })}
        toBody={(f, editing) => {
          const { job_title, department, phone, role_id, password, ...rest } = f
          const body: Record<string, unknown> = { ...rest, role_id: Number(role_id), profile: { ...(editing?.profile ?? {}), job_title, department, phone } }
          if (!editing) body.password = password
          return body
        }}
        canDelete={(u) => u.id !== me?.id}
        deleteMessage={(u) => `¿Eliminar a ${u.full_name} (${u.username})? Su historial en la bitácora se conserva.`}
        columns={[
          { header: 'Usuario', cell: (u) => (
            <span className="row" style={{ flexWrap: 'nowrap' }}>
              <span className="avatar" style={{ background: u.profile?.avatar_color || 'var(--accent)' }}>{initials(u.full_name)}</span>
              <span><span className="cell-main">{u.full_name}</span><br /><span className="small muted mono">{u.username}</span></span>
            </span>) },
          { header: 'Correo', cell: (u) => u.email },
          { header: 'Rol', cell: (u) => <span className="badge accent">{u.role.name}</span> },
          { header: 'Estado', cell: (u) => <span className={`badge ${u.is_active ? 'ok' : ''}`}>{u.is_active ? 'Activo' : 'Inactivo'}</span> },
          { header: 'Último acceso', cell: (u) => fmt.dt(u.last_login_at) },
        ]}
        fields={[
          { key: 'full_name', label: 'Nombre completo', required: true },
          { key: 'username', label: 'Usuario', required: true, mono: true, validate: (v) => (/^[a-zA-Z0-9._-]{3,}$/.test(v) ? null : 'Mínimo 3 caracteres: letras, números, punto o guion.') },
          { key: 'email', label: 'Correo', type: 'email', required: true, validate: (v) => (/^\S+@\S+\.\S+$/.test(v) ? null : 'Ingrese un correo válido.') },
          { key: 'role_id', label: 'Rol', type: 'select', required: true, options: roleOpts },
          { key: 'password', label: 'Contraseña inicial', type: 'password', required: true, onlyOnCreate: true, help: 'Mínimo 8 caracteres, con letras y números. Deberá cambiarla al ingresar.', validate: (v) => validatePassword(v) },
          { key: 'job_title', label: 'Cargo' },
          { key: 'department', label: 'Área' },
          { key: 'phone', label: 'Teléfono' },
          { key: 'is_active', label: 'Usuario activo', type: 'switch', full: true },
        ]}
        rowActions={(u) => can.update && (
          <>
            <Button size="sm" variant="ghost" icon onClick={() => { setReset(u); setPw(''); setPwErr(null) }} aria-label={`Restablecer contraseña de ${u.username}`} title="Restablecer contraseña"><KeyRound size={15} /></Button>
            {u.id !== me?.id && <Button size="sm" variant="ghost" icon onClick={() => toggle.mutate(u)} aria-label={u.is_active ? `Desactivar a ${u.username}` : `Activar a ${u.username}`} title={u.is_active ? 'Desactivar' : 'Activar'}><Power size={15} /></Button>}
          </>
        )}
      />
      <Dialog open={!!reset} onClose={() => setReset(null)} title="Restablecer contraseña"
        footer={<><Button onClick={() => setReset(null)}>Cancelar</Button><Button variant="primary" type="submit" form="reset-form" loading={doReset.isPending}>Restablecer</Button></>}>
        <form id="reset-form" onSubmit={submitReset} noValidate className="stack">
          <p>Defina una contraseña temporal para <b>{reset?.full_name}</b>. Se le pedirá cambiarla al próximo ingreso.</p>
          <TextField label="Contraseña temporal" type="text" autoComplete="off" value={pw} onChange={(e) => setPw(e.target.value)} error={pwErr} help="Mínimo 8 caracteres, con letras y números." />
        </form>
      </Dialog>
    </>
  )
}
