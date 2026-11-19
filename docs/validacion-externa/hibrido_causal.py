"""Variables de flujo + contexto CAUSAL del host de origen (causal.py: solo flujos de esa IP dentro de la ventana de W minutos hasta el flujo actual, sin futuro; prefijo c_).
Versión causal de hibrido.py: misma evaluación, mismos flujos, mismos hiperparámetros.
Mismo protocolo que ensambles.py: se deja un escenario fuera; mismos flujos submuestreados; hiperparámetros de Optuna ya hallados para flujos
(conservador: no se reajustan para las variables nuevas); umbral interno por exactitud balanceada; se evalúan los 4 modelos y el ensamble LR+RF+HGB.
Uso (contenedor): python hib.py <semilla> <W1> [<W2> ...]   (W en minutos)"""
import sys, json
SEED = int(sys.argv[1]); WS = [float(w) for w in sys.argv[2:]]; sys.argv = ["x", "anidado", "crudas", "2500", "10", str(SEED)]
src = open("/tmp/me.py").read(); exec(src.split("_FN = ")[0])
import sys as _s; _s.path.insert(0, "/tmp"); import causal as C
WC = ["c_" + c for c in C.CAUSAL]
RAW = {}
for f in sorted(glob.glob("/tmp/ctu_lab/s[0-9][0-9].binetflow")):
    k = int(f.split('/s')[-1][:2]); RAW[k] = D.frame_from_file(open(f, "rb").read(), f"s{k}.binetflow")[0]
RAW[11] = D.load_snapshot("/data/ml/datasets/1/flows.csv.gz")
def hybrid(df, n, W):
    meta = P.default_meta(n, df); d = D.labelled_frame(df, meta["label_map"])
    ff = F.build_feature_frame(d, "flow", None, only_labeled=True)
    cf = C.causal_features(d, W); cf.index = range(len(cf)); ff = pd.concat([ff.reset_index(drop=True), cf.reset_index(drop=True)], axis=1)
    ff = ff[ff["y"].notna()].reset_index(drop=True); return ff[cols + WC], ff["y"].astype(int).values
M.feature_columns = lambda unit: cols + WC
M.FLOW_LOG_COLS = list(M.FLOW_LOG_COLS) + ["c_" + c for c in C.CAUSAL_LOG]
BASE = ("logreg", "random_forest", "hist_gb", "xgboost"); ENS = ("logreg", "random_forest", "hist_gb")
prev = {(o["held_out"], o["model"]): o["params"] for o in json.load(open(f"/tmp/multi_anidado_crudas_{SEED}.json"))}
out = []
for W in WS:
    H = {k: hybrid(RAW[k], f"s{k}", W) for k in sorted(RAW)}
    for k, (X, y) in H.items(): assert len(y) == len(FULL[k][1]) and (y == FULL[k][1]).all(), k
    rng = np.random.default_rng(SEED); S = {k: sub(X, y, rng) for k, (X, y) in H.items()}
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
        for name, ms in list(((m, (m,)) for m in BASE)) + [("LR+RF+HGB", ENS)]:
            yi = inner[ms[0]][0]; pi = np.mean([inner[m][1] for m in ms], axis=0); thr = best_thr(yi, pi)
            p = np.mean([test[m] for m in ms], axis=0); pred = (p >= thr).astype(int)
            out.append({"seed": SEED, "W": W, "held_out": held, "familia": NAMES[held], "model": name, "pr_auc": pr(yte, p), "roc_auc": roc(yte, p),
                        "recall": float(recall_score(yte, pred, zero_division=0)), "precision": float(precision_score(yte, pred, zero_division=0)),
                        "balanced_acc": float(balanced_accuracy_score(yte, pred))})
            print(f"s{SEED} W={W:g} esc{held:2d} {NAMES[held]:8s} {name:10s} PR={out[-1]['pr_auc']:.3f}", flush=True)
        json.dump(out, open(f"/tmp/causal_{SEED}.json", "w"), indent=1)
