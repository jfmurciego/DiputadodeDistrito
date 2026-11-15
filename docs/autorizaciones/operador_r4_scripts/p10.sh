#!/bin/bash
# uso: p10.sh desde hasta — preparacion-fuentes de esas filas; espera a que terminen
cd /home/user/DiputadodeDistrito
r=jfmurciego/DiputadodeDistrito; W=preparacion-fuentes.yml; L=docs/autorizaciones/regeneracion_71_2026-11-14.txt; O=docs/autorizaciones/p10_r4_resultado.tsv
touch $O
last(){ gh api "repos/$r/actions/workflows/$W/runs?event=workflow_dispatch&per_page=10" -q '[.workflow_runs[]|select(.actor.login!="github-actions[bot]")][0].id'; }
prev=$(last)
sed -n "$1,$2p" $L | while IFS= read -r t; do
  grep -qF "$t	" $O && continue
  gh api -X POST repos/$r/actions/workflows/$W/dispatches -f ref=main -f "inputs[territory_id]=$t" >/dev/null || { echo "DISPATCH_FALLO $t"; exit 1; }
  id=""; for i in $(seq 1 24); do sleep 5; id=$(last); [ "$id" != "$prev" ] && break; done; prev=$id
  printf '%s\t%s\tEN_VUELO\n' "$t" "$id" >> $O
done
for rid in $(awk -F'\t' '$3=="EN_VUELO"{print $2}' $O); do
  while [ "$(gh api repos/$r/actions/runs/$rid -q .status)" != completed ]; do sleep 60; done
  c=$(gh api repos/$r/actions/runs/$rid -q .conclusion); sed -i "s/\t$rid\tEN_VUELO$/\t$rid\t$c/" $O
done
cut -f3 $O | sort | uniq -c
