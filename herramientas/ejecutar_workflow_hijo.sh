#!/usr/bin/env bash
set -euo pipefail

workflow=""
ref=""
title_contains=""
timeout_seconds=14400
report=""
inputs=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workflow) workflow="$2"; shift 2;;
    --ref) ref="$2"; shift 2;;
    --title-contains) title_contains="$2"; shift 2;;
    --timeout-seconds) timeout_seconds="$2"; shift 2;;
    --report) report="$2"; shift 2;;
    --input) inputs+=("$2"); shift 2;;
    *) echo "Argumento desconocido: $1" >&2; exit 2;;
  esac
done

: "${workflow:?Falta --workflow}"
: "${ref:?Falta --ref}"
: "${title_contains:?Falta --title-contains}"
: "${GH_TOKEN:?Falta GH_TOKEN}"
: "${GITHUB_REPOSITORY:?Falta GITHUB_REPOSITORY}"

workflow_path=".github/workflows/$workflow"
workflow_id="$(gh api --paginate "repos/$GITHUB_REPOSITORY/actions/workflows?per_page=100"   --jq ".workflows[] | select(.path == \"$workflow_path\") | .id" | head -1)"
[[ -n "$workflow_id" ]] || { echo "No se encuentra workflow registrado: $workflow_path" >&2; exit 3; }

started_epoch="$(date -u +%s)"
args=(workflow run "$workflow" --repo "$GITHUB_REPOSITORY" --ref "$ref")
for item in "${inputs[@]}"; do args+=(-f "$item"); done
gh "${args[@]}" >/dev/null

run_id=""
deadline=$((started_epoch + timeout_seconds))
while (( $(date -u +%s) < deadline )); do
  runs="$(gh api --method GET "repos/$GITHUB_REPOSITORY/actions/workflows/$workflow_id/runs"     -f branch="$ref" -f event=workflow_dispatch -f per_page=50)"
  run_id="$(jq -r --arg title "$title_contains" --argjson started "$started_epoch" '
    [.workflow_runs[]
      | select(.display_title | contains($title))
      | . + {created_epoch:(.created_at | fromdateiso8601)}
      | select(.created_epoch >= ($started - 5))]
    | sort_by(.created_epoch) | reverse | .[0].id // empty
  ' <<<"$runs")"
  [[ -n "$run_id" ]] && break
  sleep 3
done
[[ -n "$run_id" ]] || { echo "No se localizó el run hijo de $workflow para $title_contains" >&2; exit 4; }

conclusion=""
status=""
while (( $(date -u +%s) < deadline )); do
  payload="$(gh api "repos/$GITHUB_REPOSITORY/actions/runs/$run_id")"
  status="$(jq -r .status <<<"$payload")"
  conclusion="$(jq -r '.conclusion // empty' <<<"$payload")"
  [[ "$status" == "completed" ]] && break
  sleep 10
done
[[ "$status" == "completed" ]] || { echo "Timeout esperando run hijo $run_id" >&2; exit 5; }

if [[ -n "$report" ]]; then
  mkdir -p "$(dirname "$report")"
  jq -n     --arg workflow "$workflow" --arg ref "$ref" --arg title "$title_contains"     --argjson run_id "$run_id" --arg status "$status" --arg conclusion "$conclusion"     '{workflow:$workflow,ref:$ref,title:$title,run_id:$run_id,status:$status,conclusion:$conclusion}' > "$report"
fi

if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  {
    echo "run_id=$run_id"
    echo "status=$status"
    echo "conclusion=$conclusion"
  } >> "$GITHUB_OUTPUT"
fi

echo "$workflow -> run $run_id -> $conclusion"
[[ "$conclusion" == "success" ]]
