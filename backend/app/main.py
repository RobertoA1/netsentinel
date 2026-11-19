"""NetSentinel API."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.api.routers import (alerts, audit, auth, catalog, dashboard, findings, ingest, logs, reports, settings,
                             ml_data, ml_evaluation, ml_explain, ml_figures, ml_inference, ml_optuna, ml_training,
                             system, users)
from app.core.config import get_strict_settings

API_PREFIX = "/api/v1"
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app() -> FastAPI:
    cfg = get_strict_settings()  # falla con mensaje claro si faltan JWT_SECRET / ADMIN_PASSWORD
    app = FastAPI(title="NetSentinel API", version=__version__,
                  description="Analista de logs de firewall/IDS para PYMEs (detección de exfiltración y beaconing).",
                  openapi_url=f"{API_PREFIX}/openapi.json", docs_url=f"{API_PREFIX}/docs", redoc_url=None)
    app.add_middleware(CORSMiddleware, allow_origins=cfg.cors_origin_list, allow_credentials=True,
                       allow_methods=["*"], allow_headers=["*"], expose_headers=["Content-Disposition"])

    @app.exception_handler(StarletteHTTPException)
    async def http_exc(_: Request, exc: StarletteHTTPException):
        return JSONResponse({"detail": exc.detail if isinstance(exc.detail, str) else str(exc.detail)},
                            status_code=exc.status_code, headers=getattr(exc, "headers", None))

    @app.exception_handler(RequestValidationError)
    async def validation_exc(_: Request, exc: RequestValidationError):
        msgs = []
        for e in exc.errors():
            loc = ".".join(str(x) for x in e["loc"] if x not in ("body", "query", "path"))
            msgs.append(f"{loc}: {e['msg']}" if loc else e["msg"])
        return JSONResponse({"detail": "Datos inválidos: " + "; ".join(msgs)}, status_code=422)

    for r in (system.router, auth.router, users.router, audit.router, dashboard.router, logs.router,
              findings.router, alerts.router, ingest.router, catalog.router, settings.router, reports.router,
              ml_data.router, ml_training.router, ml_evaluation.router, ml_explain.router, ml_inference.router,
              ml_optuna.router, ml_figures.router):
        app.include_router(r, prefix=API_PREFIX)
    return app


app = create_app()
