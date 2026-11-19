"""Validación cruzada ANIDADA con Optuna (TPE + poda por mediana), modelo final, calibración y prueba única.

Protocolo (exacto):
  1. 5 pliegues externos x 3 internos (StratifiedGroupKFold por grupo) sobre Desarrollo, semilla fija.
  2. En CADA pliegue externo: (a) Optuna sobre los pliegues INTERNOS de outer_train; (b) reentrenar con los mejores
     hiperparámetros sobre todo outer_train; (c) evaluar UNA vez sobre outer_val (que nunca participa en la búsqueda).
  3. Agregar: una observación por pliegue externo -> media, desviación, IC 95 % (t y bootstrap).
  Final: búsqueda sobre todo Desarrollo con 3 pliegues internos; umbral y calibración en Validación; Prueba una vez.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import optuna
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from app.ml import models as M
from app.ml.groups import FoldSpec, nested_folds
from app.ml.metrics import best_threshold, compute_metrics, metric_value

optuna.logging.set_verbosity(optuna.logging.WARNING)


class Cancelled(Exception):
    pass


class TimeLimit(Exception):
    pass


@dataclass
class Prepared:
    X: pd.DataFrame          # solo variables del modelo
    y: np.ndarray
    aux: pd.DataFrame        # _src_ip, _dst_ip, _t
    groups: np.ndarray
    part: np.ndarray         # 0 dev, 1 val, 2 test
    unit: str
    window_minutes: float | None = None


@dataclass
class TrainConfig:
    model_type: str
    space: list[dict]
    n_trials: int = 20
    metric: str = "pr_auc"
    n_outer: int = 5
    n_inner: int = 3
    seed: int = 42
    n_jobs: int = 4
    pruner: str = "median"
    sampler: str = "tpe"
    timeout: float | None = None  # segundos (parada suave del estudio; usado por la optimización Optuna)


@dataclass
class Ctx:
    """Hilos de control compartidos: progreso, cancelación, tiempo límite, almacenamiento Optuna."""
    emit: Callable[[dict], None] = lambda ev: None
    cancel_check: Callable[[], bool] = lambda: False
    deadline: float | None = None
    storage: object | None = None
    study_prefix: str = "study"
    t0: float = field(default_factory=time.monotonic)

    def check(self) -> None:
        if self.cancel_check():
            raise Cancelled()
        if self.deadline is not None and time.monotonic() > self.deadline:
            raise TimeLimit()


def make_sampler(name: str, seed: int, space: list[dict]):
    if name == "random":
        return optuna.samplers.RandomSampler(seed=seed)
    if name == "cmaes":
        if any(p["type"] == "categorical" for p in space) or len(space) < 2:
            return optuna.samplers.TPESampler(seed=seed, multivariate=True)
        return optuna.samplers.CmaEsSampler(seed=seed)
    return optuna.samplers.TPESampler(seed=seed, n_startup_trials=8)


def make_pruner(name: str):
    if name == "hyperband":
        return optuna.pruners.HyperbandPruner(min_resource=1, max_resource=3, reduction_factor=3)
    if name == "none":
        return optuna.pruners.NopPruner()
    return optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=0)


def _fit_predict(cfg: TrainConfig, params: dict, unit: str, Xtr, ytr, Xva) -> np.ndarray:
    pipe = M.build_pipeline(cfg.model_type, params, unit, cfg.seed, cfg.n_jobs)
    pipe.fit(Xtr, ytr)
    return M.predict_proba(pipe, Xva)


def search(cfg: TrainConfig, prep: Prepared, X: pd.DataFrame, y: np.ndarray, inner: list[tuple[np.ndarray, np.ndarray]],
           ctx: Ctx, study_name: str, label: dict, seed_offset: int = 0) -> tuple[dict, float | None, list[dict], dict]:
    """Optuna sobre los pliegues INTERNOS `inner` (índices relativos a X). Devuelve (mejores_params, mejor_valor,
    curva_de_trials, resumen)."""
    if cfg.model_type == "dummy":
        return {}, None, [], {"n_trials": 0, "n_pruned": 0}
    try:  # reintento tras un fallo: se rehace el estudio huérfano (misma semilla => mismo resultado)
        optuna.delete_study(study_name=study_name, storage=ctx.storage)
    except KeyError:
        pass
    study = optuna.create_study(
        study_name=study_name, direction="maximize", sampler=make_sampler(cfg.sampler, cfg.seed + seed_offset, cfg.space),
        pruner=make_pruner(cfg.pruner), storage=ctx.storage, load_if_exists=False)
    curve: list[dict] = []
    best = [-np.inf]

    def objective(trial: optuna.Trial) -> float:
        ctx.check()
        params = M.suggest_params(trial, cfg.space)
        vals = []
        for i, (a, b) in enumerate(inner):
            p = _fit_predict(cfg, params, prep.unit, X.iloc[a], y[a], X.iloc[b])
            vals.append(metric_value(y[b], p, cfg.metric))
            trial.report(float(np.mean(vals)), step=i)
            if i < len(inner) - 1 and trial.should_prune():
                raise optuna.TrialPruned()
        return float(np.mean(vals))

    def cb(st: optuna.Study, tr: optuna.trial.FrozenTrial) -> None:
        if tr.value is not None:
            best[0] = max(best[0], tr.value)
        curve.append({"trial": tr.number, "value": tr.value, "best": None if best[0] == -np.inf else best[0],
                      "state": tr.state.name.lower()})
        ctx.emit({"type": "trial", **label, "trial": tr.number + 1, "n_trials": cfg.n_trials, "value": tr.value,
                  "best": None if best[0] == -np.inf else best[0], "state": tr.state.name.lower(),
                  "params": tr.params})
        if ctx.cancel_check() or (ctx.deadline is not None and time.monotonic() > ctx.deadline):
            st.stop()

    study.optimize(objective, n_trials=cfg.n_trials, timeout=cfg.timeout, callbacks=[cb], catch=())
    ctx.check()
    complete = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
    if complete:
        bt = study.best_trial
        bp, bv = dict(bt.params), float(bt.value)
    else:
        bp, bv = {}, None
    n_pruned = sum(t.state == optuna.trial.TrialState.PRUNED for t in study.trials)
    return bp, bv, curve, {"n_trials": len(study.trials), "n_pruned": int(n_pruned)}


def round_list(a, nd=5):
    return [round(float(x), nd) for x in np.asarray(a).ravel()]


def run_outer_cv(cfg: TrainConfig, prep: Prepared, folds: list[FoldSpec], ctx: Ctx) -> list[dict]:
    dev = prep.part == 0
    X, y = prep.X[dev].reset_index(drop=True), prep.y[dev]
    out = []
    for k, f in enumerate(folds):
        ctx.check()
        t0 = time.monotonic()
        ctx.emit({"type": "outer_start", "outer": k + 1, "model": cfg.model_type})
        # (a) búsqueda SOLO con los pliegues internos de outer_train (outer_val no se toca)
        bp, bv, curve, summ = search(cfg, prep, X, y, f.inner, ctx, f"{ctx.study_prefix}_{cfg.model_type}_outer{k + 1}",
                                     {"model": cfg.model_type, "outer": k + 1}, seed_offset=k)
        # (b) reentrenar con los mejores hiperparámetros sobre todo outer_train
        p = _fit_predict(cfg, bp, prep.unit, X.iloc[f.outer_train], y[f.outer_train], X.iloc[f.outer_val])
        # (c) evaluar UNA vez en outer_val
        m = compute_metrics(y[f.outer_val], p, 0.5)
        rec = {"outer": k + 1, "best_params": bp, "inner_best_value": bv, "outer_metrics": m,
               "outer_value": metric_value(y[f.outer_val], p, cfg.metric), "curve": curve, **summ,
               "duration_s": time.monotonic() - t0,
               "sizes": {"train": int(len(f.outer_train)), "val": int(len(f.outer_val)),
                         "val_pos": int(y[f.outer_val].sum()), "train_pos": int(y[f.outer_train].sum())},
               "val_idx": [int(i) for i in f.outer_val], "train_idx": [int(i) for i in f.outer_train],
               "y": [int(v) for v in y[f.outer_val]], "p": round_list(p)}
        out.append(rec)
        ctx.emit({"type": "outer_done", "outer": k + 1, "model": cfg.model_type, "outer_value": rec["outer_value"],
                  "inner_best": bv})
    return out


def final_fit(cfg: TrainConfig, prep: Prepared, ctx: Ctx) -> dict:
    """Modelo final: búsqueda sobre todo Desarrollo (CV interna de 3), umbral y calibración en Validación y
    evaluación ÚNICA en Prueba."""
    from app.ml.uncertainty import fit_uncertainty

    dev, val, test = prep.part == 0, prep.part == 1, prep.part == 2
    Xd, yd, gd = prep.X[dev].reset_index(drop=True), prep.y[dev], prep.groups[dev]
    inner = [(a, b) for a, b in StratifiedGroupKFold(cfg.n_inner, shuffle=True, random_state=cfg.seed + 99).split(Xd, yd, gd)]
    ctx.emit({"type": "final_start", "model": cfg.model_type})
    t0 = time.monotonic()
    bp, bv, curve, summ = search(cfg, prep, Xd, yd, inner, ctx, f"{ctx.study_prefix}_{cfg.model_type}_final",
                                 {"model": cfg.model_type, "outer": "final"}, seed_offset=77)
    pipe = M.build_pipeline(cfg.model_type, bp, prep.unit, cfg.seed, cfg.n_jobs).fit(Xd, yd)
    Xv, yv = prep.X[val], prep.y[val]
    p_val_raw = M.predict_proba(pipe, Xv)
    method = M.choose_calibration(len(yv), int(yv.sum()), int((yv == 0).sum()))
    cal = M.Calibrator(method).fit(p_val_raw, yv)
    p_val = cal.predict(p_val_raw)
    thr, thr_val = best_threshold(yv, p_val, "f1")
    unc = fit_uncertainty(yv, p_val, Xd, prep.unit)
    # PRUEBA: una sola vez
    Xt, yt = prep.X[test], prep.y[test]
    p_test_raw = M.predict_proba(pipe, Xt)
    p_test = cal.predict(p_test_raw)
    test_metrics = compute_metrics(yt, p_test, thr)
    test_metrics_raw = compute_metrics(yt, p_test_raw, 0.5)
    val_metrics = compute_metrics(yv, p_val, thr)
    from app.ml.uncertainty import coverage_on_test

    cov = coverage_on_test(unc, yt, p_test)
    ctx.emit({"type": "final_done", "model": cfg.model_type, "best": bv})
    return {"best_params": bp, "inner_best_value": bv, "curve": curve, **summ, "pipeline": pipe, "calibrator": cal,
            "calibration_method": method, "threshold": thr, "threshold_val_value": thr_val, "uncertainty": unc,
            "coverage_test": cov, "val_metrics": val_metrics, "test_metrics": test_metrics,
            "test_metrics_uncalibrated": test_metrics_raw, "duration_s": time.monotonic() - t0,
            "val": {"y": [int(v) for v in yv], "p": round_list(p_val), "p_raw": round_list(p_val_raw)},
            "test": {"y": [int(v) for v in yt], "p": round_list(p_test), "p_raw": round_list(p_test_raw),
                     "groups": [str(g) for g in prep.groups[test]]}}


def make_folds(prep: Prepared, n_outer: int, n_inner: int, seed: int) -> list[FoldSpec]:
    dev = prep.part == 0
    return nested_folds(prep.y[dev], prep.groups[dev], n_outer, n_inner, seed)
