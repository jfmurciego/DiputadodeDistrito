#!/usr/bin/env bash
# T-519 · ¿Se repite el exacto de Deslinde cuando cambia la velocidad de la máquina?
# USO (un comando, desde la raíz del repositorio):  bash docs/ESTUDIOS/T519_REPETICION_EXACTO/repetir.sh [territorios…]
#   Sin argumentos: nac20 nac12 nac15 nac43 nac41. Carpeta de trabajo: $T519_DIR (por defecto /tmp/t519).
# Por territorio, siempre en procesos nuevos y con PYTHONHASHSEED=0:
#   a1 y a2  dos ejecuciones normales a la vez (cada una en su copia del repositorio: la caché de M03 vive en el árbol);
#   c        una con carga: tres copias de carga.py a la vez;
#   b        una con un solo núcleo (taskset -c 0).
# No lanza nada en GitHub ni cambia el motor. Al acabar cada territorio rehace RESULTADOS.json y TABLA.md (tabla.py).
set -uo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"
RAIZ="$(cd "$AQUI/../../.." && pwd)"
W="${T519_DIR:-/tmp/t519}"
PY="$W/venv/bin/python"
TS=("$@"); [ ${#TS[@]} -gt 0 ] || TS=(nac20 nac12 nac15 nac43 nac41)
mkdir -p "$W/espejo" "$W/logs" "$W/runs"
cd "$RAIZ"

# 1) Entorno: lock base + cadenas sin dependencias + exacto con hashes (como la batería, motor2.md)
if [ ! -x "$PY" ]; then
  python3 -m venv "$W/venv"
  "$PY" -m pip install -q --requirement requirements.lock
  grep -iE '^(gerrychain|networkx|rustworkx|scipy|tqdm|six)==' requirements-ensemble.lock > "$W/cadenas.txt"
  "$PY" -m pip install -q --no-deps --requirement "$W/cadenas.txt"
  "$PY" -m pip install -q --no-deps --require-hashes --requirement requirements-exacto.lock
fi
# 2) Fuentes: seccionado del INE (bateria_motor comprueba el sha256 contra orchestracion/fuentes_r2.json)
for y in 2023 2024; do
  [ -s "$W/espejo/seccionado_$y.zip" ] || curl -sS -L --fail -o "$W/espejo/seccionado_$y.zip" \
    "https://www.ine.es/prodyser/cartografia/seccionado_$y.zip"
done
# 3) Entradas de la batería
for t in "${TS[@]}"; do
  ls "$W/bateria/entradas/$t/"*_m03_grafo.json >/dev/null 2>&1 || DDD_ESPEJO_DIR="$W/espejo" PYTHONHASHSEED=0 \
    "$PY" herramientas/bateria_motor.py entradas "$t" --desde-fuente --seccionado shapefile --out "$W/bateria" \
    > "$W/logs/entradas_$t.log" 2>&1 || echo "entradas $t: rc=$?"
done
# 4) Segunda copia del repositorio para la ejecución paralela
[ -d "$W/wt2" ] || git worktree add --detach "$W/wt2" HEAD >/dev/null 2>&1

una() {  # una <árbol> <territorio> <condición> [prefijo de orden…]
  local arbol="$1" t="$2" cond="$3"; shift 3
  local d="$W/runs/${t}_$cond" ini fin rc
  rm -rf "$d"; mkdir -p "$d"; ln -s "$W/bateria/entradas" "$d/entradas"
  ini=$(date +%s)
  (cd "$arbol" && env PYTHONHASHSEED=0 "$@" "$PY" -m ddd_motor2.competir --out "$d" "$t") > "$W/logs/${t}_$cond.log" 2>&1
  rc=$?; fin=$(date +%s)
  echo "{\"reloj_s\": $((fin - ini)), \"rc\": $rc, \"nucleos\": \"$(nproc)\"}" > "$d/reloj.json"
  echo "$(date +%H:%M:%S) $t $cond rc=$rc $((fin - ini)) s"
}

for t in "${TS[@]}"; do
  una "$RAIZ" "$t" a1 & una "$W/wt2" "$t" a2 & wait
  cargas=(); for i in 1 2 3; do "$PY" "$AQUI/carga.py" & cargas+=($!); done
  una "$RAIZ" "$t" c
  kill "${cargas[@]}" 2>/dev/null; wait 2>/dev/null
  una "$RAIZ" "$t" b taskset -c 0
  "$PY" "$AQUI/tabla.py" "$W/runs" "$AQUI"
  touch "$W/runs/$t.hecho"
done
