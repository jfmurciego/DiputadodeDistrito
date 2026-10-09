#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
PARAMS="${DDD_PARAMS:-params/ddd_params.yaml}"
RUN_ID="${GITHUB_RUN_ID:-local}"
LOG_DIR="output/logs"
mkdir -p output "$LOG_DIR"
required=(
  "$PARAMS"
  "ddd_core/config.py"
  "scripts/ddd_step1_build_sections_v6_params.py"
  "scripts/ddd_step2_export_edges_v6_params.py"
  "scripts/ddd_step3_build_graph_v6_params.py"
  "scripts/ddd_step4_seed_districts_v6_params.py"
  "scripts/ddd_step5_optimize_swaps_v6_params.py"
  "scripts/ddd_step6_export_final_v6_params.py"
  "scripts/ddd_step7_aggregate_election_results_v6_1_params.py"
  "scripts/ddd_step8_join_results_to_districts_v6_5.py"
  "inputs/seccionado_2025.zip"
  "inputs/65034.csv.zip"
  "inputs/rtve_aragon_2026_secciones.json"
)
for f in "${required[@]}"; do
  [[ -f "$f" ]] || { echo "[FATAL] Missing required file: $f" >&2; exit 20; }
done
python scripts/write_run_manifest.py --params "$PARAMS" --phase start --run-id "$RUN_ID"
run_step() {
  local n="$1" script="$2"
  echo "===== STEP $n: $script ====="
  python "$script" --params "$PARAMS" 2>&1 | tee "$LOG_DIR/step${n}.log"
}
run_step 1 scripts/ddd_step1_build_sections_v6_params.py
run_step 2 scripts/ddd_step2_export_edges_v6_params.py
run_step 3 scripts/ddd_step3_build_graph_v6_params.py
run_step 4 scripts/ddd_step4_seed_districts_v6_params.py
run_step 5 scripts/ddd_step5_optimize_swaps_v6_params.py
run_step 6 scripts/ddd_step6_export_final_v6_params.py
run_step 7 scripts/ddd_step7_aggregate_election_results_v6_1_params.py
run_step 8 scripts/ddd_step8_join_results_to_districts_v6_5.py
python scripts/validate_run.py --params "$PARAMS"
python scripts/write_run_manifest.py --params "$PARAMS" --phase finish --run-id "$RUN_ID"
echo "[OK] DDD pipeline complete and validation passed."
