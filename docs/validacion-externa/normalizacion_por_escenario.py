"""Adaptación de dominio sin etiquetas: cada variable numérica se reemplaza por su rango percentil DENTRO de su escenario
(se calcula con las variables del propio escenario, sin usar la etiqueta; en producción equivale a normalizar por red/ventana).
Compara contra las variables crudas en validación dejando un escenario fuera (3 semillas, 4 000 flujos/escenario, parámetros por defecto)."""
import json, sys, warnings
import numpy as np, pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score
from app.ml import data as D, prepare as P, models as M
from app.ml import features as F
warnings.filterwarnings("ignore")
CAP, SEEDS = int(sys.argv[1]), [int(s) for s in sys.argv[2:]]
files = {"Esc. 9": "/tmp/s09.binetflow", "Esc. 12": "/tmp/s12.binetflow", "Esc. 13": "/tmp/s13.binetflow"}
raw = {k: D.frame_from_file(open(v, "rb").read(), k + ".binetflow")[0] for k, v in files.items()}
raw["Esc. 11"] = D.load_snapshot("/data/ml/datasets/1/flows.csv.gz")
cols = F.feature_columns("flow"); NUM = [c for c in cols if c not in F.FLOW_CATEGORICAL]
def frame(df, n):
    meta = P.default_meta(n, df); ff = P.feature_frame(df, meta, True); ff = ff[ff["y"].notna()].reset_index(drop=True)
    return ff[cols], ff["y"].astype(int).values
FULL = {k: frame(v, k) for k, v in raw.items()}
def sub(X, y, rng):
    if len(y) <= CAP: return X, y
    idx = np.concatenate([rng.choice(np.where(y == c)[0], max(1, round(CAP * (y == c).mean())), replace=False) for c in (0, 1)])
    return X.iloc[idx].reset_index(drop=True), y[idx]
def rank(X):
    X = X.copy()
    for c in NUM: X[c] = X[c].astype(float).rank(pct=True)
    return X
res = {}
for seed in SEEDS:
    rng = np.random.default_rng(seed); S = {k: sub(X, y, rng) for k, (X, y) in FULL.items()}
    for mode in ("crudas", "rango por escenario"):
        T = {k: ((rank(X) if mode != "crudas" else X), y) for k, (X, y) in S.items()}
        for held in T:
            Xtr = pd.concat([T[k][0] for k in T if k != held], ignore_index=True); ytr = np.concatenate([T[k][1] for k in T if k != held])
            for mt in ("logreg", "random_forest", "hist_gb", "xgboost"):
                pipe = M.build_pipeline(mt, {}, "flow", seed, 6); pipe.fit(Xtr, ytr); p = M.predict_proba(pipe, T[held][0]); yt = T[held][1]
                res.setdefault((mode, mt, held), []).append((average_precision_score(yt, p), roc_auc_score(yt, p)))
    print("semilla", seed, flush=True)
out = [{"modo": a, "model": b, "held_out": c, "pr_auc": float(np.mean([x for x, _ in v])), "roc_auc": float(np.mean([y for _, y in v]))} for (a, b, c), v in res.items()]
json.dump(out, open("/tmp/normalizacion.json", "w"), indent=1)
for mode in ("crudas", "rango por escenario"):
    for mt in ("logreg", "random_forest", "hist_gb", "xgboost"):
        print(f"{mode:20s} {mt:14s} " + " ".join(f"{h[-2:].strip()}:{[o for o in out if o['modo']==mode and o['model']==mt and o['held_out']==h][0]['pr_auc']:.2f}/{[o for o in out if o['modo']==mode and o['model']==mt and o['held_out']==h][0]['roc_auc']:.2f}" for h in FULL))
