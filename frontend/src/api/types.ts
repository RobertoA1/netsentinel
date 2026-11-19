// Tipos derivados de docs/API_CONTRACT.md
export type FindingType = 'beaconing' | 'unusual_port' | 'exfiltration' | 'ids_alert' | 'talker_anomaly'
export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info'
export type FindingStatus = 'new' | 'in_review' | 'confirmed' | 'false_positive' | 'closed'
export type LlmVerdict = 'real' | 'noise' | 'uncertain'
export type LogType = 'firewall' | 'ids' | 'flow'
export type LogAction = 'pass' | 'block' | 'alert'
export type Direction = 'outbound' | 'inbound' | 'internal'
export type SourceFormat = 'opnsense_filterlog' | 'suricata_eve' | 'ctu13_binetflow'
export type AuditEventType =
  | 'login' | 'logout' | 'login_failed' | 'module_enter' | 'module_exit'
  | 'create' | 'update' | 'delete' | 'export' | 'execute'
export type AlertChannel = 'in_app' | 'email' | 'webhook'
export type ReportFormat = 'pdf' | 'docx' | 'xlsx'
export type RangeKey = '1h' | '24h' | '7d' | '30d'
export type ModuleCode =
  | 'dashboard' | 'logs' | 'findings' | 'alerts' | 'reports' | 'assets' | 'sources'
  | 'lists' | 'ingestion' | 'detection' | 'llm' | 'users' | 'roles' | 'audit'
export type ActionCode = 'view' | 'create' | 'update' | 'delete' | 'export' | 'execute'

export interface Page<T> { items: T[]; total: number; page: number; page_size: number }

export interface RoleRef { id: number; name: string; description: string }
export interface Profile {
  job_title: string; department: string; phone: string; avatar_color: string
  theme: 'system' | 'light' | 'dark'; language: string; timezone: string
}
export interface User {
  id: number; username: string; email: string; full_name: string; is_active: boolean
  must_change_password: boolean; last_login_at: string | null
  role: RoleRef; profile: Profile; created_at?: string
}
export interface UserMe extends User { permissions: string[] }
export interface Role {
  id: number; name: string; description: string; is_system: boolean
  permissions: string[]; user_count: number
}
export interface PermissionModule { code: string; label: string; actions: string[] }

export interface FirewallLog {
  id: number; ts: string; source_id: number; source_name: string; log_type: LogType
  action: LogAction; proto: string; src_ip: string; src_port: number | null
  dst_ip: string; dst_port: number | null; direction: Direction
  bytes_out: number; bytes_in: number; packets: number; duration: number
  signature: string | null; signature_id: number | null; category: string | null
  ids_severity: number | null; label: string | null; raw: Record<string, unknown>
}

export interface Comment { id: number; author: string; body: string; created_at: string }

export interface BeaconEvidence {
  connections: number; mean_interval_s: number; stdev_interval_s: number; cv: number
  mean_bytes: number; bytes_cv: number; duration_h: number; intervals_sample: number[]
}
export interface UnusualPortEvidence {
  port: number; service: string; connections: number; bytes: number
  distinct_sources: number; in_baseline: boolean; first_seen: string
}
export interface ExfilEvidence {
  bytes_out: number; baseline_mean: number; baseline_stdev: number; zscore: number
  ratio_out_in: number; top_destinations: { ip: string; bytes: number }[]
}
export interface IdsEvidence {
  signature: string; signature_id: number; category: string; ids_severity: number
  count: number; distinct_sources: number
}
export interface TalkerEvidence {
  metric: string; value: number; baseline_mean: number; zscore: number; unique_destinations: number
}

export interface Finding {
  id: number; created_at: string; first_seen: string; last_seen: string; occurrences: number
  finding_type: FindingType; severity: Severity; score: number; status: FindingStatus
  title: string; src_ip: string | null; dst_ip: string | null; dst_port: number | null; proto: string | null
  window_start: string | null; window_end: string | null
  evidence: Record<string, any>
  llm_verdict: LlmVerdict | null; llm_confidence: number | null; is_noise: boolean
  llm_explanation: string | null; llm_recommendation: string | null; llm_model: string | null
  assigned_to: { id: number; full_name: string } | null
  comments?: Comment[]
}

export interface Alert {
  id: number; created_at: string; finding_id: number; rule_id: number; severity: Severity
  title: string; message: string; channel: AlertChannel; delivered: boolean
  acknowledged_at: string | null; acknowledged_by: string | { id: number; full_name: string } | null
}
export interface AlertRule {
  id: number; name: string; enabled: boolean; min_severity: Severity
  finding_types: FindingType[]; channels: AlertChannel[]
  webhook_url: string | null; email_to: string | null; include_noise: boolean
}

export interface Source {
  id: number; name: string; format: SourceFormat; description: string
  enabled: boolean; last_ingest_at: string | null; log_count: number
}
export interface Asset {
  id: number; ip: string; hostname: string; owner: string; asset_type: string
  criticality: 'low' | 'medium' | 'high' | 'critical'; expected_ports: number[]; notes: string
}
export interface ListEntry {
  id: number; list_type: 'allow' | 'deny'; kind: 'ip' | 'cidr' | 'port' | 'domain'
  value: string; note: string; created_at: string
}
export interface IngestRun {
  id: number; started_at: string; finished_at: string | null
  status: 'running' | 'success' | 'error'; trigger: 'n8n' | 'upload' | 'manual' | 'dataset'
  source_id: number | null; source_name: string | null; filename: string | null
  lines_read: number; logs_inserted: number; parse_errors: number
  findings_created: number; findings_noise: number; error: string | null
}
export interface IngestStatus {
  last_run: IngestRun | null; dataset_available: boolean; dataset_loaded: boolean; pending_files: number
}
export interface DetectResult {
  findings_created: number; findings_updated: number; findings_noise: number; duration_ms: number
}

export interface AuditEvent {
  id: number; ts: string; user_id: number | null; username: string; event_type: AuditEventType
  module: string | null; entity: string | null; entity_id: number | string | null
  description: string; ip: string; user_agent: string; details: Record<string, unknown>
}
export interface ModuleSession {
  id: number; user_id: number; username: string; module: string; entered_at: string
  exited_at: string | null; duration_seconds: number | null; ip: string
  exit_reason: 'navigation' | 'logout' | 'timeout' | 'close' | null
}
export interface AuditSummary {
  by_module: { module: string; visits: number; total_seconds: number }[]
  by_user: { username: string; visits: number; total_seconds: number; last_seen: string }[]
  by_event_type: { event_type: string; count: number }[]
}

export interface DashboardSummary {
  total_logs: number; total_bytes_out: number; total_bytes_in: number
  unique_sources: number; unique_destinations: number; blocked_connections: number
  open_findings: number; critical_findings: number; noise_filtered: number; noise_ratio: number
  alerts_unacknowledged: number; last_ingest_at: string | null
  deltas: Record<string, number>
}
export interface TrafficPoint { ts: string; bytes_out: number; bytes_in: number; connections: number; blocked: number }
export interface Talker {
  ip: string; hostname: string | null; bytes_out: number; bytes_in: number
  connections: number; unique_destinations: number; findings: number
}
export interface TopDestination { ip: string; bytes: number; connections: number; unique_sources: number; in_denylist: boolean }
export interface TopPort { port: number; proto: string; service: string | null; connections: number; bytes: number; unusual: boolean }
export interface FlowRow { src_ip: string; dst_ip: string; dst_port: number; bytes: number; connections: number }

export interface DetectionSettings {
  beacon_min_connections: number; beacon_max_cv: number; beacon_min_score: number
  exfil_zscore: number; exfil_min_bytes: number; common_ports: number[]
  unusual_port_min_connections: number; internal_cidrs: string[]; detection_window_hours: number
}
export interface LlmSettings {
  enabled: boolean; base_url: string; model: string; temperature: number
  timeout_seconds: number; noise_confidence_threshold: number
}
export interface LlmTestResult { ok: boolean; model: string; latency_ms: number; message: string }
export interface RetentionSettings { logs_days: number; findings_days: number; audit_days: number }

export interface ReportCatalogItem {
  code: string; name: string; description: string; category: 'operational' | 'management' | 'ml'
  formats: ReportFormat[]
  params?: ('dataset_version_id' | 'job_id' | 'model_id')[]
}
export interface ReportHistoryItem {
  id: number; report_code: string; report_name: string; format: ReportFormat
  date_from: string; date_to: string; generated_by: string; generated_at: string; size_bytes: number
}
export interface Health { status: string; db: boolean; llm: boolean; version: string }
export interface LoginResponse { access_token: string; refresh_token: string; token_type: string; user: UserMe }
