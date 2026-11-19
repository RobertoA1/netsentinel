"""Exportación de figuras del Laboratorio ML a PNG (600 DPI) o SVG, con la misma especificación que dibuja la pantalla."""
from __future__ import annotations

import re
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from app.core.deps import AuditCtx, Principal, audited, require
from app.ml import figures

router = APIRouter(prefix="/ml/figures", tags=["ml-figures"])
MODULES = ("ml_data", "ml_training", "ml_evaluation", "ml_explain", "ml_inference", "ml_optuna")
KINDS = {"bars", "lines", "dots", "heatmap", "swarm", "waterfall", "parcoords"}


class FigureIn(BaseModel):
    spec: dict[str, Any]
    format: Literal["png", "svg"] = "png"
    module: str = "ml_evaluation"


@router.post("/export")
def export(body: FigureIn, p: Principal = Depends(require("reports:view")),
           audit: AuditCtx = Depends(audited("export", "ml_evaluation", "figure"))):
    if body.module not in MODULES or f"{body.module}:view" not in p.permissions and not p.is_api_key:
        raise HTTPException(403, "No tiene permiso para exportar figuras de este módulo")
    kind = body.spec.get("kind")
    if kind not in KINDS or not isinstance(body.spec.get("data"), dict):
        raise HTTPException(422, "Especificación de figura no válida")
    try:
        content = figures.render(body.spec, body.format, 600)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(422, f"No se pudo dibujar la figura: {type(e).__name__}") from e
    mime = "image/png" if body.format == "png" else "image/svg+xml"
    slug = re.sub(r"[^a-z0-9]+", "_", str(body.spec.get("title", "figura")).lower())[:60].strip("_") or "figura"
    audit.set(None, f"Figura exportada: {body.spec.get('title', '')[:120]} ({body.format})", {"format": body.format, "kind": kind, "dpi": 600})
    return Response(content=content, media_type=mime,
                    headers={"Content-Disposition": f'attachment; filename="{slug}.{body.format}"',
                             "Access-Control-Expose-Headers": "Content-Disposition"})
