#!/usr/bin/env bash
# T-509 · L1 — reproduce el laboratorio de mejora local exacta con una orden, desde la raíz del repositorio:
#   bash docs/ESTUDIOS/T509_LAB_MEJORA_LOCAL/reproducir.sh [carpeta de trabajo] [territorios…]
# VERSIÓN: 1.0.0 · FECHA: 2026-11-28 · ANTERIOR: ninguna (fichero nuevo)
# Necesita red a www.ine.es y pypi. No lanza workflows ni toca el motor. Unos 4 núcleos y 8 GB.
set -uo pipefail
W="${1:-/tmp/lab}"
shift || true
T=("$@")
[[ ${#T[@]} -gt 0 ]] || T=(nac50 nac03 nac46 aut17 aut06 aut03)

python -m pip install -q --requirement requirements.lock
grep -iE '^(gerrychain|networkx|rustworkx|scipy|tqdm|six)==' requirements-ensemble.lock > "$W.cadenas.txt"
python -m pip install -q --no-deps --requirement "$W.cadenas.txt"
python -m pip install -q --no-deps --require-hashes --requirement requirements-exacto.lock

mkdir -p "$W/espejo"
for a in 2023 2024; do
  [[ -f "$W/espejo/seccionado_$a.zip" ]] || curl -sS -L --retry 4 -o "$W/espejo/seccionado_$a.zip" \
    "https://www.ine.es/prodyser/cartografia/seccionado_$a.zip"
done
grep -q "inputs/_nacional/" .git/info/exclude 2>/dev/null || echo "inputs/_nacional/" >> .git/info/exclude

export PYTHONHASHSEED=0 DDD_ESPEJO_DIR="$W/espejo"
# sin «&&»: entradas devuelve ≠0 si falla un territorio y los demás siguen valiendo
python herramientas/bateria_motor.py entradas --desde-fuente --seccionado shapefile --out "$W/B" "${T[@]}"
python docs/ESTUDIOS/T509_LAB_MEJORA_LOCAL/mejora_local.py --out "$W/B" "${T[@]}"
