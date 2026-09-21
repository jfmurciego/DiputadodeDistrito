#!/usr/bin/env bash
# PROYECTO: Diputado de Distrito
# FICHERO: procedimiento.sh
# VERSIÓN: 2.9.1
# NOMBRE DE VERSIÓN: Estrategia de optimización seleccionable en M05
# FECHA: 2026-09-20
# ESTADO: candidato
# CAMBIOS: mantiene la selección Canónico/GerryChain y añade fallback operativo de GerryChain a Canónico cuando la estrategia alternativa no puede producir salida.
# MOTIVO: una optimización opcional no debe dejar sin producto una formación inicial válida; el fallo GerryChain queda trazado y el flujo continúa con la estrategia canónica.
# ANTERIOR: legacy/procedimiento/procedimiento_v2.7.0.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$ROOT"
PARAMS="${DDD_PARAMS:-territorios/aragon/config/aragon_2025.yaml}"
MODO="${DDD_MODO:-completo}"
RUN_ID="${DDD_RUN_ID:-${GITHUB_RUN_ID:-local-$(date -u +%Y%m%dT%H%M%SZ)}}"
FROM_STAGE="${DDD_FROM_STAGE:-TERRITORY_PREPARATION}"
TO_STAGE="${DDD_TO_STAGE:-PUBLIC_PRODUCT_PUBLICATION}"
RESUME_MANIFEST="${DDD_CHECKPOINT_MANIFEST:-}"
CHAIN_STATE="${DDD_CHAIN_STATE:-}"
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
readarray -t CONTRACT_DIRS < <(python - "$PARAMS" "$RUN_ID" <<'PY'
import sys,yaml
from pathlib import Path
cfg=yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8")) or {}
io=cfg.get("io") or {}
cache=((io.get("cache") or {}).get("dir") or ".cache/ddd/preparacion/{run_name}")
runs=((io.get("runs") or {}).get("dir") or "ejecuciones/{run_id}")
values={"run_name":(cfg.get("meta") or {}).get("run_name", Path(sys.argv[1]).stem),"run_id":sys.argv[2],"year":(cfg.get("meta") or {}).get("year","")}
print(str(cache).format(**values))
print(str(runs).format(**values))
PY
)
CACHE_DIR="${DDD_CHECKPOINT_CACHE_DIR:-${CONTRACT_DIRS[0]}}"
RUN_DIR="${CONTRACT_DIRS[1]}"; LOG_DIR="$RUN_DIR/logs"
mkdir -p "$RUN_DIR" "$LOG_DIR" "$CACHE_DIR"
declare -a SCRIPTS=("" "modulos/01_preparar_base_territorial.py" "modulos/02_construir_adyacencias.py" "modulos/03_construir_grafo.py" "modulos/04_generar_semillas.py" "modulos/05_optimizar_distritos.py" "modulos/06_consolidar_distritos.py" "modulos/07_agregar_resultados_electorales.py" "modulos/08_integrar_resultados.py")
for n in $(seq "$FROM" "$TO"); do test -f "${SCRIPTS[$n]}" || { echo "[FATAL] Falta ${SCRIPTS[$n]}" >&2; exit 20; }; done
BASE_OK="$CACHE_DIR/${RUN_NAME}_m03_grafo.json"
if (( FROM > 1 )); then
  if [[ -n "$CHAIN_STATE" ]]; then
    test -f "$CHAIN_STATE" || { echo "[FATAL] Encadenamiento modular requiere DDD_CHAIN_STATE existente." >&2; exit 21; }
    python - "$CHAIN_STATE" "$PARAMS" "$((FROM - 1))" <<'PY'
import json,sys
state=json.load(open(sys.argv[1],encoding="utf-8"))
expected_params=sys.argv[2]
required=int(sys.argv[3])
completed=int(state.get("completed_stage",0))
if state.get("params") != expected_params:
    raise SystemExit(f"CHAIN_STATE pertenece a otro contrato: {state.get('params')} != {expected_params}")
if completed < required:
    raise SystemExit(f"CHAIN_STATE incompleto: M{completed:02d}; se requiere al menos M{required:02d}")
PY
    python herramientas/validar_fuentes_reanudacion.py \
      --params "$PARAMS" \
      --package .ddd-source-package \
      --root-dir .
    if (( FROM >= 4 )); then
      test -f "$BASE_OK" || { echo "[FATAL] M04+ requiere checkpoint M03 materializado en $BASE_OK." >&2; exit 21; }
    fi
  else
    test -n "$RESUME_MANIFEST" && test -f "$RESUME_MANIFEST" || { echo "[FATAL] Reenganche requiere DDD_CHECKPOINT_MANIFEST existente." >&2; exit 21; }
    python - "$RESUME_MANIFEST" <<'PY'
import json,sys
data=json.load(open(sys.argv[1],encoding="utf-8"))
if not data.get("products"): raise SystemExit("PRODUCTOS.json sin productos")
PY
    test -f "$BASE_OK" || { echo "[FATAL] Reenganche requiere checkpoint M03 materializado en $BASE_OK." >&2; exit 21; }
  fi
fi
python - "$RUN_DIR/REENGANCHE.json" "$PARAMS" "$RUN_ID" "$FROM_STAGE" "$TO_STAGE" "$RESUME_MANIFEST" "$CACHE_DIR" <<'PY'
import datetime,json,sys
from pathlib import Path
out,params,run_id,first,last,manifest,cache=map(str,sys.argv[1:])
Path(out).write_text(json.dumps({"schema_version":"1.0","run_id":run_id,"params":params,"from_stage":first,"to_stage":last,"checkpoint_manifest":manifest or None,"checkpoint_cache_dir":cache,"created_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat()},ensure_ascii=False,indent=2),encoding="utf-8")
PY
python herramientas/registrar_ejecucion.py --params "$PARAMS" --phase start --run-id "$RUN_ID"
resolver_perfil_m05(){
  case "${DDD_OPTIMIZATION_ALGORITHM:-}" in
    "Canónico"|canonical) printf '%s|%s\n' canonical 0 ;;
    "GerryChain"|gerrychain_recom) printf '%s|%s\n' gerrychain_recom 1 ;;
    "GerryChain 25"|gerrychain_25) printf '%s|%s\n' gerrychain_recom 25 ;;
    "GerryChain 50"|gerrychain_50) printf '%s|%s\n' gerrychain_recom 50 ;;
    "")
      python - "$PARAMS" <<'PY'
import sys,yaml
from pathlib import Path
cfg=yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8")) or {}
m05=((cfg.get("modulos") or {}).get("modulo_05_optimizar_distritos") or {})
strategy=m05.get("optimization_strategy") or "canonical"
seed_count=((m05.get("gerrychain") or {}).get("seed_count") or 0) if strategy=="gerrychain_recom" else 0
print(f"{strategy}|{seed_count}")
PY
      ;;
    *)
      echo "[FATAL] Estrategia de optimización desconocida: ${DDD_OPTIMIZATION_ALGORITHM}" >&2
      exit 20
      ;;
  esac
}
ejecutar(){
  local n="$1" script="$2"
  if [[ "$n" == "5" ]]; then
    local profile strategy candidate_count
    profile="$(resolver_perfil_m05)"
    strategy="${profile%%|*}"
    candidate_count="${profile#*|}"
    echo "===== MÓDULO 5: Estrategia de optimización — $strategy; candidatos=$candidate_count ====="
    case "$strategy" in
      canonical)
        python "$script" --params "$PARAMS" 2>&1 | tee "$LOG_DIR/modulo_${n}.log"
        ;;
      gerrychain_recom)
        local gerry_rc=0 baseline_rc=0
        seed_args=()
        if [[ "$candidate_count" =~ ^[0-9]+$ ]] && (( candidate_count > 0 )); then
          seed_args=(--seed-count "$candidate_count")
        fi

        # La validez del contrato y de la Formación inicial se comprueba siempre,
        # incluso si el runtime aislado de GerryChain no está disponible.
        set +e
        python ddd_core/m05_gerrychain_strategy.py \
          --params "$PARAMS" --run-id "$RUN_ID" --validate-baseline-only \
          2>&1 | tee "$LOG_DIR/modulo_${n}_baseline_validation.log"
        baseline_rc=${PIPESTATUS[0]}
        set -e
        if (( baseline_rc != 0 )); then
          echo "[FATAL] Contrato o Formación inicial inválidos; no se permite fallback." | tee -a "$LOG_DIR/modulo_${n}.log"
          exit 42
        fi

        if [[ -x /opt/ddd-gerrychain/bin/python ]]; then
          set +e
          PYTHONHASHSEED=0 /opt/ddd-gerrychain/bin/python ddd_core/m05_gerrychain_strategy.py \
            --params "$PARAMS" --run-id "$RUN_ID" "${seed_args[@]}" 2>&1 | tee "$LOG_DIR/modulo_${n}.log"
          gerry_rc=${PIPESTATUS[0]}
          set -e
        else
          gerry_rc=20
          echo "[WARN] Entorno reproducible GerryChain no disponible tras validar baseline." | tee "$LOG_DIR/modulo_${n}.log"
        fi

        if (( gerry_rc == 42 )); then
          echo "[FATAL] GerryChain detectó entrada inválida tras el preflight; no se permite fallback." | tee -a "$LOG_DIR/modulo_${n}.log"
          exit 42
        fi

        if (( gerry_rc != 0 )); then
          echo "[WARN] GerryChain falló después de validar la entrada (rc=$gerry_rc); se ejecuta Canónico como fallback." | tee -a "$LOG_DIR/modulo_${n}.log"
          python - "$RUN_DIR/OPTIMIZATION_FALLBACK.json" "$gerry_rc" "$candidate_count" <<'PY'
import datetime,json,sys
from pathlib import Path
out,rc,candidates=sys.argv[1:]
payload={
    "schema":"ddd.optimization-fallback/1.2",
    "requested_strategy":"gerrychain_recom",
    "requested_candidates":int(candidates),
    "gerrychain_exit_code":int(rc),
    "fallback_strategy":"canonical",
    "reason":"gerrychain_runtime_failure_after_valid_baseline",
    "baseline_validated":True,
    "created_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
}
Path(out).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
PY
          python "$script" --params "$PARAMS" 2>&1 | tee "$LOG_DIR/modulo_${n}_fallback_canonical.log"
        fi
        ;;
      *)
        echo "[FATAL] Estrategia de optimización desconocida: $strategy" >&2
        exit 20
        ;;
    esac
    return
  fi
  echo "===== MÓDULO $n: $script ====="
  python "$script" --params "$PARAMS" 2>&1 | tee "$LOG_DIR/modulo_${n}.log"
}
write_chain_state(){
  [[ -n "$CHAIN_STATE" ]] || return 0
  mkdir -p "$(dirname "$CHAIN_STATE")"
  python - "$CHAIN_STATE" "$PARAMS" "$RUN_ID" "$TO" "$CACHE_DIR" <<'PY'
import datetime,json,sys
from pathlib import Path
out,params,run_id,completed,cache=sys.argv[1:]
payload={"schema":"ddd.module-chain-state/1.0","params":params,"run_id":run_id,"completed_stage":int(completed),"completed_stage_label":f"M{int(completed):02d}","cache_dir":cache,"updated_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
Path(out).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
PY
}
if (( FROM <= 3 )); then
  if [[ "$MODO" == "iterativo" && -f "$BASE_OK" ]]; then
    echo "[PREPARACIÓN] Reutilización local M01-M03: checkpoint materializado."
  else
    for n in $(seq "$FROM" "$(( TO < 3 ? TO : 3 ))"); do ejecutar "$n" "${SCRIPTS[$n]}"; done
  fi
fi
if (( TO >= 4 )); then
  if (( FROM <= 4 )); then
    echo "===== PREPARACIÓN INTERNA: unidades declarativas previas a formación de distritos ====="
    python herramientas/preparar_unidades_internas.py --params "$PARAMS" --run-id "$RUN_ID" --job-report "$RUN_DIR/preparacion_unidades_internas.json" 2>&1 | tee "$LOG_DIR/preparacion_unidades_internas.log"
  fi
  for n in $(seq "$(( FROM > 4 ? FROM : 4 ))" "$TO"); do
    ejecutar "$n" "${SCRIPTS[$n]}"
  done
fi
if (( TO < 8 )); then
  echo "[PARCIAL] Tramo $FROM_STAGE → $TO_STAGE terminado; validación pública diferida hasta M08."
  python herramientas/registrar_ejecucion.py --params "$PARAMS" --phase finish --run-id "$RUN_ID"
  write_chain_state
  exit 0
fi
set +e
python herramientas/validar_ejecucion.py --params "$PARAMS" --run-id "$RUN_ID"; VALIDATION_RC=$?
set -e
python herramientas/registrar_ejecucion.py --params "$PARAMS" --phase finish --run-id "$RUN_ID"
if (( VALIDATION_RC == 0 )); then write_chain_state; fi
exit "$VALIDATION_RC"
