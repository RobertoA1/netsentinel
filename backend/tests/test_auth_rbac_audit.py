import os
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

import pytest

from conftest import login
from helpers import API

ADMIN_PW = os.environ["ADMIN_PASSWORD"]


def test_startup_fails_without_secrets():
    env = {k: v for k, v in os.environ.items() if k not in ("JWT_SECRET", "ADMIN_PASSWORD")}
    p = subprocess.run([sys.executable, "-c", "import app.main"], cwd=Path(__file__).parents[1], env=env,
                       capture_output=True, text=True)
    assert p.returncode != 0
    assert "JWT_SECRET" in p.stderr and "ADMIN_PASSWORD" in p.stderr and "Configuración incompleta" in p.stderr


def test_login_me_refresh_logout(app_client):
    r = login(app_client, "admin", ADMIN_PW)
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer" and body["user"]["role"]["name"] == "admin"
    assert "audit:view" in body["user"]["permissions"] and body["user"]["profile"]["language"] == "es"
    h = {"Authorization": f"Bearer {body['access_token']}"}
    assert app_client.get(f"{API}/auth/me", headers=h).json()["username"] == "admin"
    # un refresh token no sirve como access token y viceversa
    assert app_client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {body['refresh_token']}"}).status_code == 401
    rf = app_client.post(f"{API}/auth/refresh", json={"refresh_token": body["refresh_token"]})
    assert rf.status_code == 200 and rf.json()["access_token"]
    assert app_client.post(f"{API}/auth/refresh", json={"refresh_token": body["access_token"]}).status_code == 401
    assert app_client.get(f"{API}/auth/me").status_code == 401
    assert app_client.get(f"{API}/auth/me", headers={"Authorization": "Bearer basura"}).status_code == 401
    assert app_client.post(f"{API}/auth/logout", headers=h).status_code == 204


def test_failed_login_lockout_after_5(app_client, make_user, admin_headers):
    make_user("bloqueado", "analyst")
    for i in range(4):
        r = login(app_client, "bloqueado", "mala-clave")
        assert r.status_code == 401 and "incorrectos" in r.json()["detail"]
    r = login(app_client, "bloqueado", "mala-clave")
    assert r.status_code == 403 and "bloqueada" in r.json()["detail"]
    r = login(app_client, "bloqueado", "Passw0rd-Test!")     # clave correcta, pero sigue bloqueado 15 min
    assert r.status_code == 403 and "Intente de nuevo" in r.json()["detail"]
    ev = app_client.get(f"{API}/audit/events?event_type=login_failed&q=bloqueado&page_size=50", headers=admin_headers).json()
    assert ev["total"] >= 5
    # el administrador puede reactivar la cuenta
    uid = app_client.get(f"{API}/users?q=bloqueado", headers=admin_headers).json()["items"][0]["id"]
    assert app_client.put(f"{API}/users/{uid}", headers=admin_headers, json={"is_active": True}).status_code == 200
    assert login(app_client, "bloqueado", "Passw0rd-Test!").status_code == 200


def test_unknown_user_logs_failed_event(app_client, admin_headers):
    assert login(app_client, "fantasma", "x").status_code == 401
    ev = app_client.get(f"{API}/audit/events?event_type=login_failed&q=fantasma", headers=admin_headers).json()
    assert ev["total"] == 1 and ev["items"][0]["details"]["reason"] == "unknown_user"


def test_must_change_password_flow(app_client, admin_headers):
    roles = {r["name"]: r["id"] for r in app_client.get(f"{API}/roles", headers=admin_headers).json()}
    app_client.post(f"{API}/users", headers=admin_headers, json={"username": "nuevo", "email": "nuevo@x.com", "password": "Temporal-1234", "role_id": roles["analyst"]})
    r = login(app_client, "nuevo", "Temporal-1234")
    assert r.json()["user"]["must_change_password"] is True
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert app_client.get(f"{API}/auth/me", headers=h).status_code == 200
    d = app_client.get(f"{API}/dashboard/summary", headers=h)
    assert d.status_code == 403 and "contraseña" in d.json()["detail"]
    assert app_client.post(f"{API}/auth/me/password", headers=h, json={"current_password": "otra", "new_password": "Nueva-Clave-99"}).status_code == 400
    assert app_client.post(f"{API}/auth/me/password", headers=h, json={"current_password": "Temporal-1234", "new_password": "corta"}).status_code == 422
    assert app_client.post(f"{API}/auth/me/password", headers=h, json={"current_password": "Temporal-1234", "new_password": "Nueva-Clave-99"}).status_code == 204
    assert app_client.get(f"{API}/dashboard/summary", headers=h).status_code == 200
    assert login(app_client, "nuevo", "Temporal-1234").status_code == 401
    assert login(app_client, "nuevo", "Nueva-Clave-99").json()["user"]["must_change_password"] is False


def test_profile_update(app_client, make_user):
    h = make_user("perfil1", "analyst")
    r = app_client.put(f"{API}/auth/me/profile", headers=h, json={"job_title": "SysAdmin", "theme": "dark", "full_name": "Ana P"})
    assert r.status_code == 200 and r.json()["profile"]["job_title"] == "SysAdmin" and r.json()["full_name"] == "Ana P"
    assert app_client.put(f"{API}/auth/me/profile", headers=h, json={"theme": "neon"}).status_code == 422


# ---- RBAC ------------------------------------------------------------------

MATRIX = [  # (rol, método, ruta, cuerpo, status esperado)
    ("manager", "GET", "/dashboard/summary", None, 200),
    ("manager", "GET", "/findings", None, 403),
    ("manager", "GET", "/logs", None, 403),
    ("manager", "GET", "/users", None, 403),
    ("manager", "GET", "/reports/catalog", None, 200),
    ("manager", "GET", "/audit/events", None, 403),
    ("auditor", "GET", "/findings", None, 200),
    ("auditor", "GET", "/audit/events", None, 200),
    ("auditor", "GET", "/audit/summary", None, 200),
    ("auditor", "GET", "/users", None, 403),
    ("auditor", "POST", "/ingest/run", {}, 403),
    ("auditor", "POST", "/alert-rules", {"name": "x1"}, 403),
    ("analyst", "GET", "/findings", None, 200),
    ("analyst", "POST", "/ingest/run", {}, 200),
    ("analyst", "POST", "/detect/run", {}, 200),
    ("analyst", "GET", "/audit/events", None, 403),
    ("analyst", "GET", "/users", None, 403),
    ("analyst", "PUT", "/settings/detection", None, 403),
    ("analyst", "POST", "/lists", {"list_type": "allow", "kind": "ip", "value": "1.1.1.1"}, 403),
    ("analyst", "POST", "/maintenance/purge", None, 403),
]


@pytest.mark.parametrize("role,method,path,body,expected", MATRIX)
def test_rbac_matrix(app_client, make_user, role, method, path, body, expected):
    h = make_user(f"u_{role}", role) if role not in _cache else _cache[role]
    _cache[role] = h
    r = app_client.request(method, API + path, headers=h, json=body)
    assert r.status_code == expected, (role, method, path, r.text)
    if expected == 403:
        assert "permiso" in r.json()["detail"].lower() or "administrador" in r.json()["detail"].lower()


_cache: dict = {}


def test_manager_catalog_only_management_reports(app_client, make_user):
    h = _cache.get("manager") or make_user("u_manager", "manager")
    cat = app_client.get(f"{API}/reports/catalog", headers=h).json()
    assert cat and {c["category"] for c in cat} <= {"management", "ml"} and "management" in {c["category"] for c in cat}
    r = app_client.post(f"{API}/reports/generate", headers=h, json={"report_code": "op_findings", "format": "pdf", "date_from": "2011-08-10", "date_to": "2011-08-11"})
    assert r.status_code == 403
    r = app_client.post(f"{API}/reports/generate", headers=h, json={"report_code": "mg_executive_summary", "format": "pdf", "date_from": "2011-08-10", "date_to": "2011-08-11"})
    assert r.status_code == 200 and r.content.startswith(b"%PDF")


def test_api_key_scope(app_client):
    k = {"X-API-Key": "test-n8n-key"}
    assert app_client.get(f"{API}/users", headers=k).status_code == 403        # la key no abre rutas de usuario
    assert app_client.get(f"{API}/findings", headers=k).status_code == 403
    assert app_client.get(f"{API}/alerts/pending-dispatch", headers=k).status_code == 200
    assert app_client.post(f"{API}/auth/logout", headers=k).status_code == 403
    assert app_client.post(f"{API}/detect/run", headers=k, json={}).status_code == 200


def test_roles_and_permissions_crud(app_client, admin_headers):
    cat = app_client.get(f"{API}/permissions", headers=admin_headers).json()
    assert {m["code"] for m in cat["modules"]} >= {"dashboard", "findings", "audit", "ingestion", "llm"}
    assert next(m for m in cat["modules"] if m["code"] == "findings")["actions"] == ["view", "update", "export"]
    roles = app_client.get(f"{API}/roles", headers=admin_headers).json()
    admin = next(r for r in roles if r["name"] == "admin")
    assert admin["is_system"] and admin["user_count"] >= 1 and "users:delete" in admin["permissions"]
    assert app_client.delete(f"{API}/roles/{admin['id']}", headers=admin_headers).status_code == 400
    r = app_client.post(f"{API}/roles", headers=admin_headers, json={"name": "soc-nivel1", "description": "N1", "permissions": ["findings:view", "alerts:view"]})
    assert r.status_code == 201 and r.json()["permissions"] == ["alerts:view", "findings:view"]
    rid = r.json()["id"]
    assert app_client.post(f"{API}/roles", headers=admin_headers, json={"name": "soc-nivel1"}).status_code == 409
    assert app_client.post(f"{API}/roles", headers=admin_headers, json={"name": "malo", "permissions": ["x:y"]}).status_code == 422
    assert app_client.put(f"{API}/roles/{rid}", headers=admin_headers, json={"name": "soc-nivel1", "permissions": ["findings:view"]}).json()["permissions"] == ["findings:view"]
    app_client.post(f"{API}/users", headers=admin_headers, json={"username": "soc1", "email": "soc1@x.com", "password": "Temporal-1234", "role_id": rid})
    assert app_client.delete(f"{API}/roles/{rid}", headers=admin_headers).status_code == 409   # tiene usuarios
    uid = app_client.get(f"{API}/users?q=soc1", headers=admin_headers).json()["items"][0]["id"]
    assert app_client.delete(f"{API}/users/{uid}", headers=admin_headers).status_code == 204
    assert app_client.delete(f"{API}/roles/{rid}", headers=admin_headers).status_code == 204
    assert app_client.get(f"{API}/roles/{rid}", headers=admin_headers).status_code == 404


def test_cannot_remove_last_admin_or_self(app_client, admin_headers):
    me = app_client.get(f"{API}/auth/me", headers=admin_headers).json()
    assert app_client.delete(f"{API}/users/{me['id']}", headers=admin_headers).status_code == 400
    assert app_client.put(f"{API}/users/{me['id']}", headers=admin_headers, json={"is_active": False}).status_code == 400


def test_users_listing_and_reset_password(app_client, admin_headers, make_user):
    make_user("lista1", "auditor")
    page = app_client.get(f"{API}/users?q=lista&page=1&page_size=5", headers=admin_headers).json()
    assert page["total"] == 1 and "permissions" not in page["items"][0] and page["items"][0]["created_at"]
    uid = page["items"][0]["id"]
    assert app_client.post(f"{API}/users/{uid}/reset-password", headers=admin_headers, json={"new_password": "Reset-Clave-77"}).status_code == 204
    assert login(app_client, "lista1", "Reset-Clave-77").json()["user"]["must_change_password"] is True
    assert app_client.post(f"{API}/users", headers=admin_headers, json={"username": "lista1", "email": "otro@x.com", "password": "Temporal-1234", "role_id": 1}).status_code == 409


# ---- Bitácora ---------------------------------------------------------------

def test_module_sessions_enter_exit_logout(app_client, make_user, admin_headers):
    h = make_user("auditado", "analyst")
    uid = app_client.get(f"{API}/auth/me", headers=h).json()["id"]
    s1 = app_client.post(f"{API}/audit/module-enter", headers=h, json={"module": "findings"}).json()["session_id"]
    s2 = app_client.post(f"{API}/audit/module-enter", headers=h, json={"module": "alerts"}).json()["session_id"]   # cierra s1 por navegación
    assert app_client.post(f"{API}/audit/module-enter", headers=h, json={"module": "inexistente"}).status_code == 422
    ms = app_client.get(f"{API}/audit/module-sessions?user_id={uid}&sort=entered_at", headers=admin_headers).json()
    by = {m["id"]: m for m in ms["items"]}
    assert by[s1]["exit_reason"] == "navigation" and by[s1]["exited_at"] and by[s1]["duration_seconds"] >= 0
    assert by[s2]["exited_at"] is None and by[s2]["module"] == "alerts" and by[s2]["username"] == "auditado" and by[s2]["ip"]
    # salida explícita con motivo
    assert app_client.post(f"{API}/audit/module-exit", headers=h, json={"session_id": s2, "reason": "close"}).status_code == 204
    assert app_client.post(f"{API}/audit/module-exit", headers=h, json={"session_id": s2, "reason": "close"}).status_code == 204  # idempotente
    s3 = app_client.post(f"{API}/audit/module-enter", headers=h, json={"module": "dashboard"}).json()["session_id"]
    # otro usuario no puede cerrar mi sesión
    assert app_client.post(f"{API}/audit/module-exit", headers=admin_headers, json={"session_id": s3}).status_code == 404
    # el logout cierra las sesiones abiertas
    assert app_client.post(f"{API}/auth/logout", headers=h).status_code == 204
    ms = app_client.get(f"{API}/audit/module-sessions?user_id={uid}", headers=admin_headers).json()["items"]
    by = {m["id"]: m for m in ms}
    assert by[s2]["exit_reason"] == "close" and by[s3]["exit_reason"] == "logout"
    types = [e["event_type"] for e in app_client.get(f"{API}/audit/events?user_id={uid}&sort=id&page_size=100", headers=admin_headers).json()["items"]]
    assert types.count("module_enter") == 3 and types.count("module_exit") == 3 and "login" in types and types[-1] == "logout"
    mod = app_client.get(f"{API}/audit/events?module=alerts&event_type=module_enter", headers=admin_headers).json()["items"][0]
    assert mod["username"] == "auditado" and mod["ip"] and mod["user_agent"] and mod["description"]


def test_module_session_lazy_timeout(app_client, make_user, admin_headers):
    from app.db.base import utcnow
    from app.db.session import new_session
    from app.models import ModuleSession

    h = make_user("inactivo", "analyst")
    sid = app_client.post(f"{API}/audit/module-enter", headers=h, json={"module": "logs"}).json()["session_id"]
    db = new_session()
    try:
        s = db.get(ModuleSession, sid)
        s.entered_at = utcnow() - timedelta(minutes=50)
        s.last_activity_at = utcnow() - timedelta(minutes=40)
        db.commit()
    finally:
        db.close()
    ms = app_client.get(f"{API}/audit/module-sessions?module=logs", headers=admin_headers).json()["items"]
    m = next(x for x in ms if x["id"] == sid)
    assert m["exit_reason"] == "timeout" and m["exited_at"] is not None
    assert 590 <= m["duration_seconds"] <= 610            # 50 min de entrada - 40 min de inactividad = 10 min de uso
    ev = app_client.get(f"{API}/audit/events?event_type=module_exit&q=timeout", headers=admin_headers).json()
    assert ev["total"] >= 1


def test_activity_keeps_session_alive(app_client, make_user, admin_headers):
    from app.db.base import utcnow
    from app.db.session import new_session
    from app.models import ModuleSession

    h = make_user("activo", "analyst")
    sid = app_client.post(f"{API}/audit/module-enter", headers=h, json={"module": "logs"}).json()["session_id"]
    db = new_session()
    try:
        s = db.get(ModuleSession, sid)
        s.last_activity_at = utcnow() - timedelta(minutes=20)
        db.commit()
    finally:
        db.close()
    app_client.get(f"{API}/logs", headers=h)   # actividad: renueva la sesión
    ms = app_client.get(f"{API}/audit/module-sessions?module=logs&user_id=" + str(app_client.get(f"{API}/auth/me", headers=h).json()["id"]), headers=admin_headers).json()["items"]
    assert next(x for x in ms if x["id"] == sid)["exited_at"] is None


def test_crud_events_and_summary_and_append_only(app_client, admin_headers):
    r = app_client.post(f"{API}/sources", headers=admin_headers, json={"name": "Fuente audit", "format": "suricata_eve"})
    sid = r.json()["id"]
    app_client.put(f"{API}/sources/{sid}", headers=admin_headers, json={"name": "Fuente audit 2", "format": "suricata_eve"})
    app_client.delete(f"{API}/sources/{sid}", headers=admin_headers)
    evs = app_client.get(f"{API}/audit/events?q=Fuente&sort=id&page_size=50", headers=admin_headers).json()["items"]
    kinds = [(e["event_type"], e["entity"], e["entity_id"]) for e in evs if e["entity"] == "source"]
    assert kinds[-3:] == [("create", "source", str(sid)), ("update", "source", str(sid)), ("delete", "source", str(sid))]
    assert evs[-1]["username"] == "admin"
    # un intento fallido (404) no deja evento de update
    n = app_client.get(f"{API}/audit/events?event_type=update", headers=admin_headers).json()["total"]
    assert app_client.put(f"{API}/sources/999999", headers=admin_headers, json={"name": "zz", "format": "suricata_eve"}).status_code == 404
    assert app_client.get(f"{API}/audit/events?event_type=update", headers=admin_headers).json()["total"] == n
    sm = app_client.get(f"{API}/audit/summary", headers=admin_headers).json()
    assert set(sm) == {"by_module", "by_user", "by_event_type"}
    assert any(x["event_type"] == "login" for x in sm["by_event_type"])
    assert all(set(x) == {"module", "visits", "total_seconds"} for x in sm["by_module"]) and sm["by_user"]
    assert all(set(x) == {"username", "visits", "total_seconds", "last_seen"} for x in sm["by_user"])
    # solo inserción: no existen rutas de modificación/borrado de la bitácora
    for m in ("PUT", "PATCH", "DELETE"):
        assert app_client.request(m, f"{API}/audit/events/1", headers=admin_headers).status_code in (404, 405)
        assert app_client.request(m, f"{API}/audit/events", headers=admin_headers).status_code == 405
    paths = app_client.get(f"{API}/openapi.json").json()["paths"]
    assert all(set(v) <= {"get", "post"} for p, v in paths.items() if p.startswith(f"{API}/audit"))


def test_seed_is_idempotent(app_client):
    from sqlalchemy import func, select
    from app.db.seed import seed
    from app.db.session import new_session
    from app.models import AlertRule, AppSetting, Role, Source, User

    db = new_session()
    try:
        counts = lambda: [db.execute(select(func.count()).select_from(m)).scalar_one() for m in (Role, User, Source, AlertRule, AppSetting)]  # noqa: E731
        before = counts()
        seed(db)
        seed(db)
        assert counts() == before
        assert db.execute(select(Role.name)).scalars().all()[:4] == ["admin", "analyst", "auditor", "manager"]
        assert before[2] >= 3 and before[3] >= 2 and before[4] == 4  # +1: bandera ml_permissions_seeded
    finally:
        db.close()
