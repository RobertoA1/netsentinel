import type { Severity, FindingType, FindingStatus, LlmVerdict, LogAction, Direction, SourceFormat, AuditEventType, AlertChannel, RangeKey } from '../api/types'

export const SEVERITIES: Severity[] = ['critical', 'high', 'medium', 'low', 'info']
export const SEVERITY_LABEL: Record<Severity, string> = {
  critical: 'Crítica', high: 'Alta', medium: 'Media', low: 'Baja', info: 'Informativa',
}
/** Peldaños de la regla de intensidad (1 a 5). */
export const SEVERITY_STEPS: Record<Severity, number> = { critical: 5, high: 4, medium: 3, low: 2, info: 1 }

export const FINDING_TYPE_LABEL: Record<FindingType, string> = {
  beaconing: 'Beaconing', unusual_port: 'Puerto inusual', exfiltration: 'Exfiltración',
  ids_alert: 'Alerta IDS', talker_anomaly: 'Anomalía de talker',
}
export const FINDING_TYPE_PLAIN: Record<FindingType, string> = {
  beaconing: 'Un equipo se comunica con un destino a intervalos demasiado regulares, como lo haría un programa malicioso que "reporta" a su controlador.',
  unusual_port: 'Tráfico por un puerto que esta red normalmente no usa.',
  exfiltration: 'Un equipo envió mucho más datos hacia afuera de lo que suele enviar.',
  ids_alert: 'El sistema de detección de intrusos reconoció una firma de ataque conocida.',
  talker_anomaly: 'Un equipo se comporta distinto a su línea base habitual.',
}
export const STATUS_LABEL: Record<FindingStatus, string> = {
  new: 'Nuevo', in_review: 'En revisión', confirmed: 'Confirmado', false_positive: 'Falso positivo', closed: 'Cerrado',
}
export const VERDICT_LABEL: Record<LlmVerdict, string> = { real: 'Real', noise: 'Ruido', uncertain: 'Incierto' }
export const ACTION_LABEL: Record<LogAction, string> = { pass: 'Permitido', block: 'Bloqueado', alert: 'Alerta' }
export const DIRECTION_LABEL: Record<Direction, string> = { outbound: 'Saliente', inbound: 'Entrante', internal: 'Interno' }
export const FORMAT_LABEL: Record<SourceFormat, string> = {
  opnsense_filterlog: 'OPNsense filterlog', suricata_eve: 'Suricata EVE', ctu13_binetflow: 'CTU-13 binetflow',
}
export const LOG_TYPE_LABEL = { firewall: 'Firewall', ids: 'IDS', flow: 'Flujo' } as const
export const EVENT_LABEL: Record<AuditEventType, string> = {
  login: 'Inicio de sesión', logout: 'Cierre de sesión', login_failed: 'Inicio fallido',
  module_enter: 'Entrada a módulo', module_exit: 'Salida de módulo', create: 'Creación',
  update: 'Modificación', delete: 'Eliminación', export: 'Exportación', execute: 'Ejecución',
}
export const CHANNEL_LABEL: Record<AlertChannel, string> = { in_app: 'En la aplicación', email: 'Correo', webhook: 'Webhook' }
export const RANGE_LABEL: Record<RangeKey, string> = { '1h': '1 hora', '24h': '24 horas', '7d': '7 días', '30d': '30 días' }
export const CRITICALITY_LABEL = { low: 'Baja', medium: 'Media', high: 'Alta', critical: 'Crítica' } as const
export const ASSET_TYPES: Record<string, string> = {
  workstation: 'Estación de trabajo', server: 'Servidor', network: 'Equipo de red', printer: 'Impresora', iot: 'IoT', other: 'Otro',
}

export const MODULES: Record<string, { label: string; path: string }> = {
  dashboard: { label: 'Panel', path: '/dashboard' },
  findings: { label: 'Hallazgos', path: '/findings' },
  alerts: { label: 'Alertas', path: '/alerts' },
  logs: { label: 'Registros', path: '/logs' },
  reports: { label: 'Reportes', path: '/reports' },
  ingestion: { label: 'Ingesta', path: '/ingestion' },
  assets: { label: 'Activos', path: '/assets' },
  sources: { label: 'Fuentes', path: '/sources' },
  lists: { label: 'Listas', path: '/lists' },
  detection: { label: 'Detección', path: '/detection' },
  llm: { label: 'Motor IA', path: '/llm' },
  users: { label: 'Usuarios', path: '/users' },
  roles: { label: 'Roles', path: '/roles' },
  audit: { label: 'Bitácora', path: '/audit' },
  ml_data: { label: 'ML · Datos', path: '/ml/datos' },
  ml_training: { label: 'ML · Entrenamiento', path: '/ml/entrenamiento' },
  ml_evaluation: { label: 'ML · Evaluación', path: '/ml/evaluacion' },
  ml_explain: { label: 'ML · Explicabilidad', path: '/ml/explicabilidad' },
  ml_inference: { label: 'ML · Inferencia', path: '/ml/inferencia' },
  ml_optuna: { label: 'ML · Optuna', path: '/ml/optuna' },
}
/** Módulo al que pertenece una ruta (la ruta más larga que la contiene como prefijo). */
export function moduleOfRoute(pathname: string): string | null {
  let best: string | null = null
  for (const [code, m] of Object.entries(MODULES)) {
    if ((pathname === m.path || pathname.startsWith(m.path + '/')) && (!best || m.path.length > MODULES[best].path.length)) best = code
  }
  return best
}
export const moduleLabel = (code: string | null | undefined) => (code ? MODULES[code]?.label ?? code : '—')
export const ACTION_PERM_LABEL: Record<string, string> = {
  view: 'Ver', create: 'Crear', update: 'Editar', delete: 'Eliminar', export: 'Exportar', execute: 'Ejecutar',
}
