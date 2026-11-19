#!/usr/bin/env bash
# Uso: ./ejecutar_db.sh <nombre> <usuarios> <rampup_s> <duracion_s> [think_ms] [pool]
# Credenciales de BD: se leen de ../../.env (DATABASE_URL) y no se guardan. Driver JDBC: jar local de ~/.m2.
set -euo pipefail
cd "$(dirname "$0")"
N=$1; U=$2; R=$3; D=$4; T=${5:-1000}; POOL=${6:-80}
set -a; . ../../.env; set +a
read -r DBU DBP DBN < <(python3 -I -c "
import os,urllib.parse as p
u=p.urlparse(os.environ['DATABASE_URL']); print(u.username, p.unquote(u.password), u.path.lstrip('/'))")
JAR=$(ls ~/.m2/repository/org/postgresql/postgresql/*/postgresql-*.jar | tail -1)
OUT=resultados/$N; rm -rf "$OUT"; mkdir -p "$OUT"
JVM_ARGS="-Xms512m -Xmx2g" jmeter -n -t plan/netsentinel_db.jmx -l "$OUT/resultados.jtl" -e -o "$OUT/informe" \
  -Jsearch_paths="$JAR" -Jusers=$U -Jrampup=$R -Jduration=$D -Jthink_ms=$T -Jpool=$POOL -Jdbuser="$DBU" -Jdbpassword="$DBP" -Jdbname="$DBN" \
  -Jjmeter.save.saveservice.output_format=csv -Jjmeter.save.saveservice.timestamp_format=ms > "$OUT/consola.txt" 2>&1
python3 resumen.py "$OUT/resultados.jtl" "$N" "$U"
