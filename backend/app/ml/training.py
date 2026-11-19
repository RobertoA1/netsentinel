"""Trabajo de entrenamiento: valida grupos, parte por grupos, CV anidada con Optuna por modelo, modelo final,
calibración, umbral, prueba única y registro de ejecuciones/pliegues/modelos."""
from __future__ import annotations

import time
from datetime import datetime

import numpy as np
import pandas as pd
from sqlalchemy import delete, select

from app.db.base import utcnow
from app.db.session import new_session
from app.ml import data as D
from app.ml import models as M
from app.ml import prepare as P
from app.ml.groups import validate_key
from app.ml.jobs import JobRunner, default_storage
from app.ml.metrics import aggregate_metrics, metric_value, OBJECTIVES
from app.ml.nested import TrainConfig, final_fit, make_folds, run_outer_cv
from app.ml.store import dump_json, job_dir, run_dir, save_model
from app.models import MlDataset, MlDatasetVersion, MlFoldResult, MlModel, MlRun

DEFAULT_TRIALS = 20


def load_version(db, version_id: int):
    v = db.get(MlDatasetVersion, version_id)
    if v is None:
        raise ValueError("Versión de dataset inexistente")
    ds = db.get(MlDataset, v.dataset_id)
    return ds, v


def prepare_from_version(version_id: int, seed: int):
    db = new_session()
    try:
        ds, v = load_version(db, version_id)
        meta = dict(v.meta)
        flows = D.load_snapshot(ds.snapshot_path, ds.snapshot_sha256)
    finally:
        db.close()
    return flows, meta, P.prepare(flows, meta, seed)


def plan_models(params: dict) -> list[dict]:
    """Modelos pedidos (+ línea base trivial siempre incluida), con espacios validados."""
    out = []
    seen = set()
    for m in params.get("models", []):
        t = m["type"]
        if t not in M.MODEL_TYPES or t in seen:
            continue
        seen.add(t)
        out.append({"type": t, "n_trials": int(m.get("n_trials") or params.get("n_trials") or DEFAULT_TRIALS),
                    "space": M.effective_space(t, m.get("space"))})
    if "dummy" not in seen:
        out.insert(0, {"type": "dummy", "n_trials": 0, "space": []})
    return out


def train_job(r: JobRunner) -> dict:
    p = r.params
    seed = r.seed
    metric = p.get("metric", "pr_auc")
    if metric not in OBJECTIVES:
        raise ValueError("Métrica objetivo no soportada")
    n_outer, n_inner = int(p.get("n_outer", 5)), int(p.get("n_inner", 3))
    if not (2 <= n_outer <= M.MAX_FOLDS_HARD and 2 <= n_inner <= M.MAX_FOLDS_HARD):
        raise ValueError("Número de pliegues fuera de rango")
    from app.core.config import get_settings

    n_jobs = get_settings().ml_n_jobs
    plan = plan_models(p)
    r.log(f"Cargando dataset (versión {r.dataset_version_id}) y construyendo variables")
    flows, meta, prep = prepare_from_version(r.dataset_version_id, seed)
    # --- el entrenamiento se bloquea si la configuración de grupos es inviable
    ff = P.feature_frame(flows, meta)
    ff = ff[ff["y"].notna()].reset_index(drop=True)
    from app.ml.features import feature_columns

    v = validate_key(ff[feature_columns(meta["unit"])], ff["y"].astype(int).values,
                     ff[[c for c in ff.columns if c.startswith("_")]], meta["group_key"], meta["unit"],
                     meta["time_block_seconds"], seed, n_outer, n_inner)
    if not v["viable"]:
        raise ValueError("Configuración de grupos inviable: " + " | ".join(v["blocking"][:3]))
    pt = P.partition_table(prep)
    r.log(f"Partición por grupos ({meta['group_key']}): " + "; ".join(
        f"{x['partition']} {x['rows_botnet']} Botnet / {x['rows_normal']} Normal" for x in pt["rows"]))
    folds = make_folds(prep, n_outer, n_inner, seed)
    storage = default_storage()
    # estructura de trabajo
    db = new_session()
    try:
        # reintento: se conservan los modelos ya terminados (misma semilla y datos => mismo resultado) y se rehace el resto
        done_runs = {x.model_type: x for x in db.execute(select(MlRun).where(MlRun.job_id == r.job_id,
                                                                              MlRun.status == "succeeded")).scalars()}
        db.execute(delete(MlRun).where(MlRun.job_id == r.job_id, MlRun.status != "succeeded"))
        db.commit()
        kept = {}
        for t, x in done_runs.items():
            mdl = db.execute(select(MlModel).where(MlModel.run_id == x.id)).scalar_one_or_none()
            kept[t] = {"run_id": x.id, "model_type": t, "model_id": mdl.id if mdl else None}
        run_ids = {}
        for m in plan:
            if m["type"] in kept:
                continue
            run = MlRun(job_id=r.job_id, dataset_version_id=r.dataset_version_id, model_type=m["type"], status="pending",
                        config={"n_trials": m["n_trials"], "space": m["space"], "metric": metric, "n_outer": n_outer,
                                "n_inner": n_inner, "seed": seed, "group_key": meta["group_key"], "unit": meta["unit"],
                                "sampler": p.get("sampler", "tpe"), "pruner": p.get("pruner", "median"),
                                "from_study": p.get("from_study")})
            db.add(run)
            db.flush()
            run_ids[m["type"]] = run.id
        db.commit()
    finally:
        db.close()
    total_units = sum((n_outer + 1) * m["n_trials"] for m in plan)
    r.progress(phase="start", units_total=total_units, units_done=0, outer_total=n_outer * len(plan), outer_done=0,
               models=[{"type": m["type"], "status": "pending"} for m in plan], n_inner=n_inner, n_outer=n_outer,
               metric=metric, partition=pt, group_key=meta["group_key"], unit=meta["unit"])
    dump_json(job_dir(r.job_id) / "partition.json",
              {"part": prep.part.tolist(), "seed": seed})
    ctx = r.ctx(f"job{r.job_id}", storage)
    results = []
    for m in plan:
        if m["type"] in kept:
            r.log(f"== {M.MODEL_ES[m['type']]}: ya completado en un intento anterior, se conserva ==")
            results.append(kept[m["type"]])
            _mark_model(r, m["type"], "done")
            continue
        t0 = time.monotonic()
        cfg = TrainConfig(model_type=m["type"], space=m["space"], n_trials=m["n_trials"], metric=metric, n_outer=n_outer,
                          n_inner=n_inner, seed=seed, n_jobs=n_jobs, pruner=p.get("pruner", "median"),
                          sampler=p.get("sampler", "tpe"))
        r.log(f"== {M.MODEL_ES[m['type']]}: CV anidada {n_outer}x{n_inner}, {m['n_trials']} trials por pliegue ==")
        _mark_model(r, m["type"], "running")
        _set_run(run_ids[m["type"]], status="running")
        ctx.emit({"type": "model_start", "model": m["type"]})
        if m["type"] == "dummy":
            cfg.space = []
        outer = run_outer_cv(cfg, prep, folds, ctx)
        fin = final_fit(cfg, prep, ctx)
        dur = time.monotonic() - t0
        results.append(_persist_run(r, run_ids[m["type"]], cfg, outer, fin, prep, meta, dur, seed))
        _mark_model(r, m["type"], "done")
    r.progress(phase="done", eta_s=0)
    r.log("Entrenamiento completo")
    return {"runs": [{"run_id": x["run_id"], "model_type": x["model_type"], "model_id": x["model_id"]} for x in results],
            "partition": pt, "group_validation": {k: v[k] for k in ("group_key", "label", "viable", "warnings", "partition",
                                                                    "class_stats", "shared_keys_across_partitions",
                                                                    "duplicate_vectors_across_partitions") if k in v},
            "seed": seed, "metric": metric}


def _mark_model(r: JobRunner, mt: str, status: str) -> None:
    ms = r._progress.get("models", [])
    for m in ms:
        if m["type"] == mt:
            m["status"] = status
    r.progress(models=ms)


def _set_run(run_id: int, **kw) -> None:
    db = new_session()
    try:
        run = db.get(MlRun, run_id)
        for k, v in kw.items():
            setattr(run, k, v)
        db.commit()
    finally:
        db.close()


def _persist_run(r: JobRunner, run_id: int, cfg: TrainConfig, outer: list[dict], fin: dict, prep, meta: dict,
                 dur: float, seed: int) -> dict:
    from app.ml.features import feature_spec

    agg = aggregate_metrics([f["outer_metrics"] for f in outer], seed=seed)
    gaps = [(f["inner_best_value"], f["outer_value"]) for f in outer]
    spec = feature_spec(prep.unit, prep.window_minutes)
    bg = prep.X[prep.part == 0].sample(min(100, int((prep.part == 0).sum())), random_state=seed).reset_index(drop=True)
    bundle = {"pipeline": fin["pipeline"], "calibrator": fin["calibrator"], "model_type": cfg.model_type,
              "unit": prep.unit, "window_minutes": prep.window_minutes, "threshold": fin["threshold"],
              "uncertainty": fin["uncertainty"], "spec": spec, "background": bg, "label_map": meta["label_map"],
              "calibration_method": fin["calibration_method"], "params": fin["best_params"], "seed": seed,
              "metric": cfg.metric}
    rd = run_dir(run_id)
    dump_json(rd / "preds.json", {"folds": [{"outer": f["outer"], "y": f["y"], "p": f["p"], "val_idx": f["val_idx"],
                                             "train_idx": f["train_idx"]} for f in outer],
                                  "val": fin["val"], "test": fin["test"]})
    dump_json(rd / "metrics.json", {"cv": agg, "val": fin["val_metrics"], "test": fin["test_metrics"],
                                    "test_uncalibrated": fin["test_metrics_uncalibrated"],
                                    "coverage_test": fin["coverage_test"], "gaps": gaps, "final_curve": fin["curve"]})
    db = new_session()
    try:
        run = db.get(MlRun, run_id)
        ds_name = db.get(MlDataset, db.get(MlDatasetVersion, run.dataset_version_id).dataset_id).name
        nmodel = db.execute(select(MlModel).where(MlModel.name.like(f"{M.MODEL_ES[cfg.model_type]}%"))).scalars().all()
        for f in outer:
            db.add(MlFoldResult(run_id=run_id, outer_fold=f["outer"], best_params=f["best_params"],
                                inner_best_value=f["inner_best_value"], outer_metrics=f["outer_metrics"],
                                n_trials=f["n_trials"], n_pruned=f["n_pruned"], duration_s=f["duration_s"],
                                curve=f["curve"], sizes=f["sizes"]))
        run.status, run.duration_s = "succeeded", dur
        run.summary = {"cv": agg, "objective": cfg.metric, "inner_outer": gaps,
                       "coverage_test": fin["coverage_test"], "final_inner_best": fin["inner_best_value"],
                       "final_n_trials": fin["n_trials"], "final_n_pruned": fin["n_pruned"]}
        run.final_params, run.val_metrics, run.test_metrics = fin["best_params"], fin["val_metrics"], fin["test_metrics"]
        run.artifact_dir = str(rd)
        db.flush()
        path, sha = save_model(bundle, f"run{run_id}")
        mv = len(nmodel) + 1
        model = MlModel(run_id=run_id, dataset_version_id=run.dataset_version_id,
                        name=f"{M.MODEL_ES[cfg.model_type]} v{mv} · {ds_name}", model_type=cfg.model_type,
                        unit=prep.unit, window_minutes=prep.window_minutes, model_path=path, sha256=sha,
                        threshold=fin["threshold"], calibration_method=fin["calibration_method"],
                        feature_spec_version=spec["version"], metrics={"test": fin["test_metrics"],
                                                                      "val": fin["val_metrics"], "cv": {
                                                                          k: {"mean": agg[k]["mean"], "std": agg[k]["std"],
                                                                              "ci_t": agg[k]["ci_t"]} for k in agg}},
                        uncertainty={k: v for k, v in fin["uncertainty"].items() if k not in ("ranges", "categories")}
                        | {"coverage_test": fin["coverage_test"]}, is_baseline=cfg.model_type == "dummy")
        db.add(model)
        db.commit()
        mid = model.id
    finally:
        db.close()
    r.log(f"{M.MODEL_ES[cfg.model_type]}: PR-AUC CV {_fm(agg['pr_auc'])}; Prueba PR-AUC "
          f"{fin['test_metrics']['pr_auc']}; F1 prueba {fin['test_metrics']['f1']} (umbral {fin['threshold']:.3f}); "
          f"{dur:.0f} s")
    return {"run_id": run_id, "model_type": cfg.model_type, "model_id": mid}


def _fm(a: dict) -> str:
    return "n/d" if a.get("mean") is None else f"{a['mean']:.4f} ± {a['std']:.4f}"
