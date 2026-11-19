"""Variables de contexto del host CAUSALES: para cada flujo, agregados de los flujos de su misma IP de origen dentro de su ventana (tumbling, W minutos)
que ocurrieron hasta ese flujo inclusive (orden por tiempo; los empates, por orden de fila). No usa ningún flujo posterior: una detección en línea no necesita esperar.
Variables (prefijo c_): n_conn, n_dst, n_dport, entropy_dport, entropy_dst, bytes_out_sum, bytes_in_sum, pkts_sum, bytes_out_mean, pkts_mean, ratio_out,
prop_tcp, prop_udp, prop_icmp, prop_state_est, prop_state_attempt, prop_state_reset, mean_gap_s, std_gap_s, cv_gap  (se omiten las de beaconing)."""
import numpy as np, pandas as pd
from app.ml import features as F
CAUSAL = ["n_conn", "n_dst", "n_dport", "entropy_dport", "entropy_dst", "bytes_out_sum", "bytes_in_sum", "pkts_sum", "bytes_out_mean", "pkts_mean", "ratio_out",
          "prop_tcp", "prop_udp", "prop_icmp", "prop_state_est", "prop_state_attempt", "prop_state_reset", "mean_gap_s", "std_gap_s", "cv_gap"]
CAUSAL_LOG = ["n_conn", "n_dst", "n_dport", "bytes_out_sum", "bytes_in_sum", "pkts_sum", "bytes_out_mean", "pkts_mean", "mean_gap_s", "std_gap_s"]
def _xlogx(c): c = np.asarray(c, float); return np.where(c > 0, c * np.log2(np.where(c > 0, c, 1)), 0.0)
def causal_features(d: pd.DataFrame, W: float) -> pd.DataFrame:
    """d: flujos con src_ip, dst_ip, dst_port, proto, state, bytes_out, bytes_in, packets, ts. Devuelve DataFrame con CAUSAL, alineado con d.index."""
    w = max(1, int(round(float(W) * 60)))
    t = pd.to_numeric(d["ts"], errors="coerce").astype(float).values
    x = pd.DataFrame({"src": d["src_ip"].values, "dst": d["dst_ip"].values, "dp": d["dst_port"].astype(str).values, "t": t,
                      "ws": np.floor(t / w) * w, "_o": np.arange(len(d))})
    proto = d["proto"].fillna("").astype(str).str.lower(); fam = F._state_family(d["state"], proto)
    x["tcp"] = proto.eq("tcp").values.astype(float); x["udp"] = proto.eq("udp").values.astype(float); x["icmp"] = proto.str.startswith("icmp").values.astype(float)
    x["est"] = fam["est"].values.astype(float); x["att"] = fam["attempt"].values.astype(float); x["rst"] = fam["reset"].values.astype(float)
    x["bo"] = pd.to_numeric(d["bytes_out"], errors="coerce").fillna(0).values; x["bi"] = pd.to_numeric(d["bytes_in"], errors="coerce").fillna(0).values
    x["pk"] = pd.to_numeric(d["packets"], errors="coerce").fillna(0).values
    x = x.sort_values(["src", "ws", "t", "_o"], kind="mergesort").reset_index(drop=True)
    g = x.groupby(["src", "ws"], sort=False); n = g.cumcount().values + 1.0
    out = pd.DataFrame(index=x.index); out["n_conn"] = n
    for name, col in (("n_dst", "dst"), ("n_dport", "dp")):
        out[name] = (x.groupby(["src", "ws", col], sort=False).cumcount().values == 0).astype(float); out[name] = out[name].groupby([x["src"], x["ws"]], sort=False).cumsum()
    for name, col in (("entropy_dport", "dp"), ("entropy_dst", "dst")):
        c_prior = x.groupby(["src", "ws", col], sort=False).cumcount().values.astype(float)       # veces que ya apareció antes de este flujo
        delta = _xlogx(c_prior + 1) - _xlogx(c_prior); s = pd.Series(delta).groupby([x["src"], x["ws"]], sort=False).cumsum().values
        out[name] = np.maximum(0.0, np.log2(n) - s / n)
    for name, col in (("bytes_out_sum", "bo"), ("bytes_in_sum", "bi"), ("pkts_sum", "pk")): out[name] = g[col].cumsum().values
    out["bytes_out_mean"] = out["bytes_out_sum"] / n; out["pkts_mean"] = out["pkts_sum"] / n
    tot = out["bytes_out_sum"] + out["bytes_in_sum"]; out["ratio_out"] = np.where(tot > 0, out["bytes_out_sum"] / np.where(tot > 0, tot, 1), np.nan)
    for name, col in (("prop_tcp", "tcp"), ("prop_udp", "udp"), ("prop_icmp", "icmp"), ("prop_state_est", "est"), ("prop_state_attempt", "att"), ("prop_state_reset", "rst")):
        out[name] = g[col].cumsum().values / n
    gap = (x["t"] - g["t"].shift(1)).where(g.cumcount() > 0); gs = gap.fillna(0.0)
    cg = gs.groupby([x["src"], x["ws"]], sort=False).cumsum().values; cg2 = (gs ** 2).groupby([x["src"], x["ws"]], sort=False).cumsum().values; m = n - 1
    mean = np.where(m > 0, cg / np.where(m > 0, m, 1), np.nan); var = np.where(m > 0, np.maximum(0.0, cg2 / np.where(m > 0, m, 1) - mean ** 2), np.nan)
    out["mean_gap_s"] = mean; out["std_gap_s"] = np.sqrt(var); out["cv_gap"] = np.where((m > 0) & (mean > 0), out["std_gap_s"] / np.where(mean > 0, mean, 1), np.nan)
    res = out[CAUSAL].copy(); res.index = x["_o"].values; res = res.sort_index(); res.index = d.index; res.columns = ["c_" + c for c in CAUSAL]
    return res
