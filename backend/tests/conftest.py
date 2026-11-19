import os
import tempfile
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="ns-tests-"))
os.environ.update({
    "DATABASE_URL": f"sqlite:///{_TMP}/test.db",
    "JWT_SECRET": "test-secret-0123456789-abcdef-0123456789",
    "ADMIN_PASSWORD": "Admin-Test-Pass-1",
    "N8N_API_KEY": "test-n8n-key",
    "INGEST_DIR": str(_TMP / "ingest"),
    "DATASET_DIR": str(_TMP / "dataset"),
    "REPORTS_DIR": str(_TMP / "reports"),
    "ML_DIR": str(_TMP / "ml"),
    "OLLAMA_BASE_URL": "http://127.0.0.1:9",  # puerto cerrado: Ollama "caído"
})

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from helpers import API  # noqa: E402


@pytest.fixture(scope="session")
def tmp_dirs():
    return _TMP


@pytest.fixture(scope="session")
def app_client():
    from app.db.base import Base
    from app.db.seed import seed
    from app.db.session import get_engine, new_session
    from app.main import app as fastapi_app
    import app.models  # noqa: F401

    Base.metadata.create_all(get_engine())
    db = new_session()
    try:
        seed(db)
    finally:
        db.close()
    with TestClient(fastapi_app) as c:
        yield c


def login(client, username, password):
    r = client.post(f"{API}/auth/login", json={"username": username, "password": password})
    return r


@pytest.fixture(scope="session")
def admin_headers(app_client):
    r = login(app_client, "admin", os.environ["ADMIN_PASSWORD"])
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def make_user(app_client, admin_headers):
    """Crea un usuario con un rol del sistema y devuelve headers (cambia la clave temporal)."""
    def _make(username, role_name, password="Passw0rd-Test!"):
        roles = {r["name"]: r["id"] for r in app_client.get(f"{API}/roles", headers=admin_headers).json()}
        r = app_client.post(f"{API}/users", headers=admin_headers, json={
            "username": username, "email": f"{username}@example.com", "full_name": username.title(),
            "password": "Temporal-1234", "role_id": roles[role_name], "is_active": True})
        assert r.status_code == 201, r.text
        tok = login(app_client, username, "Temporal-1234").json()["access_token"]
        h = {"Authorization": f"Bearer {tok}"}
        assert app_client.post(f"{API}/auth/me/password", headers=h,
                               json={"current_password": "Temporal-1234", "new_password": password}).status_code == 204
        tok = login(app_client, username, password).json()["access_token"]
        return {"Authorization": f"Bearer {tok}"}
    return _make
