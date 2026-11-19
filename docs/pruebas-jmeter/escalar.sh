#!/usr/bin/env bash
# Prueba de carga escalonada: cada escalon dura 90 s (rampa 20 s). Muestrea CPU/RAM de contenedores.
cd "$(dirname "$0")"
for U in "$@"; do
  N=carga_$(printf %04d $U)
  ( while true; do echo "$(date +%s),$(newgrp docker <<< "docker stats --no-stream --format '{{.Name}},{{.CPUPerc}},{{.MemUsage}}'" 2>/dev/null | tr '\n' ';')"; sleep 5; done ) > /tmp/stats_$N.csv &
  SP=$!
  ./ejecutar.sh $N $U 20 90 1000
  kill $SP 2>/dev/null; mkdir -p resultados/$N; mv /tmp/stats_$N.csv resultados/$N/recursos.csv
done
