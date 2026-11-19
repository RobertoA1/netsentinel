"""Ejecuta el trabajo ML «optimize»: `python -m app.ml.scripts.optimize --job-id N` (también lo invoca el ml-worker)."""
from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--job-id", type=int, required=True, help="id del trabajo en ml_jobs (créelo por la API o la BD)")
    a = ap.parse_args(argv)
    from app.ml.jobs import run_job
    from app.ml.optimizing import optimize_job

    return run_job(a.job_id, optimize_job)


if __name__ == "__main__":
    sys.exit(main())
