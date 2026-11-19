# NetSentinel — Contrato de API (fuente de verdad compartida)

Analista de logs de firewall/IDS para PYMEs (Caso 26). Este documento es el contrato entre
backend (FastAPI), frontend (React), y n8n. Si algo no está aquí, el backend decide y lo
refleja en `docs/openapi.json`; lo que SÍ está aquí no se cambia sin actualizar este archivo.

## Convenciones

- Base: `/api/v1`. JSON en `snake_case`. Fechas ISO-8601 UTC (`2026-11-11T16:00:00Z`).
- Auth: `Authorization: Bearer <access_token>` (JWT). Access 30 min, refresh 7 días.
- Llamadas de máquina (n8n): cabecera `X-API-Key: <N8N_API_KEY>` en lugar de JWT.
- Paginación: `?page=1&page_size=25&sort=-ts` → `{ "items": [...], "total": 0, "page": 1, "page_size": 25 }`.
- Errores: `{ "detail": "mensaje en español" }` con 400/401/403/404/409/422.
- 401 = token ausente/expirado (el frontend intenta refresh una vez). 403 = sin permiso.
- Rango temporal común: `?range=1h|24h|7d|30d` o `?date_from=&date_to=` (tienen prioridad).
- Los textos visibles para el usuario van en español. Identificadores y enums en inglés.

## Puertos (docker compose)

| Servicio | Host | Interno |
|---|---|---|
| frontend (nginx) | 5173 | 80 — hace proxy de `/api` a `backend:8000` |
| backend | 8000 | 8000 |
| db (PostgreSQL 16) | 5433 | 5432 |
| n8n | 5678 | 5678 |
| ollama | 11434 | 11434 |

## Permisos (RBAC)

Permiso = `"<module>:<action>"`. Módulos: `dashboard, logs, findings, alerts, reports, assets,
sources, lists, ingestion, detection, llm, users, roles, audit, ml_data, ml_training, ml_evaluation,
ml_explain, ml_inference, ml_optuna`. Acciones: `view, create,
update, delete, export, execute`.

Roles semilla: `admin` (todo), `analyst` (operación: ver todo lo operativo, gestionar
hallazgos/alertas, ejecutar ingesta, exportar reportes), `auditor` (solo lectura + bitácora
+ reportes), `manager` (dashboard + reportes de gestión). El rol `admin` no se puede borrar.

## Enums

- `finding_type`: `beaconing | unusual_port | exfiltration | ids_alert | talker_anomaly`
- `severity`: `critical | high | medium | low | info`
- `finding_status`: `new | in_review | confirmed | false_positive | closed`
- `llm_verdict`: `real | noise | uncertain` (null si el LLM no respondió)
- `log_type`: `firewall | ids | flow`
- `log_action`: `pass | block | alert`
- `direction`: `outbound | inbound | internal`
- `source_format`: `opnsense_filterlog | suricata_eve | ctu13_binetflow`
- `audit_event_type`: `login | logout | login_failed | module_enter | module_exit | create | update | delete | export | execute`
- `alert_channel`: `in_app | email | webhook`
- `report_format`: `pdf | docx | xlsx`

## Objetos

```jsonc
// UserMe (login y /auth/me)
{ "id": 1, "username": "admin", "email": "a@b.c", "full_name": "Administrador",
  "is_active": true, "must_change_password": false, "last_login_at": "...",
  "role": { "id": 1, "name": "admin", "description": "..." },
  "profile": { "job_title": "", "department": "", "phone": "", "avatar_color": "#3b82f6",
               "theme": "system", "language": "es", "timezone": "America/Lima" },
  "permissions": ["dashboard:view", "..."] }

// User (listado)  = UserMe sin permissions, + created_at
// Role
{ "id": 1, "name": "analyst", "description": "", "is_system": true,
  "permissions": ["findings:view"], "user_count": 3 }

// FirewallLog
{ "id": 1, "ts": "...", "source_id": 1, "source_name": "OPNsense LAN", "log_type": "flow",
  "action": "pass", "proto": "tcp", "src_ip": "10.0.0.5", "src_port": 51234,
  "dst_ip": "8.8.8.8", "dst_port": 443, "direction": "outbound",
  "bytes_out": 1200, "bytes_in": 5400, "packets": 12, "duration": 1.2,
  "signature": null, "signature_id": null, "category": null, "ids_severity": null,
  "label": null, "raw": { } }

// Finding
{ "id": 1, "created_at": "...", "first_seen": "...", "last_seen": "...", "occurrences": 3,
  "finding_type": "beaconing", "severity": "high", "score": 87.5, "status": "new",
  "title": "Beaconing regular hacia 185.1.2.3:443",
  "src_ip": "10.0.0.5", "dst_ip": "185.1.2.3", "dst_port": 443, "proto": "tcp",
  "window_start": "...", "window_end": "...",
  "evidence": { },            // métricas deterministas (ver Detectores)
  "llm_verdict": "real", "llm_confidence": 0.82, "is_noise": false,
  "llm_explanation": "…", "llm_recommendation": "…", "llm_model": "llama3.2:3b",
  "assigned_to": { "id": 2, "full_name": "..." },   // o null
  "comments": [ { "id": 1, "author": "Ana", "body": "…", "created_at": "..." } ] } // solo en detalle

// Alert
{ "id": 1, "created_at": "...", "finding_id": 1, "rule_id": 1, "severity": "high",
  "title": "...", "message": "...", "channel": "in_app", "delivered": true,
  "acknowledged_at": null, "acknowledged_by": null }

// AlertRule
{ "id": 1, "name": "Críticos y altos", "enabled": true, "min_severity": "high",
  "finding_types": ["beaconing","exfiltration"], "channels": ["in_app","webhook"],
  "webhook_url": null, "email_to": null, "include_noise": false }

// Source
{ "id": 1, "name": "OPNsense LAN", "format": "opnsense_filterlog", "description": "",
  "enabled": true, "last_ingest_at": null, "log_count": 0 }

// Asset
{ "id": 1, "ip": "10.0.0.5", "hostname": "pc-contab", "owner": "", "asset_type": "workstation",
  "criticality": "medium", "expected_ports": [80,443,53], "notes": "" }

// ListEntry
{ "id": 1, "list_type": "allow", "kind": "ip", "value": "8.8.8.8", "note": "", "created_at": "..." }
//   list_type: allow|deny ; kind: ip|cidr|port|domain

// IngestRun
{ "id": 1, "started_at": "...", "finished_at": "...", "status": "success", // running|success|error
  "trigger": "n8n", // n8n|upload|manual|dataset
  "source_id": 1, "source_name": "...", "filename": null,
  "lines_read": 0, "logs_inserted": 0, "parse_errors": 0, "findings_created": 0,
  "findings_noise": 0, "error": null }

// AuditEvent
{ "id": 1, "ts": "...", "user_id": 1, "username": "admin", "event_type": "module_enter",
  "module": "findings", "entity": null, "entity_id": null, "description": "…",
  "ip": "…", "user_agent": "…", "details": { } }

// ModuleSession (un usuario entró y salió de un módulo)
{ "id": 1, "user_id": 1, "username": "admin", "module": "findings", "entered_at": "...",
  "exited_at": null, "duration_seconds": null, "ip": "…", "exit_reason": null } // navigation|logout|timeout|close
```

## Endpoints

### Salud
- `GET /health` → `{ "status": "ok", "db": true, "llm": true|false, "version": "1.0.0" }` (sin auth)

### Auth
- `POST /auth/login` `{username, password}` → `{access_token, refresh_token, token_type:"bearer", user: UserMe}`.
  5 intentos fallidos → bloqueo 15 min (423 no; usar 403 con detail claro).
- `POST /auth/refresh` `{refresh_token}` → `{access_token, refresh_token}`
- `POST /auth/logout` → 204 (cierra sesiones de módulo abiertas, registra `logout`)
- `GET /auth/me` → UserMe
- `PUT /auth/me/profile` (campos de profile + full_name, email) → UserMe
- `POST /auth/me/password` `{current_password, new_password}` → 204

### Usuarios, roles, perfiles
- `GET /users` (`?q=&role_id=&is_active=`, paginado) · `POST /users` `{username,email,full_name,password,role_id,is_active,profile?}` ·
  `GET/PUT/DELETE /users/{id}` · `POST /users/{id}/reset-password` `{new_password}` → 204
- `GET /roles` (lista completa, sin paginar) · `POST /roles` `{name,description,permissions[]}` · `GET/PUT/DELETE /roles/{id}`
- `GET /permissions` → `{ "modules": [ { "code": "findings", "label": "Hallazgos", "actions": ["view","update","export"] } ] }`

### Bitácora (auditoría)
- `POST /audit/module-enter` `{module}` → `{session_id}` (cierra automáticamente la sesión de módulo abierta anterior del mismo usuario como `navigation`)
- `POST /audit/module-exit` `{session_id, reason?}` → 204 (el frontend lo llama con `fetch(..., {keepalive:true})` al cambiar de módulo o cerrar pestaña)
- `GET /audit/events` (`?user_id=&event_type=&module=&q=`, rango, paginado) → AuditEvent
- `GET /audit/module-sessions` (`?user_id=&module=`, rango, paginado) → ModuleSession
- `GET /audit/summary` (rango) → `{ "by_module": [{module, visits, total_seconds}], "by_user": [{username, visits, total_seconds, last_seen}], "by_event_type": [{event_type, count}] }`
- La bitácora es de solo inserción: no hay PUT/DELETE.

### Dashboard (todos aceptan rango)
- `GET /dashboard/summary` → `{ "total_logs", "total_bytes_out", "total_bytes_in", "unique_sources", "unique_destinations",
  "blocked_connections", "open_findings", "critical_findings", "noise_filtered", "noise_ratio", "alerts_unacknowledged",
  "last_ingest_at", "deltas": { "total_logs": 12.5, "open_findings": -3.0 } }` (delta % vs período anterior)
- `GET /dashboard/traffic-timeseries` (`?bucket=auto|5m|1h|1d`) → `[ { "ts", "bytes_out", "bytes_in", "connections", "blocked" } ]`
- `GET /dashboard/top-talkers` (`?metric=bytes|connections|destinations&limit=10&direction=outbound`) →
  `[ { "ip", "hostname", "bytes_out", "bytes_in", "connections", "unique_destinations", "findings" } ]`
- `GET /dashboard/top-destinations` (`?limit=10`) → `[ { "ip", "bytes", "connections", "unique_sources", "in_denylist" } ]`
- `GET /dashboard/top-ports` (`?limit=10`) → `[ { "port", "proto", "service", "connections", "bytes", "unusual" } ]`
- `GET /dashboard/findings-by-severity` → `[ { "severity", "count" } ]`
- `GET /dashboard/findings-by-type` → `[ { "finding_type", "count", "noise" } ]`
- `GET /dashboard/findings-timeseries` → `[ { "ts", "real", "noise" } ]`
- `GET /dashboard/flows` (`?limit=30`) → `[ { "src_ip", "dst_ip", "dst_port", "bytes", "connections" } ]`
- `GET /dashboard/recent-findings` (`?limit=8`) → `[Finding]` (sin comments, excluye ruido)

### Logs
- `GET /logs` (`?q=&src_ip=&dst_ip=&dst_port=&proto=&action=&log_type=&direction=&source_id=`, rango, paginado) → FirewallLog
- `GET /logs/{id}` → FirewallLog

### Hallazgos
- `GET /findings` (`?finding_type=&severity=&status=&is_noise=false&src_ip=&dst_ip=&assigned_to_id=&q=`, rango, paginado)
- `GET /findings/{id}` → Finding con comments
- `PATCH /findings/{id}` `{status?, severity?, assigned_to_id?, is_noise?}` → Finding
- `POST /findings/{id}/comments` `{body}` → Finding
- `POST /findings/{id}/reanalyze` → Finding (vuelve a pasar por la cadena LangChain)
- `GET /findings/{id}/related-logs` (paginado) → FirewallLog

### Alertas
- `GET /alerts` (`?acknowledged=&severity=`, rango, paginado) · `GET /alerts/unread-count` → `{count}`
- `POST /alerts/{id}/ack` → Alert · `POST /alerts/ack-all` → `{acknowledged}`
- `GET/POST /alert-rules` · `GET/PUT/DELETE /alert-rules/{id}`

### Ingesta y detección
- `POST /ingest/upload` multipart `file`, `source_id`, `run_detection=true` → IngestRun
- `POST /ingest/run` `{source_id?}` → IngestRun — lo llama n8n (X-API-Key) o un usuario con `ingestion:execute`.
  Lee archivos nuevos de `INGEST_DIR/<source_id>/` y luego ejecuta detección.
- `POST /detect/run` `{window_hours?: 24}` → `{findings_created, findings_updated, findings_noise, duration_ms}`
- `POST /ingest/dataset` `{rebase_time: true}` → IngestRun — importa el dataset demo desde `DATASET_DIR` si existe (404 si no)
- `GET /ingest/runs` (paginado) · `GET /ingest/status` → `{ "last_run": IngestRun|null, "dataset_available": bool, "dataset_loaded": bool, "pending_files": 0 }`
- `GET /alerts/pending-dispatch` (X-API-Key) → `[Alert]` webhook/email no entregadas · `POST /alerts/{id}/delivered` (X-API-Key) → 204

### Catálogos y configuración
- `GET/POST /sources` · `GET/PUT/DELETE /sources/{id}`
- `GET/POST /assets` (paginado, `?q=`) · `GET/PUT/DELETE /assets/{id}`
- `GET/POST /lists` (`?list_type=&kind=&q=`, paginado) · `DELETE /lists/{id}`
- `GET/PUT /settings/detection` → `{ "beacon_min_connections": 10, "beacon_max_cv": 0.25, "beacon_min_score": 60,
  "exfil_zscore": 3.0, "exfil_min_bytes": 52428800, "common_ports": [53,80,123,443,...],
  "unusual_port_min_connections": 3, "internal_cidrs": ["10.0.0.0/8","172.16.0.0/12","192.168.0.0/16"],
  "detection_window_hours": 24 }`
- `GET/PUT /settings/llm` → `{ "enabled": true, "base_url": "http://ollama:11434", "model": "llama3.2:3b",
  "temperature": 0.1, "timeout_seconds": 60, "noise_confidence_threshold": 0.7 }`
- `POST /settings/llm/test` → `{ "ok": bool, "model": "...", "latency_ms": 0, "message": "..." }`
- `GET/PUT /settings/retention` → `{ "logs_days": 90, "findings_days": 365, "audit_days": 730 }`

### Reportes
- `GET /reports/catalog` → `[ { "code", "name", "description", "category": "operational|management|ml", "formats": ["pdf","docx","xlsx"], "params": ["job_id"] } ]`
- `POST /reports/generate` `{report_code, format, date_from, date_to, params?}` → archivo binario
  (`Content-Disposition: attachment; filename="..."`). Registra `export` en bitácora.
- `GET /reports/history` (paginado) → `[ { "id", "report_code", "report_name", "format", "date_from", "date_to", "generated_by", "generated_at", "size_bytes" } ]`

Códigos de reporte — operacionales: `op_findings` (hallazgos del período), `op_top_talkers`,
`op_beaconing`, `op_unusual_ports`, `op_ids_alerts`, `op_ingestion`, `op_audit_log` (bitácora).
De gestión: `mg_executive_summary`, `mg_trends`, `mg_response_metrics` (MTTA/MTTR, tasa de
falsos positivos, eficacia del filtro de ruido), `mg_user_activity`, `mg_risk_by_asset`.

### Laboratorio ML

Clasificación binaria supervisada **Botnet vs Normal** sobre CTU-13 (escenario 11). Los flujos *Background* se
excluyen del entrenamiento y la evaluación (no tienen verdad conocida); solo se puntúan en inferencia.
Prefijo `/ml`. Permisos por módulo: `ml_data`, `ml_training`, `ml_evaluation`, `ml_explain`, `ml_inference`,
`ml_optuna` (admin: todo; analista: ver todo + ejecutar inferencia + exportar; auditor: solo lectura;
gerente: ver evaluación y reportes). Todas las acciones de crear/editar/lanzar/cancelar/promover/exportar
quedan en la bitácora; la entrada y salida de cada módulo la registra el rastreador del frontend.

**Contrato común de figuras y tablas** (lo dibuja React en pantalla y matplotlib a 600 DPI en reportes/exportación):
`{ "id", "kind": "bars|lines|dots|heatmap|swarm|waterfall|parcoords|table", "title", "note", "data",
"interpretation": { "meaning": ["..."], "caution": ["..."] } }`. Las tablas llevan `columns: [{key,label}]` y
`rows: [{}]`. `meaning` (1-3 frases) y `caution` se generan con los valores reales; no hay textos fijos.

**Trabajos** (`ml_jobs`): `{ id, kind: train|evaluate|explain|optimize, status: queued|running|cancel_requested|cancelled|failed|succeeded,
name, params, progress, resources: {pid, rss_mb, cpu_percent, ...}, error, attempts, seed, libs, created_by, created_at, started_at,
finished_at, heartbeat_at, dataset_version_id, time_limit_s }`. Los ejecuta el servicio `ml-worker`
(misma imagen, `python -m app.ml.worker`) lanzando `python -m app.ml.scripts.{train,evaluate,explain,optimize} --job-id N`.
El monitoreo es por *polling* corto (2-3 s) sobre `GET /ml/training/jobs/{id}` y `.../log?since=N`.

#### Fase 1 · Datos (`/ml/data`, módulo `ml_data`)
- `GET /ml/data/sources` fuentes ingeridas elegibles · `GET /ml/data/datasets` · `GET /ml/data/datasets/{id}`
- `POST /ml/data/datasets` `{name, source_id, description?, unit?: flow|window, window_minutes?, group_key?: src_ip|src_dst|time_block, time_block_seconds?}`
- `POST /ml/data/datasets/upload` (multipart: `file`, `name`, `description`) archivo etiquetado `.binetflow|.csv|.txt|.gz`, tamaño máx. `ML_MAX_UPLOAD_MB`; se valida y no se descarga nada de Internet.
- `PUT /ml/data/datasets/{id}` `{note, name?, description?, provenance?, license?, label_map?, unit?, window_minutes?, group_key?, time_block_seconds?, notes?}` crea una **versión inmutable** nueva.
- `DELETE /ml/data/datasets/{id}` (409 si tiene modelos)
- `GET /ml/data/versions/{vid}/summary[?refresh=true]` → `{ n_rows, n_labeled, n_botnet, n_normal, n_excluded, figures[], tables[] }`
- `GET /ml/data/versions/{vid}/validation[?refresh=true]` → validador de grupos: `{ keys: {src_ip|src_dst|time_block: {viable, blocking[], class_stats, partition...}}, recommended, recommended_block_seconds, n_hosts_botnet, interpretation_global, partition_table }`
- `GET /ml/data/feature-spec?unit=&window_minutes=` definición versionada de variables (sin IP, ids, marca de tiempo absoluta ni etiqueta).

#### Fase 2 · Entrenamiento (`/ml/training`, módulo `ml_training`)
- `GET /ml/training/spaces` espacios de búsqueda editables, límites duros y justificación por hiperparámetro.
- `POST /ml/training/jobs` `{dataset_version_id, models:[{type: dummy|logreg|random_forest|hist_gb|xgboost, n_trials?, space?}], metric, n_outer=5, n_inner=3, n_trials, seed, sampler: tpe|random|cmaes, pruner: median|hyperband|none, time_limit_s?, from_study?}`.
  **422 si la agrupación elegida es inviable** para 5×3 pliegues (p. ej. por host con 3 hosts Botnet), con la recomendación.
- `GET /ml/training/jobs[?kind=&status=]` (paginado) · `GET /ml/training/jobs/{id}` · `GET /ml/training/jobs/{id}/log?since=N`
- `POST /ml/training/jobs/{id}/cancel` · `POST /ml/training/jobs/{id}/retry`
- `GET /ml/training/jobs/{id}/analysis` figuras y tablas (dispersión entre pliegues, optimismo interno/externo, estabilidad de hiperparámetros, convergencia, partición).
- `GET /ml/training/runs/{run_id}` ejecución: `config, summary:{cv:{metric:{mean,std,ci_t,ci_boot,values,n}}}, test_metrics, folds[], final_params, artifact_dir`.

#### Fase 3 · Evaluación (`/ml/evaluation`, módulo `ml_evaluation`)
- `GET /ml/evaluation/models` · `POST /ml/evaluation/evaluations` `{job_id | run_ids}` (Friedman, Wilcoxon+Holm, McNemar, bootstrap pareado por grupos, tamaños de efecto, línea base y detectores deterministas sobre la misma partición de Prueba) · `GET /ml/evaluation/evaluations/{job_id}`
- `GET /ml/evaluation/runs/{run_id}/confusion?threshold=` matrices absoluta y normalizada en Prueba y barrido de umbral.
- `POST /ml/evaluation/models/{id}/promote` (módulo `ml_evaluation:update`, auditado) · `POST /ml/evaluation/models/deactivate`

#### Fase 4 · Explicabilidad (`/ml/explain`, módulo `ml_explain`)
- `POST /ml/explain/jobs` `{model_id, force?}` (SHAP global/local, permutación como contraste con discrepancias, mapas host×tiempo y variable×tiempo, PDP/ICE, oclusión, estabilidad Kendall) · `GET /ml/explain/models/{model_id}` último resultado.

#### Fase 6 · Inferencia (`/ml/inference`, módulo `ml_inference`)
- `GET /ml/inference/active` → `{ model, pipeline_enabled }` · `PUT /ml/inference/pipeline` `{enabled}` (permiso `detection:update`; apagado por defecto; auditado). Con el interruptor encendido y un modelo activo, los hallazgos nuevos reciben `evidence.ml = { ml_probability, interval, model, model_id, model_version, predicted_class, severity_ml, top_factors[], ood }` y el LLM lo recibe como contexto.
- `GET/PUT /ml/inference/severity-config` regla de severidad configurable (pesos, umbrales, penalización por incertidumbre, criticidad del activo, tope por fuera de distribución).
- `POST /ml/inference/predict` `{model_id?, kind: flow|window|finding|manual, log_id?|src_ip?+window_end?+minutes?|finding_id?|values?}` → `{ probability, interval, set, predicted_class, threshold, ood, severity, severity_steps[], contributions, narrative, narrative_source: template|llm }`. La narrativa se genera después, bajo demanda: `POST /ml/inference/predictions/{id}/narrative` (la cadena LangChain/Ollama recibe solo cifras calculadas y degrada a plantilla determinista).
- `GET /ml/inference/predictions` (paginado; filtros `model_id, kind, severity`) · `GET /ml/inference/predictions/{id}` · `GET /ml/inference/models/{id}/uncertainty` (cobertura conforme verificada en Prueba).

#### Fase 7 · Optuna (`/ml/optuna`, módulo `ml_optuna`)
- `GET /ml/optuna/options` · `POST /ml/optuna/studies` `{dataset_version_id, model_type, space?, n_trials, timeout_s?, sampler, pruner, metric, direction, seed, n_folds}` · `GET /ml/optuna/studies` · `GET /ml/optuna/studies/{id}` (tabla de trials en vivo) · `GET /ml/optuna/studies/{id}/viz` (historial, importancia fANOVA, coordenadas paralelas, cortes, contorno, línea de tiempo: JSON en el contrato de figuras) · `GET /ml/optuna/studies/{id}/best` (alimenta «Usar estos hiperparámetros» → Entrenamiento `?study=`) · `DELETE /ml/optuna/studies/{id}`. Cancelar con `POST /ml/training/jobs/{id}/cancel`. Los estudios viven en PostgreSQL, esquema `optuna`.

#### Exportación de figuras
- `POST /ml/figures/export` `{spec: {kind, title, data}, format: png|svg, module}` → imagen (PNG a 600 DPI con metadatos pHYs, o SVG). Auditado como `export`.

#### Reportes ML (Fase 5)
Códigos con `category: "ml"` y `params` requeridos en `POST /reports/generate`: `ml_dataset` (`dataset_version_id`), `ml_training` (`job_id`),
`ml_evaluation` (`job_id`), `ml_explainability` (`model_id`), `ml_inference` (período; `model_id` opcional), `ml_model_card` (`model_id`).
Todas las figuras de **todos** los reportes (también los existentes) se incrustan a 600 DPI.

## Detectores (campo `evidence`)

- `beaconing`: `{ connections, mean_interval_s, stdev_interval_s, cv, mean_bytes, bytes_cv, duration_h, intervals_sample: [..] }`
- `unusual_port`: `{ port, service, connections, bytes, distinct_sources, in_baseline: false, first_seen }`
- `exfiltration`: `{ bytes_out, baseline_mean, baseline_stdev, zscore, ratio_out_in, top_destinations: [{ip, bytes}] }`
- `ids_alert`: `{ signature, signature_id, category, ids_severity, count, distinct_sources }`
- `talker_anomaly`: `{ metric, value, baseline_mean, zscore, unique_destinations }`
