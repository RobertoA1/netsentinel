"""Catálogo RBAC `modulo:accion`."""
from __future__ import annotations

# módulo -> (etiqueta, acciones aplicables)
MODULES: dict[str, tuple[str, list[str]]] = {
    "dashboard": ("Panel", ["view"]),
    "logs": ("Registros", ["view", "export"]),
    "findings": ("Hallazgos", ["view", "update", "export"]),
    "alerts": ("Alertas", ["view", "create", "update", "delete"]),
    "reports": ("Reportes", ["view", "export"]),
    "assets": ("Activos", ["view", "create", "update", "delete"]),
    "sources": ("Fuentes", ["view", "create", "update", "delete"]),
    "lists": ("Listas allow/deny", ["view", "create", "delete"]),
    "ingestion": ("Ingesta", ["view", "execute"]),
    "detection": ("Detección", ["view", "update", "execute"]),
    "llm": ("Modelo LLM", ["view", "update", "execute"]),
    "users": ("Usuarios", ["view", "create", "update", "delete"]),
    "roles": ("Roles", ["view", "create", "update", "delete"]),
    "audit": ("Bitácora", ["view", "export"]),
    "ml_data": ("ML: Datos", ["view", "create", "update", "delete", "export"]),
    "ml_training": ("ML: Entrenamiento", ["view", "create", "update", "delete", "execute"]),
    "ml_evaluation": ("ML: Evaluación", ["view", "update", "export"]),
    "ml_explain": ("ML: Explicabilidad", ["view", "execute", "export"]),
    "ml_inference": ("ML: Inferencia", ["view", "execute", "update", "export"]),
    "ml_optuna": ("ML: Optimización", ["view", "create", "execute", "delete"]),
}

ALL_PERMISSIONS: list[str] = [f"{m}:{a}" for m, (_, acts) in MODULES.items() for a in acts]
MODULE_CODES = list(MODULES.keys())


def _views(*mods: str) -> list[str]:
    return [f"{m}:view" for m in mods]


OPERATIONAL_VIEW = ["dashboard", "logs", "findings", "alerts", "assets", "sources", "lists",
                    "ingestion", "detection", "llm"]

ML_MODULES = ["ml_data", "ml_training", "ml_evaluation", "ml_explain", "ml_inference", "ml_optuna"]
ML_VIEW = [f"{m}:view" for m in ML_MODULES]

ROLE_SEEDS: dict[str, tuple[str, list[str]]] = {
    "admin": ("Administrador: acceso total", list(ALL_PERMISSIONS)),
    "analyst": (
        "Analista: opera hallazgos, alertas e ingesta",
        _views(*OPERATIONAL_VIEW, "reports")
        + ["findings:update", "findings:export", "logs:export", "alerts:create", "alerts:update",
           "alerts:delete", "ingestion:execute", "detection:execute", "reports:export"]
        + ML_VIEW + ["ml_inference:execute", "ml_inference:export", "ml_data:export", "ml_evaluation:export",
                     "ml_explain:export"],
    ),
    "auditor": (
        "Auditor: solo lectura, bitácora y reportes",
        _views(*OPERATIONAL_VIEW, "reports", "audit") + ML_VIEW + ["reports:export", "audit:export", "logs:export"],
    ),
    "manager": ("Gerencia: panel y reportes de gestión",
                ["dashboard:view", "reports:view", "reports:export", "ml_evaluation:view"]),
}


def valid_permission(code: str) -> bool:
    return code in ALL_PERMISSIONS


def permissions_catalog() -> dict:
    return {"modules": [{"code": m, "label": lbl, "actions": list(acts)} for m, (lbl, acts) in MODULES.items()]}
