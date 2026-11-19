"""CV anidada POR ESCENARIO (CTU-13): el escenario de prueba nunca participa en el ajuste.
Externo: se deja fuera 1 de 4 escenarios. Interno: dentro de los 3 restantes, leave-one-scenario-out (3 pliegues);
Optuna (TPE) optimiza PR-AUC media sobre esos 3 pliegues y el umbral se elige con las predicciones internas
(máx. exactitud balanceada, invariante a la prevalencia). Se submuestrea cada escenario a CAP flujos (estratificado)
para que ninguno domine. Se repite con varias semillas (submuestreo + modelos + Optuna). Ejecutar en el contenedor backend.
Uso: python anidada_por_escenario.py <cap> <trials> <semilla> [<semilla> ...]"""
import json, sys, time, warnings
import numpy as np, pandas as pd, optuna
from sklearn.metrics import average_precision_score, roc_auc_score, balanced_accuracy_score, recall_score, precision_score, confusion_matrix
from app.ml import data as D, prepare as P, models as M
from app.ml.features import feature_columns
warnings.filterwarnings("ignore"); optuna.logging.set_verbosity(optuna.logging.WARNING)
CAP, TRIALS, SEEDS = int(sys.argv[1]), int(sys.argv[2]), [int(s) for s in sys.argv[3:]]
files = {"Esc. 9 (Neris)": "/tmp/s09.binetflow", "Esc. 12 (NSIS.ay)": "/tmp/s12.binetflow", "Esc. 13 (Virut)": "/tmp/s13.binetflow"}
raw = {k: D.frame_from_file(open(v, "rb").read(), k.replace(" ", "_") + ".binetflow")[0] for k, v in files.items()}
raw["Esc. 11 (Rbot)"] = D.load_snapshot("/data/ml/datasets/1/flows.csv.gz")
def frame(df, name):
    meta = P.default_meta(name, df); ff = P.feature_frame(df, meta, True); ff = ff[ff["y"].notna()].reset_index(drop=True)
    return ff[feature_columns("flow")], ff["y"].astype(int).values
FULL = {k: frame(v, k) for k, v in raw.items()}
def sub(X, y, cap, rng):
    if len(y) <= cap: return X, y
    idx = np.concatenate([rng.choice(np.where(y == c)[0], max(1, round(cap * (y == c).mean())), replace=False) for c in (0, 1)])
    return X.iloc[idx].reset_index(drop=True), y[idx]
def pr(y, p): return float(average_precision_score(y, p)) if len(np.unique(y)) > 1 else float("nan")
def best_thr(y, p):
    ts = np.unique(np.round(p, 4)); ts = ts[(ts > 0) & (ts < 1)] if len(ts) > 2 else np.array([0.5])
    if len(ts) > 200: ts = np.quantile(p, np.linspace(0.01, 0.99, 199))
    return float(ts[int(np.argmax([balanced_accuracy_score(y, (p >= t).astype(int)) for t in ts]))])
def fitp(mt, params, seed, X, y):
    pipe = M.build_pipeline(mt, params, "flow", seed, 6); pipe.fit(X, y); return pipe
out, path = [], "/tmp/resultado_anidada_escenarios.json"
for seed in SEEDS:
    rng = np.random.default_rng(seed)
    S = {k: sub(X, y, CAP, rng) for k, (X, y) in FULL.items()}
    for held in S:
        tr = [k for k in S if k != held]; Xte, yte = S[held]
        for mt in ("dummy", "logreg", "random_forest", "hist_gb", "xgboost"):
            t0 = time.time(); space = M.effective_space(mt, None) if mt != "dummy" else []
            def cv_preds(params):
                res = []
                for v in tr:
                    Xa = pd.concat([S[k][0] for k in tr if k != v], ignore_index=True); ya = np.concatenate([S[k][1] for k in tr if k != v])
                    res.append((S[v][1], M.predict_proba(fitp(mt, params, seed, Xa, ya), S[v][0])))
                return res
            if space:
                st = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed), pruner=optuna.pruners.MedianPruner())
                def obj(trial):
                    rs = cv_preds(M.suggest_params(trial, space)); return float(np.nanmean([pr(y, p) for y, p in rs]))
                st.optimize(obj, n_trials=TRIALS); bp = st.best_params if False else M.suggest_params(optuna.trial.FixedTrial(st.best_params), space)
                rs = cv_preds(bp); thr = best_thr(np.concatenate([y for y, _ in rs]), np.concatenate([p for _, p in rs]))
                inner = float(st.best_value)
            else: bp, thr, inner = {}, 0.5, None
            Xtr = pd.concat([S[k][0] for k in tr], ignore_index=True); ytr = np.concatenate([S[k][1] for k in tr])
            p = M.predict_proba(fitp(mt, bp, seed, Xtr, ytr), Xte)
            def at(t):
                pred = (p >= t).astype(int); tn, fp, fn, tp = confusion_matrix(yte, pred, labels=[0, 1]).ravel()
                return {"recall": float(recall_score(yte, pred, zero_division=0)), "precision": float(precision_score(yte, pred, zero_division=0)), "balanced_acc": float(balanced_accuracy_score(yte, pred))}
            r = {"seed": seed, "held_out": held, "model": mt, "prevalence": float(yte.mean()), "n_test": int(len(yte)), "pr_auc": pr(yte, p),
                 "roc_auc": float(roc_auc_score(yte, p)) if len(np.unique(p)) > 1 else 0.5, "inner_pr_auc": inner, "threshold": thr, "at_thr": at(thr), "at_0.5": at(0.5),
                 "params": bp, "secs": round(time.time() - t0)}
            out.append(r); json.dump(out, open(path, "w"), indent=1)
            print(f"s{seed} {held:18s} {mt:14s} PR={r['pr_auc']:.3f} ROC={r['roc_auc']:.3f} thr={thr:.3f} bal@thr={r['at_thr']['balanced_acc']:.3f} bal@.5={r['at_0.5']['balanced_acc']:.3f} {r['secs']}s", flush=True)
