#!/usr/bin/env bash
# Barrido fino de hilos + repeticiones. Tras cada escalon verifica que el backend responde; si quedo bloqueado lo registra y lo reinicia.
cd "$(dirname "$0")"
chequeo() {
  sleep 5
  if ! curl -s -m 10 -o /dev/null -f localhost:8000/api/v1/health; then
    echo "BLOQUEO tras $1" | tee -a resultados/bloqueos.log
    newgrp docker <<< "docker compose -f ../../docker-compose.yml restart backend" >/dev/null 2>&1; sleep 15
  fi
}
for U in 500 600 700 900 1000 1100; do ./ejecutar.sh carga_$(printf %04d $U) $U 20 90 1000; chequeo carga_$U; done
for U in 150 300; do ./ejecutar_db.sh db_$(printf %04d $U) $U 20 90 1000 80; done
for R in r2 r3; do for U in 175 190 200 250; do ./ejecutar.sh carga_$(printf %04d $U)_$R $U 20 90 1000; chequeo carga_${U}_$R; done; done
