# NetSentinel — backend

API FastAPI que ingiere logs de firewall/IDS (OPNsense/pfSense, Suricata EVE, CTU-13), ejecuta detectores
deterministas (beaconing, puertos inusuales, exfiltración, alertas IDS, anomalía de top talkers), pasa cada
hallazgo por una cadena LangChain/Ollama (descarta ruido y explica en español) y genera alertas, bitácora y reportes
PDF/Word/Excel. Contrato: `docs/API_CONTRACT.md`; esquema generado: `docs/openapi.json`.

## Estructura

```
app/
  core/        config (pydantic-settings), seguridad (Argon2/JWT), RBAC, deps (auth + auditoría), paginación, rangos
  db/          base y tipos, sesión, semilla idempotente, espera de BD, funciones SQL portables
  models/      SQLAlchemy 2 (usuarios/roles, catálogos, logs, hallazgos/alertas, auditoría)
  schemas/     Pydantic v2
  api/routers/ un router por área (todos bajo /api/v1)
  services/
    parsers/    opnsense_filterlog, suricata_eve, ctu13_binetflow (+ clasificación de dirección)
    detectors/  módulo puro (sin BD) + queries.py con las agregaciones SQL
    llm/        cadena ChatOllama con salida validada, plantillas deterministas, salud de Ollama
    alerts/     evaluación de reglas   audit/  bitácora y sesiones de módulo   reports/  modelo común + 3 renderizadores
    pipeline.py ingest.py maintenance.py settings_service.py
  ml/          Laboratorio ML: features sin fuga, grupos, validador, CV anidada, Optuna, métricas, pruebas estadísticas,
               incertidumbre (conforme/OOD), SHAP, figuras (matplotlib 600 DPI), cola de trabajos y worker (python -m app.ml.worker)
alembic/       migraciones 0001 (inicial) y 0002 (Laboratorio ML)      scripts/export_openapi.py
tests/         pytest (SQLite para unitarias/API; fixtures reales pequeños en tests/fixtures)
```

## Pruebas

```bash
uv sync
uv run pytest
```

Las pruebas usan SQLite temporal y no requieren servicios externos (Ollama caído = modo degradado).
Regenerar el esquema: `uv run python scripts/export_openapi.py`.

## Ejecución

```bash
export DATABASE_URL=postgresql://netsentinel:netsentinel@localhost:5433/netsentinel JWT_SECRET=... ADMIN_PASSWORD=...
uv run alembic upgrade head && uv run python -m app.db.seed
uv run uvicorn app.main:app --port 8000      # docs en /api/v1/docs
```

La imagen Docker ejecuta migraciones, semilla y uvicorn (0.0.0.0:8000) al arrancar.

## Variables de entorno

| Variable | Defecto | Notas |
|---|---|---|
| `JWT_SECRET` | — | **Obligatoria** (usar >= 32 caracteres) |
| `ADMIN_PASSWORD` | — | **Obligatoria** (admin inicial; no se sobrescribe si ya existe) |
| `DATABASE_URL` | `postgresql+psycopg://netsentinel:netsentinel@db:5432/netsentinel` | acepta `postgresql://` |
| `N8N_API_KEY` | vacío | cabecera `X-API-Key`; vacía = integración n8n deshabilitada |
| `ADMIN_USERNAME` / `ADMIN_EMAIL` | `admin` / `admin@netsentinel.local` | |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | `http://ollama:11434` / `llama3.2:3b` | valores iniciales de `/settings/llm` |
| `INGEST_DIR` | `/data/ingest` | `INGEST_DIR/<source_id>/` por fuente |
| `DATASET_DIR` | `/data/dataset` | `*.binetflow` / `*.csv` de CTU-13 |
| `REPORTS_DIR` | `/data/reports` | copia de cada reporte generado |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | separadas por coma |
| `LLM_MAX_FINDINGS_PER_RUN` | `30` | tope inicial de hallazgos enviados al LLM por ejecución |

## Decisiones de diseño

- SQLAlchemy sync + psycopg 3; la carga masiva usa `COPY` en PostgreSQL.
- Los detectores son funciones puras sobre agregaciones; el LLM solo clasifica/explica (nunca calcula métricas).
- La ventana de detección se ancla al último registro ingerido (funciona con datos históricos y con el dataset rebasado).
- Los hallazgos se deduplican por `dedup_key`; `occurrences` solo crece cuando llegan datos más nuevos.
- Bitácora de solo inserción: sin rutas PUT/DELETE y trigger en PostgreSQL que bloquea UPDATE/DELETE
  (la purga de retención lo habilita solo dentro de su transacción).

## Laboratorio ML

- Routers `ml_data`, `ml_training`, `ml_evaluation`, `ml_explain`, `ml_inference`, `ml_optuna`, `ml_figures`; seis módulos RBAC nuevos (`ml_*`).
- Trabajos largos en la tabla `ml_jobs`; el servicio `ml-worker` los toma y lanza `python -m app.ml.scripts.{train,evaluate,explain,optimize} --job-id N`.
  El monitor usa sondeo corto (3 s): un solo sentido servidor-cliente, sin estado de conexión y reanudable tras reinicios.
- Optuna guarda los estudios en el esquema `optuna` de PostgreSQL. Los modelos son archivos joblib en `ML_DIR` (`/data/ml`) con sha256 verificado;
  nunca se deserializa un modelo subido por el usuario.
- Mismo contrato de figura/tabla `{id, kind, title, note, data, interpretation}` para pantalla (SVG en React) y reportes/exportación (matplotlib, 600 DPI).
- La integración con el pipeline está apagada por defecto, usa un único modelo activo y falla en silencio hacia el flujo sin ML.
- Variables: `ML_DIR`, `ML_N_JOBS`. Contrato completo en `docs/API_CONTRACT.md`.
