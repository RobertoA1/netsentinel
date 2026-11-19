#!/usr/bin/env bash
# Genera .env con secretos aleatorios a partir de .env.example si .env no existe.
# No imprime ningún valor secreto. Uso: scripts/init-env.sh [--force]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXAMPLE="$ROOT/.env.example"
TARGET="$ROOT/.env"

if [[ -f "$TARGET" && "${1:-}" != "--force" ]]; then
  echo "[init-env] .env ya existe; no se modifica (use --force para regenerarlo)."
  exit 0
fi
[[ -f "$EXAMPLE" ]] || { echo "[init-env] ERROR: falta $EXAMPLE" >&2; exit 1; }

# Cadena aleatoria alfanumérica de longitud $1 (apta para URLs y shells).
rand() {
  local n="$1" out=""
  while [[ ${#out} -lt $n ]]; do
    out+="$(head -c 256 /dev/urandom | LC_ALL=C tr -dc 'A-Za-z0-9')"
  done
  printf '%s' "${out:0:$n}"
}

PG_PASS="$(rand 32)"
JWT="$(rand 64)"
N8N_KEY="$(rand 48)"
ADMIN_PASS="$(rand 20)"
ENC_KEY="$(rand 48)"

umask 077
TMP="$(mktemp "$ROOT/.env.XXXXXX")"
trap 'rm -f "$TMP"' EXIT

while IFS= read -r line || [[ -n "$line" ]]; do
  case "$line" in
    POSTGRES_PASSWORD=*)    line="POSTGRES_PASSWORD=$PG_PASS" ;;
    DATABASE_URL=*)         line="DATABASE_URL=postgresql://netsentinel:${PG_PASS}@db:5432/netsentinel" ;;
    JWT_SECRET=*)           line="JWT_SECRET=$JWT" ;;
    N8N_API_KEY=*)          line="N8N_API_KEY=$N8N_KEY" ;;
    ADMIN_PASSWORD=*)       line="ADMIN_PASSWORD=$ADMIN_PASS" ;;
    N8N_ENCRYPTION_KEY=*)   line="N8N_ENCRYPTION_KEY=$ENC_KEY" ;;
  esac
  printf '%s\n' "$line"
done < "$EXAMPLE" > "$TMP"

mv "$TMP" "$TARGET"
trap - EXIT
chmod 600 "$TARGET"
echo "[init-env] .env generado con secretos aleatorios (permisos 600)."
echo "[init-env] La contraseña del administrador está en .env (variable ADMIN_PASSWORD); no se muestra aquí."
