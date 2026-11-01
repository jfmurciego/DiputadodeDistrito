#!/bin/zsh
# T-02 (01-11-2026): sube a la rama diagnostico/t02-20261101 el M01 y el grafo M03
# del último run de cada provincia PARADA, para el diagnóstico local en la sesión cloud.
# Uso: zsh subir_diagnostico_t02.sh   (idempotente: si el fichero ya está, no lo vuelve a subir)
set -u
export PATH="$HOME/.local/bin:$PATH"
R=jfmurciego/DiputadodeDistrito
RAMA=diagnostico/t02-20261101
BASE="$HOME/ddd-diag-t02"
REPO="$BASE/repo"
mkdir -p "$BASE"

if [ ! -d "$REPO/.git" ]; then
  git clone --quiet --depth 1 "https://github.com/$R.git" "$REPO" || { echo "ERROR: no se pudo clonar"; exit 1; }
fi
cd "$REPO" || exit 1
if git ls-remote --exit-code --heads origin "$RAMA" >/dev/null 2>&1; then
  git fetch --quiet --depth 1 origin "$RAMA:refs/remotes/origin/$RAMA" && git checkout --quiet -B "$RAMA" "origin/$RAMA"
else
  git fetch --quiet --depth 1 origin main && git checkout --quiet -B "$RAMA" origin/main
fi

# territorio|run
LISTA="congreso_alicante|41293667422
congreso_barcelona|41244711464
congreso_cadiz|41243953699
congreso_madrid|41244835816
congreso_malaga|41293427148
congreso_pontevedra|41293311168
congreso_baleares|41250230577
congreso_las_palmas|41250283081
congreso_alava|41240137880
congreso_murcia|41293548832"

echo "$LISTA" | while IFS='|' read -r T RUN; do
  DEST="diagnostico/t02-20261101/$T"
  if [ -f "$DEST/${T}_2025_m03_grafo.json.gz" ] && [ -f "$DEST/${T}_2025_m01_secciones_poblacion.geojson.zip" ]; then
    echo "OK (ya subido) $T"; continue
  fi
  AID=$(gh api "repos/$R/actions/runs/$RUN/artifacts?per_page=100" \
    --jq "[.artifacts[]|select(.name==\"ddd-state-$RUN-M03\" and (.expired|not))]|sort_by(.created_at)|last|.id // empty" 2>/dev/null)
  if [ -z "$AID" ]; then echo "AVISO: $T (run $RUN) sin artefacto M03 vigente; se salta"; continue; fi
  TMP="$BASE/tmp/$T"; rm -rf "$TMP"; mkdir -p "$TMP"
  if ! gh api "repos/$R/actions/artifacts/$AID/zip" > "$TMP/a.zip" 2>/dev/null; then
    echo "AVISO: $T no se pudo descargar el artefacto $AID; se salta"; continue
  fi
  unzip -q -o "$TMP/a.zip" -d "$TMP/x" || { echo "AVISO: $T zip ilegible; se salta"; continue; }
  mkdir -p "$DEST"
  for NOMBRE in m01_secciones_poblacion.geojson.zip m01_informe.json m03_grafo.json m03_informe.json; do
    F=$(find "$TMP/x" -type f -name "${T}_2025_$NOMBRE" | head -1)
    if [ -z "$F" ]; then echo "AVISO: $T sin $NOMBRE en el artefacto"; continue; fi
    if [ "$NOMBRE" = "m03_grafo.json" ]; then gzip -c "$F" > "$DEST/${T}_2025_m03_grafo.json.gz"
    else cp "$F" "$DEST/"; fi
  done
  echo "run=$RUN artifact=$AID" > "$DEST/ORIGEN.txt"
  rm -rf "$TMP"
  git add "$DEST" && git commit --quiet -m "diagnóstico T-02: M01 y M03 de $T (run $RUN)" && echo "SUBIDO $T"
  git push --quiet origin "$RAMA" || echo "AVISO: push de $T falló; vuelve a ejecutar el script"
done
echo "FIN: rama $RAMA"
