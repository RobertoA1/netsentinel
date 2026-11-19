import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthProvider'
import { Button } from '../ui/Button'
import { TextField } from '../ui/Fields'
import { Logo } from '../Layout'
import { errMsg } from '../lib/utils'

export function Login() {
  const { user, login } = useAuth()
  const nav = useNavigate()
  const loc = useLocation()
  const [u, setU] = useState('')
  const [p, setP] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const from = (loc.state as { from?: string } | null)?.from || '/'

  if (user) return <Navigate to={user.must_change_password ? '/change-password' : from} replace />

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (!u.trim() || !p) { setErr('Ingrese su usuario y contraseña.'); return }
    setBusy(true); setErr(null)
    try {
      const me = await login(u.trim(), p)
      nav(me.must_change_password ? '/change-password' : from, { replace: true })
    } catch (x) { setErr(errMsg(x)) } finally { setBusy(false) }
  }

  return (
    <div className="login">
      <section className="login-aside">
        <div className="brand" style={{ padding: 0 }}><Logo size={32} /> NetSentinel</div>
        <div>
          <h1>Sepa en segundos si hay algo que atender en su red.</h1>
          <p>Analiza los registros de su firewall e IDS, detecta fugas de datos y comunicaciones sospechosas, y explica cada hallazgo en lenguaje llano. Un modelo de IA local filtra el ruido; sus datos no salen de su infraestructura.</p>
        </div>
        <div className="scale" aria-hidden>
          <div><span className="gauge lg"><i className="on" /><i className="on" /><i className="on" /><i className="on" /><i className="on" /></span> Crítica: actúe ahora</div>
          <div><span className="gauge lg"><i className="on" /><i className="on" /><i className="on" /><i /><i /></span> Media: revise hoy</div>
          <div><span className="gauge lg"><i className="on" /><i /><i /><i /><i /></span> Informativa: para su registro</div>
        </div>
      </section>
      <form className="login-form" onSubmit={submit} noValidate>
        <div>
          <h2 style={{ fontSize: '1.375rem' }}>Iniciar sesión</h2>
          <p className="muted">Use las credenciales que le entregó su administrador.</p>
        </div>
        {err && <div className="banner err" role="alert">{err}</div>}
        <TextField label="Usuario" autoComplete="username" value={u} onChange={(e) => setU(e.target.value)} autoFocus />
        <TextField label="Contraseña" type="password" autoComplete="current-password" value={p} onChange={(e) => setP(e.target.value)} />
        <Button variant="primary" type="submit" loading={busy}>Ingresar</Button>
        <p className="small muted">Tras 5 intentos fallidos la cuenta se bloquea por 15 minutos.</p>
      </form>
    </div>
  )
}
