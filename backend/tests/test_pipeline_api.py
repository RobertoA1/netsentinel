"""Flujo completo (sobre SQLite de pruebas): subir fixture, detectar, dashboard, reportes, ruido, alertas."""
import io

import pytest

from helpers import API, FIXTURES

R = {"date_from": "2011-08-10T00:00:00Z", "date_to": "2011-08-11T00:00:00Z"}


@pytest.fixture(scope="module")
def ingested(app_client, admin_headers):
    sources = app_client.get(f"{API}/sources", headers=admin_headers).json()
    src = next(s for s in sources if s["format"] == "ctu13_binetflow")
    with open(FIXTURES / "ctu13_sample.binetflow", "rb") as f:
        r = app_client.post(f"{API}/ingest/upload", headers=admin_headers, data={"source_id": src["id"], "run_detection": "true"},
                            files={"file": ("ctu13_sample.binetflow", f, "text/csv")})
    assert r.status_code == 200, r.text
    return r.json()


def test_upload_and_detection_degraded_without_llm(app_client, admin_headers, ingested):
    run = ingested
    assert run["status"] == "success", run
    assert run["logs_inserted"] == 228 and run["parse_errors"] == 2 and run["trigger"] == "upload"
    assert run["findings_created"] >= 3
    fs = app_client.get(f"{API}/findings?page_size=100", headers=admin_headers).json()
    assert fs["total"] == run["findings_created"]
    types = {f["finding_type"] for f in fs["items"]}
    assert {"beaconing", "exfiltration", "unusual_port"} <= types
    for f in fs["items"]:   # Ollama caído: se guarda igual, sin veredicto y con plantilla en español
        assert f["llm_verdict"] is None and f["is_noise"] is False and f["llm_model"] is None
        assert len(f["llm_explanation"]) > 30 and len(f["llm_recommendation"]) > 20
    b = next(f for f in fs["items"] if f["finding_type"] == "beaconing" and f["dst_ip"] == "185.44.12.9")
    assert b["src_ip"] == "147.32.84.165" and b["dst_ip"] == "185.44.12.9" and b["dst_port"] == 443
    assert b["evidence"]["connections"] == 48 and b["evidence"]["cv"] < 0.05 and len(b["evidence"]["intervals_sample"]) > 5
    x = next(f for f in fs["items"] if f["finding_type"] == "exfiltration")
    assert x["src_ip"] == "147.32.84.77" and x["evidence"]["bytes_out"] > 100_000_000
    p = next(f for f in fs["items"] if f["finding_type"] == "unusual_port")
    assert p["dst_port"] == 4444


def test_detection_is_idempotent_dedup(app_client, admin_headers, ingested):
    before = app_client.get(f"{API}/findings?page_size=100", headers=admin_headers).json()
    r = app_client.post(f"{API}/detect/run", headers=admin_headers, json={"window_hours": 24})
    assert r.status_code == 200
    d = r.json()
    assert d["findings_created"] == 0 and d["findings_updated"] >= 3
    after = app_client.get(f"{API}/findings?page_size=100", headers=admin_headers).json()
    assert after["total"] == before["total"]
    by_id = {f["id"]: f for f in before["items"]}
    assert all(f["occurrences"] == by_id[f["id"]]["occurrences"] for f in after["items"])  # sin datos nuevos


def test_alerts_created_for_non_noise(app_client, admin_headers, ingested):
    al = app_client.get(f"{API}/alerts?page_size=100", headers=admin_headers).json()
    assert al["total"] >= 3 and all(a["channel"] == "in_app" and a["delivered"] for a in al["items"])
    n = app_client.get(f"{API}/alerts/unread-count", headers=admin_headers).json()["count"]
    assert n == al["total"]
    pend = app_client.get(f"{API}/alerts/pending-dispatch", headers={"X-API-Key": "test-n8n-key"}).json()
    assert pend and all(a["channel"] == "webhook" and a["delivered"] is False for a in pend)
    r = app_client.post(f"{API}/alerts/{pend[0]['id']}/delivered", headers={"X-API-Key": "test-n8n-key"})
    assert r.status_code == 204
    assert app_client.get(f"{API}/alerts/pending-dispatch", headers={"X-API-Key": "bad"}).status_code == 401
    one = al["items"][0]
    ack = app_client.post(f"{API}/alerts/{one['id']}/ack", headers=admin_headers).json()
    assert ack["acknowledged_at"] and ack["acknowledged_by"]
    assert app_client.post(f"{API}/alerts/ack-all", headers=admin_headers).json()["acknowledged"] == n - 1


def test_finding_workflow(app_client, admin_headers, ingested):
    fs = app_client.get(f"{API}/findings?finding_type=beaconing&dst_ip=185.44.12.9", headers=admin_headers).json()["items"]
    fid = fs[0]["id"]
    r = app_client.patch(f"{API}/findings/{fid}", headers=admin_headers, json={"status": "in_review"})
    assert r.status_code == 200 and r.json()["status"] == "in_review"
    r = app_client.post(f"{API}/findings/{fid}/comments", headers=admin_headers, json={"body": "Revisando el host"})
    assert r.status_code == 201 and r.json()["comments"][0]["body"] == "Revisando el host"
    assert app_client.get(f"{API}/findings/{fid}", headers=admin_headers).json()["comments"][0]["author"]
    rl = app_client.get(f"{API}/findings/{fid}/related-logs", headers=admin_headers).json()
    assert rl["total"] == 48
    r = app_client.post(f"{API}/findings/{fid}/reanalyze", headers=admin_headers)
    assert r.status_code == 200 and r.json()["llm_verdict"] is None and r.json()["llm_explanation"]
    r = app_client.patch(f"{API}/findings/{fid}", headers=admin_headers, json={"assigned_to_id": 1, "status": "closed"})
    assert r.json()["assigned_to"]["id"] == 1 and r.json()["status"] == "closed"
    assert app_client.patch(f"{API}/findings/999999", headers=admin_headers, json={"status": "closed"}).status_code == 404


def test_logs_endpoints(app_client, admin_headers, ingested):
    r = app_client.get(f"{API}/logs?dst_port=4444&page_size=5", headers=admin_headers).json()
    assert r["total"] == 12 and r["items"][0]["source_name"] == "CTU-13 Dataset" and r["items"][0]["direction"] == "outbound"
    one = app_client.get(f"{API}/logs/{r['items'][0]['id']}", headers=admin_headers)
    assert one.status_code == 200 and one.json()["bytes_out"] == 2500
    assert app_client.get(f"{API}/logs?q=Botnet&sort=-bytes_out&page_size=2", headers=admin_headers).json()["total"] > 0


def test_dashboard(app_client, admin_headers, ingested):
    q = "?" + "&".join(f"{k}={v}" for k, v in R.items())
    s = app_client.get(f"{API}/dashboard/summary{q}", headers=admin_headers).json()
    assert s["total_logs"] == 228 and s["total_bytes_out"] > 100_000_000 and s["open_findings"] >= 2
    assert set(s["deltas"]) >= {"total_logs", "open_findings"} and "noise_ratio" in s
    ts = app_client.get(f"{API}/dashboard/traffic-timeseries{q}&bucket=1h", headers=admin_headers).json()
    assert ts and set(ts[0]) == {"ts", "bytes_out", "bytes_in", "connections", "blocked"} and sum(t["connections"] for t in ts) == 228
    tt = app_client.get(f"{API}/dashboard/top-talkers{q}&metric=bytes&limit=3", headers=admin_headers).json()
    assert tt[0]["ip"] == "147.32.84.77" and set(tt[0]) == {"ip", "hostname", "bytes_out", "bytes_in", "connections",
                                                         "unique_destinations", "findings"}
    td = app_client.get(f"{API}/dashboard/top-destinations{q}", headers=admin_headers).json()
    assert td[0]["ip"] == "203.0.113.50" and "in_denylist" in td[0]
    tp = app_client.get(f"{API}/dashboard/top-ports{q}", headers=admin_headers).json()
    assert any(p["port"] == 4444 and p["unusual"] for p in tp) and all("service" in p for p in tp)
    sev = app_client.get(f"{API}/dashboard/findings-by-severity{q}", headers=admin_headers).json()
    assert [x["severity"] for x in sev] == ["critical", "high", "medium", "low", "info"] and sum(x["count"] for x in sev) >= 3
    typ = app_client.get(f"{API}/dashboard/findings-by-type{q}", headers=admin_headers).json()
    assert any(x["finding_type"] == "beaconing" and x["count"] >= 1 for x in typ)
    assert app_client.get(f"{API}/dashboard/findings-timeseries{q}", headers=admin_headers).status_code == 200
    fl = app_client.get(f"{API}/dashboard/flows{q}&limit=5", headers=admin_headers).json()
    assert len(fl) == 5 and set(fl[0]) == {"src_ip", "dst_ip", "dst_port", "bytes", "connections"}
    rf = app_client.get(f"{API}/dashboard/recent-findings{q}&limit=3", headers=admin_headers).json()
    assert 0 < len(rf) <= 3 and "comments" not in rf[0]
    # sin parámetros de fecha el rango por defecto (24h) no incluye datos de 2011
    assert app_client.get(f"{API}/dashboard/summary", headers=admin_headers).json()["total_logs"] == 0


@pytest.mark.parametrize("code", ["op_findings", "op_top_talkers", "op_beaconing", "op_unusual_ports", "op_ids_alerts",
                                  "op_ingestion", "op_audit_log", "mg_executive_summary", "mg_trends",
                                  "mg_response_metrics", "mg_user_activity", "mg_risk_by_asset"])
@pytest.mark.parametrize("fmt,magic", [("pdf", b"%PDF-"), ("docx", b"PK\x03\x04"), ("xlsx", b"PK\x03\x04")])
def test_reports_all_codes_and_formats(app_client, admin_headers, ingested, code, fmt, magic):
    r = app_client.post(f"{API}/reports/generate", headers=admin_headers,
                        json={"report_code": code, "format": fmt, "date_from": "2011-08-10T00:00:00Z",
                              "date_to": "2011-08-11T00:00:00Z"})
    assert r.status_code == 200, r.text
    assert len(r.content) > 1000 and r.content.startswith(magic)
    assert f".{fmt}" in r.headers["content-disposition"] and "attachment" in r.headers["content-disposition"]
    if fmt != "pdf":
        import zipfile
        names = zipfile.ZipFile(io.BytesIO(r.content)).namelist()
        assert ("word/document.xml" in names) if fmt == "docx" else ("xl/workbook.xml" in names)
        if fmt == "docx":
            assert any(n.startswith("word/media/") for n in names) or code in ("op_ids_alerts",)


def test_report_catalog_history_and_audit(app_client, admin_headers, ingested):
    cat = app_client.get(f"{API}/reports/catalog", headers=admin_headers).json()
    assert len(cat) == 18 and {c["category"] for c in cat} == {"operational", "management", "ml"}
    h = app_client.get(f"{API}/reports/history", headers=admin_headers).json()
    assert h["total"] >= 36 and h["items"][0]["size_bytes"] > 0 and h["items"][0]["generated_by"]
    ev = app_client.get(f"{API}/audit/events?event_type=export&page_size=100", headers=admin_headers).json()
    assert ev["total"] >= 36
    assert app_client.post(f"{API}/reports/generate", headers=admin_headers,
                           json={"report_code": "nope", "format": "pdf", "date_from": "2011-08-10", "date_to": "2011-08-11"}
                           ).status_code == 404


def test_xlsx_structure(app_client, admin_headers, ingested):
    from openpyxl import load_workbook
    r = app_client.post(f"{API}/reports/generate", headers=admin_headers,
                        json={"report_code": "op_findings", "format": "xlsx", **R})
    wb = load_workbook(io.BytesIO(r.content))
    assert wb.sheetnames[0] == "Resumen" and len(wb.sheetnames) >= 2
    ws = wb[wb.sheetnames[-1]]
    assert ws.auto_filter.ref and ws["A1"].font.bold and ws.freeze_panes == "A2"


def test_noise_findings_do_not_alert(app_client, admin_headers, ingested):
    """Un hallazgo reclasificado manualmente como ruido sale del dashboard (el ruido no genera alertas nuevas)."""
    fs = app_client.get(f"{API}/findings?finding_type=exfiltration", headers=admin_headers).json()["items"]
    r = app_client.patch(f"{API}/findings/{fs[0]['id']}", headers=admin_headers, json={"is_noise": True})
    assert r.json()["is_noise"] is True
    nf = app_client.get(f"{API}/findings?is_noise=false&finding_type=exfiltration", headers=admin_headers).json()
    assert nf["total"] == 0


def test_catalogs_lists_assets_settings(app_client, admin_headers):
    r = app_client.post(f"{API}/lists", headers=admin_headers, json={"list_type": "allow", "kind": "cidr", "value": "10.9.0.0/16"})
    assert r.status_code == 201
    assert app_client.post(f"{API}/lists", headers=admin_headers, json={"list_type": "allow", "kind": "cidr", "value": "10.9.0.0/16"}).status_code == 409
    assert app_client.post(f"{API}/lists", headers=admin_headers, json={"list_type": "deny", "kind": "ip", "value": "x"}).status_code == 422
    assert app_client.get(f"{API}/lists?list_type=allow", headers=admin_headers).json()["total"] == 1
    assert app_client.delete(f"{API}/lists/{r.json()['id']}", headers=admin_headers).status_code == 204
    a = app_client.post(f"{API}/assets", headers=admin_headers, json={"ip": "10.0.0.5", "hostname": "pc-contab", "expected_ports": [80, 443]})
    assert a.status_code == 201 and a.json()["criticality"] == "medium"
    assert app_client.put(f"{API}/assets/{a.json()['id']}", headers=admin_headers, json={"ip": "10.0.0.5", "hostname": "x", "criticality": "high"}).json()["hostname"] == "x"
    assert app_client.get(f"{API}/assets?q=10.0", headers=admin_headers).json()["total"] == 1
    d = app_client.get(f"{API}/settings/detection", headers=admin_headers).json()
    assert d["beacon_min_connections"] == 10 and 443 in d["common_ports"] and d["detection_window_hours"] == 24
    d["beacon_min_connections"] = 12
    assert app_client.put(f"{API}/settings/detection", headers=admin_headers, json=d).json()["beacon_min_connections"] == 12
    llm = app_client.get(f"{API}/settings/llm", headers=admin_headers).json()
    assert llm["model"] == "llama3.2:3b" and llm["noise_confidence_threshold"] == 0.7
    t = app_client.post(f"{API}/settings/llm/test", headers=admin_headers).json()
    assert t["ok"] is False and set(t) == {"ok", "model", "latency_ms", "message"}
    assert app_client.get(f"{API}/settings/retention", headers=admin_headers).json() == {"logs_days": 90, "findings_days": 365, "audit_days": 730}
    h = app_client.get(f"{API}/health").json()
    assert h["status"] == "ok" and h["db"] is True and h["llm"] is False and h["version"]


def test_ingest_directory_with_api_key_and_status(app_client, admin_headers, tmp_dirs):
    import shutil
    sources = {s["format"]: s["id"] for s in app_client.get(f"{API}/sources", headers=admin_headers).json()}
    d = tmp_dirs / "ingest" / str(sources["suricata_eve"])
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES / "suricata_eve.json", d / "eve.json")
    st = app_client.get(f"{API}/ingest/status", headers={"X-API-Key": "test-n8n-key"}).json()
    assert st["pending_files"] == 1 and st["dataset_available"] is False
    r = app_client.post(f"{API}/ingest/run", headers={"X-API-Key": "test-n8n-key"}, json={"source_id": sources["suricata_eve"]})
    assert r.status_code == 200, r.text
    run = r.json()
    assert run["trigger"] == "n8n" and run["logs_inserted"] == 2 and run["parse_errors"] == 2 and run["status"] == "success"
    # segunda llamada: archivo ya procesado, nada nuevo
    r2 = app_client.post(f"{API}/ingest/run", headers={"X-API-Key": "test-n8n-key"}, json={}).json()
    assert r2["logs_inserted"] == 0 and r2["status"] == "success"
    runs = app_client.get(f"{API}/ingest/runs", headers=admin_headers).json()
    assert runs["total"] >= 3
    assert app_client.post(f"{API}/ingest/dataset", headers=admin_headers, json={"rebase_time": True}).status_code == 404


def test_dataset_import_with_rebase(app_client, admin_headers, tmp_dirs):
    import shutil
    from datetime import datetime, timezone
    d = tmp_dirs / "dataset"
    d.mkdir(exist_ok=True)
    shutil.copy(FIXTURES / "ctu13_sample.binetflow", d / "scenario.binetflow")
    assert app_client.get(f"{API}/ingest/status", headers=admin_headers).json()["dataset_available"] is True
    r = app_client.post(f"{API}/ingest/dataset", headers=admin_headers, json={"rebase_time": True, "max_rows": 100})
    assert r.status_code == 200 and r.json()["trigger"] == "dataset" and r.json()["logs_inserted"] == 100, r.text
    lg = app_client.get(f"{API}/logs?sort=-ts&page_size=1&date_from=2026-01-01T00:00:00Z", headers=admin_headers).json()
    newest = datetime.fromisoformat(lg["items"][0]["ts"].replace("Z", "+00:00"))
    assert abs((datetime.now(timezone.utc) - newest).total_seconds()) < 120   # el último registro cae en "ahora"
    assert "147.32.0.0/16" in app_client.get(f"{API}/settings/detection", headers=admin_headers).json()["internal_cidrs"]
    assert app_client.get(f"{API}/ingest/status", headers=admin_headers).json()["dataset_loaded"] is True
    recent = app_client.get(f"{API}/dashboard/summary?range=24h", headers=admin_headers).json()
    # 100 del dataset (rebasados a "ahora"). Los 2 de Suricata ingeridos antes tienen fecha fija en el
    # fixture, así que solo entran en la ventana de 24 h si la prueba corre ese mismo día.
    assert recent["total_logs"] in (100, 102)


def test_purge(app_client, admin_headers):
    r = app_client.put(f"{API}/settings/retention", headers=admin_headers, json={"logs_days": 30, "findings_days": 30, "audit_days": 730})
    assert r.status_code == 200
    p = app_client.post(f"{API}/maintenance/purge", headers={"X-API-Key": "test-n8n-key"}).json()
    assert p["logs_deleted"] >= 228 and p["findings_deleted"] >= 3   # datos de 2011 fuera de retención
    assert app_client.get(f"{API}/logs?date_from=2011-01-01", headers=admin_headers).json()["total"] == 102  # los rebasados siguen
    app_client.put(f"{API}/settings/retention", headers=admin_headers, json={"logs_days": 90, "findings_days": 365, "audit_days": 730})
