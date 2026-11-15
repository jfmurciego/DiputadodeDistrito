#!/bin/bash
# uso: verif.sh <run_p10> <id canónico>  -> OK o FALLO motivo
r=jfmurciego/DiputadodeDistrito; run=$1; id=$2; desde=2026-11-15T07:50
j=$(gh api repos/$r/actions/runs/$run/jobs --jq '.jobs[]|select(.name|test("Preparar fuentes"))|.id'|head -1)
l=$(gh api repos/$r/actions/jobs/$j/logs 2>/dev/null | grep -v '36;1m')
[ -n "$l" ] || { echo "FALLO sin_log"; exit 1; }
e=$(echo "$l" | grep -m1 -oE '\{"schema": "ddd-source-execution[^}]*\}')
[ -n "$e" ] || { echo "FALLO sin_source_execution"; exit 1; }
echo "$e" | grep -q '"decision": "ACQUIRE"' || { echo "FALLO decision $(echo "$e" | grep -oE '"decision": "[A-Z]+"')"; exit 1; }
echo "$e" | grep -q '"restored_from_checkpoint": false' || { echo "FALLO restaurado"; exit 1; }
ac=$(echo "$e" | grep -oE '"acquired_at": "[^"]+"' | cut -d'"' -f4)
[ -n "$ac" ] && [[ ! "$ac" < "$desde" ]] || { echo "FALLO acquired_at ${ac:-vacío}"; exit 1; }
echo "$l" | grep -q "ddd-source-package-$id-2025-$run successfully finalized" || { echo "FALLO artefacto"; exit 1; }
echo "OK ACQUIRE $ac"
