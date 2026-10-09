#!/usr/bin/env bash
# PROYECTO: Diputado de Distrito
# FICHERO: procedimiento.sh
# VERSIÓN: 2.0.0
# NOMBRE DE VERSIÓN: Procedimiento modular reproducible
# FECHA: 2026-09-11
# ESTADO: candidato
# QUÉ HACE: orquesta los ocho módulos en orden, soporta modo completo/iterativo y registra la ejecución.
# POR QUÉ CAMBIA: sustituye run_pipeline.sh y separa la base estable 01-03 del tramo experimental 04-08.
# ANTERIOR: legacy/2026-09-11_github_pre_modulos/run_pipeline.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$ROOT"
PARAMS="${DDD_PARAMS:-configuracion/aragon_2025.yaml}"
MODO="${DDD_MODO:-completo}"
RUN_ID="${GITHUB_RUN_ID:-local-$(date -u +%Y%m%dT%H%M%SZ)}"
LOG_DIR="output/logs"; CACHE_DIR=".cache/ddd/base"
mkdir -p output "$LOG_DIR" "$CACHE_DIR"
for f in modulos/{01_preparar_base_territorial,02_construir_adyacencias,03_construir_grafo,04_generar_semillas,05_optimizar_distritos,06_consolidar_distritos,07_agregar_resultados_electorales,08_integrar_resultados}.py; do
  test -f "$f" || { echo "[FATAL] Falta $f" >&2; exit 20; }
done
test -f "$PARAMS" || { echo "[FATAL] Falta $PARAMS" >&2; exit 20; }
python herramientas/registrar_ejecucion.py --params "$PARAMS" --phase start --run-id "$RUN_ID"
ejecutar(){ local n="$1" script="$2"; echo "===== MÓDULO $n: $script ====="; python "$script" --params "$PARAMS" 2>&1 | tee "$LOG_DIR/modulo_${n}.log"; }
CACHE_MARKER="$CACHE_DIR/base_preparada.ok"
if [[ "$MODO" == "iterativo" && -f "$CACHE_MARKER" ]]; then
  echo "[CACHE] Reutilizando base preparada de módulos 01-03."; cp -f "$CACHE_DIR"/* output/ 2>/dev/null || true
else
  ejecutar 01 modulos/01_preparar_base_territorial.py
  ejecutar 02 modulos/02_construir_adyacencias.py
  ejecutar 03 modulos/03_construir_grafo.py
  cp -f output/*_m01_* output/*_m02_* output/*_m03_* "$CACHE_DIR"/ 2>/dev/null || true
  date -u +%FT%TZ > "$CACHE_MARKER"
fi
ejecutar 04 modulos/04_generar_semillas.py
ejecutar 05 modulos/05_optimizar_distritos.py
ejecutar 06 modulos/06_consolidar_distritos.py
ejecutar 07 modulos/07_agregar_resultados_electorales.py
ejecutar 08 modulos/08_integrar_resultados.py
set +e
python herramientas/validar_ejecucion.py --params "$PARAMS"; VALIDATION_RC=$?
set -e
python herramientas/registrar_ejecucion.py --params "$PARAMS" --phase finish --run-id "$RUN_ID"
exit "$VALIDATION_RC"
