"""Evaluación realista: el escenario excluido se evalúa con TODO su tráfico, tratando el Background (sin etiqueta) como Normal, sin submuestreo.
Entrenamiento idéntico al de la validación principal (flujos etiquetados submuestreados del resto de escenarios, hiperparámetros de Optuna ya hallados).
Se reportan, con el umbral elegido en la validación interna: sensibilidad sobre bots, falsos positivos sobre tráfico Normal etiquetado y sobre Background,
y alertas por cada 100 000 flujos. La PR-AUC con Background como negativo es muy sensible a la prevalencia (la prevalencia de botnet es muy baja).
Uso (contenedor, ML_MAX_UPLOAD_MB alto): python fondo.py <semilla>   (archivos en /tmp/raw/<archivo>.binetflow.xz)"""
import sys, json, lzma, gc
SEED = int(sys.argv[1]); sys.argv = ["x", "anidado", "crudas", "2500", "10", str(SEED)]
src = open("/tmp/me.py").read(); exec(src.split("_FN = ")[0])
FILE = {1: "capture20110810", 2: "capture20110811", 3: "capture20110812", 4: "capture20110815", 5: "capture20110815-2", 6: "capture20110816", 7: "capture20110816-2",
        8: "capture20110816-3", 9: "capture20110817", 11: "capture20110818-2", 12: "capture20110819", 13: "capture20110815-3"}
BASE = ("logreg", "random_forest", "hist_gb", "xgboost"); ENS = ("logreg", "random_forest", "hist_gb")
pa = {(o["held_out"], o["model"]): (o["params"], o["threshold"]) for o in json.load(open(f"/tmp/multi_anidado_crudas_{SEED}.json"))}
thr_ens = {o["held_out"]: o["threshold"] for o in json.load(open(f"/tmp/ensambles_{SEED}.json")) if o["model"] == "LR+RF+HGB"}
rng = np.random.default_rng(SEED); S = {k: sub(X, y, rng) for k, (X, y) in FULL.items()}
def pred_chunks(pipe, X, n=400000): return np.concatenate([M.predict_proba(pipe, X.iloc[i:i + n]) for i in range(0, len(X), n)])
out = []
for held in sorted(S):
    raw = D.frame_from_file(lzma.open(f"/tmp/raw/{FILE[held]}.binetflow.xz").read(), f"s{held}.binetflow")[0]
    meta = P.default_meta(f"s{held}", raw); lm = {k: ("Normal" if v == D.EXCLUDED else v) for k, v in meta["label_map"].items()}
    lab = {k: v for k, v in meta["label_map"].items()}
    d = D.labelled_frame(raw, lm); is_bg = D.labelled_frame(raw, lab)["y_flow"].isna().values
    ff = F.build_feature_frame(d, "flow", None, only_labeled=False); Xte = ff[cols]; yte = ff["y"].astype(int).values
    n, nb, nbg = len(yte), int(yte.sum()), int(is_bg.sum()); del raw, d, ff; gc.collect()
    tr = [k for k in S if k != held]; Xtr = pd.concat([S[k][0] for k in tr], ignore_index=True); ytr = np.concatenate([S[k][1] for k in tr])
    P_ = {}
    for mt in BASE: P_[mt] = pred_chunks(fit(mt, pa[(held, mt)][0], SEED, Xtr, ytr), Xte)
    P_["LR+RF+HGB"] = np.mean([P_[m] for m in ENS], axis=0)
    labeled = ~is_bg; normal_lab = labeled & (yte == 0)
    for mt, p in P_.items():
        thr = thr_ens[held] if mt == "LR+RF+HGB" else pa[(held, mt)][1]; yh = p >= thr
        r = {"seed": SEED, "held_out": held, "familia": NAMES[held], "model": mt, "n_flujos": n, "n_botnet": nb, "n_background": nbg, "prevalencia": nb / n,
             "pr_auc_realista": pr(yte, p), "pr_auc_solo_etiquetados": pr(yte[labeled], p[labeled]), "roc_auc_realista": roc(yte, p),
             "recall": float(yh[yte == 1].mean()), "fpr_normal_etiquetado": float(yh[normal_lab].mean()) if normal_lab.any() else None,
             "fpr_background": float(yh[is_bg].mean()) if is_bg.any() else None, "alertas_por_100k": float(yh.mean() * 1e5),
             "precision_realista": float(yte[yh].mean()) if yh.any() else None}
        out.append(r); print(f"s{SEED} esc{held:2d} {NAMES[held]:8s} {mt:10s} n={n} bot={nb} PRreal={r['pr_auc_realista']:.3f} PRetiq={r['pr_auc_solo_etiquetados']:.3f} rec={r['recall']:.3f} fpr_bg={r['fpr_background']} prec={r['precision_realista']}", flush=True)
    json.dump(out, open(f"/tmp/fondo_{SEED}.json", "w"), indent=1); del Xte, Xtr, P_; gc.collect()
