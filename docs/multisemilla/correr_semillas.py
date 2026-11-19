"""Repite la CV anidada 5x3 con varias semillas (misma configuración que el trabajo #1) vía la API del Laboratorio ML.
Uso: python correr_semillas.py 7 123 2024 31337. Guarda semillas.json con job_id/run_id por semilla."""
import json, os, sys, time, urllib.request

BASE = "http://localhost:8000/api/v1"
env = {}
for line in open(os.path.join(os.path.dirname(__file__), "../../.env")):
    if "=" in line and not line.startswith("#"):
        k, v = line.rstrip("\n").split("=", 1); env[k] = v

def call(path, body=None, token=None):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json", **({"Authorization": f"Bearer {token}"} if token else {})})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

tok = call("/auth/login", {"username": env["ADMIN_USERNAME"], "password": env["ADMIN_PASSWORD"]})["access_token"]
out = {}
for seed in map(int, sys.argv[1:]):
    job = call("/ml/training/jobs", {"dataset_version_id": 3, "seed": seed, "n_trials": 20, "metric": "pr_auc",
              "models": [{"type": t} for t in ("dummy", "logreg", "random_forest", "hist_gb", "xgboost")]}, tok)
    jid = job["id"]; print("semilla", seed, "job", jid, flush=True)
    while True:
        j = call(f"/ml/training/jobs/{jid}", token=tok)
        if j["status"] in ("succeeded", "failed", "cancelled"):
            break
        time.sleep(10)
    print("  ->", j["status"], flush=True)
    out[seed] = {"job_id": jid, "status": j["status"]}
    json.dump(out, open("semillas.json", "w"), indent=1)
