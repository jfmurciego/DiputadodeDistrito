#!/bin/bash
# T-285: borra las 34 releases de lista.tsv (33 borradores de ensembles + cyl-m06-checkpoint-temp) y sus etiquetas.
# Ejecutar desde la raíz del repositorio, en Git Bash: bash docs/autorizaciones/poda_releases_2026-11-14/borrar_releases.sh
r=jfmurciego/DiputadodeDistrito
tail -n +2 docs/autorizaciones/poda_releases_2026-11-14/lista.tsv | while IFS=$'\t' read id tag bytes; do
  gh api -X DELETE repos/$r/releases/$id >/dev/null && echo "release OK $tag" || echo "release FALLO $tag"
  gh api -X DELETE repos/$r/git/refs/tags/$tag >/dev/null 2>&1 && echo "  etiqueta OK" || echo "  etiqueta no existe o FALLO"
done
