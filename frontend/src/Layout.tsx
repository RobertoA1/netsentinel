import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import {
  Bell, ClipboardList, Cpu, FileBarChart, KeyRound, LayoutDashboard, ListChecks, LogOut, Menu,
  Monitor, Moon, PlugZap, Database, Dumbbell, Scale, Lightbulb, Wand2, FlaskConical, ScrollText, ShieldAlert, SlidersHorizontal, Sun, Upload, UserRound, Users, Laptop,
} from 'lucide-react'
import { useAuth } from './auth/AuthProvider'
import { useGet } from './api/hooks'
import { useTheme } from './lib/theme'
import { Button } from './ui/Button'
import { MODULES } from './lib/labels'
import type { Health } from './api/types'
import { initials } from './lib/utils'

const NAV: { title: string; items: { module: string; icon: typeof Bell }[] }[] = [
  { title: 'Monitoreo', items: [
    { module: 'dashboard', icon: LayoutDashboard }, { module: 'findings', icon: ShieldAlert },
    { module: 'alerts', icon: Bell }, { module: 'logs', icon: ScrollText },
  ] },
  { title: 'Datos', items: [
    { module: 'ingestion', icon: Upload }, { module: 'assets', icon: Laptop },
    { module: 'sources', icon: PlugZap }, { module: 'lists', icon: ListChecks },
  ] },
  { title: 'Análisis y reportes', items: [{ module: 'reports', icon: FileBarChart }] },
  { title: 'Laboratorio ML', items: [
    { module: 'ml_data', icon: Database }, { module: 'ml_training', icon: Dumbbell }, { module: 'ml_evaluation', icon: Scale },
    { module: 'ml_explain', icon: Lightbulb }, { module: 'ml_inference', icon: Wand2 }, { module: 'ml_optuna', icon: FlaskConical },
  ] },
  { title: 'Configuración', items: [{ module: 'detection', icon: SlidersHorizontal }, { module: 'llm', icon: Cpu }] },
  { title: 'Administración', items: [
    { module: 'users', icon: Users }, { module: 'roles', icon: KeyRound }, { module: 'audit', icon: ClipboardList },
  ] },
]

export function Logo({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden>
      <rect width="32" height="32" rx="7" fill="oklch(0.95 0.008 250)" />
      <path d="M5 20h4l3-9 4 14 3-10 2 5h6" fill="none" stroke="oklch(0.27 0.055 252)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function Layout() {
  const { user, can, logout } = useAuth()
  const { pref, setPref } = useTheme()
  const [open, setOpen] = useState(false)
  const [menu, setMenu] = useState(false)
  const loc = useLocation()

  useEffect(() => { setOpen(false); setMenu(false) }, [loc.pathname])
  useEffect(() => {
    const k = (e: KeyboardEvent) => { if (e.key === 'Escape') { setOpen(false); setMenu(false) } }
    window.addEventListener('keydown', k)
    return () => window.removeEventListener('keydown', k)
  }, [])

  useEffect(() => {
    if (!menu) return
    const h = (e: MouseEvent) => { if (!(e.target as HTMLElement).closest('.menu')) setMenu(false) }
    document.addEventListener('mousedown', h)
    return () => document.removeEventListener('mousedown', h)
  }, [menu])

  const unread = useGet<{ count: number }>('/alerts/unread-count', undefined, {
    enabled: can('alerts:view'), refetchInterval: 30_000, retry: false,
  })
  const health = useGet<Health>('/health', undefined, { refetchInterval: 60_000, retry: false })
  const count = unread.data?.count ?? 0

  const ThemeIcon = pref === 'dark' ? Moon : pref === 'light' ? Sun : Monitor
  const nextTheme = pref === 'system' ? 'light' : pref === 'light' ? 'dark' : 'system'
  const themeName = { system: 'del sistema', light: 'claro', dark: 'oscuro' }

  return (
    <div className="app">
      <a href="#main" className="sr-only" onFocus={(e) => e.currentTarget.classList.remove('sr-only')} onBlur={(e) => e.currentTarget.classList.add('sr-only')}>Saltar al contenido</a>
      <aside className={`sidebar${open ? ' open' : ''}`} aria-label="Navegación principal">
        <div className="brand">
          <Logo />
          <div>NetSentinel<small>Análisis de logs de red</small></div>
        </div>
        <nav>
          {NAV.map((g) => {
            const items = g.items.filter((i) => can(`${i.module}:view`))
            if (!items.length) return null
            return (
              <div className="nav-group" key={g.title}>
                <div className="nav-title">{g.title}</div>
                {items.map((i) => {
                  const Icon = i.icon
                  return (
                    <NavLink key={i.module} to={MODULES[i.module].path} className="nav-link">
                      <Icon size={17} aria-hidden />
                      {MODULES[i.module].label}
                      {i.module === 'alerts' && count > 0 && <span className="pill" aria-label={`${count} sin acusar`}>{count > 99 ? '99+' : count}</span>}
                    </NavLink>
                  )
                })}
              </div>
            )
          })}
        </nav>
        <div className="sidebar-foot">
          <div className="row" style={{ gap: 6 }}>
            <span className={`dot ${health.data ? (health.data.llm ? 'ok' : 'warn') : health.isError ? 'bad' : ''}`} />
            {health.isError ? 'Servidor sin respuesta' : health.data ? (health.data.llm ? 'Motor IA activo' : 'Motor IA sin respuesta') : 'Comprobando…'}
          </div>
          {health.data && <div style={{ marginTop: 2 }}>v{health.data.version}</div>}
        </div>
      </aside>
      <div className={`scrim${open ? ' show' : ''}`} onClick={() => setOpen(false)} aria-hidden />

      <div className="main">
        <header className="topbar">
          <Button variant="ghost" icon className="menu-btn" onClick={() => setOpen(true)} aria-label="Abrir navegación"><Menu size={20} /></Button>
          <div className="spacer" />
          {can('alerts:view') && (
            <Link to="/alerts" className="btn ghost icon bell" aria-label={count > 0 ? `Alertas: ${count} sin acusar` : 'Alertas'}>
              <Bell size={18} />
              {count > 0 && <span className="pill">{count > 99 ? '99+' : count}</span>}
            </Link>
          )}
          <Button variant="ghost" icon onClick={() => setPref(nextTheme)} aria-label={`Tema ${themeName[pref]}. Cambiar a ${themeName[nextTheme]}`} title={`Tema: ${themeName[pref]}`}><ThemeIcon size={18} /></Button>
          <div className="menu">
            <Button variant="ghost" onClick={() => setMenu((m) => !m)} aria-expanded={menu} aria-haspopup="menu">
              <span className="avatar" style={{ background: user?.profile.avatar_color || 'var(--accent)' }}>{initials(user?.full_name || user?.username || '?')}</span>
              <span className="small" style={{ fontWeight: 600 }}>{user?.full_name || user?.username}</span>
            </Button>
            {menu && (
              <div className="menu-pop" role="menu">
                <div className="who">
                  <div style={{ fontWeight: 600 }}>{user?.full_name}</div>
                  <div className="small muted">{user?.email}</div>
                  <div className="small muted">Rol: {user?.role.name}</div>
                </div>
                <hr />
                <Link to="/profile" role="menuitem"><UserRound size={16} /> Mi perfil</Link>
                <button role="menuitem" onClick={() => void logout()}><LogOut size={16} /> Cerrar sesión</button>
              </div>
            )}
          </div>
        </header>
        <main id="main" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}


