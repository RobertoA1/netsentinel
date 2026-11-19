from __future__ import annotations

import time

import httpx

from app.schemas.settings import LLMSettings

_cache: dict[str, tuple[float, bool]] = {}


def ollama_reachable(s: LLMSettings, ttl: float = 15.0) -> bool:
    if not s.enabled:
        return False
    hit = _cache.get(s.base_url + '|' + s.model)
    if hit and time.monotonic() - hit[0] < ttl:
        return hit[1]
    try:
        r = httpx.get(s.base_url.rstrip("/") + "/api/tags", timeout=2.0)
        names = [m.get("name", "") for m in r.json().get("models", [])] if r.status_code == 200 else []
        # Disponible solo si el modelo configurado ya está descargado, no basta con que Ollama responda.
        ok = any(n == s.model or (":" not in s.model and n.split(":")[0] == s.model) for n in names)
    except Exception:
        ok = False
    _cache[s.base_url + '|' + s.model] = (time.monotonic(), ok)
    return ok


def test_llm(s: LLMSettings) -> dict:
    from app.services.llm.chain import build_chat_model

    t0 = time.monotonic()
    try:
        tags = httpx.get(s.base_url.rstrip("/") + "/api/tags", timeout=min(s.timeout_seconds, 5)).json()
        names = [m.get("name", "") for m in tags.get("models", [])]
        if not any(n == s.model or n.split(":")[0] == s.model.split(":")[0] and ":" not in s.model for n in names):
            lat = int((time.monotonic() - t0) * 1000)
            return {"ok": False, "model": s.model, "latency_ms": lat,
                    "message": f"Ollama responde, pero el modelo '{s.model}' no está descargado "
                               f"(disponibles: {', '.join(names) or 'ninguno'})."}
        m = build_chat_model(s)
        m.invoke("Responde solo con la palabra OK en formato JSON: {\"respuesta\": \"OK\"}")
        lat = int((time.monotonic() - t0) * 1000)
        return {"ok": True, "model": s.model, "latency_ms": lat, "message": "Conexión correcta con el modelo."}
    except Exception as e:
        lat = int((time.monotonic() - t0) * 1000)
        return {"ok": False, "model": s.model, "latency_ms": lat,
                "message": f"No se pudo contactar con Ollama en {s.base_url}: {type(e).__name__}"}
