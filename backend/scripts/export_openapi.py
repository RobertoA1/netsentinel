"""Exporta el esquema OpenAPI a docs/openapi.json (no requiere base de datos)."""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("JWT_SECRET", "export-only-secret")
os.environ.setdefault("ADMIN_PASSWORD", "export-only-password")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import app  # noqa: E402

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "docs" / "openapi.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2), encoding="utf-8")
print(f"OpenAPI escrito en {out}")
