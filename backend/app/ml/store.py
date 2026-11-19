"""Artefactos en el volumen ML: rutas seguras, JSON, carga de modelos SOLO generados por el propio sistema."""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

import joblib
import numpy as np

from app.ml.data import ml_root


def lib_versions() -> dict:
    import optuna
    import pandas
    import scipy
    import shap
    import sklearn
    import xgboost

    return {"python": sys.version.split()[0], "platform": platform.platform(), "numpy": np.__version__,
            "pandas": pandas.__version__, "scipy": scipy.__version__, "scikit-learn": sklearn.__version__,
            "optuna": optuna.__version__, "shap": shap.__version__, "xgboost": xgboost.__version__,
            "joblib": joblib.__version__}


def safe_path(p: str | Path) -> Path:
    rp = Path(p).resolve()
    root = ml_root().resolve()
    if root not in rp.parents and rp != root:
        raise ValueError("Ruta fuera del volumen ML")
    return rp


def run_dir(run_id: int) -> Path:
    d = ml_root() / "runs" / str(run_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def model_dir() -> Path:
    d = ml_root() / "models"
    d.mkdir(parents=True, exist_ok=True)
    return d


def job_dir(job_id: int) -> Path:
    d = ml_root() / "jobs" / str(job_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


class _Enc(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return None if (np.isnan(o) or np.isinf(o)) else float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        return super().default(o)


def _clean(o):
    if isinstance(o, float) and (o != o or o in (float("inf"), float("-inf"))):
        return None
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    return o


def dump_json(path: Path, obj) -> None:
    path.write_text(json.dumps(_clean(obj), cls=_Enc, ensure_ascii=False))


def load_json(path: Path | str):
    return json.loads(safe_path(path).read_text())


def save_model(bundle: dict, model_id_hint: str) -> tuple[str, str]:
    """Guarda el paquete del modelo con joblib y devuelve (ruta, sha256)."""
    path = model_dir() / f"{model_id_hint}.joblib"
    joblib.dump(bundle, path, compress=3)
    return str(path), hashlib.sha256(path.read_bytes()).hexdigest()


def load_model(path: str, sha256: str) -> dict:
    """Carga un modelo SOLO si está dentro del volumen ML y su suma SHA-256 coincide con la registrada al entrenar.
    (joblib usa pickle: por eso jamás se cargan archivos subidos por usuarios.)"""
    p = safe_path(path)
    if p.parent != model_dir().resolve():
        raise ValueError("El modelo no está en el directorio de modelos del sistema")
    if hashlib.sha256(p.read_bytes()).hexdigest() != sha256:
        raise ValueError("Suma de verificación del modelo inválida: el archivo fue alterado")
    return joblib.load(p)
