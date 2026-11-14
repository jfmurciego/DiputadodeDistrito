#!/bin/bash
# uso: cadena.sh DESDE_ISO "Congreso X" ...
desde=$1; shift
R=repos/jfmurciego/DiputadodeDistrito
: > /tmp/claude-0/-home-user-DiputadodeDistrito/ad112f8d-0821-54f1-8315-9b95a26b5cbd/scratchpad/allruns.tsv
for p in 1 2 3; do gh api "$R/actions/runs?created=>=$desde&per_page=100&page=$p" --jq '.workflow_runs[]|[.id,.display_title,.status,(.conclusion//""),.actor.login]|@tsv' >> /tmp/claude-0/-home-user-DiputadodeDistrito/ad112f8d-0821-54f1-8315-9b95a26b5cbd/scratchpad/allruns.tsv; done
for t in "$@"; do echo "== $t"; grep -F "· $t ·" /tmp/claude-0/-home-user-DiputadodeDistrito/ad112f8d-0821-54f1-8315-9b95a26b5cbd/scratchpad/allruns.tsv | awk -F'\t' '{split($2,a," · "); print "  "$1" "a[1]" | "a[3]" | "$3" "$4" | "$5}'; done
