"""Semilla idempotente: solo catálogos (roles, permisos, admin, fuentes, reglas, configuración)."""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_strict_settings
from app.core.permissions import ALL_PERMISSIONS, ML_MODULES, ROLE_SEEDS
from app.core.security import hash_password
from app.db.session import new_session
from app.models import AlertRule, AppSetting, Role, Source, User, UserProfile
from app.services import settings_service

log = logging.getLogger("netsentinel.seed")

DEFAULT_SOURCES = [
    ("OPNsense LAN", "opnsense_filterlog", "Logs filterlog del firewall OPNsense/pfSense (syslog)"),
    ("Suricata IDS", "suricata_eve", "EVE JSON de Suricata (alertas y flujos)"),
    ("CTU-13 Dataset", "ctu13_binetflow", "Dataset real CTU-13 (demo)"),
]

DEFAULT_RULES = [
    dict(name="Críticos y altos", enabled=True, min_severity="high", finding_types=[],
         channels=["in_app", "webhook"], include_noise=False),
    dict(name="Exfiltración y beaconing (medios o superiores)", enabled=True, min_severity="medium",
         finding_types=["exfiltration", "beaconing"], channels=["in_app"], include_noise=False),
]


def _seed_ml_permissions(db: Session) -> None:
    """Concede UNA sola vez los permisos ML de la semilla a los roles de sistema ya existentes
    (no pisa ajustes posteriores del administrador: la bandera queda en app_settings)."""
    if db.get(AppSetting, "ml_permissions_seeded") is not None:
        return
    for name, (_, perms) in ROLE_SEEDS.items():
        role = db.execute(select(Role).where(Role.name == name)).scalar_one_or_none()
        if role is None:
            continue
        ml = [p for p in perms if p.split(":")[0] in ML_MODULES]
        role.set_permissions(sorted(set(role.permissions) | set(ml)))
    db.add(AppSetting(key="ml_permissions_seeded", value={"done": True}))
    db.flush()


def seed(db: Session) -> None:
    cfg = get_strict_settings()
    # Roles
    for name, (desc, perms) in ROLE_SEEDS.items():
        role = db.execute(select(Role).where(Role.name == name)).scalar_one_or_none()
        if role is None:
            role = Role(name=name, description=desc, is_system=True)
            role.set_permissions(perms)
            db.add(role)
        else:
            role.is_system = True
            if name == "admin":  # admin siempre tiene todos los permisos vigentes
                role.set_permissions(list(ALL_PERMISSIONS))
    db.flush()
    _seed_ml_permissions(db)
    # Admin
    admin_role = db.execute(select(Role).where(Role.name == "admin")).scalar_one()
    if db.execute(select(User).where(User.username == cfg.admin_username)).unique().scalar_one_or_none() is None:
        u = User(username=cfg.admin_username, email=cfg.admin_email, full_name="Administrador",
                 password_hash=hash_password(cfg.admin_password), role_id=admin_role.id, is_active=True,
                 must_change_password=False)
        u.profile = UserProfile()
        db.add(u)
        log.info("Usuario administrador '%s' creado", cfg.admin_username)
    # Fuentes
    for name, fmt, desc in DEFAULT_SOURCES:
        if db.execute(select(Source).where(Source.name == name)).scalar_one_or_none() is None:
            db.add(Source(name=name, format=fmt, description=desc, enabled=True))
    # Reglas de alerta (solo si no existe ninguna)
    if db.execute(select(AlertRule.id).limit(1)).first() is None:
        for r in DEFAULT_RULES:
            db.add(AlertRule(**r))
    db.commit()
    settings_service.ensure_defaults(db)  # configuración + lista de puertos comunes


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    db = new_session()
    try:
        seed(db)
        print("Semilla aplicada")
    finally:
        db.close()


if __name__ == "__main__":
    main()
