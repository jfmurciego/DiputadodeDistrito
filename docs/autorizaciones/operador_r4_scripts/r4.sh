#!/bin/bash
# r4: piloto aut11 + pasos 1, 2 y 4. Para al primer fallo. Reanudable por marcas en $Q.
cd /home/user/DiputadodeDistrito
r=jfmurciego/DiputadodeDistrito; Q=/tmp/claude-0/-home-user-DiputadodeDistrito/5a52b161-2314-5f9d-b922-721b3406fb2a/scratchpad/r4
L=docs/autorizaciones/regeneracion_71_2026-11-14.txt; P=docs/autorizaciones/p10_r4_resultado.tsv; A=docs/autorizaciones/archivo_p10_r4_resultado.tsv
log(){ echo "$(date -u +%H:%M) $*"; }
verde(){ while :; do n=0; for st in in_progress pending queued; do n=$((n+$(gh api "repos/$r/actions/workflows/pruebas-plataforma.yml/runs?branch=main&status=$st&per_page=5" -q '.workflow_runs|length'))); done; [ "$n" = 0 ] && break; sleep 60; done
  st=$(gh api "repos/$r/actions/workflows/pruebas-plataforma.yml/runs?branch=main&per_page=100" -q '[.workflow_runs[]|select(.status=="completed" and .conclusion!="cancelled")][0].conclusion'); [ "$st" = success ]; }
congelado(){ git fetch -q origin main; n=$(git diff --name-only "$(cat $Q/base)" origin/main -- ddd_motor2 ddd_core modulos paquetes/deslinde .github/workflows/ejecucion-completa-proyecto.yml .github/workflows/preparacion-fuentes.yml .github/workflows/produccion-distritos.yml .github/workflows/desplegar-visor-publico.yml '.github/workflows/_reutilizable-*' .github/workflows/preparacion-legislatura-vigente.yml | wc -l); [ "$n" -eq 0 ]; }
check(){ verde && congelado || { log "PARADA antes de $1 (main rojo o congelación)"; exit 2; }; }
p10tanda(){ # $1 $2 filas
  $Q/p10.sh $1 $2 >/dev/null
  python3 $Q/mapa_ids.py >/dev/null || { log "PARADA mapa ids"; exit 3; }
  for k in $(seq $1 $2); do t=$(sed -n "${k}p" $L); row=$(grep -F "$t	" $P) || continue
    run=$(echo "$row" | cut -f2); c=$(echo "$row" | cut -f3); [ "$c" = success ] || { log "PARADA P10 $t $run $c"; exit 3; }
    id=$(grep -P "\t$run\t" docs/autorizaciones/p10_r4_paquetes.tsv | cut -f1)
    grep -q "^$id " $Q/verif.txt 2>/dev/null && continue
    v=$($Q/verif.sh $run $id) || { log "PARADA verificación $t $run: $v"; exit 3; }; echo "$id $run $v" >> $Q/verif.txt
  done; }
tanda(){ k=$1; shift; [ -f $Q/ok_$k ] && return 0
  [ -f $Q/since_$k ] || { sleep 240; check "P00 $*"; date -u +%Y-%m-%dT%H:%M:%SZ > $Q/since_$k; }
  out=$(SINCE=$(cat $Q/since_$k) $Q/tanda_multi.sh "$@"); echo "$out" >> $Q/tandas.txt
  echo "$out" | awk -F'\t' 'NF>=5{print $5}' | grep -qv '^success$' && { log "PARADA P00 filas $*"; echo "$out"; exit 5; }
  [ "$(echo "$out" | grep -c 'P00')" -ge $(( $# * 2 )) ] || { log "PARADA P00 filas $*: cadenas incompletas"; echo "$out"; exit 5; }
  touch $Q/ok_$k; log "P00 filas $* OK"; }
# 0. piloto aut11
if [ ! -f $Q/ok_piloto ]; then
  check "P10 aut11"; p10tanda 11 11; log "piloto: P10 aut11 OK $(tail -1 $Q/verif.txt)"
  $Q/archivar.sh 1 1 >/dev/null; [ "$(cut -f4 $A | grep -c '^success$')" -ge 1 ] || { log "PARADA archivado aut11"; cat $A; exit 4; }
  log "piloto: archivo aut11 OK"
  tanda t11 11; touch $Q/ok_piloto; log "PILOTO OK"; [ -n "$STOP_AFTER_PILOTO" ] && exit 0
fi
# 1. P10 de los otros 70
for rg in "1 10" "12 21" "22 31" "32 41" "42 51" "52 61" "62 71"; do set -- $rg; [ -f $Q/ok_p10_$1 ] && continue; check "P10 $rg"; p10tanda $1 $2; touch $Q/ok_p10_$1; log "P10 filas $rg OK"; done
[ "$(grep -c '	success$' $P)" -eq 71 ] && [ "$(wc -l < $Q/verif.txt)" -eq 71 ] || { log "PARADA P10 incompletos"; exit 3; }
log "paso 1 OK 71/71 verificados"
# 2. archivado
if [ ! -f $Q/ok_archivo ]; then check "archivado"; for a in 2 12 22 32 42 52 62; do b=$((a+9)); [ $b -gt 71 ] && b=71; $Q/archivar.sh $a $b >/dev/null; [ "$(cut -f4 $A | grep -vc '^success$')" -eq 0 ] || { log "PARADA archivado"; grep -v "	success$" $A; exit 4; }; done
  [ "$(wc -l < $A)" -eq 71 ] || { log "PARADA archivado incompleto"; exit 4; }; touch $Q/ok_archivo; fi
log "paso 2 OK 71/71"
# 4. tandas de 5
set -- $(seq 1 71 | grep -vx 11)
while [ $# -gt 0 ]; do g=(); for k in 1 2 3 4 5; do [ $# -gt 0 ] && { g+=($1); shift; }; done; tanda t_$(IFS=_; echo "${g[*]}") "${g[@]}"; done
log "paso 4 OK: 71 regenerados"
