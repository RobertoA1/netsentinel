"""Validación dejando un escenario fuera con los 12 escenarios de CTU-13 disponibles (todos menos el 10, que no publica binetflow).
Modo 'rapido': parámetros por defecto, compara variables crudas vs rango percentil por escenario (adaptación de dominio sin etiquetas).
Modo 'anidado': Optuna (TPE) en validación interna por grupos de escenarios (4 grupos) sobre los 11 restantes; umbral interno.
Uso (en el contenedor backend): python multiescenario.py rapido <cap> <semillas...>   |   python multiescenario.py anidado <rep> <cap> <trials> <semillas...>
rep = crudas | rango"""
import json, sys, time, warnings, glob
import numpy as np, pandas as pd, optuna
from sklearn.metrics import average_precision_score, roc_auc_score, balanced_accuracy_score, recall_score, precision_score
from app.ml import data as D, prepare as P, models as M
from app.ml import features as F
warnings.filterwarnings("ignore"); optuna.logging.set_verbosity(optuna.logging.WARNING)
import os
MODE = sys.argv[1]
if MODE == "rapido": REP, CAP, TRIALS, SEEDS = None, int(sys.argv[2]), 0, [int(s) for s in sys.argv[3:]]
else: REP, CAP, TRIALS, SEEDS = sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), [int(s) for s in sys.argv[5:]]
cols = F.feature_columns("flow"); NUM = [c for c in cols if c not in F.FLOW_CATEGORICAL]
NAMES = {1: "Neris", 2: "Neris", 3: "Rbot", 4: "Rbot", 5: "Virut", 6: "Menti", 7: "Sogou", 8: "Murlo", 9: "Neris", 11: "Rbot", 12: "NSIS.ay", 13: "Virut"}
def frame(df, n):
    meta = P.default_meta(n, df); ff = P.feature_frame(df, meta, True); ff = ff[ff["y"].notna()].reset_index(drop=True)
    return ff[cols], ff["y"].astype(int).values
FULL = {}
for f in sorted(glob.glob("/tmp/ctu_lab/s[0-9][0-9].binetflow")):
    k = int(f.split('/s')[-1][:2]); FULL[k] = frame(D.frame_from_file(open(f, "rb").read(), f"s{k}.binetflow")[0], f"s{k}")
FULL[11] = frame(D.load_snapshot("/data/ml/datasets/1/flows.csv.gz"), "s11")
FULL = dict(sorted(FULL.items()))
for k, (X, y) in FULL.items(): print(f"Esc. {k} ({NAMES[k]}): {len(y)} flujos, Botnet {y.mean():.1%}", flush=True)
def sub(X, y, rng):
    if len(y) <= CAP: return X, y
    idx = np.concatenate([rng.choice(np.where(y == c)[0], max(1, round(CAP * (y == c).mean())), replace=False) for c in (0, 1)])
    return X.iloc[idx].reset_index(drop=True), y[idx]
def rank(X):
    X = X.copy()
    for c in NUM: X[c] = X[c].astype(float).rank(pct=True)
    return X
def pr(y, p): return float(average_precision_score(y, p)) if len(np.unique(y)) > 1 else float("nan")
def roc(y, p): return float(roc_auc_score(y, p)) if len(np.unique(y)) > 1 and len(np.unique(p)) > 1 else 0.5
def fit(mt, params, seed, X, y): pipe = M.build_pipeline(mt, params, "flow", seed, int(os.environ.get("NJ", 6))); pipe.fit(X, y); return pipe
def best_thr(y, p):
    ts = np.quantile(p, np.linspace(0.01, 0.99, 199)); return float(ts[int(np.argmax([balanced_accuracy_score(y, (p >= t).astype(int)) for t in ts]))])
_FN = f"/tmp/multi_{MODE}_{REP or 'x'}_{'_'.join(map(str,SEEDS))}{'' if TRIALS == 10 else '_t' + str(TRIALS)}.json"
out = json.load(open(_FN)) if os.path.exists(_FN) else []
_done = {(o['seed'], o['rep'], o['held_out'], o['model']) for o in out}
for seed in SEEDS:
    rng = np.random.default_rng(seed); S0 = {k: sub(X, y, rng) for k, (X, y) in FULL.items()}
    reps = ("crudas", "rango") if MODE == "rapido" else (REP,)
    for rep in reps:
        S = {k: ((rank(X) if rep == "rango" else X), y) for k, (X, y) in S0.items()}
        for held in S:
            tr = [k for k in S if k != held]; Xte, yte = S[held]
            Xtr = pd.concat([S[k][0] for k in tr], ignore_index=True); ytr = np.concatenate([S[k][1] for k in tr])
            for mt in (("dummy", "logreg", "random_forest", "hist_gb", "xgboost") if MODE == "anidado" else ("logreg", "random_forest", "hist_gb", "xgboost")):
                if (seed, rep, held, mt) in _done: continue
                t0 = time.time(); bp, thr, inner = {}, 0.5, None
                if MODE == "anidado" and mt != "dummy":
                    space = M.effective_space(mt, None); order = np.random.default_rng(seed).permutation(tr); groups = [list(order[i::4]) for i in range(4)]
                    def cvp(params):
                        res = []
                        for g in groups:
                            ta = [k for k in tr if k not in g]
                            Xa = pd.concat([S[k][0] for k in ta], ignore_index=True); ya = np.concatenate([S[k][1] for k in ta])
                            pipe = fit(mt, params, seed, Xa, ya)
                            for k in g: res.append((S[k][1], M.predict_proba(pipe, S[k][0])))
                        return res
                    st = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed), pruner=optuna.pruners.MedianPruner())
                    st.optimize(lambda t: float(np.nanmean([pr(y, p) for y, p in cvp(M.suggest_params(t, space))])), n_trials=TRIALS)
                    bp = M.suggest_params(optuna.trial.FixedTrial(st.best_params), space); rs = cvp(bp); inner = float(st.best_value)
                    thr = best_thr(np.concatenate([y for y, _ in rs]), np.concatenate([p for _, p in rs]))
                p = M.predict_proba(fit(mt, bp, seed, Xtr, ytr), Xte); pred = (p >= thr).astype(int)
                out.append({"seed": seed, "rep": rep, "held_out": held, "familia": NAMES[held], "model": mt, "prevalence": float(yte.mean()), "n_pos_test": int(yte.sum()),
                            "pr_auc": pr(yte, p), "roc_auc": roc(yte, p), "inner_pr_auc": inner, "threshold": thr, "params": bp,
                            "recall": float(recall_score(yte, pred, zero_division=0)), "precision": float(precision_score(yte, pred, zero_division=0)),
                            "balanced_acc": float(balanced_accuracy_score(yte, pred)), "secs": round(time.time() - t0)})
                json.dump(out, open(_FN, "w"), indent=1)
                print(f"s{seed} {rep:6s} esc{held:2d} {NAMES[held]:8s} {mt:13s} PR={out[-1]['pr_auc']:.3f} ROC={out[-1]['roc_auc']:.3f} {out[-1]['secs']}s", flush=True)
