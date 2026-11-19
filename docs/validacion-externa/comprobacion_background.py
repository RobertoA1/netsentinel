"""Comprobación de fuga indirecta en las variables de host: las ventanas de hibrido.py se calcularon sobre archivos con solo flujos Botnet/Normal,
de modo que la ventana de un host infectado contiene solo flujos botnet. Aquí el escenario excluido se evalúa de tres formas sobre EXACTAMENTE los mismos flujos etiquetados:
 (a) solo flujo (sin contexto); (b) flujo + ventana PURA (calculada sin Background); (c) flujo + ventana REAL (calculada con todo el tráfico, incl. Background).
Entrenamiento: siempre con las variables de (a) o (b) del resto de escenarios (archivos solo etiquetados). Hiperparámetros de Optuna ya hallados. Métrica: PR-AUC.
Uso (contenedor): python bg.py <semilla> <W> <escenario>...   (requiere /tmp/raw/<archivo>.binetflow.xz)"""
import sys, json, lzma
SEED = int(sys.argv[1]); W = float(sys.argv[2]); HELD = [int(x) for x in sys.argv[3:]]; sys.argv = ["x", "anidado", "crudas", "2500", "10", str(SEED)]
src = open("/tmp/me.py").read(); exec(src.split("_FN = ")[0])
FILE = {5: "capture20110815-2", 7: "capture20110816-2", 12: "capture20110819"}
WN = F.WINDOW_NUMERIC; WC = ["w_" + c for c in WN]
RAW = {}
for f in sorted(glob.glob("/tmp/ctu_lab/s[0-9][0-9].binetflow")):
    k = int(f.split('/s')[-1][:2]); RAW[k] = D.frame_from_file(open(f, "rb").read(), f"s{k}.binetflow")[0]
RAW[11] = D.load_snapshot("/data/ml/datasets/1/flows.csv.gz")
def feats(df, n, W, with_window):
    meta = P.default_meta(n, df); d = D.labelled_frame(df, meta["label_map"])
    ff = F.build_feature_frame(d, "flow", None, only_labeled=False)
    if with_window:
        wf = F.window_features(d, W, only_labeled=False)[["src_ip", "win_start"] + WN]; wf.columns = ["_src_ip", "_ws"] + WC
        w = max(1, int(round(W * 60))); ff["_ws"] = (np.floor(ff["_t"].astype(float) / w) * w).astype(float)
        n0 = len(ff); ff = ff.merge(wf, on=["_src_ip", "_ws"], how="left"); assert len(ff) == n0
    ff = ff[ff["y"].notna()].reset_index(drop=True)
    return ff[cols + (WC if with_window else [])], ff["y"].astype(int).values
def feats_ids(df, n):  # claves de los flujos etiquetados, para comprobar que (a), (b) y (c) usan los mismos
    meta = P.default_meta(n, df); d = D.labelled_frame(df, meta["label_map"]); return int(d["y_flow"].notna().sum())
PURA = {k: feats(RAW[k], f"s{k}", W, True) for k in sorted(RAW)}
PURA_F = {k: (X[cols], y) for k, (X, y) in PURA.items()}
BASE = ("logreg", "random_forest", "hist_gb", "xgboost")
prev = {(o["held_out"], o["model"]): o["params"] for o in json.load(open(f"/tmp/multi_anidado_crudas_{SEED}.json"))}
CUR = list(cols)
res = []
for held in HELD:
    raw = D.frame_from_file(lzma.open(f"/tmp/raw/{FILE[held]}.binetflow.xz").read(), f"s{held}.binetflow")[0]
    # (a),(b): ventana pura sobre los flujos etiquetados del archivo original; (c): ventana real con Background
    Xa, ya = feats(raw, f"s{held}", W, False)
    lab = raw[raw["label_raw"].notna()] if "label_raw" in raw else raw
    meta = P.default_meta(f"s{held}", raw); dl = D.labelled_frame(raw, meta["label_map"])
    pure_raw = dl[dl["y_flow"].notna()]
    wfp = F.window_features(pure_raw, W, only_labeled=False)[["src_ip", "win_start"] + WN]; wfp.columns = ["_src_ip", "_ws"] + WC
    ffp = F.build_feature_frame(pure_raw, "flow", None, only_labeled=False)
    w = max(1, int(round(W * 60))); ffp["_ws"] = (np.floor(ffp["_t"].astype(float) / w) * w).astype(float); ffp = ffp.merge(wfp, on=["_src_ip", "_ws"], how="left")
    Xb, yb = ffp[cols + WC], ffp["y"].astype(int).values
    Xc, yc = feats(raw, f"s{held}", W, True)
    assert len(yb) == len(yc) == len(ya) and (yb == yc).all()
    print(f"esc {held}: {len(yc)} flujos etiquetados, {int(yc.sum())} botnet; flujos totales del archivo {len(raw)}", flush=True)
    tr = [k for k in sorted(RAW) if k != held]; rng = np.random.default_rng(SEED)
    S = {k: sub(*PURA[k], rng) for k in PURA}
    Xtr_b = pd.concat([S[k][0] for k in tr], ignore_index=True); ytr = np.concatenate([S[k][1] for k in tr])
    for mt in BASE:
        bp = prev[(held, mt)]
        M.feature_columns = lambda unit, c=cols: c; M.FLOW_LOG_COLS = [c for c in M.FLOW_LOG_COLS if not c.startswith("w_")]
        pa = M.predict_proba(fit(mt, bp, SEED, Xtr_b[cols], ytr), Xa)
        M.feature_columns = lambda unit: cols + WC; M.FLOW_LOG_COLS = M.FLOW_LOG_COLS + ["w_" + c for c in F.WINDOW_LOG_COLS]
        m = fit(mt, bp, SEED, Xtr_b, ytr); pb = M.predict_proba(m, Xb); pc = M.predict_proba(m, Xc)
        r = {"seed": SEED, "W": W, "held_out": held, "model": mt, "n": len(yc), "n_pos": int(yc.sum()), "pr_flujo": pr(ya, pa), "pr_ventana_pura": pr(yb, pb), "pr_ventana_real": pr(yc, pc)}
        res.append(r); print(json.dumps(r), flush=True)
    json.dump(res, open(f"/tmp/bg_{SEED}.json", "w"), indent=1)
