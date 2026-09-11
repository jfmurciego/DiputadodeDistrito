#!/usr/bin/env bash
# PROYECTO: Diputado de Distrito
# FICHERO: procedimiento.sh
# VERSIÓN: 2.2.0
# NOMBRE DE VERSIÓN: Lanzador multi-territorio por configuración
# FECHA: 2026-09-11
# QUÉ HACE: ejecuta M01-M08 para cualquier territorio definido por un YAML compatible, reutiliza M01-M03 y guarda M04-M08, logs, manifiesto y validación por run_id.
# ESTADO: vigente — R018 arquitectura multi-territorio.
# CAMBIOS: elimina el nombre duro aragon_2025 del directorio de caché y deriva run_name desde el YAML seleccionado; conserva compatibilidad con la ruta histórica de Aragón.
# MOTIVO: permitir Castilla y León, Extremadura y futuros territorios sin clonar el motor ni el procedimiento.
# ANTERIOR: legacy/procedimiento/procedimiento_v2.1.1.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$ROOT"
PARAMS="${DDD_PARAMS:-territorios/aragon/config/aragon_2025.yaml}"
MODO="${DDD_MODO:-completo}"
RUN_ID="${DDD_RUN_ID:-${GITHUB_RUN_ID:-local-$(date -u +%Y%m%dT%H%M%SZ)}}"
export DDD_RUN_ID="$RUN_ID"
test -f "$PARAMS" || { echo "[FATAL] Falta $PARAMS" >&2; exit 20; }
RUN_NAME="$(python - "$PARAMS" <<'PY'
import sys, yaml
from pathlib import Path
p=Path(sys.argv[1])
data=yaml.safe_load(p.read_text(encoding='utf-8')) or {}
print((data.get('meta') or {}).get('run_name') or p.stem)
PY
)"
[[ -n "$RUN_NAME" ]] || { echo "[FATAL] run_name vacío" >&2; exit 20; }
RUN_DIR="ejecuciones/$RUN_ID"; LOG_DIR="$RUN_DIR/logs"; CACHE_DIR=".cache/ddd/preparacion/$RUN_NAME"
mkdir -p "$RUN_DIR" "$LOG_DIR" "$CACHE_DIR"
for f in modulos/{01_preparar_base_territorial,02_construir_adyacencias,03_construir_grafo,04_generar_semillas,05_optimizar_distritos,06_consolidar_distritos,07_agregar_resultados_electorales,08_integrar_resultados}.py; do test -f "$f" || { echo "[FATAL] Falta $f" >&2; exit 20; }; done
python herramientas/registrar_ejecucion.py --params "$PARAMS" --phase start --run-id "$RUN_ID"
ejecutar(){ local n="$1" script="$2"; echo "===== MÓDULO $n: $script ====="; python "$script" --params "$PARAMS" 2>&1 | tee "$LOG_DIR/modulo_${n}.log"; }
BASE_OK="$CACHE_DIR/${RUN_NAME}_m03_grafo.json"
if [[ "$MODO" == "iterativo" && -f "$BASE_OK" ]]; then echo "[PREPARACIÓN] Reutilizando M01-M03 para $RUN_NAME."; else ejecutar 01 modulos/01_preparar_base_territorial.py; ejecutar 02 modulos/02_construir_adyacencias.py; ejecutar 03 modulos/03_construir_grafo.py; fi
ejecutar 04 modulos/04_generar_semillas.py
ejecutar 05 modulos/05_optimizar_distritos.py
ejecutar 06 modulos/06_consolidar_distritos.py
ejecutar 07 modulos/07_agregar_resultados_electorales.py
ejecutar 08 modulos/08_integrar_resultados.py
set +e
python herramientas/validar_ejecucion.py --params "$PARAMS" --run-id "$RUN_ID"; VALIDATION_RC=$?
set -e
python herramientas/registrar_ejecucion.py --params "$PARAMS" --phase finish --run-id "$RUN_ID"
exit "$VALIDATION_RC"
