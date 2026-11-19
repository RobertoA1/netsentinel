#!/usr/bin/env bash
cd "$(dirname "$0")"
for U in 10 25 50 100 200 400 800; do ./ejecutar_db.sh db_$(printf %04d $U) $U 20 90 1000 80; done
# Repeticion tras reiniciar el backend (las anteriores quedaron invalidadas por el bloqueo del backend)
./ejecutar.sh login_0020 20 5 60 0 plan/netsentinel_login.jmx
./ejecutar.sh resistencia_0150_10min 150 30 600 1000
