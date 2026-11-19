// Laboratorio ML simulado (VITE_MOCK=1). Datos sintéticos conformes al contrato; SOLO desarrollo.
const json = (data: unknown, status = 200) => new Response(status === 204 ? null : JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } })
const err = (status: number, detail: string) => json({ detail }, status)
const iso = (t: number) => new Date(t).toISOString()
const T0 = Date.now()
const ip = (meaning: string[], caution: string[] = []) => ({ meaning, caution })
const fig = (id: string, kind: string, title: string, data: unknown, note: string, i: ReturnType<typeof ip>) => ({ id, kind, title, note, data, interpretation: i })
const table = (id: string, title: string, columns: [string, string][], rows: Record<string, unknown>[], note: string, i: ReturnType<typeof ip>) => ({ id, kind: 'table', title, note, columns: columns.map(([key, label]) => ({ key, label })), rows, interpretation: i })
const pageOf = <T,>(items: T[], p: URLSearchParams) => { const pg = Number(p.get('page') || 1), ps = Number(p.get('page_size') || 25); return { items: items.slice((pg - 1) * ps, pg * ps), total: items.length, page: pg, page_size: ps } }
const rnd = (seed: number) => { let s = seed; return () => { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646 } }
const MODEL_ES: Record<string, string> = { dummy: 'Línea base (Dummy)', logreg: 'Regresión logística', random_forest: 'Random Forest', hist_gb: 'HistGradientBoosting', xgboost: 'XGBoost' }

const META = { name: 'CTU-13 escenario 11 (flujos)', description: 'Fuente «CTU-13 Dataset» (#3)', provenance: 'CTU-13, escenario 11 (botnet Rbot). Stratosphere Laboratory, CTU University (Praga).', license: 'Uso libre citando: García, S., Grill, M., Stiborek, J., Zunino, A. (2014). Computers & Security 45.', label_map: { 'flow=From-Botnet-V52-1-ICMP': 'Botnet', 'flow=From-Normal-V52-Grill': 'Normal', 'flow=Background': 'excluded' } as Record<string, string>, unit: 'flow', window_minutes: 0.25, group_key: 'time_block', time_block_seconds: 10, notes: '', span_minutes: 16 }
const versions = [
  { id: 1, version: 1, change_note: 'Versión inicial', created_by: 'Administrador TI', created_at: iso(T0 - 3 * 86400e3), content_hash: 'a41f0c9e2b77d013', meta: { ...META, group_key: 'src_ip' } },
  { id: 2, version: 2, change_note: 'Prueba de bloqueo', created_by: 'Administrador TI', created_at: iso(T0 - 2 * 86400e3), content_hash: 'b25c81d0ee4a9f12', meta: { ...META, group_key: 'src_ip' } },
  { id: 3, version: 3, change_note: 'Agrupación recomendada: bloque temporal', created_by: 'Administrador TI', created_at: iso(T0 - 86400e3), content_hash: 'c9d03e7a51b6f8e4', meta: META },
]
const dataset = () => ({ id: 1, name: META.name, origin: 'source', source_id: 3, n_rows: 107194, n_duplicates_dropped: 107194, current_version: 3, current_version_id: 3, created_by: 'Administrador TI', created_at: iso(T0 - 3 * 86400e3), meta: META, snapshot_sha256: '5be0c1e3a9d77f2c4a1b0e8d6c3f9a2e7b1d4c5f8a0e3b6d9c2f1a4e7b0d3c6f' })

const validation = () => {
  const mk = (g: string, label: string, viable: boolean, b: number, n: number, why: string[]) => ({ group_key: g, label, viable, blocking: why, warnings: [], applicable: true, class_stats: { Botnet: { rows: 8164, groups: b }, Normal: { rows: 2718, groups: n } } })
  return {
    chosen: META.group_key, recommended: 'time_block', recommended_block_seconds: 10,
    keys: {
      src_ip: mk('src_ip', 'Host origen', false, 3, 15, ['Hay 3 grupo(s) de Botnet y 15 de Normal; se necesitan al menos 8 de cada clase (5 pliegues externos sobre el 70 % de Desarrollo, y 3 internos dentro de cada uno).', 'La partición Prueba se queda sin grupos de Botnet.']),
      src_dst: mk('src_dst', 'Par origen-destino', false, 11, 190, ['La partición Validación solo tiene 10 filas de Botnet (mínimo 30 para estimar métricas); los grupos son demasiado grandes.']),
      time_block: mk('time_block', 'Bloque temporal', true, 19, 97, []),
    },
    time_block_options: [5, 10, 15, 30, 60].map((s, i) => ({ seconds: s, viable: i < 2, groups_botnet: [32, 19, 14, 9, 5][i], groups_normal: [151, 97, 65, 33, 17][i], problem: i < 2 ? null : 'Pliegue interno con una sola clase' })),
    n_rows: 10882, n_botnet: 8164, n_normal: 2718, n_hosts_botnet: 3, n_hosts_normal: 15, unit: 'flow',
    interpretation: ip(['La agrupación elegida es viable.']),
    interpretation_global: ip(['Solo 3 hosts generan flujos Botnet: agrupar por host NO permite 5 pliegues (cada pliegue necesita al menos un host Botnet distinto en validación y otro en entrenamiento).', 'Agrupación recomendada: «Bloque temporal» con bloques de 10 s. Es una validación MENOS exigente que por host y generaliza peor a hosts nuevos.']),
    partition_table: table('partition', 'Partición 70/15/15 por grupos', [['partition', 'Partición'], ['rows_botnet', 'Filas Botnet'], ['rows_normal', 'Filas Normal'], ['groups_botnet', 'Grupos Botnet'], ['groups_normal', 'Grupos Normal']],
      [{ partition: 'Desarrollo', rows_botnet: 5792, rows_normal: 1902, groups_botnet: 8, groups_normal: 66 }, { partition: 'Validación', rows_botnet: 1254, rows_normal: 409, groups_botnet: 3, groups_normal: 8 }, { partition: 'Prueba', rows_botnet: 1118, rows_normal: 407, groups_botnet: 8, groups_normal: 23 }],
      'n = 10 882 flujos etiquetados; ningún grupo aparece en dos particiones.', ip(['Cada partición contiene ambas clases y grupos distintos.'])),
  }
}
const summary = () => ({
  n_rows: 107194, n_labeled: 10882, n_botnet: 8164, n_normal: 2718, n_excluded: 96312,
  figures: [
    fig('classes', 'bars', 'Distribución de clases entre flujos etiquetados', { labels: ['Botnet', 'Normal', 'Excluidos (Background)'], series: [{ name: 'Flujos', values: [8164, 2718, 96312] }], ylabel: 'Flujos' }, 'n = 107 194 flujos únicos tras descartar duplicados de carga.', ip(['De 10 882 flujos con etiqueta conocida, 8 164 son Botnet (75,0 %) y 2 718 son Normal (25,0 %).', 'Un clasificador trivial que dijera siempre «Botnet» acertaría 75,0 % sin aprender nada.'], ['Datos de un solo escenario de CTU-13: los resultados no se pueden extrapolar a otras redes sin validarlos.'])),
    fig('proto', 'bars', 'Protocolos por clase', { labels: ['tcp', 'udp', 'icmp'], series: [{ name: 'Botnet', values: [5200, 2500, 464] }, { name: 'Normal', values: [2100, 500, 118] }], ylabel: 'Flujos' }, 'n = 10 882 flujos etiquetados.', ip(['El tráfico Botnet usa sobre todo TCP (63,7 %) y UDP (30,6 %).'])),
  ],
  tables: [table('class_comparison', 'Comparación de variables entre clases', [['feature', 'Variable'], ['botnet', 'Mediana Botnet'], ['normal', 'Mediana Normal'], ['ks', 'KS']], [{ feature: 'Bytes totales', botnet: 310, normal: 5200, ks: 0.82 }, { feature: 'Duración', botnet: 0.4, normal: 1.9, ks: 0.61 }], 'Prueba KS de dos muestras; n = 10 882.', ip(['Bytes totales separa las clases con KS = 0,82.'], ['Una separación tan alta anticipa que el problema es casi trivial.']))],
})

const params = (m: string) => {
  const sp: Record<string, unknown[]> = {
    logreg: [{ name: 'C', type: 'float', low: 0.001, high: 100, log: true, hard: [1e-6, 1e4], why: 'Inversa de la regularización; escala log porque su efecto es multiplicativo.' }, { name: 'class_weight', type: 'categorical', choices: ['none', 'balanced'], hard_choices: ['none', 'balanced'], why: 'Compensa el desbalance Botnet/Normal sin remuestrear.' }],
    random_forest: [{ name: 'n_estimators', type: 'int', low: 200, high: 800, step: 100, hard: [50, 1500], why: 'Más árboles reducen la varianza con rendimientos decrecientes.' }, { name: 'max_depth', type: 'int', low: 4, high: 30, hard: [2, 60], why: 'Controla el sobreajuste.' }, { name: 'class_weight', type: 'categorical', choices: ['none', 'balanced'], hard_choices: ['none', 'balanced', 'balanced_subsample'], why: 'Compensa el desbalance.' }],
    hist_gb: [{ name: 'learning_rate', type: 'float', low: 0.01, high: 0.3, log: true, hard: [0.001, 1], why: 'Tasa de aprendizaje: baja = más estable.' }, { name: 'max_depth', type: 'int', low: 3, high: 12, hard: [2, 30], why: 'Profundidad de cada árbol.' }],
    xgboost: [{ name: 'learning_rate', type: 'float', low: 0.01, high: 0.3, log: true, hard: [0.001, 1], why: 'Tasa de aprendizaje.' }, { name: 'max_depth', type: 'int', low: 3, high: 10, hard: [2, 20], why: 'Profundidad máxima.' }],
  }
  return { model: m, label: MODEL_ES[m], params: sp[m] ?? [], fixed: {} }
}

/* ------------------------------------------------------------ trabajos simulados (avanzan con el reloj) */
interface SimJob { id: number; kind: string; name: string; params: any; created: number; dur: number; cancelled?: boolean; user: string; seed: number }
const jobs: SimJob[] = [
  { id: 1, kind: 'train', name: 'Línea base (Dummy), Regresión logística, Random Forest · CTU-13 escenario 11 (flujos) v3', params: { metric: 'pr_auc', n_outer: 5, n_inner: 3, n_trials: 20, sampler: 'tpe', pruner: 'median', models: [{ type: 'dummy' }, { type: 'logreg' }, { type: 'random_forest' }] }, created: T0 - 3 * 3600e3, dur: 600e3, user: 'Administrador TI', seed: 42 },
  { id: 2, kind: 'optimize', name: 'Random Forest · CTU-13 escenario 11 (flujos) v3', params: { model_type: 'random_forest', metric: 'pr_auc', sampler: 'tpe', pruner: 'median', n_trials: 30, n_folds: 3 }, created: T0 - 2 * 3600e3, dur: 300e3, user: 'Administrador TI', seed: 42 },
]
let nextJob = 10
const status = (j: SimJob) => (j.cancelled ? 'cancelled' : Date.now() - j.created >= j.dur ? 'succeeded' : 'running')
const frac = (j: SimJob) => Math.min(1, (Date.now() - j.created) / j.dur)
const jobOut = (j: SimJob, log = false) => {
  const st = status(j), f = st === 'succeeded' ? 1 : frac(j)
  const total = j.kind === 'optimize' ? j.params.n_trials : 360
  const progress = j.kind === 'train'
    ? { unit: 'flow', phase: st === 'succeeded' ? 'done' : 'outer', eta_s: Math.round((1 - f) * j.dur / 1000), metric: 'pr_auc', units_total: total, units_done: Math.round(total * f), current: { model: 'random_forest', outer: 1 + Math.floor(f * 5) % 5, trial: 7, n_trials: 20 }, best_value: 0.998, elapsed_s: Math.round(f * j.dur / 1000), models: [] }
    : { eta_s: Math.round((1 - f) * j.dur / 1000), units_total: total, units_done: Math.round(total * f) }
  const ms = ['dummy', 'logreg', 'random_forest']
  const runs = j.kind === 'train' ? ms.map((m, i) => { const done = st === 'succeeded' || f > (i + 1) / 3; return { id: 10 + i, model_type: m, status: done ? 'succeeded' : f > i / 3 ? 'running' : 'pending', duration_s: done ? [1, 64, 420][i] : null, pr_auc_cv: done ? [0.47, 1, 0.999][i] : null, pr_auc_test: done ? [0.733, 0.995, 0.997][i] : null } }) : undefined
  return { id: j.id, kind: j.kind, status: st, name: j.name, params: j.params, progress, resources: st === 'running' ? { pid: 9, rss_mb: 412, cpu_count: 12, cpu_percent: 118, mem_total_mb: 16438 } : null, error: null, attempts: 1, seed: j.seed, libs: { 'scikit-learn': '1.9.0', optuna: '5.0.0', shap: '0.51.0' }, created_by: j.user, created_at: iso(j.created), started_at: iso(j.created + 5e3), finished_at: st === 'succeeded' ? iso(j.created + j.dur) : null, heartbeat_at: iso(Date.now()), dataset_version_id: 3, time_limit_s: 7200, ...(runs ? { runs } : {}), ...(log ? { log: '' } : {}), result: {} }
}

const FOLDS = [0, 1, 2, 3, 4]
const trainAnalysis = () => ({
  figures: [
    fig('dispersion', 'dots', 'Dispersión de PR-AUC entre pliegues externos', { groups: [{ name: 'Dummy', values: [0.47, 0.5, 0.44, 0.49, 0.46] }, { name: 'Regresión logística', values: [1, 1, 0.999, 1, 1] }, { name: 'Random Forest', values: [0.998, 0.999, 1, 0.997, 0.999] }], ylabel: 'PR-AUC' }, 'Una observación por pliegue externo (n = 5); la marca es la media.', ip(['Regresión logística: PR-AUC media 1,000 ± 0,000 entre 5 pliegues externos.', 'Random Forest: 0,999 ± 0,001.'], ['Con n = 5 pliegues el IC es amplio y poco fiable (cada pliegue cuenta como una sola observación).'])),
    fig('convergence', 'lines', 'Convergencia de la búsqueda interna (mejor valor hasta el trial)', { series: FOLDS.map((k) => ({ name: `Pliegue ${k + 1}`, x: Array.from({ length: 20 }, (_, i) => i), y: Array.from({ length: 20 }, (_, i) => 0.9 + 0.1 * (1 - Math.exp(-(i + 1) / (2 + k)))) })), xlabel: 'Trial', ylabel: 'PR-AUC interna', ylim: [0.85, 1.01] }, 'Random Forest, 20 trials por pliegue.', ip(['La búsqueda alcanza su mejor valor en los primeros 6 trials.'], ['Valores internos cercanos a 1,0 indican separabilidad casi trivial.'])),
  ],
  tables: [table('optimism', 'Optimismo: PR-AUC interna frente a externa', [['model', 'Modelo'], ['inner', 'Interna'], ['outer', 'Externa'], ['gap', 'Diferencia']], [{ model: 'Random Forest', inner: 0.9995, outer: 0.9990, gap: 0.0005 }], 'Media de 5 pliegues.', ip(['La diferencia es mínima: no hay señal de sobreajuste en la búsqueda.']))],
  runs: [{ run_id: 10, model_type: 'dummy', duration_s: 1, summary: {}, final_params: {}, test_metrics: { pr_auc: 0.733, f1: 0.846 } }, { run_id: 11, model_type: 'logreg', duration_s: 64, summary: {}, final_params: { C: 12.4, class_weight: 'balanced' }, test_metrics: { pr_auc: 0.995, f1: 0.99 } }, { run_id: 12, model_type: 'random_forest', duration_s: 420, summary: {}, final_params: { n_estimators: 400, max_depth: 14, class_weight: 'none' }, test_metrics: { pr_auc: 0.997, f1: 0.992 } }],
})

/* ------------------------------------------------------------ modelos y evaluación */
const cvm = (m: number, s: number) => ({ mean: m, std: s, ci_t: [m - 2.78 * s / Math.sqrt(5), Math.min(1, m + 2.78 * s / Math.sqrt(5))] })
const mkModel = (id: number, run: number, type: string, cv: number, sd: number, test: number, f1: number, base = false): any => ({
  id, run_id: run, name: `${MODEL_ES[type]} · job 1`, model_type: type, unit: 'flow', window_minutes: null, threshold: base ? 0.5 : 0.41, calibration_method: base ? 'none' : 'sigmoid', feature_spec_version: '1.0.0',
  metrics: { cv: { pr_auc: cvm(cv, sd), f1: cvm(f1, sd) }, test: { pr_auc: test, f1, roc_auc: base ? 0.5 : 0.999, precision: base ? 0.733 : 0.99, recall: base ? 1 : 0.99, brier: 0.01, n: 1525, n_pos: 1118 } },
  uncertainty: { alpha: 0.1, coverage_test: { nominal: 0.9, empirical_set: 0.93, meets_nominal: true, n: 1525, share_ambiguous: 0.02 } }, is_baseline: base, is_active: false, promoted_by: null, promoted_at: null, created_at: iso(T0 - 2.5 * 3600e3), dataset_version_id: 3, sha256: `${id}`.repeat(64).slice(0, 64), job_id: 1,
})
const models = [mkModel(1, 10, 'dummy', 0.47, 0.04, 0.733, 0.846, true), mkModel(2, 11, 'logreg', 1, 0, 0.995, 0.99), mkModel(3, 12, 'random_forest', 0.999, 0.001, 0.997, 0.992)]
const cm = (thr: number) => { const rec = Math.max(0, Math.min(1, 1.02 - thr * 0.04)), spec = Math.max(0, Math.min(1, 0.9 + thr * 0.1)); const tp = Math.round(1118 * rec), fn = 1118 - tp, tn = Math.round(407 * spec), fp = 407 - tn; return { tp, fn, tn, fp } }
const confusion = (thr: number) => {
  const c = cm(thr), rows = ['Normal real', 'Botnet real'], cols = ['Normal predicho', 'Botnet predicho']
  const sweep = Array.from({ length: 51 }, (_, i) => i / 50)
  return {
    threshold: thr, model_threshold: 0.41, metrics: { ...c, n: 1525, n_pos: 1118, recall: c.tp / 1118, precision: c.tp / Math.max(1, c.tp + c.fp) },
    figures: [
      fig('confusion_abs', 'heatmap', 'Matriz de confusión (absoluta)', { rows, cols, values: [[c.tn, c.fp], [c.fn, c.tp]], vlabel: 'Casos', scale: 'seq', vmin: 0, vmax: 1118, annotate: true, fmt: 'int' }, `Prueba, n = 1 525; umbral ${thr.toFixed(2).replace('.', ',')}.`, ip([`Con este umbral se detectan ${c.tp} de 1 118 flujos Botnet y hay ${c.fp} falsas alarmas.`])),
      fig('confusion_norm', 'heatmap', 'Matriz de confusión (normalizada por fila)', { rows, cols, values: [[c.tn / 407, c.fp / 407], [c.fn / 1118, c.tp / 1118]], vlabel: 'Proporción', scale: 'seq', vmin: 0, vmax: 1, annotate: true, fmt: 'pct' }, 'Cada fila suma 100 %.', ip(['La exhaustividad es la celda Botnet/Botnet.'])),
    ],
    sweep: { threshold: sweep, precision: sweep.map((t) => Math.min(1, 0.9 + t * 0.1)), recall: sweep.map((t) => Math.max(0, 1.02 - t * 0.04)), f1: sweep.map((t) => 0.95 - Math.abs(t - 0.4) * 0.1) },
  }
}
const evalResult = () => {
  const xs = Array.from({ length: 41 }, (_, i) => i / 40)
  const roc = (k: number) => xs.map((x) => Math.pow(x, 1 / (1 + k)))
  return {
    n_folds: 5, test_n: 1525, prevalence: 0.733, models: models.map((m) => ({ run_id: m.run_id, model_id: m.id, name: m.name, model_type: m.model_type })),
    figures: [
      fig('roc', 'lines', 'Curvas ROC en validación externa (media y banda ±1 desv.)', { series: [{ name: 'Regresión logística', x: xs, y: roc(40), lo: roc(30), hi: roc(60) }, { name: 'Random Forest', x: xs, y: roc(25), lo: roc(18), hi: roc(35) }, { name: 'Dummy', x: xs, y: xs }], xlabel: 'Tasa de falsos positivos', ylabel: 'Tasa de verdaderos positivos', diagonal: true, xlim: [0, 1], ylim: [0, 1.02] }, '5 pliegues externos; banda = variabilidad entre pliegues.', ip(['Regresión logística: ROC-AUC 1,000; Random Forest: 0,999.'], ['Curvas casi perfectas: la separabilidad es casi trivial en este escenario.'])),
      fig('pr', 'lines', 'Curvas precisión-exhaustividad', { series: [{ name: 'Regresión logística', x: xs, y: xs.map(() => 0.99), lo: xs.map(() => 0.98), hi: xs.map(() => 1) }, { name: 'Dummy', x: xs, y: xs.map(() => 0.733) }], xlabel: 'Exhaustividad', ylabel: 'Precisión', xlim: [0, 1], ylim: [0.5, 1.02], hlines: [{ y: 0.733, label: 'Prevalencia' }] }, 'Prevalencia Botnet 73,3 %.', ip(['La precisión se mantiene sobre 0,98 en todo el rango.'])),
      fig('calibration', 'lines', 'Calibración (diagrama de fiabilidad)', { series: [{ name: 'Regresión logística', x: [0.05, 0.25, 0.5, 0.75, 0.95], y: [0.04, 0.22, 0.52, 0.78, 0.97], points: true, sizes: [300, 60, 30, 50, 1000] }], xlabel: 'Probabilidad predicha', ylabel: 'Frecuencia observada', diagonal: true, xlim: [0, 1], ylim: [0, 1.02] }, 'Prueba, n = 1 525.', ip(['ECE 0,012: las probabilidades están bien calibradas.'])),
    ],
    tables: [
      table('metrics', 'Métricas por modelo (media ± desv., IC 95 %)', [['model', 'Modelo'], ['pr', 'PR-AUC CV'], ['ci', 'IC 95 % (t)'], ['test', 'PR-AUC Prueba']], [{ model: 'Regresión logística', pr: '1,000 ± 0,000', ci: '[1,000; 1,000]', test: 0.995 }, { model: 'Random Forest', pr: '0,999 ± 0,001', ci: '[0,998; 1,000]', test: 0.997 }, { model: 'Dummy', pr: '0,470 ± 0,040', ci: '[0,420; 0,520]', test: 0.733 }], 'n = 5 pliegues externos.', ip(['Ambos modelos superan holgadamente a la línea base.'])),
      table('wilcoxon', 'Wilcoxon por pares con corrección de Holm', [['pair', 'Comparación'], ['dz', 'd de Cohen (pareado)'], ['p', 'p'], ['holm', 'p (Holm)']], [{ pair: 'Regresión logística vs Random Forest', dz: 0.4, p: 0.0625, holm: 0.0625 }, { pair: 'Regresión logística vs Dummy', dz: 12, p: 0.0625, holm: 0.125 }], 'n = 5 pliegues.', ip(['Ningún par llega a p < 0,05.'], ['Con n = 5 pliegues el p mínimo posible es 0,0625: la prueba no puede ser significativa.'])),
      table('baselines', 'Comparación con los detectores deterministas de NetSentinel (misma partición de Prueba)', [['who', 'Método'], ['recall', 'Exhaustividad'], ['precision', 'Precisión']], [{ who: 'Random Forest', recall: 0.99, precision: 0.99 }, { who: 'Beaconing + puertos inusuales', recall: 0, precision: null }, { who: 'Dummy', recall: 1, precision: 0.733 }], 'n = 1 525 flujos de Prueba.', ip(['Los detectores deterministas no marcan ningún flujo Botnet en este escenario.'], ['Los detectores se aproximaron tratando toda la captura como una ventana.'])),
    ],
  }
}

const explainResult = () => {
  const r = rnd(11)
  const feats = ['Bytes totales', 'Duración', 'Puerto destino', 'Estado de conexión', 'Paquetes', 'Razón salida/entrada'].map((label, i) => ({ feature: label, label, points: Array.from({ length: 60 }, () => { const c = r(); return { x: (c - 0.5) * (4 - i * 0.5) + (r() - 0.5) * 0.5, c } }) }))
  const rows = ['10.0.0.1', '10.0.0.2', '10.0.0.3', '10.0.1.5', '10.0.1.9'], cols = ['0–2 min', '2–4', '4–6', '6–8', '8–10', '10–12', '12–14', '14–16']
  return {
    model: 'Random Forest',
    figures: [
      fig('shap_global', 'bars', 'Importancia global SHAP (media del valor absoluto)', { labels: feats.map((f) => f.label), series: [{ name: 'SHAP medio', values: [1.9, 1.3, 0.9, 0.5, 0.3, 0.2] }], horizontal: true, xlabel: 'Media de |SHAP|' }, 'Validación, n = 1 663; espacio de probabilidad.', ip(['Bytes totales explica la mayor parte de las decisiones del modelo.'], ['SHAP describe el modelo, no causalidad.'])),
      fig('swarm', 'swarm', 'Enjambre SHAP: efecto de cada variable por flujo', { features: feats, xlabel: 'Valor SHAP (empuja hacia Botnet →)' }, 'Cada punto es un flujo; color = valor de la variable.', ip(['Valores bajos de Bytes totales empujan hacia Botnet.'])),
      fig('heat_host_time', 'heatmap', 'Riesgo medio por host y minuto', { rows, cols, values: rows.map(() => cols.map(() => r())), vlabel: 'Prob. Botnet', scale: 'seq', vmin: 0, vmax: 1 }, '5 hosts, 8 ventanas.', ip(['Los hosts 10.0.0.1 a 10.0.0.3 concentran el riesgo.'])),
      fig('perm_vs_shap', 'dots', 'Rangos: SHAP frente a permutación', { groups: [{ name: 'SHAP', values: [1, 2, 3, 4, 5, 6] }, { name: 'Permutación', values: [1, 3, 2, 4, 6, 5] }], ylabel: 'Rango' }, 'Dos métodos independientes.', ip(['Hay discrepancias en 4 variables.'], ['Discrepancias grandes sugieren variables correlacionadas.'])),
    ],
    tables: [table('stability', 'Estabilidad de la importancia entre pliegues', [['k', 'Métrica'], ['v', 'Valor']], [{ k: 'W de Kendall', v: 0.91 }, { k: 'τ medio por pares', v: 0.88 }], '5 pliegues.', ip(['El ranking es muy estable entre pliegues.']))],
  }
}

/* ------------------------------------------------------------ inferencia */
let active: number | null = null
let pipeline = false
let sev: any = { weights: { probability: 0.6, deterministic: 0.4 }, thresholds: { critical: 85, high: 70, medium: 50, low: 30 }, uncertainty: { interval_width_gt: 0.3, penalty_points: 10, ambiguous_set_penalty_points: 10 }, asset_bump: { critical: 1, high: 1, medium: 0, low: 0 }, ood_cap: 'medium' }
const SEVD = JSON.parse(JSON.stringify(sev))
const preds: any[] = []
const predict = (body: any, user: string) => {
  const id = preds.length + 1, p = body.kind === 'manual' ? 0.62 : 0.93, det = body.kind === 'finding' ? 78 : null
  const pts = det == null ? p * 100 : (0.6 * p * 100 + 0.4 * det)
  const level = pts >= 85 ? 'critical' : pts >= 70 ? 'high' : pts >= 50 ? 'medium' : pts >= 30 ? 'low' : 'info'
  const items = [{ feature: 'Bytes totales', label: 'Bytes totales', shap: 0.31, value: 310 }, { feature: 'Puerto destino', label: 'Puerto destino', shap: 0.12, value: 6667 }, { feature: 'Duración', label: 'Duración', shap: -0.06, value: 1.9 }]
  const rec = {
    id, probability: p, interval: [p - 0.04, Math.min(1, p + 0.03)], prediction_set: ['Botnet'], predicted_class: 'Botnet', threshold: 0.41, ambiguous: false,
    ood: body.kind === 'manual' ? { is_ood: true, out_of_range: [{ feature: 'bytes_out', value: 9e9, lo: 40, hi: 8e6 }] } : { is_ood: false },
    severity: level, severity_steps: [{ step: 'probabilidad', points: p * 100, text: `Probabilidad calibrada de Botnet ${p.toFixed(3).replace('.', ',')} = ${(p * 100).toFixed(1).replace('.', ',')} puntos.` }, { step: 'detector_determinista', text: det == null ? 'No hay puntaje determinista asociado: solo cuenta la probabilidad.' : `Se combina con el puntaje determinista ${det} (pesos 0,6/0,4): ${pts.toFixed(1).replace('.', ',')} puntos.` }, { step: 'incertidumbre', text: 'Incertidumbre baja (ancho del intervalo 0,07): sin penalización.' }, { step: 'resultado', level, text: `Severidad final: ${level}.` }],
    narrative: `El modelo estima una probabilidad de ${Math.round(p * 100)} % de que este tráfico corresponda a una botnet; se clasifica como Botnet al umbral 0,41.`, narrative_source: 'template',
    contributions: { favor: items.filter((i) => i.shap > 0), contra: items.filter((i) => i.shap < 0), base: 0.62, space: 'log-odds', all: items }, model: { id: body.model_id ?? active ?? 3, name: models[2].name, threshold: 0.41 },
    interpretation: ip([`La severidad ${level} resulta de ${pts.toFixed(0)} puntos frente a los umbrales configurados.`]), features: {},
    ts: iso(Date.now()), username: user, input_kind: body.kind, input_ref: String(body.finding_id ?? body.log_id ?? body.src_ip ?? 'manual'),
  }
  preds.unshift(rec)
  return rec
}

/* ------------------------------------------------------------ Optuna */
const trials = (n: number) => { const r = rnd(5); return Array.from({ length: n }, (_, i) => { const pr = r() < 0.25; return { number: i, state: pr ? 'pruned' : 'complete', state_es: pr ? 'podado' : 'completo', value: pr ? null : Math.min(0.999, 0.95 + 0.045 * (1 - Math.exp(-(i + 1) / 8)) + (r() - 0.5) * 0.008), params: { n_estimators: 200 + Math.floor(r() * 6) * 100, max_depth: 4 + Math.floor(r() * 26), class_weight: r() < 0.5 ? 'none' : 'balanced' }, duration_s: 6 + r() * 20 } }) }
const studyDetail = (j: SimJob) => {
  const f = status(j) === 'succeeded' ? 1 : frac(j), n = Math.max(1, Math.round(j.params.n_trials * f))
  const tr = trials(n), done = tr.filter((t) => t.state === 'complete'), best = done.reduce((a, b) => ((b.value ?? 0) > (a?.value ?? 0) ? b : a), done[0])
  return { ...jobOut(j, true), trials: tr, space: params('random_forest').params, summary: { n_trials: n, n_complete: done.length, n_pruned: n - done.length, n_running: status(j) === 'running' ? 1 : 0, best_value: best?.value ?? null, best_number: best?.number ?? null, best_params: best?.params ?? {} }, result: {} }
}
const studyViz = (j: SimJob) => {
  const d = studyDetail(j), done = d.trials.filter((t) => t.state === 'complete')
  if (!done.length) return null
  let run = 0
  const figs = [
    fig('history', 'lines', 'Historial de optimización', { series: [{ name: 'Valor del trial', x: done.map((t) => t.number), y: done.map((t) => t.value), mode: 'markers' }, { name: 'Mejor hasta ahora', x: done.map((t) => t.number), y: done.map((t) => (run = Math.max(run, t.value ?? 0))), bold: true }], xlabel: 'Trial', ylabel: 'PR-AUC' }, `n = ${d.trials.length} trials.`, ip(['El mejor valor se alcanzó pronto y luego se estabilizó.'])),
    fig('importance', 'bars', 'Importancia de hiperparámetros (fANOVA)', { labels: ['max_depth', 'n_estimators', 'class_weight'], series: [{ name: 'Importancia', values: [0.55, 0.3, 0.15] }], horizontal: true, xlabel: 'Importancia relativa' }, 'Calculada con los trials completados.', ip(['max_depth explica 55 % de la variación del resultado.'], ['Con pocos trials la importancia es una estimación gruesa.'])),
    fig('parallel', 'parcoords', 'Coordenadas paralelas de los trials completados', { axes: [{ name: 'n_estimators', min: 200, max: 700 }, { name: 'max_depth', min: 4, max: 30 }, { name: 'class_weight', categories: ['none', 'balanced'] }], lines: done.map((t) => ({ values: [t.params.n_estimators, t.params.max_depth, t.params.class_weight], value: t.value })), objective: 'PR-AUC' }, `n = ${done.length} trials completados.`, ip(['Los mejores trials usan profundidades medias.'])),
    fig('timeline', 'lines', 'Línea de tiempo de trials', { mode: 'segments', series: d.trials.map((t, i) => ({ name: `#${t.number}`, x: [i * 8, i * 8 + (t.duration_s ?? 6)], y: [t.number, t.number], state: t.state })), xlabel: 'Segundos desde el inicio', ylabel: 'Trial', legend: false }, 'Duración de cada trial por estado.', ip(['Los trials podados terminan antes.'])),
  ]
  return { figures: figs, summary: d.summary }
}

const PNG = Uint8Array.from(atob('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='), (c) => c.charCodeAt(0))

export function mlMock(path: string, method: string, body: any, p: URLSearchParams, user: { full_name: string }, perms: Set<string>): Response | null {
  if (!path.startsWith('/ml/')) return null
  const need = (x: string) => (perms.has(x) ? null : err(403, 'No tiene permiso para esta acción.'))
  const any = (...xs: string[]) => (xs.some((x) => perms.has(x)) ? null : err(403, 'No tiene permiso para esta acción.'))
  let d: Response | null
  // ---- datos
  if (path === '/ml/data/sources') return need('ml_data:view') ?? json([{ id: 3, name: 'CTU-13 Dataset', format: 'ctu13_binetflow', logs: 214388 }])
  if (path === '/ml/data/datasets' && method === 'GET') return need('ml_data:view') ?? json([dataset()])
  if (path === '/ml/data/datasets' && method === 'POST') return need('ml_data:create') ?? json({ ...dataset(), name: body.name }, 201)
  if (path === '/ml/data/datasets/upload') return need('ml_data:create') ?? json(dataset(), 201)
  if (/^\/ml\/data\/datasets\/\d+$/.test(path)) {
    if (method === 'PUT') return need('ml_data:update') ?? json(dataset())
    return need('ml_data:view') ?? json({ ...dataset(), versions: [...versions].reverse() })
  }
  if (path.endsWith('/summary')) return need('ml_data:view') ?? json(summary())
  if (path.endsWith('/validation')) return need('ml_data:view') ?? json(validation())
  if (path === '/ml/data/feature-spec') return need('ml_data:view') ?? json({ numeric: ['duration', 'bytes_out', 'bytes_in', 'packets', 'dst_port'], categorical: ['proto', 'state'] })
  // ---- entrenamiento / trabajos
  if (path === '/ml/training/spaces') return need('ml_training:view') ?? json({ models: ['logreg', 'random_forest', 'hist_gb', 'xgboost'].map(params), metrics: ['pr_auc', 'roc_auc', 'f1', 'mcc'], max_trials: 300, protocol: { n_outer: 5, n_inner: 3 } })
  if (path === '/ml/training/jobs' && method === 'POST') {
    if ((d = need('ml_training:execute'))) return d
    const j: SimJob = { id: nextJob++, kind: 'train', name: `${(body.models as { type: string }[]).map((m) => MODEL_ES[m.type]).join(', ')} · ${META.name} v3`, params: { ...body, models: body.models }, created: Date.now(), dur: 40e3, user: user.full_name, seed: body.seed ?? 42 }
    jobs.unshift(j)
    return json(jobOut(j), 201)
  }
  if (path === '/ml/training/jobs' && method === 'GET') { if ((d = any('ml_training:view', 'ml_evaluation:view'))) return d; const k = p.get('kind') ?? 'train'; return json(pageOf(jobs.filter((j) => j.kind === k).map((j) => jobOut(j)), p)) }
  let m = /^\/ml\/training\/jobs\/(\d+)(\/\w+)?$/.exec(path)
  if (m) {
    const j = jobs.find((x) => x.id === +m![1])
    if (!j) return err(404, 'Trabajo no encontrado')
    if (m[2] === '/log') return json({ text: `[${new Date(j.created).toLocaleTimeString('es-PE')}] Inicio (${j.kind}); semilla ${j.seed}\n[…] Partición por grupos (time_block): Desarrollo 5792 Botnet / 1902 Normal\n` })
    if (m[2] === '/cancel') { j.cancelled = true; return json(jobOut(j)) }
    if (m[2] === '/retry') { j.created = Date.now(); j.cancelled = false; return json(jobOut(j)) }
    if (m[2] === '/analysis') return json({ ...trainAnalysis(), job: jobOut(j) })
    return any('ml_training:view', 'ml_evaluation:view', 'ml_explain:view', 'ml_optuna:view') ?? json(jobOut(j, true))
  }
  // ---- evaluación
  if (path === '/ml/evaluation/models') return any('ml_evaluation:view', 'ml_inference:view', 'ml_explain:view') ?? json(models.map((x) => ({ ...x, is_active: x.id === active })))
  if (path === '/ml/evaluation/evaluations' && method === 'POST') { const j: SimJob = { id: 900 + (body.job_id ?? 1), kind: 'evaluate', name: 'Evaluación', params: { run_ids: [10, 11, 12] }, created: Date.now() - 5e3, dur: 4e3, user: user.full_name, seed: 42 }; if (!jobs.find((x) => x.id === j.id)) jobs.push(j); return json(jobOut(j), 201) }
  m = /^\/ml\/evaluation\/evaluations\/(\d+)$/.exec(path)
  if (m) return need('ml_evaluation:view') ?? json({ id: +m[1], status: 'succeeded', result: evalResult() })
  if (/^\/ml\/evaluation\/runs\/\d+\/confusion$/.test(path)) return need('ml_evaluation:view') ?? json(confusion(p.get('threshold') ? Number(p.get('threshold')) : 0.41))
  m = /^\/ml\/evaluation\/models\/(\d+)\/promote$/.exec(path)
  if (m) { if ((d = need('ml_evaluation:update'))) return d; active = +m[1]; return json(models.find((x) => x.id === active)) }
  if (path === '/ml/evaluation/models/deactivate') { if ((d = need('ml_evaluation:update'))) return d; active = null; pipeline = false; return json({ deactivated: 1 }) }
  // ---- explicabilidad
  if (path === '/ml/explain/jobs') return need('ml_explain:execute') ?? json(jobOut({ id: 950, kind: 'explain', name: 'Explicabilidad', params: {}, created: Date.now(), dur: 6e3, user: user.full_name, seed: 42 }), 201)
  if (/^\/ml\/explain\/models\/\d+$/.test(path)) return need('ml_explain:view') ?? json({ ...jobOut({ id: 950, kind: 'explain', name: 'Explicabilidad', params: { model_id: 3 }, created: T0 - 3600e3, dur: 6e3, user: 'Administrador TI', seed: 42 }), result: explainResult() })
  // ---- inferencia
  if (path === '/ml/inference/active') { if ((d = any('ml_inference:view', 'detection:view'))) return d; const am = models.find((x) => x.id === active); return json({ model: am ? { ...am, is_active: true, promoted_by: user.full_name } : null, pipeline_enabled: pipeline }) }
  if (path === '/ml/inference/pipeline') { if ((d = need('detection:update'))) return d; if (body.enabled && active == null) return err(422, 'No hay modelo ML activo: promueva uno desde Evaluación antes de activar la integración'); pipeline = !!body.enabled; return json({ pipeline_enabled: pipeline }) }
  if (path === '/ml/inference/severity-config') { if (method === 'PUT') { if ((d = need('ml_inference:update'))) return d; sev = { ...sev, ...body }; return json({ config: sev, default: SEVD }) } return need('ml_inference:view') ?? json({ config: sev, default: SEVD }) }
  if (path === '/ml/inference/predict') return need('ml_inference:execute') ?? json(predict(body, user.full_name), 201)
  if (path === '/ml/inference/predictions') return need('ml_inference:view') ?? json(pageOf(preds.filter((x) => !p.get('severity') || x.severity === p.get('severity')), p))
  m = /^\/ml\/inference\/predictions\/(\d+)\/narrative$/.exec(path)
  if (m) return need('ml_inference:execute') ?? json({ narrative: 'Interpretación generada por el modelo de lenguaje local a partir de las cifras calculadas: el flujo envía muy pocos bytes de forma repetitiva hacia el puerto 6667, un patrón típico de control de botnets IRC. Confirme con el responsable del equipo.', source: 'llm' })
  if (/^\/ml\/inference\/models\/\d+\/uncertainty$/.test(path)) return need('ml_inference:view') ?? json({ coverage: { nominal: 0.9, empirical_set: 0.93, meets_nominal: true, n: 1525 }, conformal_interpretation: ip(['La cobertura nominal es 90 %; en Prueba el conjunto conforme contiene la clase verdadera en 93,0 % de los 1 525 casos (cumple la cobertura declarada).'], ['Predicción conforme dividida: la garantía es marginal, no por caso individual.']), reliability: fig('reliability', 'lines', 'Diagrama de fiabilidad (calibración) en Prueba', { series: [{ name: 'Modelo', x: [0.05, 0.25, 0.5, 0.75, 0.95], y: [0.04, 0.22, 0.52, 0.78, 0.97], points: true, sizes: [300, 60, 30, 50, 1000] }], xlabel: 'Probabilidad media predicha', ylabel: 'Frecuencia observada', diagonal: true, xlim: [0, 1], ylim: [0, 1.02] }, 'Prueba, n = 1 525.', ip(['ECE 0,012: bien calibrado.'])) })
  // ---- Optuna
  if (path === '/ml/optuna/options') return need('ml_optuna:view') ?? json({ samplers: ['tpe', 'random', 'cmaes'], pruners: ['median', 'hyperband', 'none'], metrics: ['pr_auc', 'roc_auc', 'f1', 'mcc'], max_trials: 300, models: ['logreg', 'random_forest', 'hist_gb', 'xgboost'].map(params), notes: { direction: 'Todas las métricas se maximizan.', cmaes: 'CMA-ES solo admite parámetros numéricos; los categóricos se muestrean al azar.' } })
  if (path === '/ml/optuna/studies' && method === 'POST') { if ((d = need('ml_optuna:create'))) return d; const j: SimJob = { id: nextJob++, kind: 'optimize', name: `${MODEL_ES[body.model_type]} · ${META.name} v3`, params: body, created: Date.now(), dur: 30e3, user: user.full_name, seed: body.seed ?? 42 }; jobs.unshift(j); return json(jobOut(j), 201) }
  if (path === '/ml/optuna/studies') return need('ml_optuna:view') ?? json(pageOf(jobs.filter((j) => j.kind === 'optimize').map((j) => ({ ...jobOut(j), best_value: studyDetail(j).summary.best_value })), p))
  m = /^\/ml\/optuna\/studies\/(\d+)(\/\w+)?$/.exec(path)
  if (m) {
    if ((d = need(method === 'DELETE' ? 'ml_optuna:delete' : 'ml_optuna:view'))) return d
    const j = jobs.find((x) => x.id === +m![1] && x.kind === 'optimize')
    if (!j) return err(404, 'Trabajo no encontrado')
    if (method === 'DELETE') { jobs.splice(jobs.indexOf(j), 1); return json(null, 204) }
    if (m[2] === '/viz') { const v = studyViz(j); return v ? json(v) : err(404, 'El estudio aún no tiene datos') }
    if (m[2] === '/best') { const s = studyDetail(j).summary; return s.best_value ? json({ job_id: j.id, model_type: j.params.model_type, best_params: s.best_params, best_value: s.best_value, dataset_version_id: 3, metric: 'pr_auc' }) : err(409, 'El estudio aún no tiene un mejor trial') }
    return json(studyDetail(j))
  }
  // ---- exportación de figuras
  if (path === '/ml/figures/export') {
    const svg = body.format === 'svg'
    return new Response(svg ? new Blob([`<svg xmlns="http://www.w3.org/2000/svg" width="300" height="80"><text x="10" y="40">${String(body.spec?.title ?? 'Figura').replace(/[<&]/g, '')} (simulado)</text></svg>`]) : new Blob([PNG]), { status: 200, headers: { 'Content-Type': svg ? 'image/svg+xml' : 'image/png', 'Content-Disposition': `attachment; filename="figura.${svg ? 'svg' : 'png'}"` } })
  }
  return err(404, `Ruta ML simulada no implementada: ${method} ${path}`)
}

export const ML_REPORTS = [
  ['ml_dataset', 'ML · Dataset y validación de grupos', 'Estadística descriptiva y validación anti-fuga de grupos.', ['dataset_version_id']],
  ['ml_training', 'ML · Entrenamiento', 'Protocolo, validación cruzada anidada e hiperparámetros.', ['job_id']],
  ['ml_evaluation', 'ML · Evaluación', 'Métricas con IC, curvas y pruebas estadísticas entre modelos.', ['job_id']],
  ['ml_explainability', 'ML · Explicabilidad', 'SHAP, permutación, mapas de calor, PDP y oclusión.', ['model_id']],
  ['ml_inference', 'ML · Predicciones del período', 'Predicciones registradas en el período.', []],
  ['ml_model_card', 'ML · Ficha del modelo', 'Datos, uso previsto, métricas, limitaciones y riesgos.', ['model_id']],
].map(([code, name, description, params]) => ({ code, name, description, category: 'ml', formats: ['pdf', 'docx', 'xlsx'], params }))
export const ML_MODULES = [
  { code: 'ml_data', label: 'ML · Datos', actions: ['view', 'create', 'update', 'delete', 'export'] },
  { code: 'ml_training', label: 'ML · Entrenamiento', actions: ['view', 'create', 'update', 'delete', 'execute'] },
  { code: 'ml_evaluation', label: 'ML · Evaluación', actions: ['view', 'update', 'export'] },
  { code: 'ml_explain', label: 'ML · Explicabilidad', actions: ['view', 'execute', 'export'] },
  { code: 'ml_inference', label: 'ML · Inferencia', actions: ['view', 'execute', 'update', 'export'] },
  { code: 'ml_optuna', label: 'ML · Optuna', actions: ['view', 'create', 'execute', 'delete'] },
]
