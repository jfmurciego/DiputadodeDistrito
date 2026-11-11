#!/bin/bash
# Poda de ramas autorizada por el propietario el 2026-11-11 (criterio del Planificador).
# Uso en el Mac:  cd <repo>; git pull; bash docs/autorizaciones/poda_ramas_2026-11-11/podar_ramas.sh
# Lee ramas_borradas.tsv (rama<TAB>sha). Solo borra si la rama sigue apuntando al mismo sha.
# Restaurar una rama:  gh api -X POST repos/jfmurciego/DiputadodeDistrito/git/refs -f ref=refs/heads/<rama> -f sha=<sha>
set -u
R=jfmurciego/DiputadodeDistrito
F="$(dirname "$0")/ramas_borradas.tsv"
ok=0; salt=0; fal=0
tail -n +2 "$F" | while IFS=$'\t' read -r rama sha; do
  actual=$(gh api "repos/$R/git/ref/heads/$rama" --jq .object.sha 2>/dev/null)
  if [ "$actual" != "$sha" ]; then echo "SALTADA (cambió o no existe): $rama"; continue; fi
  if gh api -X DELETE "repos/$R/git/refs/heads/$rama" >/dev/null 2>&1; then echo "BORRADA $rama"; else echo "FALLO $rama"; fi
done | tee poda_ramas_resultado.txt
echo; echo "Borradas: $(grep -c ^BORRADA poda_ramas_resultado.txt)  Saltadas: $(grep -c ^SALTADA poda_ramas_resultado.txt)  Fallos: $(grep -c ^FALLO poda_ramas_resultado.txt)"
