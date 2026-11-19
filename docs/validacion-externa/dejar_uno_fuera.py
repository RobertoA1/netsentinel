"""Validación dejando un escenario completo fuera (CTU-13): entrena con 3 escenarios y prueba en el 4.º.
Ejecutar dentro del contenedor backend. Mismos pipeline/variables y mejores hiperparámetros del Laboratorio ML (esc. 11)."""
import json, sys, warnings
import numpy as np, pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score, f1_score, precision_score, recall_score, balanced_accuracy_score, confusion_matrix
from app.ml import data as D, prepare as P, models as M
from app.ml.features import feature_columns
warnings.filterwarnings("ignore")
params = json.load(open("/tmp/params.json"))
files = {"Esc. 9 (Neris)": "/tmp/s09.binetflow", "Esc. 12 (NSIS.ay)": "/tmp/s12.binetflow", "Esc. 13 (Virut)": "/tmp/s13.binetflow"}
raw = {k: D.frame_from_file(open(v, "rb").read(), k.replace(" ", "_") + ".binetflow")[0] for k, v in files.items()}
raw["Esc. 11 (Rbot)"] = D.load_snapshot("/data/ml/datasets/1/flows.csv.gz")
def frame(df, name):
    meta = P.default_meta(name, df); ff = P.feature_frame(df, meta, True); ff = ff[ff["y"].notna()].reset_index(drop=True)
    return ff[feature_columns("flow")], ff["y"].astype(int).values
S = {k: frame(v, k) for k, v in raw.items()}
for k, (X, y) in S.items(): print(f"{k}: {len(y)} flujos, Botnet {y.mean():.1%}", flush=True)
rows = []
for held in S:
    Xtr = pd.concat([S[k][0] for k in S if k != held], ignore_index=True); ytr = np.concatenate([S[k][1] for k in S if k != held])
    Xte, yte = S[held]
    for mt in ("dummy", "logreg", "random_forest", "hist_gb", "xgboost"):
        pipe = M.build_pipeline(mt, params.get(mt, {}), "flow", 42, 4); pipe.fit(Xtr, ytr)
        p = M.predict_proba(pipe, Xte); pred = (p >= 0.5).astype(int)
        tn, fp, fn, tp = confusion_matrix(yte, pred, labels=[0, 1]).ravel()
        r = {"held_out": held, "model": mt, "n_train": int(len(ytr)), "n_test": int(len(yte)), "prevalence_test": round(float(yte.mean()), 3),
             "pr_auc": round(float(average_precision_score(yte, p)), 4), "roc_auc": round(float(roc_auc_score(yte, p)), 4) if len(np.unique(p)) > 1 else 0.5,
             "recall": round(float(recall_score(yte, pred, zero_division=0)), 4), "precision": round(float(precision_score(yte, pred, zero_division=0)), 4),
             "balanced_acc": round(float(balanced_accuracy_score(yte, pred)), 4), "tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn)}
        rows.append(r); print(r, flush=True)
json.dump(rows, open("/tmp/resultado_dejar_uno_fuera.json", "w"), indent=1)
