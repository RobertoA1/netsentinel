#!/usr/bin/env bash
cd "$(dirname "$0")"
./ejecutar.sh pico_0600 600 10 90 1000
./ejecutar.sh recuperacion_0050 50 5 60 1000
./ejecutar.sh login_0020 20 5 60 0 plan/netsentinel_login.jmx
./ejecutar.sh resistencia_0150_10min 150 30 600 1000
