"""Fase 7 — Optimización con Optuna (estudios persistidos en el esquema `optuna` de PostgreSQL)."""
from __future__ import annotations

import numpy as np
import optuna
from sklearn.model_selection import StratifiedGroupKFold

from app.core.config import get_settings
from app.ml import models as M
from app.ml.jobs import JobRunner, default_storage
from app.ml.metrics import OBJECTIVES
from app.ml.nested import TrainConfig, search
from app.ml.training import prepare_from_version

MAX_TRIALS = M.MAX_TRIALS_HARD
SAMPLERS = ("tpe", "random", "cmaes")
PRUNERS = ("median", "hyperband", "none")


def study_name(job_id: int) -> str:
    return f"opt_job{job_id}"


def optimize_job(r: JobRunner) -> dict:
    p = r.params
    mt = p["model_type"]
    if mt not in M.MODEL_TYPES or mt == "dummy":
        raise ValueError("Modelo no optimizable")
    metric = p.get("metric", "pr_auc")
    if metric not in OBJECTIVES:
        raise ValueError("Métrica no soportada")
    n_trials = max(1, min(int(p.get("n_trials", 30)), MAX_TRIALS))
    n_folds = int(p.get("n_folds", 3))
    if not 2 <= n_folds <= M.MAX_FOLDS_HARD:
        raise ValueError("Número de pliegues fuera de rango")
    sampler, pruner = p.get("sampler", "tpe"), p.get("pruner", "median")
    if sampler not in SAMPLERS or pruner not in PRUNERS:
        raise ValueError("Muestreador o podador no soportado")
    space = M.effective_space(mt, p.get("space"))
    timeout = p.get("timeout_s")
    timeout = float(timeout) if timeout else None
    flows, meta, prep = prepare_from_version(r.dataset_version_id, r.seed)
    dev = prep.part == 0
    X, y, g = prep.X[dev].reset_index(drop=True), prep.y[dev], prep.groups[dev]
    inner = list(StratifiedGroupKFold(n_folds, shuffle=True, random_state=r.seed).split(X, y, g))
    cfg = TrainConfig(model_type=mt, space=space, n_trials=n_trials, metric=metric, n_inner=n_folds, seed=r.seed,
                      n_jobs=get_settings().ml_n_jobs, pruner=pruner, sampler=sampler, timeout=timeout)
    storage = default_storage()
    name = study_name(r.job_id)
    try:
        storage.delete_study(storage.get_study_id_from_name(name))  # reintento: se rehace
    except Exception:
        pass
    r.progress(phase="optimize", units_total=n_trials, units_done=0, metric=metric, model=mt, sampler=sampler,
               pruner=pruner)
    r.log(f"Estudio Optuna «{name}»: {M.MODEL_ES[mt]}, {n_trials} trials, {sampler}/{pruner}, {n_folds} pliegues")
    ctx = r.ctx("opt", storage)
    ctx.deadline = None  # el tiempo máximo del estudio es una parada suave (timeout de Optuna)
    ctx.emit = r.on_event
    bp, bv, curve, summ = search(cfg, prep, X, y, inner, ctx, name, {"model": mt, "outer": "estudio"})
    r.log(f"Mejor valor {bv}; trials {summ['n_trials']} (podados {summ['n_pruned']})")
    return {"study_name": name, "best_value": bv, "best_params": bp, "n_trials": summ["n_trials"],
            "n_pruned": summ["n_pruned"], "model_type": mt, "metric": metric}
