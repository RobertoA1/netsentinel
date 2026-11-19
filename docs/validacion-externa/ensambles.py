"""Ensambles por voto suave (promedio de probabilidades) con los mejores hiperparámetros ya hallados por Optuna (multi_anidado_crudas_<semilla>.json).
Mismo protocolo: se deja un escenario fuera; umbral por exactitud balanceada sobre las predicciones internas agrupadas por escenario (4 grupos).
Uso (contenedor backend, con /tmp/me.py presente): python ens.py <semilla>"""
import sys, json, itertools
SEED = int(sys.argv[1]); sys.argv = ["x", "anidado", "crudas", "2500", "10", str(SEED)]
src = open("/tmp/me.py").read(); exec(src.split("_FN = ")[0])
BASE = ("logreg", "random_forest", "hist_gb", "xgboost")
COMBOS = {"RF+HGB": ("random_forest", "hist_gb"), "LR+RF+HGB": ("logreg", "random_forest", "hist_gb"), "RF+HGB+XGB": ("random_forest", "hist_gb", "xgboost"), "los 4": BASE}
prev = {(o["held_out"], o["model"]): o["params"] for o in json.load(open(f"/tmp/multi_anidado_crudas_{SEED}.json"))}
rng = np.random.default_rng(SEED); S = {k: sub(X, y, rng) for k, (X, y) in FULL.items()}
out = []
for held in S:
    tr = [k for k in S if k != held]; Xte, yte = S[held]
    Xtr = pd.concat([S[k][0] for k in tr], ignore_index=True); ytr = np.concatenate([S[k][1] for k in tr])
    order = np.random.default_rng(SEED).permutation(tr); groups = [list(order[i::4]) for i in range(4)]
    inner, test = {}, {}
    for mt in BASE:
        bp = prev[(held, mt)]; ys, ps = [], []
        for g in groups:
            ta = [k for k in tr if k not in g]
            Xa = pd.concat([S[k][0] for k in ta], ignore_index=True); ya = np.concatenate([S[k][1] for k in ta])
            pipe = fit(mt, bp, SEED, Xa, ya)
            for k in g: ys.append(S[k][1]); ps.append(M.predict_proba(pipe, S[k][0]))
        inner[mt] = (np.concatenate(ys), np.concatenate(ps)); test[mt] = M.predict_proba(fit(mt, bp, SEED, Xtr, ytr), Xte)
    for name, ms in COMBOS.items():
        yi = inner[ms[0]][0]; pi = np.mean([inner[m][1] for m in ms], axis=0); thr = best_thr(yi, pi)
        p = np.mean([test[m] for m in ms], axis=0); pred = (p >= thr).astype(int)
        out.append({"seed": SEED, "held_out": held, "familia": NAMES[held], "model": name, "pr_auc": pr(yte, p), "roc_auc": roc(yte, p), "threshold": thr,
                    "recall": float(recall_score(yte, pred, zero_division=0)), "precision": float(precision_score(yte, pred, zero_division=0)),
                    "balanced_acc": float(balanced_accuracy_score(yte, pred))})
        print(f"s{SEED} esc{held:2d} {NAMES[held]:8s} {name:11s} PR={out[-1]['pr_auc']:.3f}", flush=True)
    json.dump(out, open(f"/tmp/ensambles_{SEED}.json", "w"), indent=1)
