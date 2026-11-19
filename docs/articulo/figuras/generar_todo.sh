#!/bin/sh
# Regenera las 6 figuras (300 dpi). Requiere: uv. Uso: sh generar_todo.sh
cd "$(dirname "$0")"
for f in fig1_arquitectura fig2_flujo fig3_cv fig4_curvas fig5_umbral_llm fig6_latencia_usabilidad; do
  uv run --quiet --with matplotlib --with numpy --with scipy python $f.py || exit 1
done
