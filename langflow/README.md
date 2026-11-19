# Flujo LangFlow: interpretación de hallazgos

`netsentinel-interpretacion.json` es el equivalente visual de la cadena LangChain que usa el backend
para interpretar un hallazgo: **descarta ruido y explica**. Sirve para demostrar y ajustar el prompt
sin tocar código. LangFlow **no corre en contenedor** dentro de este proyecto; se usa aparte.

## Qué contiene

```
Hallazgo (TextInput) ─▶ Prompt Template (español) ─▶ Ollama (llama3.2:3b) ─▶ JSON Cleaner (parser) ─▶ Chat Output
```

| Nodo | Función |
|---|---|
| Hallazgo (entrada) | JSON del hallazgo con su evidencia (ejemplo de *beaconing* precargado). |
| Prompt NetSentinel | Prompt en español con la variable `{hallazgo}`; pide veredicto, confianza, explicación y recomendación en JSON. |
| Ollama | Modelo `llama3.2:3b`, temperatura 0,1, `base_url` `http://localhost:11434`. |
| Parser de salida | *JSON Cleaner*: quita texto sobrante y valida que la salida sea JSON. |
| Veredicto (salida) | Muestra `{"verdict": "real\|noise\|uncertain", "confidence": 0-1, "explanation": "...", "recommendation": "..."}`, los mismos campos que guarda NetSentinel en cada hallazgo (`llm_verdict`, `llm_confidence`, `llm_explanation`, `llm_recommendation`). |

## Cómo importarlo

1. Tenga Ollama accesible. Con el stack de NetSentinel levantado ya escucha en `http://localhost:11434`
   y el modelo se descarga con el servicio `ollama-init` (o `ollama pull llama3.2:3b`).
2. Instale y ejecute LangFlow fuera de Docker, por ejemplo: `uv pip install langflow` y `langflow run`
   (abre `http://localhost:7860`).
3. En LangFlow: **Flujos → Importar** (o arrastre el archivo) y elija `langflow/netsentinel-interpretacion.json`.
4. Abra el componente **Ollama** y confirme `Base URL` (`http://localhost:11434`) y el modelo; si LangFlow corre
   en otro equipo o contenedor, use la IP/host correspondiente.
5. Pegue en **Hallazgo (entrada)** el JSON de un hallazgo (puede copiarlo de la pestaña *Evidencia* de un
   hallazgo en la interfaz de NetSentinel) y pulse **Ejecutar** en *Veredicto (salida)*.

## Honestidad sobre la validación

- Se preparó con los componentes de **LangFlow 1.13.x** (última versión estable al momento de escribirlo,
  1.13.2): los nodos se generaron programáticamente con las clases oficiales de `lfx` 1.14.0.dev
  (`TextInput`, `Prompt Template`, `OllamaModel` de `lfx-ollama` 0.2.1, `JSONCleaner`, `ChatOutput`), de modo
  que la plantilla de cada nodo y su código coinciden con los de esas versiones.
- **No se pudo validar ejecutándolo**: no se importó en una instancia de LangFlow ni se corrió contra Ollama.
  Solo se comprobó que el archivo es JSON válido y que los componentes se instancian y producen sus plantillas.
- Si LangFlow le muestra un aviso de componentes desactualizados, use el botón **Actualizar** del nodo; si
  una conexión no se dibuja, vuelva a enlazar la salida con la entrada correspondiente (los nombres de campo
  están en la tabla de arriba).
- El flujo es una **referencia para experimentar el prompt**. La cadena que gobierna el sistema es la del backend
  (`backend/app/...`), configurable desde *Configuración → LLM* en NetSentinel.
