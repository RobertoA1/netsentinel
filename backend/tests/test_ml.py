"""Laboratorio ML: metodología (sin fuga, grupos, CV anidada), estadística, interpretación, severidad, LLM y RBAC."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.ml import features as F
from app.ml import groups as G
from app.ml import interpret as I
from app.ml import nested as N
from app.ml import models as M
from app.ml import serve as S
from app.ml import stats_tests as T
from app.ml.nested import Prepared, TrainConfig
from helpers import API

rng = np.random.default_rng(7)


def synth_flows(n=3000, span=960.0) -> pd.DataFrame:
    """16 min de captura: 3 hosts Botnet y 25 Normal, con tráfico distinguible."""
    t = np.sort(rng.uniform(0, span, n))
    bot_hosts = ["10.0.0.1", "10.0.0.2", "10.0.0.3"]
    norm_hosts = [f"10.0.1.{i}" for i in range(1, 26)]
    is_bot = rng.random(n) < 0.15
    src = np.where(is_bot, rng.choice(bot_hosts, n), rng.choice(norm_hosts, n))
    return pd.DataFrame({
        "ts": 1.3e9 + t, "src_ip": src, "dst_ip": np.where(is_bot, "185.1.1.1", rng.choice([f"8.8.{i}.1" for i in range(30)], n)),
        "src_port": rng.integers(1024, 65000, n), "dst_port": np.where(is_bot, 6667, rng.choice([80, 443, 53], n)),
        "proto": "tcp", "state": np.where(is_bot, "S_RA", "SR_SA"), "dir": "->", "direction": "out",
        "bytes_out": np.where(is_bot, rng.integers(200, 400, n), rng.integers(100, 9000, n)),
        "bytes_in": rng.integers(0, 5000, n), "packets": rng.integers(2, 40, n), "duration": rng.uniform(0, 3, n),
        "label_raw": np.where(is_bot, "flow=From-Botnet-V42", "flow=From-Normal-V42"),
    })


@pytest.fixture(scope="module")
def prep() -> Prepared:
    from app.ml.prepare import default_meta, prepare, validate_meta

    df = synth_flows()
    meta = validate_meta(default_meta("t", df))
    return prepare(df, meta, seed=42)


# --------------------------------------------------------------------------------------------------- variables
def test_features_have_no_leakage_columns(prep):
    for unit in ("flow", "window"):
        cols = F.feature_columns(unit)
        assert not (set(cols) & F.FORBIDDEN_FEATURES)
        F.assert_no_leakage(cols)
    assert not (set(prep.X.columns) & F.FORBIDDEN_FEATURES)
    assert not any(c.startswith("_") for c in prep.X.columns)
    with pytest.raises(Exception):
        F.assert_no_leakage(["duration", "src_ip"])


def test_feature_spec_is_versioned():
    s = F.feature_spec("flow")
    assert s["version"] == F.FEATURE_SPEC_VERSION and s["numeric"] and "src_ip" in s["excluded_by_design"]


# --------------------------------------------------------------------------------------------------- grupos
def test_partition_has_no_group_in_two_partitions(prep):
    for g in np.unique(prep.groups):
        assert len(set(prep.part[prep.groups == g])) == 1
    assert set(np.unique(prep.part)) == {0, 1, 2}
    share = np.bincount(prep.part) / len(prep.part)
    assert abs(share[0] - 0.70) < 0.12 and abs(share[1] - 0.15) < 0.10
    for k in range(3):
        assert prep.y[prep.part == k].sum() > 0  # cada partición tiene Botnet


def test_nested_folds_no_group_in_train_and_val(prep):
    dev = prep.part == 0
    y, g = prep.y[dev], prep.groups[dev]
    folds = G.nested_folds(y, g, 5, 3, seed=42)
    assert len(folds) == 5
    for f in folds:
        assert not (set(g[f.outer_train]) & set(g[f.outer_val]))
        assert len(f.inner) == 3
        for a, b in f.inner:
            assert not (set(g[a]) & set(g[b]))
            assert set(a) | set(b) <= set(f.outer_train)          # lo interno vive dentro de outer_train
            assert not ((set(a) | set(b)) & set(f.outer_val))    # outer_val nunca entra en la búsqueda
    assert sorted(np.concatenate([f.outer_val for f in folds]).tolist()) == list(range(len(y)))


def test_outer_val_never_participates_in_search(prep, monkeypatch):
    seen = []
    real = N.search

    def spy(cfg, prep_, X, y, inner, ctx, *a, **kw):
        seen.append([(set(map(int, a_)), set(map(int, b_))) for a_, b_ in inner])
        return real(cfg, prep_, X, y, inner, ctx, *a, **kw)

    monkeypatch.setattr(N, "search", spy)
    cfg = TrainConfig("logreg", M.effective_space("logreg", None), n_trials=2, n_outer=3, n_inner=3, n_jobs=1)
    folds = N.make_folds(prep, 3, 3, 42)
    out = N.run_outer_cv(cfg, prep, folds, N.Ctx())
    assert len(out) == 3 and len(seen) == 3
    for f, inner in zip(folds, seen):
        used = set().union(*[a | b for a, b in inner])
        assert not (used & set(map(int, f.outer_val)))
    for r in out:
        assert 0 <= r["outer_value"] <= 1 and set(r["val_idx"]).isdisjoint(r["train_idx"])


# --------------------------------------------------------------------------------------------------- validador
def test_validator_detects_three_host_case(prep):
    aux = prep.aux
    y = prep.y
    r = G.validate_key(prep.X, y, aux, "src_ip", "flow", 10.0)
    assert r["viable"] is False
    assert r["class_stats"]["Botnet"]["groups"] == 3
    assert "3" in " ".join(r["blocking"])
    allv = G.validate_all(prep.X, y, aux, "flow", 10.0, "src_ip")
    assert allv["keys"]["src_ip"]["viable"] is False
    assert allv["recommended"] in ("time_block", "src_dst")
    assert allv["keys"][allv["recommended"]]["viable"] is True


# --------------------------------------------------------------------------------------------------- estadística
def test_stats_against_known_values():
    assert T.wilcoxon_min_p(5) == pytest.approx(0.0625)
    m = T.mcnemar(np.ones(12), np.r_[np.ones(10), np.zeros(2)], np.r_[np.zeros(10), np.ones(2)])
    assert (m["b_a_right_b_wrong"], m["c_a_wrong_b_right"]) == (10, 2)
    assert m["p_value"] == pytest.approx(0.03857, abs=1e-4)
    assert T.holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])
    assert T.cliffs_delta([3, 4, 5], [1, 2, 3.5]) == pytest.approx((8 - 1) / 9)
    assert T.cliffs_delta([1, 2], [1, 2]) == 0.0
    tab = {"a": [.9, .8, .85, .9, .95], "b": [.7, .6, .65, .7, .75], "c": [.5, .4, .45, .5, .55]}
    fr = T.friedman(tab)
    assert fr["applicable"] and fr["p_value"] < 0.05 and fr["mean_ranks"]["a"] == 1.0
    w = T.pairwise_wilcoxon(tab)
    assert all(r["p_value"] == pytest.approx(0.0625) for r in w)      # n = 5: el mínimo posible
    assert all(r["p_holm"] >= 0.0625 for r in w) and not any(r["significant_005"] for r in w)
    assert T.friedman({"a": [1, 2], "b": [2, 1]})["applicable"] is False


def test_paired_bootstrap_by_groups_ci_contains_diff():
    y = rng.integers(0, 2, 400)
    pa = np.clip(y * 0.7 + rng.normal(0.15, 0.15, 400), 0, 1)
    pb = np.clip(y * 0.2 + rng.normal(0.4, 0.2, 400), 0, 1)
    g = rng.integers(0, 40, 400).astype(str)
    r = T.paired_bootstrap_diff(y, pa, pb, g, "roc_auc", n_boot=200, seed=1)
    lo, hi = r["ci"]
    assert lo <= r["diff"] <= hi and lo > 0


def test_kendall_w_extremes():
    same = np.tile(np.arange(6), (4, 1))
    assert T.kendalls_w(same) == pytest.approx(1.0)


# --------------------------------------------------------------------------------------------------- interpretación
def test_interpretations_depend_on_data():
    a = I.class_distribution(50, 950, 0, "flujos")
    b = I.class_distribution(450, 550, 5000, "flujos")
    assert a["meaning"] != b["meaning"]
    assert any("Desbalance" in c for c in a["caution"]) and not any("Desbalance" in c for c in b["caution"])
    assert any("5 000" in c for c in b["caution"])
    agg = lambda n: {"mean": 0.9, "std": 0.02, "n": n, "ci_t": [0.88, 0.92], "values": [0.9] * n}
    assert any("n = 5" in c for c in I.cv_dispersion("X", agg(5), "PR-AUC")["caution"])
    assert not I.cv_dispersion("X", agg(30), "PR-AUC")["caution"]


# --------------------------------------------------------------------------------------------------- severidad y LLM
def test_severity_steps_and_rules():
    lvl, steps = S.severity(0.95, 0.05, False, False, None, None, {})
    assert lvl == "critical" and steps[0]["step"] == "probabilidad" and steps[-1]["step"] == "resultado"
    lvl, steps = S.severity(0.95, 0.5, True, False, None, None, {})        # incertidumbre: -20 puntos
    assert lvl == "high" and any(s["step"] == "incertidumbre" and "restan" in s["text"] for s in steps)
    lvl, _ = S.severity(0.55, 0.05, False, False, None, "critical", {})     # criticidad sube un nivel
    assert lvl == "high"
    lvl, steps = S.severity(0.99, 0.05, False, True, None, None, {})        # fuera de distribución: tope
    assert lvl == "medium" and any(s["step"] == "fuera_de_distribucion" for s in steps)
    lvl, _ = S.severity(0.2, 0.05, False, False, None, "critical", {})
    assert lvl == "info"
    with pytest.raises(ValueError):
        S.validate_severity_config({"thresholds": {"low": 90, "medium": 50}})


def _pred():
    return {"probability": 0.93, "interval": [0.9, 0.97], "predicted_class": "Botnet", "threshold": 0.4,
            "ood": {"is_ood": False}, "ambiguous": False, "contributions": {"favor": [{"label": "Puertos destino", "value": 6667, "shap": 0.4}], "contra": []}}


def test_narrative_degrades_to_template():
    class Boom:
        def invoke(self, *_):
            raise TimeoutError("ollama caído")

    class Echo:
        def invoke(self, *_):
            return type("R", (), {"content": "Texto del modelo de lenguaje con más de veinte caracteres."})()

    t0, s0 = S.narrate(_pred(), "high", [], "flow", None, None)
    t1, s1 = S.narrate(_pred(), "high", [], "flow", None, Boom())
    t2, s2 = S.narrate(_pred(), "high", [], "flow", None, Echo())
    assert (s0, s1, s2) == ("template", "template", "llm") and t0 == t1 and "93 %" in t0


# --------------------------------------------------------------------------------------------------- API y RBAC
GET_ENDPOINTS = {
    "ml_data": "/ml/data/datasets", "ml_training": "/ml/training/spaces", "ml_evaluation": "/ml/evaluation/models",
    "ml_explain": "/ml/explain/models/1", "ml_inference": "/ml/inference/severity-config", "ml_optuna": "/ml/optuna/options",
}


def _status(c, h, path):
    code = c.get(f"{API}{path}", headers=h).status_code
    return 200 if code == 404 and "/explain/models/" in path else code  # 404 = permitido, sin modelo aún


def test_ml_rbac_matrix(app_client, admin_headers, make_user):
    auditor, analyst, manager = (make_user(f"ml_{r}", r) for r in ("auditor", "analyst", "manager"))
    for mod, path in GET_ENDPOINTS.items():
        assert _status(app_client, admin_headers, path) == 200, mod
        assert _status(app_client, auditor, path) == 200, mod
        assert _status(app_client, analyst, path) == 200, mod
    assert _status(app_client, manager, "/ml/evaluation/models") == 200
    for mod in ("ml_data", "ml_training", "ml_optuna", "ml_inference"):
        assert _status(app_client, manager, GET_ENDPOINTS[mod]) == 403, mod
    assert _status(app_client, None or {}, "/ml/data/datasets") == 401
    # el auditor es de solo lectura
    assert app_client.post(f"{API}/ml/training/jobs", headers=auditor, json={}).status_code == 403
    assert app_client.post(f"{API}/ml/optuna/studies", headers=auditor, json={}).status_code == 403
    assert app_client.post(f"{API}/ml/inference/predict", headers=auditor, json={}).status_code == 403
    assert app_client.post(f"{API}/ml/evaluation/models/1/promote", headers=auditor).status_code == 403
    assert app_client.put(f"{API}/ml/inference/pipeline", headers=auditor, json={"enabled": True}).status_code == 403
    # el analista ejecuta inferencia pero no promueve ni entrena
    assert app_client.post(f"{API}/ml/evaluation/models/1/promote", headers=analyst).status_code == 403
    assert app_client.post(f"{API}/ml/training/jobs", headers=analyst, json={}).status_code == 403
    assert app_client.post(f"{API}/ml/inference/predict", headers=analyst, json={"model_id": 999, "kind": "manual", "values": {}}).status_code in (404, 422)


def test_ml_modules_accepted_by_audit_and_catalog(app_client, admin_headers):
    mods = app_client.get(f"{API}/audit/modules", headers=admin_headers)
    if mods.status_code == 200:
        names = {m if isinstance(m, str) else m.get("code") for m in mods.json()}
        assert {"ml_data", "ml_training", "ml_evaluation", "ml_explain", "ml_inference", "ml_optuna"} <= names
    cat = {c["code"]: c for c in app_client.get(f"{API}/reports/catalog", headers=admin_headers).json()}
    assert {"ml_dataset", "ml_training", "ml_evaluation", "ml_explainability", "ml_inference", "ml_model_card"} <= set(cat)
    assert cat["ml_model_card"]["params"] == ["model_id"]
    r = app_client.post(f"{API}/reports/generate", headers=admin_headers,
                        json={"report_code": "ml_model_card", "format": "pdf", "date_from": "2011-08-10", "date_to": "2011-08-11", "params": {"model_id": 12345}})
    assert r.status_code == 404


def test_dummy_and_validation_endpoints_reject_bad_input(app_client, admin_headers):
    r = app_client.post(f"{API}/ml/figures/export", headers=admin_headers, json={"spec": {"kind": "evil", "data": {}}, "format": "png"})
    assert r.status_code == 422
    r = app_client.post(f"{API}/ml/figures/export", headers=admin_headers, json={
        "spec": {"kind": "bars", "title": "Prueba", "data": {"labels": ["a", "b"], "series": [{"name": "s", "values": [1, 2]}]}}, "format": "svg", "module": "ml_data"})
    assert r.status_code == 200 and b"<svg" in r.content[:600]
    r = app_client.post(f"{API}/ml/figures/export", headers=admin_headers, json={
        "spec": {"kind": "bars", "title": "Prueba", "data": {"labels": ["a", "b"], "series": [{"name": "s", "values": [1, 2]}]}}, "format": "png"})
    assert r.status_code == 200 and r.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_model_loading_enforces_path_and_checksum(tmp_path):
    from app.ml import store

    with pytest.raises(Exception):
        store.load_model("/etc/passwd", "0" * 64)
    with pytest.raises(Exception):
        store.safe_path("../../etc/passwd")
