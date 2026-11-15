#!/bin/bash
# uso: tanda.sh desde hasta — lanza las 00 de esas filas, espera a que no quede ninguna 00/activación en curso y resume
cd /home/user/DiputadodeDistrito
r=jfmurciego/DiputadodeDistrito; L=docs/autorizaciones/regeneracion_71_2026-11-14.txt; O=docs/autorizaciones/regeneracion_r4_resultado.tsv
touch $O
since=${SINCE:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}
prev=$(gh api "repos/$r/actions/workflows/ejecucion-completa-proyecto.yml/runs?event=workflow_dispatch&per_page=10" -q '[.workflow_runs[]|select(.actor.login!="github-actions[bot]")][0].id')
for n in "$@"; do sed -n "${n}p" $L; done | while IFS= read -r t; do
  grep -qF "$t	" $O && continue
  gh api -X POST repos/$r/actions/workflows/ejecucion-completa-proyecto.yml/dispatches -f ref=main \
    -f "inputs[territory_id]=$t" -f "inputs[data_edition]=2025" -f "inputs[execution_mode]=Generar desde fuente territorial acreditada" \
    -f "inputs[optimization_algorithm]=Canónico" -f "inputs[motor]=motor2" -f "inputs[publication_mode]=territorial_only" \
    -f "inputs[publish_result]=false" -f "inputs[cadena_electoral]=true" >/dev/null || { echo "DISPATCH_FALLO $t"; exit 1; }
  id=""; for i in $(seq 1 24); do sleep 5; id=$(gh api "repos/$r/actions/workflows/ejecucion-completa-proyecto.yml/runs?event=workflow_dispatch&per_page=10" -q '[.workflow_runs[]|select(.actor.login!="github-actions[bot]")][0].id'); [ "$id" != "$prev" ] && break; done; prev=$id
  printf '%s\t%s\tterritorial\n' "$t" "${id:-DESCONOCIDO}" >> $O
done
sleep 600
while :; do
  n=0; for st in in_progress queued waiting pending; do n=$((n+$(gh api "repos/$r/actions/runs?status=$st&created=>=$since&per_page=100" -q '[.workflow_runs[]|select(.event!="pull_request" and (.name|test("P00|Activación";"i")))]|length'))); done
  [ $n -eq 0 ] && break
  f=$(gh api "repos/$r/actions/runs?status=completed&created=>=$since&per_page=100" -q '[.workflow_runs[]|select(.event!="pull_request" and (.name|test("P00|Activación";"i")) and .conclusion!="success")]|length')
  [ "$f" -gt 0 ] && break
  sleep 120
done
gh api "repos/$r/actions/runs?created=>=$since&per_page=100" -q '.workflow_runs[]|select(.event!="pull_request" and (.name|test("P00|Activación";"i")))|[.id,.name[0:30],.display_title[0:90],.actor.login,.conclusion]|@tsv'
