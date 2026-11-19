"""Carga de flujos etiquetados (desde una fuente ya ingerida o desde un archivo binetflow), instantánea
del dataset ML y mapeo de etiquetas crudas -> clase."""
from __future__ import annotations

import gzip
import hashlib
import io
import os
from datetime import timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.ml.features import RAW_COLUMNS
from app.models import FirewallLog as L
from app.services.parsers.base import DirectionClassifier, ParseError
from app.services.parsers.ctu13 import Ctu13Parser

CLASSES = ["Normal", "Botnet"]  # índice 1 = positiva (Botnet)
EXCLUDED = "excluded"
ALLOWED_UPLOAD_EXT = (".binetflow", ".csv", ".txt", ".gz")
DEDUP_COLS = ["src_ip", "src_port", "dst_ip", "dst_port", "proto", "state", "dir", "bytes_out", "bytes_in",
              "packets", "duration", "label_raw"]


def to_epoch(s: pd.Series) -> pd.Series:
    """Segundos desde 1970 (independiente de la resolución de datetime de pandas)."""
    t = pd.to_datetime(s, utc=True)
    return (t - pd.Timestamp("1970-01-01", tz="UTC")) / pd.Timedelta(seconds=1)


def ml_root() -> Path:
    p = Path(get_settings().ml_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def default_class(raw: str | None) -> str:
    r = (raw or "").lower()
    if "botnet" in r:
        return "Botnet"
    if "normal" in r:
        return "Normal"
    return EXCLUDED  # Background u otras: sin verdad conocida


def default_label_map(raw_labels) -> dict[str, str]:
    return {str(k): default_class(str(k)) for k in sorted({str(x) for x in raw_labels if x is not None})}


def apply_label_map(raw: pd.Series, label_map: dict[str, str]) -> pd.Series:
    """Serie y_flow: 1 = Botnet, 0 = Normal, NaN = excluida/sin etiqueta."""
    m = {k: (1.0 if v == "Botnet" else 0.0 if v == "Normal" else np.nan) for k, v in label_map.items()}
    return raw.map(lambda x: m.get(str(x), np.nan) if x is not None and x == x else np.nan).astype(float)


def _dedupe(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Detecta la CARGA DUPLICADA del mismo archivo (dos ingestas con distinto rebase de fechas): si la segunda mitad
    (por orden de inserción) repite exactamente el contenido de la primera, se conserva solo la primera mitad.
    No se eliminan flujos repetidos legítimos (mismo contenido en instantes distintos)."""
    n = len(df)
    if n >= 2 and n % 2 == 0:
        a = df.iloc[: n // 2][DEDUP_COLS].reset_index(drop=True)
        b = df.iloc[n // 2:][DEDUP_COLS].reset_index(drop=True)
        if a.equals(b):
            return df.iloc[: n // 2].reset_index(drop=True), n // 2
    return df, 0


def frame_from_source(db: Session, source_id: int) -> tuple[pd.DataFrame, int]:
    """Lee los flujos de una fuente. Quita duplicados exactos de contenido (p. ej. el mismo dataset cargado dos
    veces con distinto rebase de fechas) y devuelve (df, duplicados_eliminados)."""
    stmt = select(L.ts, L.src_ip, L.dst_ip, L.src_port, L.dst_port, L.proto, L.raw["state"].as_string(),
                  L.raw["dir"].as_string(), L.direction, L.bytes_out, L.bytes_in, L.packets, L.duration,
                  L.label).where(L.source_id == source_id, L.log_type == "flow").order_by(L.id)
    rows = db.execute(stmt).all()
    df = pd.DataFrame([tuple(r) for r in rows], columns=RAW_COLUMNS)
    if df.empty:
        return df, 0
    df["ts"] = to_epoch(df["ts"])
    return _dedupe(df)


def frame_from_file(content: bytes, filename: str, cidrs: list[str] | None = None) -> tuple[pd.DataFrame, dict]:
    """Parsea un archivo binetflow subido. Nunca deserializa objetos: solo texto CSV."""
    mb = get_settings().ml_max_upload_mb
    if len(content) > mb * 1024 * 1024:
        raise ValueError(f"El archivo supera el máximo de {mb} MB")
    name = filename.lower()
    if not name.endswith(ALLOWED_UPLOAD_EXT):
        raise ValueError("Extensión no permitida (use .binetflow, .csv, .txt o .gz de texto)")
    if content[:2] == b"\x1f\x8b":
        try:
            content = gzip.decompress(content)
        except OSError as e:
            raise ValueError("Archivo gzip inválido") from e
        if len(content) > 4 * mb * 1024 * 1024:
            raise ValueError("El archivo descomprimido es demasiado grande")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ValueError("El archivo no es texto UTF-8") from e
    first = text.split("\n", 1)[0]
    if not first.startswith("StartTime") or "Label" not in first:
        raise ValueError("Cabecera binetflow no reconocida: se espera StartTime,...,Label")
    parser = Ctu13Parser()
    clf = DirectionClassifier(cidrs or [])
    recs, errors, total = [], 0, 0
    for line in io.StringIO(text):
        line = line.strip()
        if not line:
            continue
        total += 1
        try:
            r = parser.parse_line(line)
        except ParseError:
            errors += 1
            continue
        if r is None:
            continue
        raw = r.get("raw") or {}
        recs.append((r["ts"].astimezone(timezone.utc).timestamp(), r["src_ip"], r["dst_ip"], r.get("src_port"),
                     r.get("dst_port"), r.get("proto"), raw.get("state"), raw.get("dir"),
                     clf.classify(r["src_ip"], r["dst_ip"]),
                     r.get("bytes_out", 0), r.get("bytes_in", 0), r.get("packets"), r.get("duration"),
                     r.get("label")))
    if total == 0 or errors / max(total, 1) > 0.1:
        raise ValueError(f"Demasiados errores de lectura ({errors} de {total} líneas)")
    df = pd.DataFrame(recs, columns=RAW_COLUMNS)
    df, dup = _dedupe(df)
    return df, {"lines": total, "parse_errors": errors, "duplicates_dropped": dup}


def save_snapshot(df: pd.DataFrame, dataset_id: int) -> tuple[str, str]:
    d = ml_root() / "datasets" / str(dataset_id)
    d.mkdir(parents=True, exist_ok=True)
    path = d / "flows.csv.gz"
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
        gz.write(df.to_csv(index=False).encode())
    data = buf.getvalue()
    path.write_bytes(data)
    return str(path), hashlib.sha256(data).hexdigest()


def load_snapshot(path: str, sha256: str | None = None) -> pd.DataFrame:
    p = Path(path).resolve()
    if ml_root().resolve() not in p.parents:
        raise ValueError("Ruta de dataset fuera del volumen ML")
    raw = p.read_bytes()
    if sha256 and hashlib.sha256(raw).hexdigest() != sha256:
        raise ValueError("La instantánea del dataset fue modificada (suma de verificación distinta)")
    df = pd.read_csv(io.BytesIO(raw), compression="gzip",
                     dtype={"src_ip": str, "dst_ip": str, "proto": str, "state": str, "dir": str,
                            "direction": str, "label_raw": str})
    return df


def labelled_frame(df: pd.DataFrame, label_map: dict[str, str]) -> pd.DataFrame:
    d = df.copy()
    d["y_flow"] = apply_label_map(d["label_raw"], label_map)
    return d
