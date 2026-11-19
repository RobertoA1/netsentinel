import type { Interp, Spec } from './figures'

export type JobStatus = 'queued' | 'running' | 'cancel_requested' | 'cancelled' | 'failed' | 'succeeded'
export interface MlJob {
  id: number; kind: 'train' | 'evaluate' | 'explain' | 'optimize'; status: JobStatus; name: string
  params: any; progress: any; resources: { pid?: number; rss_mb?: number; cpu_percent?: number; cpu_count?: number; mem_total_mb?: number } | null
  error: string | null; attempts: number; seed: number; libs: Record<string, string> | null; created_by: string
  created_at: string; started_at: string | null; finished_at: string | null; heartbeat_at: string | null
  dataset_version_id: number | null; time_limit_s: number | null
  runs?: { id: number; model_type: string; status: string; duration_s: number | null; pr_auc_cv: number | null; pr_auc_test: number | null }[]
  result?: any; log?: string
}
export interface DatasetMeta {
  name: string; description: string; provenance: string; license: string; label_map: Record<string, string>
  unit: 'flow' | 'window'; window_minutes: number; group_key: 'src_ip' | 'src_dst' | 'time_block'; time_block_seconds: number; notes: string; span_minutes?: number
}
export interface DatasetVersion { id: number; version: number; change_note: string; created_by: string; created_at: string; content_hash: string; meta: DatasetMeta }
export interface Dataset {
  id: number; name: string; origin: 'source' | 'upload'; source_id: number | null; n_rows: number; n_duplicates_dropped: number
  current_version: number; current_version_id: number; created_by: string; created_at: string; meta: DatasetMeta; snapshot_sha256: string
  versions?: DatasetVersion[]
}
export interface Summary { n_rows: number; n_labeled: number; n_botnet: number; n_normal: number; n_excluded: number; figures: Spec[]; tables: Spec[] }
export interface KeyValidation {
  group_key: string; label: string; viable: boolean; blocking: string[]; warnings: string[]; applicable?: boolean
  class_stats?: { Botnet: { rows: number; groups: number }; Normal: { rows: number; groups: number } }
  interpretation?: Interp
}
export interface Validation {
  chosen: string; recommended: string | null; recommended_block_seconds: number | null; keys: Record<string, KeyValidation>
  time_block_options: { seconds: number; viable: boolean; groups_botnet: number; groups_normal: number; problem: string | null }[]
  n_rows: number; n_botnet: number; n_normal: number; n_hosts_botnet: number; n_hosts_normal: number; unit: string
  interpretation: Interp; interpretation_global: Interp; partition_table: Spec
}
export interface SpaceParam { name: string; type: 'int' | 'float' | 'categorical'; low?: number; high?: number; step?: number; log?: boolean; hard?: [number, number]; choices?: string[]; hard_choices?: string[]; why: string }
export interface ModelSpace { model: string; label: string; params: SpaceParam[]; fixed: Record<string, unknown> }
export interface MlModel {
  id: number; run_id: number; name: string; model_type: string; unit: string; window_minutes: number | null; threshold: number
  calibration_method: string; feature_spec_version: string; metrics: { cv: Record<string, { mean: number; std: number; ci_t: [number, number] }>; test: Record<string, number> }
  uncertainty: { alpha: number; coverage_test?: Record<string, number | boolean> }; is_baseline: boolean; is_active: boolean
  promoted_by: string | null; promoted_at: string | null; created_at: string; dataset_version_id: number; sha256: string; job_id: number | null
}
export interface Page<T> { items: T[]; total: number; page: number; page_size: number }
export type SpecList = { figures: Spec[]; tables: Spec[] }
export const MODEL_LABEL: Record<string, string> = {
  dummy: 'Línea base (Dummy)', logreg: 'Regresión logística', random_forest: 'Random Forest', hist_gb: 'HistGradientBoosting', xgboost: 'XGBoost',
}
export const STATUS_LABEL: Record<JobStatus, string> = {
  queued: 'En cola', running: 'En ejecución', cancel_requested: 'Cancelando', cancelled: 'Cancelado', failed: 'Con error', succeeded: 'Terminado',
}
export const METRIC_LABEL: Record<string, string> = { pr_auc: 'PR-AUC', roc_auc: 'ROC-AUC', f1: 'F1', mcc: 'MCC', brier: 'Brier', recall: 'Exhaustividad', precision: 'Precisión', accuracy: 'Exactitud', specificity: 'Especificidad', balanced_accuracy: 'Exactitud balanceada' }
