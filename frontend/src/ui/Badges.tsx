import type { FindingStatus, LogAction, LlmVerdict } from '../api/types'
import { ACTION_LABEL, STATUS_LABEL, VERDICT_LABEL } from '../lib/labels'

export function StatusBadge({ status }: { status: FindingStatus }) {
  const cls = status === 'new' ? 'accent' : status === 'in_review' ? 'med' : status === 'confirmed' ? 'crit' : status === 'false_positive' ? '' : 'ok'
  return <span className={`badge ${cls}`}>{STATUS_LABEL[status]}</span>
}
export function ActionBadge({ action }: { action: LogAction }) {
  return <span className={`badge ${action === 'block' ? 'crit' : action === 'alert' ? 'med' : ''}`}>{ACTION_LABEL[action]}</span>
}
export function VerdictBadge({ verdict }: { verdict: LlmVerdict | null }) {
  if (!verdict) return <span className="badge outline">Sin veredicto IA</span>
  return <span className={`badge ${verdict === 'real' ? 'crit' : verdict === 'noise' ? '' : 'med'}`}>IA: {VERDICT_LABEL[verdict]}</span>
}
