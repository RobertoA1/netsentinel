// Adaptador fetch simulado: SOLO desarrollo (VITE_MOCK=1). No entra al build de producción.
import type { AuditSummary, DetectionSettings, FirewallLog, Finding, LlmSettings, ModuleSession, RetentionSettings, UserMe } from '../api/types'
import { mlMock, ML_REPORTS } from './ml'
import { alertRules, alerts, assets, auditEvents, closeSession, findings, lists, logs, MODULE_LIST, NOW, openSession, pushEvent, roles, runs, sessions, sources, users } from './data'

const json = (data: unknown, status = 200) => new Response(status === 204 ? null : JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } })
const err = (status: number, detail: string) => json({ detail }, status)
const wait = (ms: number) => new Promise((r) => setTimeout(r, ms))

const RANGE_H: Record<string, number> = { '1h': 1, '24h': 24, '7d': 168, '30d': 720 }
function inRange<T>(items: T[], ts: (x: T) => string, p: URLSearchParams) {
  let from = 0, to = Infinity
  if (p.get('date_from') || p.get('date_to')) { if (p.get('date_from')) from = Date.parse(p.get('date_from')!); if (p.get('date_to')) to = Date.parse(p.get('date_to')!) }
  else if (p.get('range')) from = NOW - RANGE_H[p.get('range')!] * 3600_000
  return items.filter((x) => { const t = Date.parse(ts(x)); return t >= from && t <= to })
}
function page<T>(items: T[], p: URLSearchParams) {
  const pg = Number(p.get('page') || 1), ps = Number(p.get('page_size') || 25)
  const sort = p.get('sort')
  let arr = items
  if (sort) {
    const k = sort.replace('-', '') as keyof T, dir = sort.startsWith('-') ? -1 : 1
    arr = [...items].sort((a, b) => (a[k] < b[k] ? -1 : a[k] > b[k] ? 1 : 0) * dir)
  }
  return { items: arr.slice((pg - 1) * ps, pg * ps), total: arr.length, page: pg, page_size: ps }
}
const has = (s: string | null | undefined, q: string) => (s ?? '').toLowerCase().includes(q.toLowerCase())

let detection: DetectionSettings = { beacon_min_connections: 10, beacon_max_cv: 0.25, beacon_min_score: 60, exfil_zscore: 3, exfil_min_bytes: 52428800, common_ports: [53, 80, 123, 443, 22, 25, 993], unusual_port_min_connections: 3, internal_cidrs: ['10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16'], detection_window_hours: 24 }
let llm: LlmSettings = { enabled: true, base_url: 'http://ollama:11434', model: 'llama3.2:3b', temperature: 0.1, timeout_seconds: 60, noise_confidence_threshold: 0.7 }
let retention: RetentionSettings = { logs_days: 90, findings_days: 365, audit_days: 730 }
const history: any[] = [{ id: 1, report_code: 'mg_executive_summary', report_name: 'Resumen ejecutivo', format: 'pdf', date_from: new Date(NOW - 30 * 864e5).toISOString(), date_to: new Date(NOW).toISOString(), generated_by: 'Carla Huamán', generated_at: new Date(NOW - 2 * 864e5).toISOString(), size_bytes: 184_320 }]

const CATALOG: { code: string; name: string; description: string; category: string; formats: string[]; params: string[] }[] = [
  ['op_findings', 'Hallazgos del período', 'Lista completa de hallazgos con severidad, estado y evidencia.', 'operational'],
  ['op_top_talkers', 'Top talkers', 'Equipos con más tráfico saliente y sus destinos.', 'operational'],
  ['op_beaconing', 'Beaconing', 'Comunicaciones periódicas detectadas, con intervalos y regularidad.', 'operational'],
  ['op_unusual_ports', 'Puertos inusuales', 'Tráfico por puertos fuera de la línea base.', 'operational'],
  ['op_ids_alerts', 'Alertas IDS', 'Firmas de intrusión detectadas por Suricata.', 'operational'],
  ['op_ingestion', 'Ingesta', 'Ejecuciones de ingesta, volumen y errores de formato.', 'operational'],
  ['op_audit_log', 'Bitácora de auditoría', 'Eventos y sesiones de módulo de los usuarios.', 'operational'],
  ['mg_executive_summary', 'Resumen ejecutivo', 'Estado de seguridad de la red en una página para gerencia.', 'management'],
  ['mg_trends', 'Tendencias', 'Evolución de hallazgos y tráfico frente a períodos anteriores.', 'management'],
  ['mg_response_metrics', 'Métricas de respuesta', 'MTTA, MTTR, tasa de falsos positivos y eficacia del filtro de ruido.', 'management'],
  ['mg_user_activity', 'Actividad de usuarios', 'Uso de módulos por usuario, para control interno.', 'management'],
  ['mg_risk_by_asset', 'Riesgo por activo', 'Activos con más hallazgos ponderados por criticidad.', 'management'],
].map(([code, name, description, category]) => ({ code, name, description, category, formats: category === 'management' ? ['pdf', 'docx'] : ['pdf', 'docx', 'xlsx'], params: [] as string[] }))
CATALOG.push(...(ML_REPORTS as unknown as typeof CATALOG))

function userMe(u: (typeof users)[number]): UserMe {
  const { password: _p, ...rest } = u
  void _p
  return { ...rest, permissions: roles.find((r) => r.id === u.role.id)!.permissions }
}
const me = (h: Headers) => { const m = /mock-access-(\d+)/.exec(h.get('Authorization') ?? ''); return m ? users.find((u) => u.id === +m[1]) ?? null : null }

function dashboardLogs(p: URLSearchParams) { return inRange(logs, (l) => l.ts, p) }
function bucketMs(p: URLSearchParams) { const r = p.get('range') || '24h'; return r === '1h' ? 120_000 : r === '24h' ? 3600_000 : r === '7d' ? 6 * 3600_000 : 86400_000 }

export async function mockFetch(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
  const url = new URL(typeof input === 'string' ? input : input instanceof URL ? input.href : input.url, location.origin)
  const path = url.pathname.replace(/^\/api\/v1/, '')
  const p = url.searchParams
  const method = (init.method ?? 'GET').toUpperCase()
  const headers = new Headers(init.headers)
  let body: any = {}
  if (typeof init.body === 'string') { try { body = JSON.parse(init.body) } catch { /* nada */ } }
  await wait(path.startsWith('/audit/') || path === '/alerts/unread-count' ? 20 : 120 + Math.random() * 120)

  if (path === '/health') return json({ status: 'ok', db: true, llm: true, version: '1.0.0-mock' })
  if (path === '/auth/login') {
    const u = users.find((x) => x.username === body.username)
    if (!u || u.password !== body.password) { pushEvent(null, 'login_failed', `Intento de inicio fallido para "${body.username}"`, null, { username: body.username }); return err(401, 'Usuario o contraseña incorrectos.') }
    if (!u.is_active) return err(403, 'La cuenta está desactivada.')
    u.last_login_at = new Date().toISOString(); pushEvent(u, 'login', `${u.username} inició sesión`)
    return json({ access_token: `mock-access-${u.id}`, refresh_token: `mock-refresh-${u.id}`, token_type: 'bearer', user: userMe(u) })
  }
  if (path === '/auth/refresh') { const m = /mock-refresh-(\d+)/.exec(body.refresh_token ?? ''); return m ? json({ access_token: `mock-access-${m[1]}`, refresh_token: body.refresh_token }) : err(401, 'Sesión expirada.') }

  const user = me(headers)
  if (!user) return err(401, 'No autenticado.')
  const perms = new Set(roles.find((r) => r.id === user.role.id)!.permissions)
  const need = (perm: string) => (perms.has(perm) ? null : err(403, 'No tiene permiso para esta acción.'))
  const mod = path.split('/')[1]
  const MODMAP: Record<string, string> = { dashboard: 'dashboard', logs: 'logs', findings: 'findings', alerts: 'alerts', 'alert-rules': 'alerts', reports: 'reports', assets: 'assets', sources: 'sources', lists: 'lists', ingest: 'ingestion', detect: 'ingestion', ml: '', users: 'users', roles: 'roles', audit: 'audit' }
  const act = method === 'GET' ? 'view' : method === 'DELETE' ? 'delete' : method === 'POST' && ['generate', 'run', 'upload', 'dataset', 'reanalyze', 'test'].some((k) => path.endsWith(k)) ? (path.startsWith('/reports') ? 'export' : 'execute') : method === 'POST' ? (mod === 'findings' || path.includes('/ack') ? 'update' : 'create') : 'update'
  if (!['auth', 'health', 'audit', 'permissions'].includes(mod) && MODMAP[mod] && !(path === '/alerts/unread-count') && !(mod === 'users' && method === 'GET' && perms.has('audit:view')) && !(mod === 'roles' && method === 'GET' && (perms.has('users:view') || perms.has('audit:view')))) {
    const d = need(`${MODMAP[mod]}:${act}`); if (d) return d
  }

  const ml = mlMock(path, method, body, p, user, perms)
  if (ml) return ml

  if (path === '/auth/me') return json(userMe(user))
  if (path === '/auth/logout') {
    sessions.filter((s) => s.user_id === user.id && !s.exited_at).forEach((s) => closeSession(s, 'logout'))
    pushEvent(user, 'logout', `${user.username} cerró sesión`); return json(null, 204)
  }
  if (path === '/auth/me/profile') { const { full_name, email, ...pr } = body; Object.assign(user, { full_name, email }); user.profile = { ...user.profile, ...pr }; return json(userMe(user)) }
  if (path === '/auth/me/password') { if (body.current_password !== user.password) return err(400, 'La contraseña actual no es correcta.'); user.password = body.new_password; user.must_change_password = false; return json(null, 204) }

  // ----- bitácora
  if (path === '/audit/module-enter') {
    sessions.filter((s) => s.user_id === user.id && !s.exited_at).forEach((s) => closeSession(s, 'navigation'))
    const s = openSession(user, body.module); pushEvent(user, 'module_enter', `Entró al módulo ${body.module}`, body.module)
    return json({ session_id: s.id })
  }
  if (path === '/audit/module-exit') {
    const s = sessions.find((x) => x.id === body.session_id)
    if (s && !s.exited_at) { closeSession(s, body.reason ?? 'navigation'); pushEvent(user, 'module_exit', `Salió del módulo ${s.module}`, s.module) }
    return json(null, 204)
  }
  if (mod === 'audit') {
    const d = need('audit:view'); if (d) return d
    if (path === '/audit/events') {
      let it = inRange(auditEvents, (e) => e.ts, p)
      if (p.get('user_id')) it = it.filter((e) => e.user_id === +p.get('user_id')!)
      if (p.get('event_type')) it = it.filter((e) => e.event_type === p.get('event_type'))
      if (p.get('module')) it = it.filter((e) => e.module === p.get('module'))
      if (p.get('q')) it = it.filter((e) => has(e.description, p.get('q')!) || has(e.username, p.get('q')!))
      return json(page(it, p))
    }
    if (path === '/audit/module-sessions') {
      let it: ModuleSession[] = inRange(sessions, (s) => s.entered_at, p)
      if (p.get('user_id')) it = it.filter((e) => e.user_id === +p.get('user_id')!)
      if (p.get('module')) it = it.filter((e) => e.module === p.get('module'))
      return json(page(it, p))
    }
    if (path === '/audit/summary') {
      const ss = inRange(sessions, (s) => s.entered_at, p), ev = inRange(auditEvents, (e) => e.ts, p)
      const by = <K extends string>(arr: any[], key: (x: any) => K) => { const m = new Map<K, any[]>(); arr.forEach((x) => m.set(key(x), [...(m.get(key(x)) ?? []), x])); return m }
      const out: AuditSummary = {
        by_module: [...by(ss, (s) => s.module)].map(([module, a]) => ({ module, visits: a.length, total_seconds: a.reduce((t, s) => t + (s.duration_seconds ?? 0), 0) })).sort((a, b) => b.total_seconds - a.total_seconds),
        by_user: [...by(ss, (s) => s.username)].map(([username, a]) => ({ username, visits: a.length, total_seconds: a.reduce((t, s) => t + (s.duration_seconds ?? 0), 0), last_seen: a[0].entered_at })).sort((a, b) => b.total_seconds - a.total_seconds),
        by_event_type: [...by(ev, (e) => e.event_type)].map(([event_type, a]) => ({ event_type, count: a.length })).sort((a, b) => b.count - a.count),
      }
      return json(out)
    }
  }

  // ----- usuarios, roles
  if (path === '/permissions') return json({ modules: MODULE_LIST })
  if (path === '/users' && method === 'GET') {
    let it = users.map(({ password: _p, ...u }) => { void _p; return u })
    if (p.get('q')) it = it.filter((u) => has(u.full_name, p.get('q')!) || has(u.username, p.get('q')!))
    return json(page(it, p))
  }
  if (path === '/users' && method === 'POST') {
    if (users.some((u) => u.username === body.username)) return err(409, 'Ya existe un usuario con ese nombre.')
    const id = Math.max(...users.map((u) => u.id)) + 1
    users.push({ id, ...body, password: body.password, must_change_password: true, last_login_at: null, role: { id: body.role_id, name: roles.find((r) => r.id === body.role_id)?.name ?? '', description: '' }, profile: { theme: 'system', language: 'es', timezone: 'America/Lima', avatar_color: '#475569', ...(body.profile ?? {}) }, created_at: new Date().toISOString() })
    pushEvent(user, 'create', `Creó el usuario ${body.username}`, 'users'); return json({ id }, 201)
  }
  let m = /^\/users\/(\d+)(\/reset-password)?$/.exec(path)
  if (m) {
    const u = users.find((x) => x.id === +m![1]); if (!u) return err(404, 'Usuario no encontrado.')
    if (m[2]) { u.password = body.new_password; u.must_change_password = true; pushEvent(user, 'update', `Restableció la contraseña de ${u.username}`, 'users'); return json(null, 204) }
    if (method === 'DELETE') { users.splice(users.indexOf(u), 1); return json(null, 204) }
    if (method === 'PUT') { Object.assign(u, body, { role: { id: body.role_id, name: roles.find((r) => r.id === body.role_id)?.name ?? u.role.name, description: '' } }); pushEvent(user, 'update', `Modificó al usuario ${u.username}`, 'users'); return json(u) }
    return json(u)
  }
  if (path === '/roles' && method === 'GET') return json(roles.map((r) => ({ ...r, user_count: users.filter((u) => u.role.id === r.id).length })))
  if (path === '/roles' && method === 'POST') { const r = { id: Math.max(...roles.map((x) => x.id)) + 1, is_system: false, user_count: 0, ...body }; roles.push(r); return json(r, 201) }
  m = /^\/roles\/(\d+)$/.exec(path)
  if (m) {
    const r = roles.find((x) => x.id === +m![1]); if (!r) return err(404, 'Rol no encontrado.')
    if (method === 'DELETE') { if (r.is_system) return err(409, 'Los roles del sistema no se pueden eliminar.'); roles.splice(roles.indexOf(r), 1); return json(null, 204) }
    if (method === 'PUT') { Object.assign(r, body); return json(r) }
    return json(r)
  }

  // ----- dashboard
  if (mod === 'dashboard') {
    const L = dashboardLogs(p)
    const out = L.filter((l) => l.direction === 'outbound')
    if (path === '/dashboard/summary') {
      const F = inRange(findings, (f) => f.last_seen, p)
      const real = F.filter((f) => !f.is_noise)
      const open = real.filter((f) => f.status === 'new' || f.status === 'in_review')
      const noise = F.filter((f) => f.is_noise).length
      return json({ total_logs: L.length, total_bytes_out: L.reduce((s, l) => s + l.bytes_out, 0), total_bytes_in: L.reduce((s, l) => s + l.bytes_in, 0), unique_sources: new Set(L.map((l) => l.src_ip)).size, unique_destinations: new Set(L.map((l) => l.dst_ip)).size,
        blocked_connections: L.filter((l) => l.action === 'block').length, open_findings: open.length, critical_findings: open.filter((f) => f.severity === 'critical').length, noise_filtered: noise, noise_ratio: F.length ? noise / F.length : 0,
        alerts_unacknowledged: alerts.filter((a) => !a.acknowledged_at).length, last_ingest_at: runs[0].started_at,
        deltas: { total_logs: 12.5, unique_destinations: 4.2, blocked_connections: -8.1, open_findings: 25, bytes_out: 310 } })
    }
    if (path === '/dashboard/traffic-timeseries') {
      const b = bucketMs(p), from = NOW - (RANGE_H[p.get('range') || '24h']) * 3600_000, map = new Map<number, any>()
      for (let t = Math.floor(from / b) * b; t <= NOW; t += b) map.set(t, { ts: new Date(t).toISOString(), bytes_out: 0, bytes_in: 0, connections: 0, blocked: 0 })
      L.forEach((l) => { const k = Math.floor(Date.parse(l.ts) / b) * b; const r = map.get(k); if (r) { r.bytes_out += l.bytes_out; r.bytes_in += l.bytes_in; r.connections++; if (l.action === 'block') r.blocked++ } })
      return json([...map.values()])
    }
    if (path === '/dashboard/top-talkers') {
      const g = new Map<string, FirewallLog[]>(); out.forEach((l) => g.set(l.src_ip, [...(g.get(l.src_ip) ?? []), l]))
      const metric = p.get('metric') || 'bytes'
      const rows = [...g].map(([ip, a]) => ({ ip, hostname: assets.find((x) => x.ip === ip)?.hostname ?? null, bytes_out: a.reduce((s, l) => s + l.bytes_out, 0), bytes_in: a.reduce((s, l) => s + l.bytes_in, 0), connections: a.length, unique_destinations: new Set(a.map((l) => l.dst_ip)).size, findings: findings.filter((f) => f.src_ip === ip && !f.is_noise && f.status !== 'closed').length }))
      const key = metric === 'bytes' ? 'bytes_out' : metric === 'connections' ? 'connections' : 'unique_destinations'
      return json(rows.sort((a, b) => (b as any)[key] - (a as any)[key]).slice(0, Number(p.get('limit') || 10)))
    }
    if (path === '/dashboard/top-destinations') {
      const g = new Map<string, FirewallLog[]>(); out.forEach((l) => g.set(l.dst_ip, [...(g.get(l.dst_ip) ?? []), l]))
      return json([...g].map(([ip, a]) => ({ ip, bytes: a.reduce((s, l) => s + l.bytes_out, 0), connections: a.length, unique_sources: new Set(a.map((l) => l.src_ip)).size, in_denylist: lists.some((e) => e.list_type === 'deny' && e.kind === 'ip' && e.value === ip) })).sort((a, b) => b.bytes - a.bytes).slice(0, Number(p.get('limit') || 10)))
    }
    if (path === '/dashboard/top-ports') {
      const g = new Map<string, FirewallLog[]>(); L.filter((l) => l.dst_port && l.direction !== 'inbound').forEach((l) => g.set(`${l.dst_port}/${l.proto}`, [...(g.get(`${l.dst_port}/${l.proto}`) ?? []), l]))
      const svc: Record<number, string> = { 443: 'https', 80: 'http', 53: 'dns', 22: 'ssh' }
      return json([...g].map(([k, a]) => { const port = +k.split('/')[0]; return { port, proto: k.split('/')[1], service: svc[port] ?? null, connections: a.length, bytes: a.reduce((s, l) => s + l.bytes_out, 0), unusual: ![443, 80, 53, 22, 123].includes(port) } }).sort((a, b) => b.connections - a.connections).slice(0, Number(p.get('limit') || 10)))
    }
    const F = inRange(findings, (f) => f.last_seen, p)
    if (path === '/dashboard/findings-by-severity') return json(['critical', 'high', 'medium', 'low', 'info'].map((s) => ({ severity: s, count: F.filter((f) => !f.is_noise && f.severity === s).length })))
    if (path === '/dashboard/findings-by-type') return json(['beaconing', 'exfiltration', 'unusual_port', 'ids_alert', 'talker_anomaly'].map((t) => ({ finding_type: t, count: F.filter((f) => !f.is_noise && f.finding_type === t).length, noise: F.filter((f) => f.is_noise && f.finding_type === t).length })))
    if (path === '/dashboard/findings-timeseries') {
      const b = bucketMs(p) * (p.get('range') === '1h' ? 5 : 1), from = NOW - RANGE_H[p.get('range') || '24h'] * 3600_000, map = new Map<number, any>()
      for (let t = Math.floor(from / b) * b; t <= NOW; t += b) map.set(t, { ts: new Date(t).toISOString(), real: 0, noise: 0 })
      F.forEach((f) => { const r = map.get(Math.floor(Date.parse(f.last_seen) / b) * b); if (r) if (f.is_noise) r.noise++; else r.real++ })
      return json([...map.values()])
    }
    if (path === '/dashboard/flows') {
      const g = new Map<string, any>(); out.forEach((l) => { const k = `${l.src_ip}|${l.dst_ip}|${l.dst_port}`; const r = g.get(k) ?? { src_ip: l.src_ip, dst_ip: l.dst_ip, dst_port: l.dst_port, bytes: 0, connections: 0 }; r.bytes += l.bytes_out; r.connections++; g.set(k, r) })
      return json([...g.values()].sort((a, b) => b.bytes - a.bytes).slice(0, Number(p.get('limit') || 30)))
    }
    if (path === '/dashboard/recent-findings') return json(F.filter((f) => !f.is_noise).sort((a, b) => (a.last_seen < b.last_seen ? 1 : -1)).slice(0, Number(p.get('limit') || 8)).map(({ comments: _c, ...f }) => { void _c; return f }))
  }

  // ----- logs
  if (path === '/logs' && method === 'GET') {
    let it = inRange(logs, (l) => l.ts, p)
    for (const k of ['src_ip', 'dst_ip', 'proto', 'action', 'log_type', 'direction'] as const) if (p.get(k)) it = it.filter((l) => l[k] === p.get(k))
    if (p.get('dst_port')) it = it.filter((l) => String(l.dst_port) === p.get('dst_port'))
    if (p.get('source_id')) it = it.filter((l) => String(l.source_id) === p.get('source_id'))
    if (p.get('q')) it = it.filter((l) => has(l.src_ip + l.dst_ip + (l.signature ?? '') + (l.category ?? ''), p.get('q')!))
    return json(page(it, p))
  }
  m = /^\/logs\/(\d+)$/.exec(path); if (m) { const l = logs.find((x) => x.id === +m![1]); return l ? json(l) : err(404, 'Registro no encontrado.') }

  // ----- hallazgos
  if (path === '/findings' && method === 'GET') {
    let it: Finding[] = inRange(findings, (f) => f.last_seen, p)
    if (p.get('is_noise') === 'false') it = it.filter((f) => !f.is_noise)
    for (const k of ['finding_type', 'severity', 'status', 'src_ip', 'dst_ip'] as const) if (p.get(k)) it = it.filter((f) => f[k] === p.get(k))
    if (p.get('q')) it = it.filter((f) => has(f.title + f.src_ip + (f.dst_ip ?? ''), p.get('q')!))
    return json(page(it.map(({ comments: _c, ...f }) => { void _c; return f as Finding }), p))
  }
  m = /^\/findings\/(\d+)(\/[a-z-]+)?$/.exec(path)
  if (m) {
    const f = findings.find((x) => x.id === +m![1]); if (!f) return err(404, 'Hallazgo no encontrado.')
    if (m[2] === '/related-logs') {
      const it = logs.filter((l) => l.src_ip === f.src_ip && (!f.dst_ip || l.dst_ip === f.dst_ip) && (!f.dst_port || l.dst_port === f.dst_port)).reverse()
      return json(page(it, p))
    }
    if (m[2] === '/comments') { f.comments = [...(f.comments ?? []), { id: Date.now(), author: user.full_name, body: body.body, created_at: new Date().toISOString() }]; return json(f) }
    if (m[2] === '/reanalyze') { await wait(900); f.llm_model = 'llama3.2:3b'; return json(f) }
    if (method === 'PATCH') {
      if ('assigned_to_id' in body) f.assigned_to = body.assigned_to_id ? { id: body.assigned_to_id, full_name: users.find((u) => u.id === body.assigned_to_id)?.full_name ?? '' } : null
      for (const k of ['status', 'severity', 'is_noise'] as const) if (k in body) (f as any)[k] = body[k]
      pushEvent(user, 'update', `Actualizó el hallazgo #${f.id}`, 'findings', { entity: 'finding', entity_id: f.id }); return json(f)
    }
    return json(f)
  }

  // ----- alertas
  if (path === '/alerts/unread-count') return json({ count: alerts.filter((a) => !a.acknowledged_at).length })
  if (path === '/alerts' && method === 'GET') {
    let it = inRange(alerts, (a) => a.created_at, p)
    if (p.get('acknowledged')) it = it.filter((a) => !!a.acknowledged_at === (p.get('acknowledged') === 'true'))
    if (p.get('severity')) it = it.filter((a) => a.severity === p.get('severity'))
    return json(page(it, p))
  }
  if (path === '/alerts/ack-all') { let n = 0; alerts.forEach((a) => { if (!a.acknowledged_at) { a.acknowledged_at = new Date().toISOString(); a.acknowledged_by = user.full_name; n++ } }); return json({ acknowledged: n }) }
  m = /^\/alerts\/(\d+)\/ack$/.exec(path); if (m) { const a = alerts.find((x) => x.id === +m![1]); if (!a) return err(404, 'Alerta no encontrada.'); a.acknowledged_at = new Date().toISOString(); a.acknowledged_by = user.full_name; return json(a) }
  if (path === '/alert-rules') { if (method === 'POST') { const r = { id: Date.now(), ...body }; alertRules.push(r); return json(r, 201) } return json(alertRules) }
  m = /^\/alert-rules\/(\d+)$/.exec(path); if (m) { const i = alertRules.findIndex((x) => x.id === +m![1]); if (i < 0) return err(404, 'Regla no encontrada.'); if (method === 'DELETE') { alertRules.splice(i, 1); return json(null, 204) } if (method === 'PUT') Object.assign(alertRules[i], body); return json(alertRules[i]) }

  // ----- catálogos genéricos
  const crud = (store: any[], base: string, key: string) => {
    if (path === base && method === 'POST') { const r = { id: Date.now(), ...body }; store.push(r); pushEvent(user, 'create', `Creó ${key}`, mod); return json(r, 201) }
    const mm = new RegExp(`^${base}/(\\d+)$`).exec(path)
    if (mm) { const i = store.findIndex((x) => x.id === +mm[1]); if (i < 0) return err(404, 'No encontrado.'); if (method === 'DELETE') { store.splice(i, 1); pushEvent(user, 'delete', `Eliminó ${key}`, mod); return json(null, 204) } if (method === 'PUT') Object.assign(store[i], body); return json(store[i]) }
    return null
  }
  if (path === '/sources' && method === 'GET') return json(sources)
  { const r = crud(sources, '/sources', 'una fuente'); if (r) return r }
  if (path === '/assets' && method === 'GET') { let it = assets; if (p.get('q')) it = it.filter((a) => has(a.ip + a.hostname + a.owner, p.get('q')!)); return json(page(it, p)) }
  { const r = crud(assets, '/assets', 'un activo'); if (r) return r }
  if (path === '/lists' && method === 'GET') { let it = lists; if (p.get('list_type')) it = it.filter((e) => e.list_type === p.get('list_type')); if (p.get('q')) it = it.filter((e) => has(e.value + e.note, p.get('q')!)); return json(page(it, p)) }
  if (path === '/lists' && method === 'POST') { const r = { id: Date.now(), created_at: new Date().toISOString(), ...body }; lists.push(r); return json(r, 201) }
  m = /^\/lists\/(\d+)$/.exec(path); if (m && method === 'DELETE') { const i = lists.findIndex((x) => x.id === +m![1]); if (i >= 0) lists.splice(i, 1); return json(null, 204) }

  // ----- ingesta
  if (path === '/ingest/status') return json({ last_run: runs[0], dataset_available: true, dataset_loaded: runs.some((r) => r.trigger === 'dataset'), pending_files: 2 })
  if (path === '/ingest/runs') return json(page(runs, p))
  if (path.startsWith('/ingest/') && method === 'POST' || path === '/detect/run') {
    await wait(1200)
    if (path === '/detect/run') return json({ findings_created: 2, findings_updated: 5, findings_noise: 4, duration_ms: 1840 })
    const r = { id: runs.length + 1, started_at: new Date().toISOString(), finished_at: new Date(Date.now() + 1200).toISOString(), status: 'success' as const, trigger: path.endsWith('upload') ? 'upload' as const : path.endsWith('dataset') ? 'dataset' as const : 'manual' as const, source_id: 1, source_name: 'OPNsense LAN', filename: path.endsWith('upload') ? 'filter.log' : null, lines_read: 5000, logs_inserted: 4980, parse_errors: 20, findings_created: 1, findings_noise: 2, error: null }
    runs.unshift(r); pushEvent(user, 'execute', 'Ejecutó una ingesta', 'ingestion'); return json(r)
  }

  // ----- configuración
  if (path === '/settings/detection') { if (method === 'PUT') detection = body; return json(detection) }
  if (path === '/settings/llm/test') { await wait(900); return json({ ok: true, model: llm.model, latency_ms: 1420, message: 'El modelo respondió correctamente.' }) }
  if (path === '/settings/llm') { if (method === 'PUT') llm = body; return json(llm) }
  if (path === '/settings/retention') { if (method === 'PUT') retention = body; return json(retention) }

  // ----- reportes
  if (path === '/reports/catalog') return json(CATALOG)
  if (path === '/reports/history') return json(page(history, p))
  if (path === '/reports/generate') {
    const c = CATALOG.find((x) => x.code === body.report_code); const name = `${body.report_code}_${body.date_from.slice(0, 10)}_${body.date_to.slice(0, 10)}.${body.format}`
    history.unshift({ id: history.length + 1, report_code: body.report_code, report_name: c?.name ?? body.report_code, format: body.format, date_from: body.date_from, date_to: body.date_to, generated_by: user.full_name, generated_at: new Date().toISOString(), size_bytes: 52_000 })
    pushEvent(user, 'export', `Generó el reporte ${c?.name} (${body.format})`, 'reports')
    return new Response(new Blob(['Reporte simulado (modo mock)']), { status: 200, headers: { 'Content-Type': 'application/octet-stream', 'Content-Disposition': `attachment; filename="${name}"` } })
  }
  return err(404, `Ruta simulada no implementada: ${method} ${path}`)
}
