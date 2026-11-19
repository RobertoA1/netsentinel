#!/bin/sh
# Importa y publica (activa) los workflows de NetSentinel en n8n al primer arranque.
# Se ejecuta en el servicio de un solo uso `n8n-import` con el MISMO volumen y la MISMA
# N8N_ENCRYPTION_KEY que `n8n`. Es idempotente: si ya se importó, no pisa los cambios hechos
# desde la interfaz (p. ej. habilitar el nodo de correo). Para reimportar: `make n8n-reimport`.
set -eu

DATA_DIR="${N8N_USER_FOLDER:-/home/node}/.n8n"
MARKER="$DATA_DIR/.netsentinel-workflows-imported"
WORKFLOWS_DIR="/workflows"
# IDs fijos definidos dentro de cada JSON. El 02 va primero: el 01 lo invoca y n8n exige que el subflujo ya esté publicado.
IDS="ns-despacho-02 ns-ingesta-01 ns-mantenimiento-03"

if [ -f "$MARKER" ]; then
  echo "[n8n-import] Workflows ya importados (marca $MARKER). Nada que hacer."
  exit 0
fi

echo "[n8n-import] Importando workflows desde $WORKFLOWS_DIR ..."
n8n import:workflow --separate --input="$WORKFLOWS_DIR"

for id in $IDS; do
  echo "[n8n-import] Publicando (activando) $id ..."
  n8n publish:workflow --id="$id"
done

mkdir -p "$DATA_DIR"
date -u +"%Y-%m-%dT%H:%M:%SZ" > "$MARKER"
echo "[n8n-import] Listo. Los workflows quedan activos cuando arranca n8n."
