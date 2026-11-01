#!/bin/zsh
# T-02 (01-11-2026): sube a la rama diagnostico/t02-20261101 el M01 y el grafo M03
# del último run de cada provincia PARADA, para el diagnóstico local en la sesión cloud.
# Uso: zsh subir_diagnostico_t02.sh 2>&1 | tee ~/subir_diagnostico_t02.log
# Idempotente: lo ya subido no se repite. Acepta el estado M03 o M03U del run.
set -u
export PATH="$HOME/.local/bin:$PATH"
R=jfmurciego/DiputadodeDistrito
RAMA=diagnostico/t02-20261101
BASE="$HOME/ddd-diag-t02"
REPO="$BASE/repo"
mkdir -p "$BASE"
echo "gh: $(command -v gh)"; gh auth status || { echo "ERROR: gh sin autenticar"; exit 1; }
SUBIDOS=0; YA=0

if [ ! -d "$REPO/.git" ]; then
  git clone --quiet --depth 1 "https://github.com/$R.git" "$REPO" || { echo "ERROR: no se pudo clonar"; exit 1; }
fi
cd "$REPO" || exit 1
if git ls-remote --exit-code --heads origin "$RAMA" >/dev/null 2>&1; then
  git fetch --quiet --depth 1 origin "$RAMA:refs/remotes/origin/$RAMA" && git checkout --quiet -B "$RAMA" "origin/$RAMA"
else
  git fetch --quiet --depth 1 origin main && git checkout --quiet -B "$RAMA" origin/main
fi

# Pushes grandes por HTTP: buffer amplio, HTTP/1.1 y sin límite de velocidad baja.
git config http.postBuffer 524288000
git config http.version HTTP/1.1
git config http.lowSpeedLimit 0
git config http.lowSpeedTime 999999

empujar() {
  local i
  for i in 1 2 3 4; do
    git push --quiet origin "HEAD:refs/heads/$RAMA" && return 0
    echo "AVISO: push falló (intento $i); reintento en $((i*15)) s"; sleep $((i*15))
  done
  return 1
}

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
congreso_murcia|41335095516"

for LINEA in ${(f)LISTA}; do
  T=${LINEA%%|*}; RUN=${LINEA##*|}
  DEST="diagnostico/t02-20261101/$T"
  if git ls-remote --exit-code --heads origin "$RAMA" >/dev/null 2>&1 \
     && git fetch --quiet --depth 1 origin "$RAMA" \
     && git cat-file -e "FETCH_HEAD:$DEST/${T}_2025_m03_grafo.json.gz" 2>/dev/null; then
    echo "OK (ya subido) $T"; YA=$((YA+1)); continue
  fi
  if [ -f "$DEST/${T}_2025_m03_grafo.json.gz" ]; then
    echo "$T: ya descargado en local, falta subirlo"
    if empujar; then echo "SUBIDO $T"; SUBIDOS=$((SUBIDOS+1)); else echo "AVISO: $T sigue sin subir"; fi
    continue
  fi
  AID=""
  for SUF in M03 M03U; do
    AID=$(gh api "repos/$R/actions/runs/$RUN/artifacts?per_page=100" \
      --jq "[.artifacts[]|select(.name==\"ddd-state-$RUN-$SUF\" and (.expired|not))]|sort_by(.created_at)|last|.id // empty")
    [ -n "$AID" ] && { echo "$T: artefacto ddd-state-$RUN-$SUF id=$AID"; break; }
  done
  if [ -z "$AID" ]; then echo "AVISO: $T (run $RUN) sin artefacto M03/M03U vigente; se salta"; continue; fi
  TMP="$BASE/tmp/$T"; rm -rf "$TMP"; mkdir -p "$TMP"
  if ! gh api "repos/$R/actions/artifacts/$AID/zip" > "$TMP/a.zip"; then
    echo "AVISO: $T no se pudo descargar el artefacto $AID; se salta"; continue
  fi
  unzip -q -o "$TMP/a.zip" -d "$TMP/x" || { echo "AVISO: $T zip ilegible; se salta"; continue; }
  mkdir -p "$DEST"
  for NOMBRE in m01_secciones_poblacion.geojson.zip m01_informe.json m03_grafo.json m03_informe.json; do
    F=$(find "$TMP/x" -type f -name "${T}_2025_$NOMBRE" | head -1)
    if [ -z "$F" ]; then echo "AVISO: $T sin $NOMBRE en el artefacto; contenido:"; find "$TMP/x" -type f | sed "s#$TMP/x/##" | head -20; continue; fi
    if [ "$NOMBRE" = "m03_grafo.json" ]; then gzip -c "$F" > "$DEST/${T}_2025_m03_grafo.json.gz"
    else cp "$F" "$DEST/"; fi
  done
  echo "run=$RUN artifact=$AID" > "$DEST/ORIGEN.txt"
  rm -rf "$TMP"
  if [ ! -f "$DEST/${T}_2025_m03_grafo.json.gz" ]; then echo "AVISO: $T sin grafo M03; no se sube"; continue; fi
  git add "$DEST" && git commit --quiet -m "diagnóstico T-02: M01 y M03 de $T (run $RUN)" || { echo "ERROR: commit de $T"; continue; }
  if empujar; then echo "SUBIDO $T"; SUBIDOS=$((SUBIDOS+1)); else echo "AVISO: push de $T falló; vuelve a ejecutar el script"; fi
done
echo "FIN: rama $RAMA · subidos=$SUBIDOS · ya estaban=$YA"
[ $((SUBIDOS+YA)) -gt 0 ] || { echo "ERROR: no se ha subido nada"; exit 1; }
