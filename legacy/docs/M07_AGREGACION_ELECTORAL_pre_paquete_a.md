# M07 — Agregar resultados electorales

## Propósito
M07 proyecta una elección sobre distritos ya calculados. La elección no participa en la creación de fronteras.

## Entradas
Secciones M06 con `district_id` y resultados RTVE 2026 por sección.

## Productos
`M07/resultados_por_partido.csv`: votos completos por distrito y partido, incluido bloque configurado. `M07/resumen_electoral.csv`: total de votos, ganador, votos del ganador, cuota y bloque por distrito. `aragon_2025_m07_secciones_resultados.geojson.zip`: sección censal enriquecida con total y ganador de sección.

## Auditoría
Debe poder rastrearse el resultado distrital hasta las secciones que lo componen y hasta los registros electorales de entrada. El CSV por partido es el detalle; el resumen es una vista derivada y no lo sustituye.

## Por qué separado
Permite aplicar otra elección, una actualización de escrutinio o una simulación distinta sin ejecutar M01-M06 de nuevo.
