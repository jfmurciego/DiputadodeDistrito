#!/bin/bash
# espera T-349 en main + CI verde sobre un commit que lo contiene; fija base y lanza el piloto
cd /home/user/DiputadodeDistrito; r=jfmurciego/DiputadodeDistrito; Q=/tmp/claude-0/-home-user-DiputadodeDistrito/5a52b161-2314-5f9d-b922-721b3406fb2a/scratchpad/r4
while :; do git fetch -q origin main; c=$(git log --format=%H -1 --grep='^T-349[:b ]' origin/main); [ -n "$c" ] && break; sleep 180; done
echo "$(date -u +%H:%M) T-349 en main: ${c:0:9}"
while :; do n=0; for st in in_progress pending queued; do n=$((n+$(gh api "repos/$r/actions/workflows/pruebas-plataforma.yml/runs?branch=main&status=$st&per_page=5" -q '.workflow_runs|length'))); done
  last=$(gh api "repos/$r/actions/workflows/pruebas-plataforma.yml/runs?branch=main&per_page=100" -q '[.workflow_runs[]|select(.status=="completed" and .conclusion!="cancelled")][0]|"\(.head_sha) \(.conclusion)"')
  sha=${last% *}; con=${last#* }
  if [ "$n" = 0 ] && git merge-base --is-ancestor $c $sha 2>/dev/null; then [ "$con" = success ] && break; echo "$(date -u +%H:%M) PARADA: main en rojo sobre ${sha:0:9} tras T-349"; exit 9; fi
  sleep 120; done
echo $sha > $Q/base; echo "$(date -u +%H:%M) main verde sobre ${sha:0:9}; base fijada"
exit 0
