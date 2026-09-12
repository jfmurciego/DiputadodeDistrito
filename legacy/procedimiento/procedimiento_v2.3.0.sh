#!/usr/bin/env bash
# PROYECTO: Diputado de Distrito
# FICHERO: procedimiento.sh
# VERSIÓN: 2.3.0
# NOMBRE DE VERSIÓN: Lanzador semántico por tramo certificado
# FECHA: 2026-09-12
# QUÉ HACE: ejecuta un intervalo explícito M01-M08, registra la decisión de reenganche y exige evidencia materializada antes de reutilizar etapas anteriores.
# ESTADO: vigente — G10 R025.
# CAMBIOS: sustituye el flujo implícito todo-o-nada por DDD_FROM_STAGE/DDD_TO_STAGE; una ejecución parcial requiere manifiesto y caché de checkpoint.
# MOTIVO: ahorrar cómputo sin declarar reutilizable una salida que no está presente en el runner.
# ANTERIOR: legacy/procedimiento/procedimiento_v2.2.0.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$ROOT"
PARAMS="${DDD_PARAMS:-territorios/aragon/config/aragon_2025.yaml}"
MODO="${DDD_MODO:-completo}"
RUN_ID="${DDD_RUN_ID:-${GITHUB_RUN_ID:-local-$(date -u +%Y%m%dT%H%M%SZ)}}"
FROM_STAGE="${DDD_FROM_STAGE:-TERRITORY_PREPARATION}"
TO_STAGE="${DDD_TO_STAGE:-PUBLIC_PRODUCT_PUBLICATION}"
RESUME_MANIFEST="${DDD_CHECKPOINT_MANIFEST:-}"
export DDD_RUN_ID="$RUN_ID"
test -f "$PARAMS" || { echo "[FATAL] Falta $PARAMS" >&2; exit 20; }
stage_module(){
  case "$1" in
    TERRITORY_PREPARATION|M01) echo 1;;
    TERRITORY_ADJACENCY|M02) echo 2;;
    TERRITORY_GRAPH|M03) echo 3;;
    DISTRICT_FORMATION|M04) echo 4;;
    DISTRICT_BALANCING|M05) echo 5;;
    TERRITORIAL_CERTIFICATION|M06) echo 6;;
    ELECTORAL_ENRICHMENT|M07) echo 7;;
    PUBLIC_PRODUCT_PUBLICATION|M08) echo 8;;
    *) return 1;;
  esac
}
FROM="$(stage_module "$FROM_STAGE")" || { echo "[FATAL] DDD_FROM_STAGE desconocida: $FROM_STAGE" >&2; exit 20; }
TO="$(stage_module "$TO_STAGE")" || { echo "[FATAL] DDD_TO_STAGE desconocida: $TO_STAGE" >&2; exit 20; }
(( FROM <= TO )) || { echo "[FATAL] El inicio no puede ser posterior al final." >&2; exit 20; }
RUN_NAME="$(python - "$PARAMS" <<'PY'
import sys,yaml
from pathlib import Path
data=yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8")) or {}
print((data.get("meta") or {}).get("run_name") or Path(sys.argv[1]).stem)
PY
)"
[[ -n "$RUN_NAME" ]] || { echo "[FATAL] run_name vacío" >&2; exit 20; }
RUN_DIR="ejecuciones/$RUN_ID"; LOG_DIR="$RUN_DIR/logs"
CACHE_DIR="${DDD_CHECKPOINT_CACHE_DIR:-.cache/ddd/preparacion/$RUN_NAME}"
mkdir -p "$RUN_DIR" "$LOG_DIR" "$CACHE_DIR"
declare -a SCRIPTS=("" "modulos/01_preparar_base_territorial.py" "modulos/02_construir_adyacencias.py" "modulos/03_construir_grafo.py" "modulos/04_generar_semillas.py" "modulos/05_optimizar_distritos.py" "modulos/06_consolidar_distritos.py" "modulos/07_agregar_resultados_electorales.py" "modulos/08_integrar_resultados.py")
for n in $(seq "$FROM" "$TO"); do test -f "${SCRIPTS[$n]}" || { echo "[FATAL] Falta ${SCRIPTS[$n]}" >&2; exit 20; }; done
BASE_OK="$CACHE_DIR/${RUN_NAME}_m03_grafo.json"
if (( FROM > 1 )); then
  test -n "$RESUME_MANIFEST" && test -f "$RESUME_MANIFEST" || { echo "[FATAL] Reenganche requiere DDD_CHECKPOINT_MANIFEST existente." >&2; exit 21; }
  python - "$RESUME_MANIFEST" <<'PY'
import json,sys
data=json.load(open(sys.argv[1],encoding="utf-8"))
if not data.get("products"): raise SystemExit("PRODUCTOS.json sin productos")
PY
  test -f "$BASE_OK" || { echo "[FATAL] Reenganche requiere checkpoint M03 materializado en $BASE_OK." >&2; exit 21; }
fi
python - "$RUN_DIR/REENGANCHE.json" "$PARAMS" "$RUN_ID" "$FROM_STAGE" "$TO_STAGE" "$RESUME_MANIFEST" "$CACHE_DIR" <<'PY'
import datetime,json,sys
from pathlib import Path
out,params,run_id,first,last,manifest,cache=map(str,sys.argv[1:])
Path(out).write_text(json.dumps({"schema_version":"1.0","run_id":run_id,"params":params,"from_stage":first,"to_stage":last,"checkpoint_manifest":manifest or None,"checkpoint_cache_dir":cache,"created_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat()},ensure_ascii=False,indent=2),encoding="utf-8")
PY
python herramientas/registrar_ejecucion.py --params "$PARAMS" --phase start --run-id "$RUN_ID"
ejecutar(){ local n="$1" script="$2"; echo "===== MÓDULO $n: $script ====="; python "$script" --params "$PARAMS" 2>&1 | tee "$LOG_DIR/modulo_${n}.log"; }
if (( FROM <= 3 )); then
  if [[ "$MODO" == "iterativo" && -f "$BASE_OK" ]]; then
    echo "[PREPARACIÓN] Reutilización local M01-M03: checkpoint materializado."
  else
    for n in $(seq "$FROM" "$(( TO < 3 ? TO : 3 ))"); do ejecutar "$n" "${SCRIPTS[$n]}"; done
  fi
fi
for n in $(seq "$(( FROM > 4 ? FROM : 4 ))" "$TO"); do ejecutar "$n" "${SCRIPTS[$n]}"; done
if (( TO < 8 )); then
  echo "[PARCIAL] Tramo $FROM_STAGE → $TO_STAGE terminado; validación pública diferida hasta M08."
  python herramientas/registrar_ejecucion.py --params "$PARAMS" --phase finish --run-id "$RUN_ID"
  exit 0
fi
set +e
python herramientas/validar_ejecucion.py --params "$PARAMS" --run-id "$RUN_ID"; VALIDATION_RC=$?
set -e
python herramientas/registrar_ejecucion.py --params "$PARAMS" --phase finish --run-id "$RUN_ID"
exit "$VALIDATION_RC"
