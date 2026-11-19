"""Diagnóstico por grupos de variables en validación dejando un escenario fuera (hiperparámetros por defecto, 3 semillas).
Ejecutar en el contenedor backend. Uso: python ablacion_variables.py <cap> <semilla>..."""
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
cols = F.feature_columns("flow")
def frame(df, n):
    meta = P.default_meta(n, df); ff = P.feature_frame(df, meta, True); ff = ff[ff["y"].notna()].reset_index(drop=True)
    return ff[cols], ff["y"].astype(int).values
FULL = {k: frame(v, k) for k, v in raw.items()}
GROUPS = {"sin dst_port y clases de puerto": ["dst_port", "dst_port_class", "src_port_class"],
          "sin proto/state/dir/direction": ["proto", "state", "dir", "direction"],
          "sin volumen (bytes, paquetes, tasas)": ["bytes_out", "bytes_in", "bytes_total", "packets", "bytes_per_packet", "ratio_out", "bytes_per_s", "pkts_per_s"],
          "sin duración": ["duration"]}
ABS = ["bytes_out", "bytes_in", "bytes_total", "packets"]
RATE = ["bytes_per_s", "pkts_per_s"]
CONFIGS = {"completo": [], "sin volumen absoluto": ABS, "sin volumen absoluto ni tasas": ABS + RATE,
           "sin volumen abs., tasas ni duración": ABS + RATE + ["duration"],
           "sin volumen abs., tasas ni dst_port": ABS + RATE + ["dst_port", "dst_port_class", "src_port_class"]}
def sub(X, y, rng):
    if len(y) <= CAP: return X, y
    idx = np.concatenate([rng.choice(np.where(y == c)[0], max(1, round(CAP * (y == c).mean())), replace=False) for c in (0, 1)])
    return X.iloc[idx].reset_index(drop=True), y[idx]
res = {}
for seed in SEEDS:
    rng = np.random.default_rng(seed); S = {k: sub(X, y, rng) for k, (X, y) in FULL.items()}
    for cname, drop in CONFIGS.items():
        keep = [c for c in cols if c not in drop]
        for held in S:
            Xtr = pd.concat([S[k][0][keep] for k in S if k != held], ignore_index=True); ytr = np.concatenate([S[k][1] for k in S if k != held])
            for mt in ("logreg", "random_forest", "xgboost"):
                F_ = F.feature_columns
                import app.ml.models as MM
                orig = MM.feature_columns; MM.feature_columns = lambda unit, k=keep: k
                ocat = F.FLOW_CATEGORICAL; F.FLOW_CATEGORICAL = [c for c in ocat if c in keep]
                try:
                    pipe = M.build_pipeline(mt, {}, "flow", seed, 6); pipe.fit(Xtr, ytr); p = M.predict_proba(pipe, S[held][0][keep])
                finally: MM.feature_columns = orig; F.FLOW_CATEGORICAL = ocat
                yt = S[held][1]; res.setdefault((cname, mt, held), []).append((average_precision_score(yt, p), roc_auc_score(yt, p)))
    print("semilla", seed, "ok", flush=True)
out = [{"config": c, "model": m, "held_out": h, "pr_auc": float(np.mean([a for a, _ in v])), "roc_auc": float(np.mean([b for _, b in v]))} for (c, m, h), v in res.items()]
json.dump(out, open("/tmp/ablacion.json", "w"), indent=1)
for c in CONFIGS:
    for m in ("logreg", "random_forest", "xgboost"):
        r = {h: next(o for o in out if o["config"] == c and o["model"] == m and o["held_out"] == h) for h in FULL}
        print(f"{c:38s} {m:14s} " + " ".join(f"{h[-2:].strip()}:{r[h]['pr_auc']:.2f}/{r[h]['roc_auc']:.2f}" for h in FULL))
