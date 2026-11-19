// Datos sintéticos SOLO para desarrollo (VITE_MOCK=1). Conformes a docs/API_CONTRACT.md.
import type { Alert, AlertRule, Asset, AuditEvent, Finding, FirewallLog, IngestRun, ListEntry, ModuleSession, Role, Source, User } from '../api/types'

let seed = 20261111
export const rnd = () => { seed = (seed * 1664525 + 1013904223) % 4294967296; return seed / 4294967296 }
const pick = <T,>(a: T[]) => a[Math.floor(rnd() * a.length)]
const ri = (a: number, b: number) => Math.floor(a + rnd() * (b - a + 1))
export const NOW = Date.now()
const H = 3600_000
const iso = (t: number) => new Date(t).toISOString()

export const MODULE_LIST = [
  { code: 'dashboard', label: 'Panel', actions: ['view'] },
  { code: 'logs', label: 'Registros', actions: ['view', 'export'] },
  { code: 'findings', label: 'Hallazgos', actions: ['view', 'update', 'execute', 'export'] },
  { code: 'alerts', label: 'Alertas', actions: ['view', 'create', 'update', 'delete'] },
  { code: 'reports', label: 'Reportes', actions: ['view', 'export'] },
  { code: 'assets', label: 'Activos', actions: ['view', 'create', 'update', 'delete'] },
  { code: 'sources', label: 'Fuentes', actions: ['view', 'create', 'update', 'delete'] },
  { code: 'lists', label: 'Listas', actions: ['view', 'create', 'delete'] },
  { code: 'ingestion', label: 'Ingesta', actions: ['view', 'execute'] },
  { code: 'detection', label: 'Detección', actions: ['view', 'update'] },
  { code: 'llm', label: 'Motor IA', actions: ['view', 'update', 'execute'] },
  { code: 'users', label: 'Usuarios', actions: ['view', 'create', 'update', 'delete'] },
  { code: 'roles', label: 'Roles', actions: ['view', 'create', 'update', 'delete'] },
  { code: 'audit', label: 'Bitácora', actions: ['view', 'export'] },
  { code: 'ml_data', label: 'ML · Datos', actions: ['view', 'create', 'update', 'delete', 'export'] },
  { code: 'ml_training', label: 'ML · Entrenamiento', actions: ['view', 'create', 'update', 'delete', 'execute'] },
  { code: 'ml_evaluation', label: 'ML · Evaluación', actions: ['view', 'update', 'export'] },
  { code: 'ml_explain', label: 'ML · Explicabilidad', actions: ['view', 'execute', 'export'] },
  { code: 'ml_inference', label: 'ML · Inferencia', actions: ['view', 'execute', 'update', 'export'] },
  { code: 'ml_optuna', label: 'ML · Optuna', actions: ['view', 'create', 'execute', 'delete'] },
]
const allPerms = MODULE_LIST.flatMap((m) => m.actions.map((a) => `${m.code}:${a}`))
const only = (mods: string[], acts?: string[]) => allPerms.filter((p) => { const [m, a] = p.split(':'); return mods.includes(m) && (!acts || acts.includes(a)) })

export const roles: Role[] = [
  { id: 1, name: 'admin', description: 'Acceso total al sistema', is_system: true, permissions: allPerms, user_count: 1 },
  { id: 2, name: 'analyst', description: 'Opera hallazgos, alertas e ingesta', is_system: true, user_count: 1,
    permissions: [...only(['dashboard', 'logs', 'findings', 'alerts', 'assets', 'sources', 'lists', 'ingestion', 'reports']), ...only(['findings'], ['update', 'execute']), 'alerts:update', 'ingestion:execute', 'reports:export', 'logs:export', 'lists:create', 'lists:delete', ...allPerms.filter((x) => x.startsWith('ml_') && x.endsWith(':view')), 'ml_inference:execute', 'ml_inference:export', 'ml_data:export', 'ml_evaluation:export', 'ml_explain:export'].filter((v, i, a) => a.indexOf(v) === i) },
  { id: 3, name: 'auditor', description: 'Solo lectura, bitácora y reportes', is_system: true, user_count: 1,
    permissions: [...allPerms.filter((p) => p.endsWith(':view') && !p.startsWith('users') && !p.startsWith('roles')), 'users:view', 'roles:view', 'audit:export', 'reports:export'] },
  { id: 4, name: 'manager', description: 'Panel y reportes de gestión', is_system: true, user_count: 1, permissions: ['dashboard:view', 'reports:view', 'reports:export', 'ml_evaluation:view'] },
]
const roleRef = (id: number) => { const r = roles.find((x) => x.id === id)!; return { id: r.id, name: r.name, description: r.description } }
const prof = (color: string, title: string, dept: string) => ({ job_title: title, department: dept, phone: '', avatar_color: color, theme: 'system' as const, language: 'es', timezone: 'America/Lima' })

export const users: (User & { password: string })[] = [
  { id: 1, username: 'admin', password: 'Demo1234', email: 'admin@pyme-andina.pe', full_name: 'Administrador TI', is_active: true, must_change_password: false, last_login_at: iso(NOW - 3 * H), role: roleRef(1), profile: prof('#2563eb', 'Jefe de TI', 'Sistemas'), created_at: iso(NOW - 90 * 24 * H) },
  { id: 2, username: 'aquispe', password: 'Demo1234', email: 'ana.quispe@pyme-andina.pe', full_name: 'Ana Quispe', is_active: true, must_change_password: false, last_login_at: iso(NOW - 26 * H), role: roleRef(2), profile: prof('#0d9488', 'Analista de seguridad', 'Sistemas'), created_at: iso(NOW - 60 * 24 * H) },
  { id: 3, username: 'lparedes', password: 'Demo1234', email: 'luis.paredes@pyme-andina.pe', full_name: 'Luis Paredes', is_active: true, must_change_password: false, last_login_at: iso(NOW - 5 * 24 * H), role: roleRef(3), profile: prof('#7c3aed', 'Auditor interno', 'Control interno'), created_at: iso(NOW - 45 * 24 * H) },
  { id: 4, username: 'chuaman', password: 'Demo1234', email: 'carla.huaman@pyme-andina.pe', full_name: 'Carla Huamán', is_active: true, must_change_password: false, last_login_at: iso(NOW - 2 * 24 * H), role: roleRef(4), profile: prof('#c2410c', 'Gerente general', 'Gerencia'), created_at: iso(NOW - 45 * 24 * H) },
  { id: 5, username: 'nuevo', password: 'Temporal1', email: 'nuevo@pyme-andina.pe', full_name: 'Usuario Nuevo', is_active: true, must_change_password: true, last_login_at: null, role: roleRef(2), profile: prof('#be185d', '', ''), created_at: iso(NOW - 1 * 24 * H) },
]

export const sources: Source[] = [
  { id: 1, name: 'OPNsense LAN', format: 'opnsense_filterlog', description: 'Firewall perimetral de la sede Lima', enabled: true, last_ingest_at: iso(NOW - 14 * 60_000), log_count: 0 },
  { id: 2, name: 'Suricata DMZ', format: 'suricata_eve', description: 'IDS en la DMZ', enabled: true, last_ingest_at: iso(NOW - 14 * 60_000), log_count: 0 },
  { id: 3, name: 'Flujos CTU-13 (demo)', format: 'ctu13_binetflow', description: 'Dataset de demostración', enabled: false, last_ingest_at: null, log_count: 0 },
]

const hosts: [string, string, string, Asset['criticality'], string][] = [
  ['10.0.0.5', 'pc-contabilidad', 'workstation', 'high', 'Rosa Medina'], ['10.0.0.8', 'pc-gerencia', 'workstation', 'critical', 'Carla Huamán'],
  ['10.0.0.12', 'srv-archivos', 'server', 'critical', 'TI'], ['10.0.0.15', 'srv-erp', 'server', 'critical', 'TI'],
  ['10.0.0.23', 'pc-ventas-02', 'workstation', 'medium', 'Jorge Salas'], ['10.0.0.31', 'imp-oficina', 'printer', 'low', 'Administración'],
  ['10.0.0.42', 'pc-logistica', 'workstation', 'medium', 'Mario Rojas'], ['10.0.0.50', 'pc-rrhh', 'workstation', 'medium', 'Lucía Vega'],
  ['10.0.0.60', 'cam-almacen', 'iot', 'low', 'Seguridad'], ['10.0.0.70', 'pc-ventas-01', 'workstation', 'medium', 'Elena Cruz'],
]
export const assets: Asset[] = hosts.map(([ip, hostname, asset_type, criticality, owner], i) => ({ id: i + 1, ip, hostname, owner, asset_type, criticality, expected_ports: asset_type === 'server' ? [22, 80, 443, 445, 1433] : [53, 80, 443], notes: '' }))

export const lists: ListEntry[] = [
  { id: 1, list_type: 'deny', kind: 'ip', value: '185.220.101.47', note: 'Nodo de salida Tor, reporte de la comunidad', created_at: iso(NOW - 12 * 24 * H) },
  { id: 2, list_type: 'deny', kind: 'ip', value: '45.9.148.21', note: 'Infraestructura de malware conocida', created_at: iso(NOW - 12 * 24 * H) },
  { id: 3, list_type: 'deny', kind: 'domain', value: 'update-check-service.top', note: '', created_at: iso(NOW - 8 * 24 * H) },
  { id: 4, list_type: 'deny', kind: 'port', value: '4444', note: 'Puerto por defecto de Metasploit', created_at: iso(NOW - 8 * 24 * H) },
  { id: 5, list_type: 'allow', kind: 'ip', value: '8.8.8.8', note: 'DNS de Google', created_at: iso(NOW - 30 * 24 * H) },
  { id: 6, list_type: 'allow', kind: 'cidr', value: '20.190.128.0/18', note: 'Microsoft 365', created_at: iso(NOW - 30 * 24 * H) },
]

const normalDst: [string, number, number][] = [['8.8.8.8', 53, 120], ['142.250.78.14', 443, 40000], ['20.190.151.8', 443, 25000], ['52.96.108.34', 443, 18000], ['151.101.1.69', 443, 60000], ['31.13.65.36', 443, 35000], ['104.18.32.7', 443, 22000], ['13.107.42.14', 443, 14000], ['34.117.59.81', 80, 9000]]

let logId = 1
function mkLog(ts: number, src: string, dst: string, port: number, o: Partial<FirewallLog> = {}): FirewallLog {
  const ids = o.log_type === 'ids'
  const l: FirewallLog = {
    id: logId++, ts: iso(ts), source_id: ids ? 2 : 1, source_name: ids ? 'Suricata DMZ' : 'OPNsense LAN', log_type: ids ? 'ids' : 'flow',
    action: 'pass', proto: port === 53 ? 'udp' : 'tcp', src_ip: src, src_port: ri(32768, 61000), dst_ip: dst, dst_port: port, direction: 'outbound',
    bytes_out: ri(400, 4000), bytes_in: ri(1000, 30000), packets: ri(6, 60), duration: Math.round(rnd() * 90) / 10,
    signature: null, signature_id: null, category: null, ids_severity: null, label: null, raw: {}, ...o,
  }
  l.raw = { timestamp: l.ts, interface: ids ? 'dmz0' : 'igc1', proto: l.proto, src: `${l.src_ip}:${l.src_port}`, dst: `${l.dst_ip}:${l.dst_port}`, action: l.action, bytes: l.bytes_out + l.bytes_in, ...(l.signature ? { alert: { signature: l.signature, signature_id: l.signature_id, category: l.category } } : {}) }
  return l
}

export const logs: FirewallLog[] = []
const T0 = NOW - 7 * 24 * H
// tráfico normal con curva diaria
for (let i = 0; i < 1500; i++) {
  const ts = T0 + rnd() * (NOW - T0)
  const hour = new Date(ts).getUTCHours() - 5
  if ((hour < 7 || hour > 20) && rnd() < 0.75) { i--; continue }
  const [dst, port, mean] = pick(normalDst)
  const src = pick(hosts)[0]
  logs.push(mkLog(ts, src, dst, port, { bytes_out: Math.round(mean * (0.2 + rnd() * 1.6) / 4), bytes_in: Math.round(mean * (0.4 + rnd() * 2)), action: rnd() < 0.05 ? 'block' : 'pass' }))
}
// bloqueos entrantes (escaneos)
for (let i = 0; i < 160; i++) logs.push(mkLog(T0 + rnd() * (NOW - T0), `${pick(['45.142.', '193.32.', '89.248.'])}${ri(1, 250)}.${ri(1, 250)}`, pick(['10.0.0.12', '10.0.0.15']), pick([22, 23, 3389, 445, 8080]), { action: 'block', direction: 'inbound', bytes_out: 0, bytes_in: ri(40, 120), packets: 1, duration: 0 }))
// beaconing 10.0.0.23 -> 185.220.101.47:443, cada ~300 s durante 9 h
const beaconTs: number[] = []
for (let t = NOW - 9 * H, k = 0; t < NOW - 20 * 60_000; k++) { beaconTs.push(t); t += (300 + (rnd() - 0.5) * 16) * 1000 }
beaconTs.forEach((t) => logs.push(mkLog(t, '10.0.0.23', '185.220.101.47', 443, { bytes_out: ri(480, 560), bytes_in: ri(1100, 1250), duration: 0.4, label: 'Background' })))
// exfiltración 10.0.0.15 -> 45.9.148.21
for (let i = 0; i < 40; i++) logs.push(mkLog(NOW - 3 * H + i * 4.2 * 60_000, '10.0.0.15', '45.9.148.21', 443, { bytes_out: ri(60, 130) * 1_048_576, bytes_in: ri(2000, 9000), packets: ri(40000, 90000), duration: ri(80, 240) }))
// puerto inusual
for (let i = 0; i < 14; i++) logs.push(mkLog(NOW - 5 * H + i * 17 * 60_000, '10.0.0.31', '91.134.200.12', 4444, { bytes_out: ri(900, 3000), bytes_in: ri(200, 900), action: i % 3 === 0 ? 'block' : 'pass' }))
// IDS
const sigs: [string, number, string, number][] = [['ET SCAN Potential SSH Scan', 2001219, 'Attempted Information Leak', 2], ['ET POLICY Possible Tor Connection', 2522000, 'Potential Corporate Privacy Violation', 3], ['ET MALWARE Win32/Emotet CnC Activity', 2404302, 'A Network Trojan was detected', 1]]
for (let i = 0; i < 90; i++) { const s = i % 9 === 0 ? sigs[2] : i % 3 === 0 ? sigs[1] : sigs[0]; logs.push(mkLog(NOW - rnd() * 3 * 24 * H, s === sigs[0] ? `${pick(['45.142.', '193.32.'])}${ri(1, 250)}.${ri(1, 250)}` : pick(['10.0.0.70', '10.0.0.50']), s === sigs[0] ? '10.0.0.12' : pick(['185.220.101.47', '45.9.148.21']), s === sigs[0] ? 22 : 443, { log_type: 'ids', action: 'alert', signature: s[0], signature_id: s[1], category: s[2], ids_severity: s[3], direction: s === sigs[0] ? 'inbound' : 'outbound', bytes_out: 0, bytes_in: 0 })) }
logs.sort((a, b) => (a.ts < b.ts ? -1 : 1))
logs.forEach((l, i) => { l.id = i + 1 })
sources[0].log_count = logs.filter((l) => l.source_id === 1).length
sources[1].log_count = logs.filter((l) => l.source_id === 2).length

const fnd = (id: number, o: Partial<Finding> & Pick<Finding, 'finding_type' | 'severity' | 'title' | 'src_ip' | 'evidence'>): Finding => ({
  id, created_at: iso(NOW - 2 * H), first_seen: iso(NOW - 9 * H), last_seen: iso(NOW - 25 * 60_000), occurrences: 1, score: 70, status: 'new',
  dst_ip: null, dst_port: null, proto: 'tcp', window_start: iso(NOW - 24 * H), window_end: iso(NOW),
  llm_verdict: 'real', llm_confidence: 0.8, is_noise: false, llm_explanation: null, llm_recommendation: null, llm_model: 'llama3.2:3b', assigned_to: null, comments: [], ...o,
})
export const findings: Finding[] = [
  fnd(1, { finding_type: 'beaconing', severity: 'critical', score: 94, title: 'Beaconing regular de pc-ventas-02 hacia 185.220.101.47:443', src_ip: '10.0.0.23', dst_ip: '185.220.101.47', dst_port: 443, occurrences: beaconTs.length, first_seen: iso(beaconTs[0]), last_seen: iso(beaconTs[beaconTs.length - 1]),
    evidence: { connections: beaconTs.length, mean_interval_s: 300.2, stdev_interval_s: 4.6, cv: 0.015, mean_bytes: 520, bytes_cv: 0.04, duration_h: 8.6, intervals_sample: beaconTs.slice(1, 49).map((t, i) => Math.round((t - beaconTs[i]) / 1000)) },
    llm_verdict: 'real', llm_confidence: 0.93, status: 'in_review', assigned_to: { id: 2, full_name: 'Ana Quispe' },
    llm_explanation: 'El equipo pc-ventas-02 se conecta cada 5 minutos exactos (variación de solo 1,5 %) a una dirección de la lista negra que corresponde a un nodo de salida Tor. Los paquetes son casi del mismo tamaño. Ningún usuario hace eso a mano: parece un programa que "avisa" a un controlador externo.',
    llm_recommendation: 'Aísle pc-ventas-02 de la red, conserve el equipo sin apagarlo para análisis y cambie las credenciales usadas en él. Revise si otros equipos contactaron 185.220.101.47.',
    comments: [{ id: 1, author: 'Ana Quispe', body: 'Equipo aislado a las 14:20. Pendiente revisar procesos con el usuario.', created_at: iso(NOW - 70 * 60_000) }] }),
  fnd(2, { finding_type: 'exfiltration', severity: 'critical', score: 91, title: 'Envío anómalo de 3,9 GB desde srv-erp hacia 45.9.148.21', src_ip: '10.0.0.15', dst_ip: '45.9.148.21', dst_port: 443, occurrences: 40, first_seen: iso(NOW - 3 * H), last_seen: iso(NOW - 10 * 60_000),
    evidence: { bytes_out: 4_180_000_000, baseline_mean: 310_000_000, baseline_stdev: 95_000_000, zscore: 40.7, ratio_out_in: 5200, top_destinations: [{ ip: '45.9.148.21', bytes: 4_100_000_000 }, { ip: '52.96.108.34', bytes: 62_000_000 }, { ip: '20.190.151.8', bytes: 18_000_000 }] },
    llm_verdict: 'real', llm_confidence: 0.88,
    llm_explanation: 'srv-erp suele enviar unos 300 MB al día y en las últimas 3 horas envió más de 4 GB, casi todo a una IP en lista negra. Recibió casi nada a cambio, lo que es típico de una copia de datos hacia afuera y no de una descarga.',
    llm_recommendation: 'Bloquee 45.9.148.21 en el firewall ahora, verifique si hay procesos de respaldo legítimos y evalúe qué datos contiene el ERP para decidir si debe notificar un incidente.' }),
  fnd(3, { finding_type: 'unusual_port', severity: 'high', score: 74, title: 'Tráfico por puerto 4444 desde imp-oficina', src_ip: '10.0.0.31', dst_ip: '91.134.200.12', dst_port: 4444, occurrences: 14, last_seen: iso(NOW - 70 * 60_000),
    evidence: { port: 4444, service: 'sin servicio conocido', connections: 14, bytes: 38400, distinct_sources: 1, in_baseline: false, first_seen: iso(NOW - 5 * H) },
    llm_verdict: 'uncertain', llm_confidence: 0.55, llm_explanation: 'Una impresora no debería iniciar conexiones por el puerto 4444, usado por herramientas de acceso remoto. Pero el volumen es muy bajo y podría ser un servicio de monitoreo del fabricante.', llm_recommendation: 'Confirme con el proveedor si la impresora usa ese puerto; si no, bloquéelo.' }),
  fnd(4, { finding_type: 'ids_alert', severity: 'high', score: 80, title: 'Firma Emotet CnC detectada desde pc-rrhh', src_ip: '10.0.0.50', dst_ip: '45.9.148.21', dst_port: 443, occurrences: 10, last_seen: iso(NOW - 6 * H),
    evidence: { signature: 'ET MALWARE Win32/Emotet CnC Activity', signature_id: 2404302, category: 'A Network Trojan was detected', ids_severity: 1, count: 10, distinct_sources: 1 }, status: 'confirmed',
    llm_verdict: 'real', llm_confidence: 0.84, llm_explanation: 'Suricata reconoció tráfico con la firma de Emotet, un troyano bancario, desde pc-rrhh hacia la misma IP maliciosa del envío de datos.', llm_recommendation: 'Trate pc-rrhh como comprometido: aíslelo y ejecute un análisis completo.' }),
  fnd(5, { finding_type: 'talker_anomaly', severity: 'medium', score: 58, title: 'pc-logistica contactó 212 destinos distintos en 1 hora', src_ip: '10.0.0.42', dst_ip: null, dst_port: null, proto: null, last_seen: iso(NOW - 8 * H),
    evidence: { metric: 'destinos únicos por hora', value: 212, baseline_mean: 14, baseline_stdev: 6, zscore: 33, unique_destinations: 212 }, llm_verdict: 'uncertain', llm_confidence: 0.5, llm_explanation: null, llm_recommendation: null }),
  fnd(6, { finding_type: 'unusual_port', severity: 'low', score: 41, title: 'Tráfico por puerto 8080 desde pc-ventas-01', src_ip: '10.0.0.70', dst_ip: '34.117.59.81', dst_port: 8080, last_seen: iso(NOW - 20 * H), is_noise: true,
    evidence: { port: 8080, service: 'http-alt', connections: 6, bytes: 12000, distinct_sources: 1, in_baseline: false, first_seen: iso(NOW - 20 * H) }, llm_verdict: 'noise', llm_confidence: 0.86, status: 'false_positive',
    llm_explanation: 'Conexiones esporádicas y pequeñas a un servicio de un proveedor de nube de uso común. Parece una aplicación web interna.', llm_recommendation: 'Agregue el destino a la lista blanca si lo reconoce.' }),
  fnd(7, { finding_type: 'ids_alert', severity: 'info', score: 20, title: 'Escaneo SSH desde 45.142.x.x contra srv-archivos', src_ip: '45.142.120.8', dst_ip: '10.0.0.12', dst_port: 22, occurrences: 60, last_seen: iso(NOW - 30 * 60_000), is_noise: true,
    evidence: { signature: 'ET SCAN Potential SSH Scan', signature_id: 2001219, category: 'Attempted Information Leak', ids_severity: 2, count: 60, distinct_sources: 11 }, llm_verdict: 'noise', llm_confidence: 0.9, llm_explanation: 'Escaneo de Internet bloqueado por el firewall. Es ruido de fondo habitual.', llm_recommendation: 'Sin acción; confirme que SSH no está expuesto a Internet.' }),
  fnd(8, { finding_type: 'beaconing', severity: 'medium', score: 63, title: 'Conexiones periódicas de cam-almacen hacia 34.117.59.81', src_ip: '10.0.0.60', dst_ip: '34.117.59.81', dst_port: 80, last_seen: iso(NOW - 3 * H), status: 'new', llm_verdict: null, llm_model: null, llm_confidence: null,
    evidence: { connections: 96, mean_interval_s: 900, stdev_interval_s: 120, cv: 0.13, mean_bytes: 340, bytes_cv: 0.2, duration_h: 24, intervals_sample: Array.from({ length: 40 }, () => ri(700, 1100)) },
    llm_explanation: 'Se detectaron conexiones con intervalos regulares (cada ~15 min). Esto puede ser software legítimo de monitoreo, pero conviene validarlo.', llm_recommendation: 'Verifique que el fabricante de la cámara use ese destino; de lo contrario, bloquéelo.' }),
]
for (let i = 9; i <= 20; i++) {
  const types: Finding['finding_type'][] = ['ids_alert', 'unusual_port', 'talker_anomaly']
  const t = types[i % 3]; const h = pick(hosts)
  findings.push(fnd(i, { finding_type: t, severity: pick(['low', 'info', 'medium']), score: ri(25, 55), is_noise: i % 2 === 0, title: t === 'ids_alert' ? 'Alerta ET POLICY Possible Tor Connection' : t === 'unusual_port' ? `Tráfico por puerto ${pick([8443, 5222, 6881])} desde ${h[1]}` : `Aumento de tráfico de ${h[1]}`, src_ip: h[0], dst_ip: '151.101.1.69', dst_port: 443, last_seen: iso(NOW - ri(1, 6) * 24 * H + ri(0, 20) * H),
    evidence: t === 'ids_alert' ? { signature: 'ET POLICY Possible Tor Connection', signature_id: 2522000, category: 'Potential Corporate Privacy Violation', ids_severity: 3, count: ri(2, 8), distinct_sources: 1 } : t === 'unusual_port' ? { port: 6881, service: 'bittorrent', connections: ri(3, 12), bytes: ri(5000, 90000), distinct_sources: 1, in_baseline: false, first_seen: iso(NOW - 3 * 24 * H) } : { metric: 'bytes de salida por hora', value: ri(40, 90) * 1e6, baseline_mean: 20e6, zscore: 3.4, unique_destinations: ri(5, 30) },
    llm_verdict: i % 2 === 0 ? 'noise' : 'uncertain', llm_confidence: 0.6 + (i % 3) / 10, llm_explanation: 'Actividad de baja gravedad, compatible con uso personal de la red.', llm_recommendation: 'Revise la política de uso aceptable.', status: i % 4 === 0 ? 'closed' : 'new' }))
}

export const alerts: Alert[] = findings.filter((f) => !f.is_noise && f.severity !== 'info').map((f, i) => ({
  id: i + 1, created_at: f.last_seen, finding_id: f.id, rule_id: 1, severity: f.severity, title: f.title, message: `Nuevo hallazgo ${f.severity === 'critical' ? 'crítico' : 'relevante'} en ${f.src_ip}.`, channel: i % 3 === 2 ? 'webhook' : 'in_app', delivered: i % 4 !== 3,
  acknowledged_at: i > 3 ? iso(NOW - (i - 3) * H) : null, acknowledged_by: i > 3 ? 'Ana Quispe' : null,
}))
export const alertRules: AlertRule[] = [
  { id: 1, name: 'Críticos y altos', enabled: true, min_severity: 'high', finding_types: [], channels: ['in_app', 'webhook'], webhook_url: 'https://hooks.pyme-andina.pe/n8n/alertas', email_to: null, include_noise: false },
  { id: 2, name: 'Exfiltración (cualquier nivel)', enabled: true, min_severity: 'low', finding_types: ['exfiltration'], channels: ['in_app', 'email'], webhook_url: null, email_to: 'ti@pyme-andina.pe', include_noise: false },
]
export const runs: IngestRun[] = [
  { id: 4, started_at: iso(NOW - 14 * 60_000), finished_at: iso(NOW - 13 * 60_000), status: 'success', trigger: 'n8n', source_id: 1, source_name: 'OPNsense LAN', filename: null, lines_read: 8421, logs_inserted: 8390, parse_errors: 31, findings_created: 2, findings_noise: 5, error: null },
  { id: 3, started_at: iso(NOW - 2 * H), finished_at: iso(NOW - 2 * H + 40_000), status: 'success', trigger: 'upload', source_id: 2, source_name: 'Suricata DMZ', filename: 'eve-2026-11-11.json', lines_read: 1204, logs_inserted: 1204, parse_errors: 0, findings_created: 1, findings_noise: 3, error: null },
  { id: 2, started_at: iso(NOW - 26 * H), finished_at: iso(NOW - 26 * H + 5000), status: 'error', trigger: 'upload', source_id: 1, source_name: 'OPNsense LAN', filename: 'filter.log.bak', lines_read: 0, logs_inserted: 0, parse_errors: 0, findings_created: 0, findings_noise: 0, error: 'Formato no reconocido: se esperaba filterlog de OPNsense.' },
  { id: 1, started_at: iso(NOW - 5 * 24 * H), finished_at: iso(NOW - 5 * 24 * H + 120_000), status: 'success', trigger: 'dataset', source_id: 3, source_name: 'Flujos CTU-13 (demo)', filename: null, lines_read: 52000, logs_inserted: 52000, parse_errors: 0, findings_created: 6, findings_noise: 14, error: null },
]

export const auditEvents: AuditEvent[] = []
export const sessions: ModuleSession[] = []
let evId = 1, sId = 1
export function pushEvent(u: { id: number; username: string } | null, type: AuditEvent['event_type'], desc: string, module: string | null = null, extra: Partial<AuditEvent> = {}, ts = Date.now()) {
  auditEvents.unshift({ id: evId++, ts: iso(ts), user_id: u?.id ?? null, username: u?.username ?? 'desconocido', event_type: type, module, entity: null, entity_id: null, description: desc, ip: '192.168.1.20', user_agent: 'Mozilla/5.0 (X11; Linux x86_64) Firefox/131.0', details: {}, ...extra })
}
export function openSession(u: { id: number; username: string }, module: string) {
  const s: ModuleSession = { id: sId++, user_id: u.id, username: u.username, module, entered_at: iso(Date.now()), exited_at: null, duration_seconds: null, ip: '192.168.1.20', exit_reason: null }
  sessions.unshift(s)
  return s
}
export function closeSession(s: ModuleSession, reason: ModuleSession['exit_reason'], ts = Date.now()) {
  s.exited_at = iso(ts); s.duration_seconds = Math.max(0, Math.round((ts - new Date(s.entered_at).getTime()) / 1000)); s.exit_reason = reason
}
// historial previo
;(() => {
  const mods = ['dashboard', 'findings', 'alerts', 'logs', 'reports', 'ingestion', 'users', 'audit']
  for (let d = 5; d >= 1; d--) for (const u of users.slice(0, 4)) {
    let t = NOW - d * 24 * H + ri(0, 3) * H
    pushEvent(u, 'login', `${u.username} inició sesión`, null, {}, t)
    for (let k = 0; k < ri(3, 6); k++) {
      const m = u.id === 4 ? pick(['dashboard', 'reports']) : pick(mods)
      const s = { id: sId++, user_id: u.id, username: u.username, module: m, entered_at: iso(t), exited_at: null, duration_seconds: null, ip: '192.168.1.20', exit_reason: null } as ModuleSession
      pushEvent(u, 'module_enter', `Entró a ${m}`, m, {}, t)
      const dur = ri(20, 900); t += dur * 1000
      closeSession(s, k % 4 === 3 ? 'close' : 'navigation', t); sessions.unshift(s)
      pushEvent(u, 'module_exit', `Salió de ${m}`, m, {}, t)
    }
    if (u.id === 1) pushEvent(u, 'update', 'Modificó parámetros de detección', 'detection', { entity: 'settings', entity_id: 'detection' }, t)
    if (u.id === 4) pushEvent(u, 'export', 'Generó reporte Resumen ejecutivo (pdf)', 'reports', {}, t)
    pushEvent(u, 'logout', `${u.username} cerró sesión`, null, {}, t + 60_000)
  }
  pushEvent(null, 'login_failed', 'Intento de inicio fallido para "root"', null, { username: 'root', ip: '203.0.113.9' }, NOW - 30 * H)
  auditEvents.sort((a, b) => (a.ts < b.ts ? 1 : -1)); sessions.sort((a, b) => (a.entered_at < b.entered_at ? 1 : -1))
})()
