import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthProvider'
import { Button } from '../ui/Button'
import { TextField } from '../ui/Fields'
import { errMsg } from '../lib/utils'
import { Logo } from '../Layout'

export function validatePassword(p: string): string | null {
  if (p.length < 8) return 'Use al menos 8 caracteres.'
  if (!/[A-Za-z]/.test(p) || !/\d/.test(p)) return 'Combine letras y números.'
  return null
}

export function PasswordForm({ onDone, forced }: { onDone: () => void; forced?: boolean }) {
  const [cur, setCur] = useState('')
  const [n1, setN1] = useState('')
  const [n2, setN2] = useState('')
  const [errs, setErrs] = useState<{ cur?: string; n1?: string; n2?: string; form?: string }>({})
  const [busy, setBusy] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    const er: typeof errs = {}
    if (!cur) er.cur = 'Ingrese su contraseña actual.'
    const v = validatePassword(n1)
    if (v) er.n1 = v
    else if (n1 === cur) er.n1 = 'La nueva contraseña debe ser distinta de la actual.'
    if (n2 !== n1) er.n2 = 'Las contraseñas no coinciden.'
    setErrs(er)
    if (Object.keys(er).length) return
    setBusy(true)
    try {
      await api.post('/auth/me/password', { current_password: cur, new_password: n1 })
      onDone()
      if (!forced) { setCur(''); setN1(''); setN2('') }
    } catch (x) { setErrs({ form: errMsg(x) }) } finally { setBusy(false) }
  }
  return (
    <form onSubmit={submit} className="stack" noValidate style={{ maxWidth: 420 }}>
      {forced && <div className="banner warn">Por seguridad debe definir una contraseña nueva antes de continuar.</div>}
      {errs.form && <div className="banner err" role="alert">{errs.form}</div>}
      <TextField label="Contraseña actual" type="password" autoComplete="current-password" value={cur} onChange={(e) => setCur(e.target.value)} error={errs.cur} />
      <TextField label="Contraseña nueva" type="password" autoComplete="new-password" value={n1} onChange={(e) => setN1(e.target.value)} error={errs.n1} help="Mínimo 8 caracteres, con letras y números." />
      <TextField label="Repita la contraseña nueva" type="password" autoComplete="new-password" value={n2} onChange={(e) => setN2(e.target.value)} error={errs.n2} />
      <div><Button variant="primary" type="submit" loading={busy}>Cambiar contraseña</Button></div>
    </form>
  )
}

export function ChangePassword() {
  const { reload, logout } = useAuth()
  const nav = useNavigate()
  return (
    <div className="page" style={{ maxWidth: 560, paddingTop: 64 }}>
      <div className="brand" style={{ padding: 0, marginBottom: 20, color: 'var(--ink)' }}><Logo /> NetSentinel</div>
      <h1 style={{ marginBottom: 16 }}>Cambiar contraseña</h1>
      <PasswordForm forced onDone={async () => { await reload(); nav('/', { replace: true }) }} />
      <p style={{ marginTop: 24 }}><Button variant="ghost" onClick={() => void logout()}>Cerrar sesión</Button></p>
    </div>
  )
}
