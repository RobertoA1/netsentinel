"""Valores SUPUESTOS (ilustrativos) del protocolo de evaluacion y calculo de sus estadisticos.
Todo lo que sale de este modulo es dato supuesto (marca †) salvo REAL, que son mediciones reales del despliegue.
Semilla fija: los resultados son reproducibles. Sustituir por mediciones reales antes de enviar a una revista."""
import numpy as np, math
from scipy import stats

# ---------------- VALORES REALES (medidos en el despliegue) ----------------
REAL = dict(lineas=107252, registros=107194, errores_parseo=1, import_s=9.8, bot_lineas=8164,
            hallazgos=51, beacon=23, puerto=25, talker=3, crit=2, alto=15, medio=31, bajo=3,
            origenes=29146, destinos=15141, lat_min=14, lat_max=472, rep_n=36, rep_min=56, rep_max=560,
            llm_min=28, llm_max=37, llm_test=7.8, reanalizados=2, tests=114, modelo_gb=2.0)
# Reales calculados por script sobre el archivo del dataset (no desde la BD)
DS = dict(normal=2718, fondo=96369, botnet=8164, inicio='2011-08-18 15:39:35', fin='2011-08-18 15:55:46',
          icmp_bot=7663, hosts_bot={'147.32.84.165': 4151, '147.32.84.191': 4006, '147.32.84.192': 7})

rng = np.random.default_rng(20261111)

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p = k / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d; h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (max(0, c-h), min(1, c+h))

def mcnemar_exact(b, c):
    n = b + c
    if n == 0: return 1.0
    k = min(b, c)
    return min(1.0, 2*stats.binom.cdf(k, n, 0.5))

# ---------------- Hallazgos del despliegue (51 reales; adjudicacion supuesta) ----------------
# tipo: (n, reales adjudicados)
POOL = 24  # eventos reales de referencia (union de los reales hallados por cualquier metodo)
DET = {'beaconing': (23, 12), 'puerto': (25, 7), 'talker': (3, 2)}
N_DET = sum(v[0] for v in DET.values()); R_DET = sum(v[1] for v in DET.values())   # 51, 21
assert N_DET == REAL['hallazgos']
METODOS = {  # nombre: (n hallazgos, reales, hosts infectados detectados de 3)
 'Umbral fijo (≥100 conexiones/destino)': (37, 9, 2),
 'Suricata 7 (reglas por defecto)': (14, 3, 1),
 'NetSentinel: beaconing': (23, 12, 0),
 'NetSentinel: puerto inusual': (25, 7, 1),
 'NetSentinel: anomalía de host': (3, 2, 2),
 'NetSentinel determinista (unión)': (51, 21, 2),
 'NetSentinel + llama3.2:3b': (50, 21, 2),
 'NetSentinel + llama3.1:8b': (36, 20, 2),
}
# sensibilidad sobre beacons inyectados (se calcula abajo)

def f1(p, r): return 0 if p+r == 0 else 2*p*r/(p+r)

def boot_f1(n, tp, pool, B=4000):
    """IC95 % por bootstrap percentil: remuestrea hallazgos (precision) y eventos de referencia (cobertura)."""
    flags = np.array([1]*tp + [0]*(n-tp)); found = np.array([1]*tp + [0]*(pool-tp))
    out = []
    for _ in range(B):
        p = rng.choice(flags, n).mean(); r = rng.choice(found, pool).mean()
        out.append(f1(p, r))
    return tuple(np.percentile(out, [2.5, 97.5]))

# ---------------- Experimento de inyeccion de beacons (usa la formula REAL del detector) ----------------
def score_beaconing(conns, mean_i, std_i, mean_b, std_b, dur_s, port=443, cfg=(10, 0.25, 60.0)):
    mc, mcv, ms = cfg
    if conns < mc or mean_i < 1.0: return None
    cv = std_i/mean_i
    if cv > mcv: return None
    bcv = std_b/mean_b if mean_b > 0 else 0.0
    reg = 1 - 0.6*(cv/mcv); size = 1 - min(bcv, 1.0)
    cnt = min(1, max(0, 0.5 + 0.5*math.log10(conns/mc))); dur = min(1, max(0, dur_s/3600/2))
    s = 100*(0.5*reg + 0.2*size + 0.2*cnt + 0.1*dur)
    if port in (53, 123): s *= 0.7
    return min(100.0, s) if min(100.0, s) >= ms else None

PERIODOS = [30, 60, 120, 300, 600]; JITTERS = [0, .10, .20, .30, .40]
PERDIDA = [0, 0, 0, 0, .02, .02, .05, .10]
def simula_beacon(per, jit, miss, horas=2.0):
    t, ts = 0.0, []
    horizon = horas*3600
    while t < horizon:
        if rng.random() >= miss: ts.append(t)
        t += per*(1 + rng.uniform(-jit, jit))
    ts = np.array(ts)
    if len(ts) < 3: return None
    gaps = np.diff(ts); sizes = rng.normal(900, 90, len(ts)).clip(50)
    return dict(per=per, jit=jit, miss=miss, n=len(ts), cv=gaps.std()/gaps.mean(), gaps=gaps,
                score=score_beaconing(len(ts), gaps.mean(), gaps.std(), sizes.mean(), sizes.std(), ts[-1]-ts[0]))
INJ = [simula_beacon(p, j, m) for p in PERIODOS for j in JITTERS for m in PERDIDA]
assert len(INJ) == 200
INJ_DET = [x for x in INJ if x['score'] is not None]
K_DET = len(INJ_DET)                                  # detectados por la formula del sistema
K_FIX = sum(1 for x in INJ if x['n'] >= 100)          # umbral fijo >=100 conexiones al mismo destino
K_SUR = 0                                             # Suricata: sin firmas para beacons genericos (SUPUESTO)
SUPRIME = {'llama3.2:3b': 0, 'qwen2.5:7b': 5, 'llama3.1:8b': 6, 'mistral:7b': 14}   # beacons detectados que el LLM descarta (SUPUESTO)

# ---------------- Modelos locales: veredictos sobre los 51 hallazgos (adjudicacion supuesta) ----------------
def _fp(confs): return [(c, False) for c in confs]
MODEL_NOISE = {   # (confianza, es_real) de cada hallazgo con veredicto 'noise'
 'llama3.2:3b': _fp([0.75, 0.62, 0.55]) + [(0.60, True)],
 'qwen2.5:7b': _fp([0.95, 0.92, 0.90, 0.88, 0.85, 0.82, 0.80, 0.78, 0.75, 0.65, 0.60]) + [(0.72, True), (0.55, True)],
 'llama3.1:8b': _fp([0.96, 0.94, 0.93, 0.91, 0.90, 0.88, 0.87, 0.85, 0.83, 0.81, 0.79, 0.77, 0.75, 0.73, 0.68, 0.66, 0.62, 0.55]) + [(0.71, True), (0.60, True)],
 'mistral:7b': _fp([0.97, 0.95, 0.92, 0.90, 0.89, 0.86, 0.84, 0.82, 0.79, 0.76, 0.72, 0.65, 0.60]) + [(0.93, True), (0.88, True), (0.80, True), (0.50, True)],
}
TAU = 0.7
MODELOS = ['llama3.2:3b', 'qwen2.5:7b', 'llama3.1:8b', 'mistral:7b']
def supr(model, tau=TAU):
    fp = sum(1 for c, r in MODEL_NOISE[model] if c >= tau and not r)
    rl = sum(1 for c, r in MODEL_NOISE[model] if c >= tau and r)
    return fp, rl
JSON_OK = {'llama3.2:3b': 48, 'qwen2.5:7b': 50, 'llama3.1:8b': 50, 'mistral:7b': 46}   # de 51, 1er intento
UNCERTAIN = {'llama3.2:3b': 44, 'qwen2.5:7b': 23, 'llama3.1:8b': 17, 'mistral:7b': 9}   # veredicto 'incierto' de 51
RAM_GB = {'llama3.2:3b': 2.0, 'qwen2.5:7b': 4.7, 'llama3.1:8b': 4.9, 'mistral:7b': 4.4}
LAT = {}
for m, (med, sd) in {'qwen2.5:7b': (71, 0.12), 'llama3.1:8b': (84, 0.13), 'mistral:7b': (69, 0.11)}.items():
    LAT[m] = rng.lognormal(math.log(med), sd, 30)
LAT['llama3.2:3b'] = np.clip(rng.normal(32.4, 2.6, 30), REAL['llm_min'], REAL['llm_max'])

def kappa_2x2(a, b, c, d):
    n = a+b+c+d; po = (a+d)/n
    pe = ((a+b)*(a+c) + (c+d)*(b+d))/n**2
    return (po-pe)/(1-pe) if pe < 1 else 1.0
def kappa_ci(model, B=4000):
    fp, rl = supr(model)
    nn = 30; nr = 21   # ruido / real segun analistas
    # item: (analista_ruido, modelo_suprime)
    items = [(1, 1)]*fp + [(1, 0)]*(nn-fp) + [(0, 1)]*rl + [(0, 0)]*(nr-rl)
    arr = np.array(items); ks = []
    for _ in range(B):
        s = arr[rng.integers(0, len(arr), len(arr))]
        a = ((s[:, 0] == 1) & (s[:, 1] == 1)).sum(); b = ((s[:, 0] == 0) & (s[:, 1] == 1)).sum()
        c = ((s[:, 0] == 1) & (s[:, 1] == 0)).sum(); d = ((s[:, 0] == 0) & (s[:, 1] == 0)).sum()
        ks.append(kappa_2x2(a, b, c, d))
    return kappa_2x2(fp, rl, nn-fp, nr-rl), tuple(np.nanpercentile(ks, [2.5, 97.5]))

# Calidad de la explicacion (Likert 1-5, media de 2 analistas por hallazgo)
LIK_MU = {'llama3.2:3b': 3.1, 'qwen2.5:7b': 4.05, 'llama3.1:8b': 4.0, 'mistral:7b': 3.6}
LIK = {m: np.clip(np.round((rng.normal(mu, 0.7, 51))*2)/2, 1, 5) for m, mu in LIK_MU.items()}
def wilcoxon_r(x, y):
    d = x - y; d = d[d != 0]
    res = stats.wilcoxon(x, y, method='approx')
    rk = stats.rankdata(np.abs(d)); wp = rk[d > 0].sum(); wn = rk[d < 0].sum()
    return res.pvalue, (wp - wn)/(wp + wn)   # correlacion biserial de rangos (tamano de efecto)

# ---------------- Estudio de usabilidad (N=12 administradores) ----------------
T_SIN = np.array([118, 142, 95, 160, 131, 104, 175, 122, 138, 110, 149, 127])
T_CON = np.array([71, 88, 64, 102, 79, 69, 181, 83, 92, 66, 95, 80])
ACC_SIN = np.array([7, 8, 6, 7, 8, 7, 6, 8, 7, 8, 7, 7]) / 10
ACC_CON = np.array([8, 7, 7, 8, 8, 7, 7, 8, 8, 7, 8, 7]) / 10
SUS = np.array([82.5, 70, 77.5, 65, 85, 72.5, 80, 67.5, 90, 75, 62.5, 87.5])
LIK_ITEMS = {  # media de 12 respuestas Likert 1-5 (supuesto)
 'La explicación es comprensible': [5, 4, 4, 5, 4, 4, 5, 4, 3, 5, 4, 4],
 'La recomendación es accionable': [4, 4, 5, 4, 3, 4, 4, 5, 4, 4, 3, 4],
 'Distingo hechos de interpretación de la IA': [5, 5, 4, 4, 5, 4, 4, 5, 4, 5, 4, 4],
 'Confío en el veredicto del modelo': [3, 4, 3, 2, 4, 3, 4, 3, 3, 4, 3, 3],
 'La carga de trabajo disminuye': [4, 5, 4, 4, 3, 4, 5, 4, 4, 3, 4, 5],
}
def boot_median_diff(a, b, B=5000):
    d = a - b; idx = rng.integers(0, len(d), (B, len(d)))
    return tuple(np.percentile(np.median(d[idx], axis=1), [2.5, 97.5]))

def calcula():
    R = {}
    # T4
    rows = []
    for nombre, (n, tp, hosts) in METODOS.items():
        p = tp/n; r = tp/POOL; f = f1(p, r)
        row = dict(nombre=nombre, n=n, tp=tp, p=p, p_ci=wilson(tp, n), r=r, r_ci=wilson(tp, POOL), f1=f, f1_ci=boot_f1(n, tp, POOL), hosts=hosts)
        if nombre == 'Umbral fijo (≥100 conexiones/destino)': row['s'] = K_FIX
        elif nombre == 'Suricata 7 (reglas por defecto)': row['s'] = K_SUR
        elif nombre in ('NetSentinel: beaconing', 'NetSentinel determinista (unión)'): row['s'] = K_DET
        elif nombre == 'NetSentinel + llama3.2:3b': row['s'] = K_DET - SUPRIME['llama3.2:3b']
        elif nombre == 'NetSentinel + llama3.1:8b': row['s'] = K_DET - SUPRIME['llama3.1:8b']
        else: row['s'] = None
        row['s_ci'] = wilson(row['s'], 200) if row['s'] is not None else None
        rows.append(row)
    R['t4'] = rows
    R['K'] = dict(det=K_DET, fix=K_FIX, sur=K_SUR)
    # McNemar sobre los 24 eventos de referencia
    R['mc_fix'] = dict(b=14, c=2, p=mcnemar_exact(14, 2))   # NS-det solo / umbral solo
    R['mc_sur'] = dict(b=19, c=1, p=mcnemar_exact(19, 1))
    # T5
    mods = []
    for m in MODELOS:
        fp, rl = supr(m); k, kci = kappa_ci(m)
        n_after = 51 - fp - rl; tp_after = 21 - rl
        mods.append(dict(m=m, fp=fp, rl=rl, red=(fp+rl)/51, red_ci=wilson(fp+rl, 51), n_after=n_after, tp_after=tp_after,
                         p=tp_after/n_after, p_ci=wilson(tp_after, n_after), fn_ci=wilson(rl, 21),
                         b=fp, c=rl, mc_p=mcnemar_exact(fp, rl), kappa=k, kappa_ci=kci,
                         unc=UNCERTAIN[m], json=JSON_OK[m], lik=LIK[m].mean(), lik_sd=LIK[m].std(ddof=1),
                         lat_med=float(np.median(LAT[m])), lat_q=tuple(np.percentile(LAT[m], [25, 75])), ram=RAM_GB[m],
                         supr_beacons=SUPRIME[m]))
    R['t5'] = mods
    R['wil_8b_3b'] = wilcoxon_r(LIK['llama3.1:8b'], LIK['llama3.2:3b'])
    R['wil_8b_qw'] = wilcoxon_r(LIK['llama3.1:8b'], LIK['qwen2.5:7b'])
    R['wil_8b_mi'] = wilcoxon_r(LIK['llama3.1:8b'], LIK['mistral:7b'])
    # Usabilidad
    w = stats.wilcoxon(T_SIN, T_CON, method='exact')
    dd = T_SIN - T_CON; rk = stats.rankdata(np.abs(dd)); rrb = (rk[dd > 0].sum() - rk[dd < 0].sum())/rk.sum()
    R['us_time'] = dict(sin=float(np.median(T_SIN)), con=float(np.median(T_CON)), p=w.pvalue, r=rrb,
                        ci=boot_median_diff(T_SIN, T_CON), red=1-np.median(T_CON)/np.median(T_SIN))
    wa = stats.wilcoxon(ACC_CON, ACC_SIN, method='approx')
    R['us_acc'] = dict(sin=ACC_SIN.mean(), con=ACC_CON.mean(), p=wa.pvalue, d=(ACC_CON-ACC_SIN).mean()/ (ACC_CON-ACC_SIN).std(ddof=1))
    tc = stats.t.interval(0.95, 11, SUS.mean(), SUS.std(ddof=1)/math.sqrt(12))
    R['sus'] = dict(mean=SUS.mean(), sd=SUS.std(ddof=1), ci=tc, min=SUS.min(), max=SUS.max())
    li = {}
    for k, v in LIK_ITEMS.items():
        v = np.array(v); p = stats.wilcoxon(v-3, method='approx', zero_method='wilcox').pvalue
        li[k] = dict(mean=v.mean(), sd=v.std(ddof=1), p=p)
    R['lik'] = li
    # F5 barrido de umbral
    taus = np.round(np.arange(0.5, 1.0001, 0.05), 2)
    R['sweep'] = {m: [(float(t),) + supr(m, t) for t in taus] for m in MODELOS}
    return R

if __name__ == '__main__':
    R = calcula()
    print('inyeccion: det', K_DET, 'fijo', K_FIX)
    for r in R['t4']: print(r['nombre'], r['n'], r['tp'], round(r['p'], 3), [round(x, 3) for x in r['p_ci']], round(r['r'], 3), round(r['f1'], 3), [round(x, 3) for x in r['f1_ci']], r['hosts'], r['s'])
    print(R['mc_fix'], R['mc_sur'])
    for m in R['t5']: print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in m.items() if k not in ('red_ci', 'p_ci', 'fn_ci', 'kappa_ci', 'lat_q')}, [round(x, 2) for x in m['kappa_ci']])
    print(R['wil_8b_3b'], R['wil_8b_qw'], R['wil_8b_mi'])
    print(R['us_time']); print(R['us_acc']); print(R['sus']); print(R['lik'])
