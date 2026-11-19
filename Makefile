.DEFAULT_GOAL := help
SHELL := /bin/bash
API_URL ?= http://localhost:8000/api/v1

.PHONY: help init up down logs dataset load-dataset test check n8n-reimport clean

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-16s %s\n", $$1, $$2}'

init: ## Genera .env con secretos aleatorios (si no existe)
	@./scripts/init-env.sh

up: init ## Construye y levanta todos los servicios en segundo plano
	docker compose up -d --build

down: ## Detiene los servicios (conserva los volúmenes)
	docker compose down

logs: ## Sigue los logs de todos los servicios
	docker compose logs -f --tail=100

dataset: ## Descarga el dataset CTU-13 (pide confirmación; use ARGS=--yes para omitirla)
	@./scripts/fetch-dataset.sh $(ARGS)

load-dataset: ## Importa el dataset en el backend (POST /ingest/dataset con X-API-Key de .env)
	@test -f .env || { echo "Falta .env: ejecute make init"; exit 1; }
	@KEY="$$(grep -E '^N8N_API_KEY=' .env | head -n1 | cut -d= -f2-)"; \
	test -n "$$KEY" || { echo "N8N_API_KEY vacío en .env"; exit 1; }; \
	printf 'header = "X-API-Key: %s"\n' "$$KEY" | \
	curl -fsS -K - -X POST "$(API_URL)/ingest/dataset" \
	  -H 'Content-Type: application/json' -d '{"rebase_time": true}'; echo

check: ## Valida JSON de workflows/LangFlow, sintaxis de scripts y docker compose
	@for f in n8n/workflows/*.json langflow/*.json; do python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$$f" && echo "JSON ok: $$f"; done
	@for f in scripts/*.sh n8n/import-workflows.sh; do bash -n "$$f" && echo "sh ok: $$f"; done
	@./scripts/init-env.sh >/dev/null && docker compose config -q && echo "docker compose config ok"

test: check ## Validaciones locales y, si existen, las pruebas del backend
	@if [ -d backend/tests ]; then docker compose run --rm --no-deps backend pytest -q; else echo "(sin backend/tests)"; fi

n8n-reimport: ## Vuelve a importar/activar los workflows (sobrescribe cambios hechos en n8n)
	docker compose run --rm --no-deps --entrypoint /bin/sh n8n-import -c 'rm -f /home/node/.n8n/.netsentinel-workflows-imported'
	docker compose up --force-recreate n8n-import
	docker compose restart n8n

clean: ## Elimina contenedores Y volúmenes (BD, n8n, modelos de Ollama). Pide confirmación
	@read -r -p "Esto borra la base de datos, n8n y los modelos descargados. ¿Continuar? [s/N] " a; \
	case "$$a" in s|S|si|SI) docker compose down -v --remove-orphans ;; *) echo "Cancelado." ;; esac
