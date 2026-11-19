"""Validación externa ENTRE ESCENARIOS de CTU-13: entrena con todo un escenario y evalúa en el otro (y al revés).
Se ejecuta dentro del contenedor backend. Usa las mismas variables, pipeline y mejores hiperparámetros del Laboratorio ML
(trabajo #1, escenario 11). Entrada: /tmp/params.json y los binetflow indicados."""
import json, sys, warnings
import numpy as np, pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score, f1_score, precision_score, recall_score, confusion_matrix
from app.ml import data as D, prepare as P, models as M
from app.ml.features import feature_columns
warnings.filterwarnings("ignore")

params = json.load(open("/tmp/params.json"))
sc11 = D.load_snapshot("/data/ml/datasets/1/flows.csv.gz")
sc12, _ = D.frame_from_file(open(sys.argv[1], "rb").read(), "e12.binetflow")

def frame(df, name):
    meta = P.default_meta(name, df)
    ff = P.feature_frame(df, meta, True)
    ff = ff[ff["y"].notna()].reset_index(drop=True)
    cols = feature_columns("flow")
    return ff[cols], ff["y"].astype(int).values

sets = {"Esc. 11": frame(sc11, "e11"), "Esc. 12": frame(sc12, "e12")}
for k, (X, y) in sets.items():
    print(f"{k}: {len(y)} flujos etiquetados, Botnet {y.mean():.1%}")
rows = []
for tr, te in (("Esc. 11", "Esc. 12"), ("Esc. 12", "Esc. 11")):
    Xa, ya = sets[tr]; Xb, yb = sets[te]
    for mt in ("dummy", "logreg", "random_forest", "hist_gb", "xgboost"):
        pipe = M.build_pipeline(mt, params.get(mt, {}), "flow", 42, 4)
        pipe.fit(Xa, ya)
        p = M.predict_proba(pipe, Xb)
        pred = (p >= 0.5).astype(int)
        tn, fp, fn, tp = confusion_matrix(yb, pred, labels=[0, 1]).ravel()
        two = len(np.unique(p)) > 1
        rows.append({"train": tr, "test": te, "model": mt, "prevalence_test": round(float(yb.mean()), 3),
                     "pr_auc": round(float(average_precision_score(yb, p)), 4), "roc_auc": round(float(roc_auc_score(yb, p)), 4) if two else 0.5,
                     "precision": round(float(precision_score(yb, pred, zero_division=0)), 4), "recall": round(float(recall_score(yb, pred, zero_division=0)), 4),
                     "f1": round(float(f1_score(yb, pred, zero_division=0)), 4), "tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn)})
        print(rows[-1], flush=True)
json.dump(rows, open("/tmp/resultado_entre_escenarios.json", "w"), indent=1)
