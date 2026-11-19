#!/usr/bin/env bash
# Descarga el dataset de demostración CTU-13 (escenario 11) a data/dataset/.
#
# Origen : Stratosphere Laboratory, CTU University (Praga) - Malware Capture Facility Project.
#          CTU-13, escenario 11 = CTU-Malware-Capture-Botnet-52 (botnet Rbot, tráfico real con C&C por IRC).
# Archivo: detailed-bidirectional-flow-labels/capture20110818-2.binetflow  (flujos bidireccionales de Argus, etiquetados)
# Tamaño : 26 305 153 bytes (~25 MB), verificado con una petición HEAD el 2026-11-11.
# Licencia: uso libre citando el proyecto y sus autores (ver data/dataset/ATTRIBUTION.txt).
#
# Uso: scripts/fetch-dataset.sh [--yes] [--dir DIRECTORIO]
#   --yes   no pide confirmación (descarga directa)
#   --dir   directorio de destino (por defecto data/dataset)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST_DIR="$ROOT/data/dataset"
ASSUME_YES=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    -y|--yes) ASSUME_YES=1 ;;
    --dir)    DEST_DIR="${2:?--dir requiere un valor}"; shift ;;
    -h|--help) sed -n '2,13p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Opción desconocida: $1 (use --help)" >&2; exit 2 ;;
  esac
  shift
done

URL="https://mcfp.felk.cvut.cz/publicDatasets/CTU-Malware-Capture-Botnet-52/detailed-bidirectional-flow-labels/capture20110818-2.binetflow"
EXPECTED_BYTES=26305153
DEST_NAME="capture20110818-2.binetflow"
DEST="$DEST_DIR/$DEST_NAME"
EXPECTED_HEADER="StartTime,Dur,Proto,SrcAddr,Sport,Dir,DstAddr,Dport,State,sTos,dTos,TotPkts,TotBytes,SrcBytes,Label"

command -v curl >/dev/null || { echo "Se requiere curl." >&2; exit 1; }

# Tamaño real anunciado por el servidor (HEAD); si falla se usa el conocido.
SIZE="$(curl -fsSIL --max-time 30 "$URL" | tr -d '\r' | awk 'tolower($1)=="content-length:"{v=$2} END{print v}')" || SIZE=""
SIZE="${SIZE:-$EXPECTED_BYTES}"
human() { awk -v b="$1" 'BEGIN{printf "%.1f MB", b/1048576}'; }

cat <<EOF
Dataset de demostración: CTU-13, escenario 11 (CTU-Malware-Capture-Botnet-52)
  Origen   : $URL
  Proyecto : Stratosphere Laboratory, CTU University, Praga (botnet real Rbot, tráfico C&C)
  Tamaño   : $SIZE bytes (~$(human "$SIZE"))
  Destino  : $DEST
  Licencia : uso libre con atribución (Garcia, S. Malware Capture Facility Project, stratosphereips.org)
EOF

if [[ -s "$DEST" ]]; then
  echo "Ya existe $DEST; no se vuelve a descargar (bórrelo para forzarlo)."
  exit 0
fi

if [[ $ASSUME_YES -ne 1 ]]; then
  read -r -p "¿Descargar ahora? [s/N] " ans
  case "${ans,,}" in s|si|sí|y|yes) ;; *) echo "Cancelado."; exit 1 ;; esac
fi

mkdir -p "$DEST_DIR"
PART="$DEST.part"
echo "Descargando..."
curl -fL --retry 3 -C - -o "$PART" "$URL"

# Verifica la cabecera del archivo (formato binetflow etiquetado).
HEADER="$(head -n 1 "$PART" | tr -d '\r\357\273\277')"
if [[ "$HEADER" != "$EXPECTED_HEADER" ]]; then
  echo "ERROR: la cabecera del archivo no coincide con la esperada." >&2
  echo "  esperada: $EXPECTED_HEADER" >&2
  echo "  obtenida: $HEADER" >&2
  rm -f "$PART"
  exit 1
fi

mv "$PART" "$DEST"

cat > "$DEST_DIR/ATTRIBUTION.txt" <<EOF
CTU-13 dataset - Scenario 11 (CTU-Malware-Capture-Botnet-52)
Fuente: $URL
Los archivos fueron generados en el Stratosphere Laboratory como parte del Malware Capture Facility
Project en la CTU University (Praga, República Checa). Puede usarlos citando el proyecto y sus autores:
  Garcia, Sebastian. Malware Capture Facility Project. https://stratosphereips.org
  Garcia, S., Grill, M., Stiborek, J., Zunino, A. An empirical comparison of botnet detection methods.
  Computers & Security 45 (2014) 100-123.
EOF

echo "Listo: $DEST ($(wc -l < "$DEST") líneas)."
echo "Siguiente paso: make up && make load-dataset"
