#!/usr/bin/env bash
# Uso: ./ejecutar.sh <nombre> <usuarios> <rampup_s> <duracion_s> [think_ms] [plan.jmx]
# Credenciales: se leen de ../../.env (no se guardan en resultados).
set -euo pipefail
cd "$(dirname "$0")"
N=$1; U=$2; R=$3; D=$4; T=${5:-1000}; PLAN=${6:-plan/netsentinel.jmx}
set -a; . ../../.env; set +a
OUT=resultados/$N; rm -rf "$OUT"; mkdir -p "$OUT"
JVM_ARGS="-Xms512m -Xmx2g" jmeter -n -t "$PLAN" -l "$OUT/resultados.jtl" -e -o "$OUT/informe" \
  -Jusers=$U -Jrampup=$R -Jduration=$D -Jthink_ms=$T -Juser="${ADMIN_USERNAME:-admin}" -Jpassword="$ADMIN_PASSWORD" \
  -Jjmeter.save.saveservice.output_format=csv -Jjmeter.save.saveservice.timestamp_format=ms > "$OUT/consola.txt" 2>&1
python3 resumen.py "$OUT/resultados.jtl" "$N" "$U"
