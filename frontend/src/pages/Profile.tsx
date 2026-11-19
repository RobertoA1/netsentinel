import { useState, type FormEvent } from 'react'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthProvider'
import type { UserMe } from '../api/types'
import { Button } from '../ui/Button'
import { TextField, SelectField } from '../ui/Fields'
import { PageHead } from '../ui/State'
import { useToast } from '../ui/Toast'
import { useTheme, type ThemePref } from '../lib/theme'
import { Segmented } from '../ui/Controls'
import { PasswordForm } from './ChangePassword'
import { errMsg } from '../lib/utils'
import { useFmt } from '../lib/format'

const TZ = ['America/Lima', 'America/Bogota', 'America/Guayaquil', 'America/Santiago', 'America/Mexico_City', 'America/Argentina/Buenos_Aires', 'America/New_York', 'Europe/Madrid', 'UTC']
const COLORS = ['#2563eb', '#0d9488', '#7c3aed', '#c2410c', '#be185d', '#475569']

export default function Profile() {
  const { user, setUser } = useAuth()
  const { pref, setPref } = useTheme()
  const toast = useToast()
  const fmt = useFmt()
  const [f, setF] = useState(() => ({
    full_name: user!.full_name, email: user!.email, job_title: user!.profile.job_title, department: user!.profile.department,
    phone: user!.profile.phone, timezone: user!.profile.timezone, avatar_color: user!.profile.avatar_color, theme: user!.profile.theme,
  }))
  const [errs, setErrs] = useState<Record<string, string>>({})
  const [busy, setBusy] = useState(false)
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF((x) => ({ ...x, [k]: e.target.value }))

  async function submit(e: FormEvent) {
    e.preventDefault()
    const er: Record<string, string> = {}
    if (!f.full_name.trim()) er.full_name = 'Ingrese su nombre.'
    if (!/^\S+@\S+\.\S+$/.test(f.email)) er.email = 'Ingrese un correo válido.'
    setErrs(er)
    if (Object.keys(er).length) return
    setBusy(true)
    try {
      const me = await api.put<UserMe>('/auth/me/profile', { ...f, theme: pref })
      setUser(me)
      toast.ok('Perfil actualizado.')
    } catch (x) { toast.err(errMsg(x)) } finally { setBusy(false) }
  }

  return (
    <div className="page">
      <PageHead title="Mi perfil" desc="Sus datos, preferencia de tema y contraseña." />
      <div className="grid">
        <section className="panel span-8" aria-labelledby="p-datos">
          <div className="panel-head"><h2 id="p-datos">Datos personales</h2></div>
          <form className="panel-body stack" onSubmit={submit} noValidate>
            <div className="form-grid">
              <TextField label="Nombre completo" value={f.full_name} onChange={set('full_name')} error={errs.full_name} />
              <TextField label="Correo" type="email" value={f.email} onChange={set('email')} error={errs.email} />
              <TextField label="Cargo" value={f.job_title} onChange={set('job_title')} />
              <TextField label="Área" value={f.department} onChange={set('department')} />
              <TextField label="Teléfono" value={f.phone} onChange={set('phone')} />
              <SelectField label="Zona horaria" value={f.timezone} onChange={set('timezone')} options={(TZ.includes(f.timezone) ? TZ : [f.timezone, ...TZ]).map((t) => ({ value: t, label: t }))} help={`Ahora: ${fmt.dt(new Date().toISOString())}`} />
            </div>
            <div className="field">
              <span className="label">Color de avatar</span>
              <div className="row" role="radiogroup" aria-label="Color de avatar">
                {COLORS.map((c) => (
                  <button key={c} type="button" role="radio" aria-checked={f.avatar_color === c} aria-label={c}
                    onClick={() => setF((x) => ({ ...x, avatar_color: c }))}
                    style={{ width: 28, height: 28, borderRadius: '50%', background: c, border: f.avatar_color === c ? '3px solid var(--ink)' : '2px solid var(--surface)', cursor: 'pointer', boxShadow: '0 0 0 1px var(--line-strong)' }} />
                ))}
              </div>
            </div>
            <div className="field">
              <span className="label">Tema</span>
              <Segmented<ThemePref> label="Tema" value={pref} onChange={setPref} options={[{ value: 'system', label: 'Sistema' }, { value: 'light', label: 'Claro' }, { value: 'dark', label: 'Oscuro' }]} />
            </div>
            <div><Button variant="primary" type="submit" loading={busy}>Guardar cambios</Button></div>
          </form>
        </section>
        <aside className="span-4 stack">
          <section className="panel">
            <div className="panel-head"><h2>Cuenta</h2></div>
            <dl className="panel-body dl">
              <dt>Usuario</dt><dd className="mono">{user!.username}</dd>
              <dt>Rol</dt><dd>{user!.role.name}</dd>
              <dt>Último acceso</dt><dd>{fmt.dt(user!.last_login_at)}</dd>
              <dt>Permisos</dt><dd>{user!.permissions.length}</dd>
            </dl>
          </section>
        </aside>
      </div>
      <section className="panel" style={{ maxWidth: 560 }} aria-labelledby="p-pass">
        <div className="panel-head"><h2 id="p-pass">Cambiar contraseña</h2></div>
        <div className="panel-body"><PasswordForm onDone={() => toast.ok('Contraseña actualizada.')} /></div>
      </section>
    </div>
  )
}
