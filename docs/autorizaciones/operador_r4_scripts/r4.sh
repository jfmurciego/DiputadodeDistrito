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
# Por tramos (frase del propietario 15-11): P10 del tramo -> verificación -> archivado del tramo -> P00 del tramo
# (primera tanda de 5 de la campaña y, si sale limpia, de 10). Con STOP_EACH sale tras cada hito.
hito(){ log "$*"; [ -n "$STOP_EACH" ] && exit 0; }
for rg in "1 10" "12 21" "22 31" "32 41" "42 51" "52 61" "62 71"; do set -- $rg; a=$1; b=$2
  if [ ! -f $Q/ok_p10_$a ]; then check "P10 $rg"; p10tanda $a $b; touch $Q/ok_p10_$a; hito "P10 filas $rg OK"; fi
  if [ ! -f $Q/ok_arch_$a ]; then check "archivado $rg"; $Q/archivar.sh 1 999 >/dev/null
    [ "$(cut -f4 $A | grep -vc '^success$')" -eq 0 ] || { log "PARADA archivado $rg"; grep -v "	success$" $A; exit 4; }
    for k in $(seq $a $b); do t=$(sed -n "${k}p" $L); run=$(grep -F "$t	" $P | cut -f2); id=$(grep -P "\t$run\t" docs/autorizaciones/p10_r4_paquetes.tsv | cut -f1)
      grep -q "^$id	$run	" $A || { log "PARADA archivado $rg: falta $t"; exit 4; }; done
    touch $Q/ok_arch_$a; hito "archivado filas $rg OK"; fi
  set -- $(seq $a $b | grep -vx 11)
  while [ $# -gt 0 ]; do g=(); sz=10; [ -f $Q/ok_t4primera ] || sz=5; for k in $(seq 1 $sz); do [ $# -gt 0 ] && { g+=($1); shift; }; done
    kk=t_$(IFS=_; echo "${g[*]}"); [ -f $Q/ok_$kk ] && continue; tanda $kk "${g[@]}"; touch $Q/ok_t4primera; hito "P00 filas ${g[*]} OK"; done
done
log "pasos 1, 2 y 4 OK: 71"
