#!/usr/bin/env bash
# Captura (Chromium headless) del tablero y de los graficos "Over Time" de los informes HTML de JMeter.
cd "$(dirname "$0")"
for r in "$@"; do
  for p in index:1500 content/pages/OverTime:2300; do
    f=${p%%:*}; h=${p##*:}; n=$(basename $f)
    chromium --headless --no-sandbox --disable-gpu --allow-file-access-from-files --window-size=1400,$h --virtual-time-budget=10000 \
      --screenshot=evidencias/capturas/${r}_${n}.png "file://$PWD/resultados/$r/informe/$f.html" >/dev/null 2>&1
  done
done
