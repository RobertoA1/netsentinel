import type { Severity } from '../api/types'
import { SEVERITY_LABEL, SEVERITY_STEPS } from '../lib/labels'

const CLS: Record<Severity, string> = { critical: 'crit', high: 'high', medium: 'med', low: 'low', info: 'info' }

/** Regla de intensidad: 5 peldaños crecientes; la severidad se lee por altura y etiqueta, no solo por color. */
export function Gauge({ severity, large }: { severity: Severity; large?: boolean }) {
  const n = SEVERITY_STEPS[severity]
  return (
    <span className={`gauge sev-${CLS[severity]}${large ? ' lg' : ''}`} role="img" aria-label={`Severidad ${SEVERITY_LABEL[severity].toLowerCase()}, ${n} de 5`}>
      {[1, 2, 3, 4, 5].map((i) => <i key={i} className={i <= n ? 'on' : ''} />)}
    </span>
  )
}

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span className={`badge ${CLS[severity]}`}>
      <Gauge severity={severity} />
      {SEVERITY_LABEL[severity]}
    </span>
  )
}
