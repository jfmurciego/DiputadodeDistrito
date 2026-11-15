#!/bin/bash
# uso: archivar.sh desde hasta  (filas del tsv, 1-based sin cabecera); lanza, espera fin y deja resultado
cd /home/user/DiputadodeDistrito
r=jfmurciego/DiputadodeDistrito; T=docs/autorizaciones/p10_r4_paquetes.tsv; O=docs/autorizaciones/archivo_p10_r4_resultado.tsv
touch $O
tail -n +2 $T | sed -n "$1,$2p" | while IFS=$'\t' read id run art exp; do
  grep -q "^$id	" $O && continue
  before=$(gh api "repos/$r/actions/workflows/bateria-motor.yml/runs?per_page=1" -q '.workflow_runs[0].id')
  gh api -X POST repos/$r/actions/workflows/bateria-motor.yml/dispatches -f ref=main -f "inputs[territorios]=$id" -f "inputs[archivar_p10]=$run" -f "inputs[motor]=motor2" >/dev/null || { echo "$id DISPATCH_FALLO"; exit 1; }
  for i in $(seq 1 20); do sleep 5; nid=$(gh api "repos/$r/actions/workflows/bateria-motor.yml/runs?per_page=1" -q '.workflow_runs[0].id'); [ "$nid" != "$before" ] && break; done
  printf '%s\t%s\t%s\tEN_VUELO\n' $id $run $nid >> $O
done
# esperar
for rid in $(awk -F'\t' '$4=="EN_VUELO"{print $3}' $O); do
  while [ "$(gh api repos/$r/actions/runs/$rid -q .status)" != completed ]; do sleep 30; done
  c=$(gh api repos/$r/actions/runs/$rid -q .conclusion); sed -i "s/\t$rid\tEN_VUELO$/\t$rid\t$c/" $O
done
cut -f4 $O | sort | uniq -c
