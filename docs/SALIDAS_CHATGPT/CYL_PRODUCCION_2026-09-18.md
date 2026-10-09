# Castilla y León — cierre factual de producción 2026-09-18

## Ejecución

- Workflow: `Producción de distritos`
- Run: `35329341120`
- Commit: `05f00efbfbd5c1c60a53af4fd5c01e8f818550c7`
- Checkpoint reutilizado: `35319351944` (M06)
- Tramo ejecutado: M07 → M08
- Recalculo M01–M06: no

## Resultado territorial y electoral

- Distritos: 82
- Auditoría geométrica M06: `PASS_WITH_EXCEPTIONS`
- Distritos bloqueados geométricamente: 0
- Excepciones geométricas justificadas: 17
- M07: `PASS_WITH_DECLARED_EXCEPTIONS`
- Votos de entrada: 1.236.753
- Votos asignados: 1.221.097
- Votos no asignados: 15.656
- M08: 82 distritos

Los 15.656 votos no asignados corresponden a diferencias declaradas entre el seccionado territorial 2025 y los resultados electorales 2026. No se realizó imputación artificial.

## Publicación

- GitHub Pages: https://jfmurciego.github.io/DiputadodeDistrito/
- Estado de despliegue: `success`
- La ejecución publicada coincide con la ejecución solicitada: sí
- Mapas nuevos publicados:
  - `data/results/m06-35329341120.geojson`
  - `data/results/m08-35329341120.geojson`

El visor publicado contiene 82 distritos en M06 y 82 distritos en M08.

## Estado de certificación

La publicación se completó correctamente, pero el estado territorial sigue siendo `BLOCK` por `POPULATION_TARGET_NOT_MET`.

La evidencia poblacional registra `TARGET_IMPROVED_NOT_MET`: la reparación redujo los distritos fuera del objetivo de 4 a 3, pero agotó el presupuesto de candidatos sin alcanzar completamente el objetivo poblacional.

Este bloqueo no impidió la ejecución de M07, M08 ni la publicación del visor; queda visible como estado técnico del resultado publicado.
