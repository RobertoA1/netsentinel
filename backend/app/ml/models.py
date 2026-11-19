"""Catálogo de modelos, espacios de búsqueda (con justificación), pipelines de preprocesamiento y calibración."""
from __future__ import annotations

import copy
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from app.core.config import get_settings
from app.ml.features import FLOW_LOG_COLS, WINDOW_LOG_COLS, feature_columns

MODEL_TYPES = ["dummy", "logreg", "random_forest", "hist_gb", "xgboost"]
MODEL_ES = {"dummy": "Línea base trivial (Dummy)", "logreg": "Regresión logística", "random_forest": "Random Forest",
            "hist_gb": "Gradient Boosting de histogramas", "xgboost": "XGBoost"}
TREE_BASED = {"random_forest", "hist_gb", "xgboost"}

# Cada parámetro: tipo, rango por defecto, rango DURO (límite de seguridad editable solo dentro de él), y por qué.
SEARCH_SPACES: dict[str, list[dict]] = {
    "logreg": [
        {"name": "C", "type": "float", "low": 1e-3, "high": 1e2, "log": True, "hard": [1e-6, 1e4],
         "why": "Inversa de la regularización; escala log porque su efecto es multiplicativo."},
        {"name": "penalty", "type": "categorical", "choices": ["l2", "l1"], "hard_choices": ["l1", "l2"],
         "why": "L2 estabiliza variables correlacionadas; L1 selecciona variables (modelo más disperso)."},
        {"name": "class_weight", "type": "categorical", "choices": ["none", "balanced"],
         "hard_choices": ["none", "balanced"], "why": "Compensa el desbalance Botnet/Normal sin remuestrear."},
    ],
    "random_forest": [
        {"name": "n_estimators", "type": "int", "low": 200, "high": 800, "step": 100, "hard": [50, 1500],
         "why": "Más árboles reducen la varianza con rendimientos decrecientes; 200-800 cubre el codo habitual."},
        {"name": "max_depth", "type": "int", "low": 4, "high": 30, "hard": [2, 60],
         "why": "Controla el sobreajuste; árboles muy profundos memorizan grupos de entrenamiento."},
        {"name": "min_samples_leaf", "type": "int", "low": 1, "high": 20, "log": True, "hard": [1, 200],
         "why": "Hojas mayores suavizan las probabilidades (útil para calibrar)."},
        {"name": "max_features", "type": "categorical", "choices": ["sqrt", "log2", "0.5"],
         "hard_choices": ["sqrt", "log2", "0.3", "0.5", "0.7", "1.0"],
         "why": "Decorrelaciona los árboles; sqrt es el valor clásico para clasificación."},
        {"name": "class_weight", "type": "categorical", "choices": ["none", "balanced", "balanced_subsample"],
         "hard_choices": ["none", "balanced", "balanced_subsample"], "why": "Compensa el desbalance de clases."},
    ],
    "hist_gb": [
        {"name": "learning_rate", "type": "float", "low": 0.01, "high": 0.3, "log": True, "hard": [0.001, 1.0],
         "why": "Paso de aprendizaje; escala log, se compensa con max_iter."},
        {"name": "max_iter", "type": "int", "low": 100, "high": 500, "hard": [20, 1500],
         "why": "Nº de iteraciones de boosting (sin parada temprana: la selección es por CV)."},
        {"name": "max_leaf_nodes", "type": "int", "low": 8, "high": 64, "hard": [4, 256],
         "why": "Complejidad de cada árbol."},
        {"name": "l2_regularization", "type": "float", "low": 1e-6, "high": 10.0, "log": True, "hard": [0, 100],
         "why": "Penaliza hojas extremas; reduce sobreajuste."},
        {"name": "min_samples_leaf", "type": "int", "low": 5, "high": 100, "hard": [1, 500],
         "why": "Evita hojas con pocos flujos (que suelen ser de un solo grupo)."},
        {"name": "class_weight", "type": "categorical", "choices": ["none", "balanced"],
         "hard_choices": ["none", "balanced"], "why": "Compensa el desbalance de clases."},
    ],
    "xgboost": [
        {"name": "eta", "type": "float", "low": 0.01, "high": 0.3, "log": True, "hard": [0.001, 1.0],
         "why": "Tasa de aprendizaje; escala log."},
        {"name": "max_depth", "type": "int", "low": 2, "high": 10, "hard": [1, 20], "why": "Profundidad de los árboles."},
        {"name": "subsample", "type": "float", "low": 0.5, "high": 1.0, "hard": [0.3, 1.0],
         "why": "Fracción de filas por árbol: aleatoriza y regulariza."},
        {"name": "colsample_bytree", "type": "float", "low": 0.4, "high": 1.0, "hard": [0.2, 1.0],
         "why": "Fracción de variables por árbol: decorrelaciona."},
        {"name": "min_child_weight", "type": "float", "low": 1.0, "high": 20.0, "log": True, "hard": [0.1, 200],
         "why": "Peso mínimo por hoja; impide hojas diminutas."},
        {"name": "gamma", "type": "float", "low": 0.0, "high": 5.0, "hard": [0, 50],
         "why": "Ganancia mínima para dividir: poda estructural."},
        {"name": "reg_lambda", "type": "float", "low": 0.01, "high": 20.0, "log": True, "hard": [0, 200],
         "why": "Regularización L2 de los pesos de hoja."},
        {"name": "scale_pos_weight", "type": "float", "low": 1.0, "high": 50.0, "log": True, "hard": [0.1, 500],
         "why": "Peso de la clase positiva frente al desbalance (≈ negativos/positivos)."},
    ],
    "dummy": [],
}
FIXED_PARAMS = {"xgboost": {"n_estimators": 300}, "logreg": {"max_iter": 2000}}
MAX_TRIALS_HARD = 300
MAX_FOLDS_HARD = 10


def space_catalog() -> list[dict]:
    return [{"model": m, "label": MODEL_ES[m], "params": copy.deepcopy(SEARCH_SPACES[m]),
             "fixed": FIXED_PARAMS.get(m, {})} for m in MODEL_TYPES]


def effective_space(model_type: str, overrides: dict | None) -> list[dict]:
    """Aplica rangos editados por el usuario validando que estén dentro de los límites duros."""
    base = copy.deepcopy(SEARCH_SPACES[model_type])
    overrides = overrides or {}
    known = {p["name"] for p in base}
    extra = set(overrides) - known
    if extra:
        raise ValueError(f"Parámetros desconocidos para {model_type}: {', '.join(sorted(extra))}")
    for p in base:
        o = overrides.get(p["name"])
        if not o:
            continue
        if p["type"] == "categorical":
            ch = [str(c) for c in o.get("choices", [])]
            bad = [c for c in ch if c not in p["hard_choices"]]
            if not ch or bad:
                raise ValueError(f"{p['name']}: opciones inválidas {bad or ch}")
            p["choices"] = ch
        else:
            lo, hi = o.get("low", p["low"]), o.get("high", p["high"])
            hl, hh = p["hard"]
            if not (isinstance(lo, (int, float)) and isinstance(hi, (int, float))) or lo > hi:
                raise ValueError(f"{p['name']}: rango inválido")
            if lo < hl or hi > hh:
                raise ValueError(f"{p['name']}: el rango debe estar dentro de [{hl}, {hh}]")
            if p.get("log") and lo <= 0:
                raise ValueError(f"{p['name']}: escala logarítmica requiere mínimo > 0")
            p["low"], p["high"] = (int(lo), int(hi)) if p["type"] == "int" else (float(lo), float(hi))
    return base


def suggest_params(trial, space: list[dict]) -> dict:
    out: dict[str, Any] = {}
    for p in space:
        n = p["name"]
        if p["type"] == "float":
            out[n] = trial.suggest_float(n, p["low"], p["high"], log=bool(p.get("log")))
        elif p["type"] == "int":
            if p.get("step") and not p.get("log"):
                out[n] = trial.suggest_int(n, p["low"], p["high"], step=p["step"])
            else:
                out[n] = trial.suggest_int(n, p["low"], p["high"], log=bool(p.get("log")))
        else:
            out[n] = trial.suggest_categorical(n, p["choices"])
    return out


def _cw(v):
    return None if v in (None, "none") else v


def build_estimator(model_type: str, params: dict, seed: int, n_jobs: int | None = None):
    n_jobs = n_jobs or get_settings().ml_n_jobs
    p = dict(params or {})
    if model_type == "dummy":
        return DummyClassifier(strategy="prior")
    if model_type == "logreg":
        return LogisticRegression(C=p.get("C", 1.0), l1_ratio=1.0 if p.get("penalty") == "l1" else 0.0,
                                  solver="liblinear", class_weight=_cw(p.get("class_weight")), max_iter=2000,
                                  random_state=seed)
    if model_type == "random_forest":
        mf = p.get("max_features", "sqrt")
        try:
            mf = float(mf)
        except (TypeError, ValueError):
            pass
        return RandomForestClassifier(n_estimators=int(p.get("n_estimators", 300)), max_depth=int(p.get("max_depth", 12)),
                                      min_samples_leaf=int(p.get("min_samples_leaf", 1)), max_features=mf,
                                      class_weight=_cw(p.get("class_weight")), n_jobs=n_jobs, random_state=seed)
    if model_type == "hist_gb":
        return HistGradientBoostingClassifier(
            learning_rate=p.get("learning_rate", 0.1), max_iter=int(p.get("max_iter", 200)),
            max_leaf_nodes=int(p.get("max_leaf_nodes", 31)), l2_regularization=p.get("l2_regularization", 1e-3),
            min_samples_leaf=int(p.get("min_samples_leaf", 20)), class_weight=_cw(p.get("class_weight")),
            early_stopping=False, random_state=seed)
    if model_type == "xgboost":
        return SafeXGB(
            n_estimators=int(p.get("n_estimators", FIXED_PARAMS["xgboost"]["n_estimators"])),
            learning_rate=p.get("eta", 0.1), max_depth=int(p.get("max_depth", 6)), subsample=p.get("subsample", 1.0),
            colsample_bytree=p.get("colsample_bytree", 1.0), min_child_weight=p.get("min_child_weight", 1.0),
            gamma=p.get("gamma", 0.0), reg_lambda=p.get("reg_lambda", 1.0),
            scale_pos_weight=p.get("scale_pos_weight", 1.0), tree_method="hist", n_jobs=n_jobs,
            random_state=seed, eval_metric="logloss", verbosity=0)
    raise ValueError(f"Modelo desconocido: {model_type}")


from xgboost import XGBClassifier  # noqa: E402


class SafeXGB(XGBClassifier):
    """XGBoost rechaza nombres con [, ] o <; las categorías one-hot (p. ej. «dir_<->») los traen.
    Pasa solo valores numéricos al booster; los nombres originales los conserva el preprocesador."""

    def fit(self, X, y=None, **kw):
        return super().fit(np.asarray(X, dtype=float), y, **kw)

    def predict_proba(self, X, **kw):
        return super().predict_proba(np.asarray(X, dtype=float), **kw)

    def predict(self, X, **kw):
        return super().predict(np.asarray(X, dtype=float), **kw)


def _log1p(X):
    return np.log1p(np.clip(np.asarray(X, dtype=float), 0, None))


def build_pipeline(model_type: str, params: dict, unit: str, seed: int, n_jobs: int | None = None) -> Pipeline:
    """Preprocesamiento DENTRO del pipeline (se ajusta solo con el entrenamiento de cada pliegue):
    imputación por mediana (+ log1p y escalado en el modelo lineal), codificación one-hot de categóricas."""
    cols = feature_columns(unit)
    from app.ml.features import FLOW_CATEGORICAL, WINDOW_CATEGORICAL
    cat = WINDOW_CATEGORICAL if unit == "window" else FLOW_CATEGORICAL
    num = [c for c in cols if c not in cat]
    logc = [c for c in (WINDOW_LOG_COLS if unit == "window" else FLOW_LOG_COLS) if c in num]
    if model_type == "logreg":
        lin = [c for c in num if c in logc]
        plain = [c for c in num if c not in logc]
        steps = []
        if lin:
            steps.append(("log", Pipeline([("imp", SimpleImputer(strategy="median")),
                                           ("log1p", FunctionTransformer(_log1p, feature_names_out="one-to-one")),
                                           ("sc", StandardScaler())]), lin))
        if plain:
            steps.append(("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), plain))
    else:
        steps = [("num", SimpleImputer(strategy="median"), num)] if num else []
    if cat:
        steps.append(("cat", OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=20,
                                           sparse_output=False), cat))
    pre = ColumnTransformer(steps, verbose_feature_names_out=False).set_output(transform="pandas")
    return Pipeline([("pre", pre), ("clf", build_estimator(model_type, params, seed, n_jobs))])


def predict_proba(pipe: Pipeline, X: pd.DataFrame) -> np.ndarray:
    return pipe.predict_proba(X)[:, 1]


class Calibrator:
    """Calibra probabilidades crudas con los datos de VALIDACIÓN: sigmoide (Platt) o isotónica."""

    def __init__(self, method: str = "sigmoid"):
        self.method = method
        self.model: Any = None

    def fit(self, p_raw, y) -> "Calibrator":
        p_raw = np.clip(np.asarray(p_raw, float), 1e-6, 1 - 1e-6)
        if self.method == "isotonic":
            self.model = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(p_raw, y)
        else:
            z = np.log(p_raw / (1 - p_raw)).reshape(-1, 1)
            self.model = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000).fit(z, y)
        return self

    def predict(self, p_raw) -> np.ndarray:
        p_raw = np.clip(np.asarray(p_raw, float), 1e-6, 1 - 1e-6)
        if self.method == "isotonic":
            return np.asarray(self.model.predict(p_raw), float)
        z = np.log(p_raw / (1 - p_raw)).reshape(-1, 1)
        return self.model.predict_proba(z)[:, 1]


def choose_calibration(n_val: int, n_pos: int, n_neg: int) -> str:
    """Regla determinista: isotónica solo con Validación grande (>=1000 filas y >=100 de cada clase)."""
    return "isotonic" if (n_val >= 1000 and min(n_pos, n_neg) >= 100) else "sigmoid"
