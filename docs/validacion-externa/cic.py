"""Validación externa: se entrena con los 12 escenarios CTU-13 (Argus/binetflow) y se prueba en CIC-IDS2017 (viernes por la mañana: Bot frente a BENIGN), un conjunto de otra red y otro exportador de flujos.
Variables comunes a ambos formatos (se excluyen 'state', 'dir' y 'direction', que son específicas de Argus): duration, bytes_out, bytes_in, bytes_total, packets, bytes_per_packet, ratio_out,
bytes_per_s, pkts_per_s, dst_port, proto, dst_port_class, src_port_class.  Variante 'host': se añaden 8 variables causales de contexto del host que no dependen de la resolución temporal ni del estado
(c_n_conn, c_n_dst, c_n_dport, c_entropy_dport, c_entropy_dst, c_prop_tcp, c_prop_udp, c_prop_icmp; ventana de 5 min; CIC tiene resolución de minuto).
Hiperparámetros: Optuna (10 intentos) con validación interna por grupos de escenarios CTU-13 (4 grupos); umbral por exactitud balanceada sobre las predicciones internas.
Limitaciones de la comparación: CIC mide longitudes de carga útil y Argus bytes totales; el estado de conexión no existe en CIC; CIC tiene errores de construcción de flujos y de etiquetado documentados en la literatura.
Uso (contenedor): python cic.py <semilla> <flow|host>   (CIC en /tmp/cic/Friday-WorkingHours-Morning.pcap_ISCX.csv)"""
import sys, json
SEED = int(sys.argv[1]); VAR = sys.argv[2]; sys.argv = ["x", "anidado", "crudas", "2500", "10", str(SEED)]
src = open("/tmp/me.py").read(); exec(src.split("_FN = ")[0])
sys.path.insert(0, "/tmp"); import causal as C
COMMON = ["duration", "bytes_out", "bytes_in", "bytes_total", "packets", "bytes_per_packet", "ratio_out", "bytes_per_s", "pkts_per_s", "dst_port", "proto", "dst_port_class", "src_port_class"]
HOST = ["c_n_conn", "c_n_dst", "c_n_dport", "c_entropy_dport", "c_entropy_dst", "c_prop_tcp", "c_prop_udp", "c_prop_icmp"]
USE = COMMON + (HOST if VAR == "host" else []); CAT = ["proto", "dst_port_class", "src_port_class"]
# ---- CIC-IDS2017
raw = pd.read_csv("/tmp/cic/Friday-WorkingHours-Morning.pcap_ISCX.csv", encoding="latin1", skipinitialspace=True); raw.columns = [c.strip() for c in raw.columns]
n_ = len(raw); dur = pd.to_numeric(raw["Flow Duration"], errors="coerce").clip(lower=0) / 1e6
cic = pd.DataFrame({"ts": pd.to_datetime(raw["Timestamp"], dayfirst=True, errors="coerce").astype("int64") / 1e9, "src_ip": raw["Source IP"], "dst_ip": raw["Destination IP"],
                    "src_port": raw["Source Port"], "dst_port": raw["Destination Port"], "proto": raw["Protocol"].map({6: "tcp", 17: "udp", 1: "icmp"}).fillna("other"),
                    "state": "unk", "dir": "unk", "direction": "unk", "duration": dur, "bytes_out": raw["Total Length of Fwd Packets"], "bytes_in": raw["Total Length of Bwd Packets"],
                    "packets": raw["Total Fwd Packets"] + raw["Total Backward Packets"]})
yc = (raw["Label"].str.strip() == "Bot").astype(int).values
fc = F.flow_features(cic).reset_index(drop=True); Xc = fc[COMMON].copy()
if VAR == "host": Xc = pd.concat([Xc, C.causal_features(cic, 5.0).reset_index(drop=True)[HOST]], axis=1)
print(f"CIC viernes mañana: {n_} flujos, {int(yc.sum())} bot ({yc.mean():.2%})", flush=True)
# ---- entrenamiento CTU-13
if VAR == "host":
    RAW = {}
    for f in sorted(glob.glob("/tmp/ctu_lab/s[0-9][0-9].binetflow")):
        k = int(f.split('/s')[-1][:2]); RAW[k] = D.frame_from_file(open(f, "rb").read(), f"s{k}.binetflow")[0]
    RAW[11] = D.load_snapshot("/data/ml/datasets/1/flows.csv.gz")
    def hyb(df, n):
        meta = P.default_meta(n, df); d = D.labelled_frame(df, meta["label_map"]); ff = F.build_feature_frame(d, "flow", None, only_labeled=True)
        cf = C.causal_features(d, 5.0); ff = pd.concat([ff.reset_index(drop=True), cf.reset_index(drop=True)], axis=1); ff = ff[ff["y"].notna()].reset_index(drop=True)
        return ff[COMMON + HOST], ff["y"].astype(int).values
    TRAIN = {k: hyb(RAW[k], f"s{k}") for k in sorted(RAW)}
else:
    TRAIN = {k: (X[COMMON], y) for k, (X, y) in FULL.items()}
rng = np.random.default_rng(SEED); S = {k: sub(X, y, rng) for k, (X, y) in TRAIN.items()}
F.FLOW_CATEGORICAL = list(CAT); M.feature_columns = lambda unit: USE; M.FLOW_LOG_COLS = [c for c in M.FLOW_LOG_COLS if c in USE] + [c for c in ("c_n_conn", "c_n_dst", "c_n_dport") if c in USE]
ks = sorted(S); order = np.random.default_rng(SEED).permutation(ks); groups = [list(order[i::4]) for i in range(4)]
Xall = pd.concat([S[k][0] for k in ks], ignore_index=True); yall = np.concatenate([S[k][1] for k in ks])
BASE = ("logreg", "random_forest", "hist_gb", "xgboost"); ENS = ("logreg", "random_forest", "hist_gb"); res, PT, TH, OOF = [], {}, {}, {}
for mt in BASE:
    space = M.effective_space(mt, None)
    def cvp(params):
        r = []
        for g in groups:
            ta = [k for k in ks if k not in g]; Xa = pd.concat([S[k][0] for k in ta], ignore_index=True); ya = np.concatenate([S[k][1] for k in ta]); pipe = fit(mt, params, SEED, Xa, ya)
            for k in g: r.append((S[k][1], M.predict_proba(pipe, S[k][0])))
        return r
    st = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=SEED), pruner=optuna.pruners.MedianPruner())
    st.optimize(lambda t: float(np.nanmean([pr(y, p) for y, p in cvp(M.suggest_params(t, space))])), n_trials=10)
    bp = M.suggest_params(optuna.trial.FixedTrial(st.best_params), space); rs = cvp(bp); OOF[mt] = (np.concatenate([y for y, _ in rs]), np.concatenate([p for _, p in rs]))
    TH[mt] = best_thr(*OOF[mt]); PT[mt] = np.concatenate([M.predict_proba(fit(mt, bp, SEED, Xall, yall), Xc.iloc[i:i + 200000]) for i in range(0, len(Xc), 200000)])
    print(f"{mt}: interno PR={st.best_value:.3f}", flush=True)
PT["LR+RF+HGB"] = np.mean([PT[m] for m in ENS], axis=0); OOF["LR+RF+HGB"] = (OOF["logreg"][0], np.mean([OOF[m][1] for m in ENS], axis=0)); TH["LR+RF+HGB"] = best_thr(*OOF["LR+RF+HGB"])
for mt, p in PT.items():
    yh = p >= TH[mt]; r = {"seed": SEED, "variante": VAR, "model": mt, "n": int(len(yc)), "n_bot": int(yc.sum()), "prevalencia": float(yc.mean()), "pr_auc": pr(yc, p), "roc_auc": roc(yc, p),
         "umbral": float(TH[mt]), "recall": float(yh[yc == 1].mean()), "fpr": float(yh[yc == 0].mean()), "precision": float(yc[yh].mean()) if yh.any() else None, "alertas_por_100k": float(yh.mean() * 1e5)}
    res.append(r); print(json.dumps(r), flush=True)
json.dump(res, open(f"/tmp/cic_{VAR}_{SEED}.json", "w"), indent=1)
