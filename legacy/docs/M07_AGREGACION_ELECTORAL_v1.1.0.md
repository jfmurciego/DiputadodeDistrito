# M07 — Agregar resultados electorales

**Versión:** 1.1.0
**Estado:** vigente — Paquete A, C-05/C-09
**Anterior:** `legacy/docs/M07_AGREGACION_ELECTORAL_pre_paquete_a.md`

## Propósito
M07 proyecta una elección sobre distritos ya calculados. La elección no participa en la creación de fronteras.

Antes de agregar, M07 conserva todas las filas electorales mediante un cruce izquierdo y reconcilia ambos universos. Toda sección presente solo en resultados o solo en el mapa debe estar declarada exactamente en el contrato. Una sección inesperada, una excepción obsoleta o un número de votos distinto del declarado produce `FAIL` después de escribir el informe.

## Entradas
Secciones M06 con `district_id` y resultados RTVE 2026 por sección.

## Productos
`M07/resultados_por_partido.csv`: votos asignados por distrito y partido. `M07/resumen_electoral.csv`: total, ganador, votos, cuota y bloque. `M07/reconciliacion.json`: votos de entrada, asignados y no asignables, más las secciones no emparejadas. El GeoJSON enriquecido conserva todas las secciones del mapa, incluidas las que carecen de resultados.

## Auditoría
Debe poder rastrearse el resultado distrital hasta las secciones que lo componen y hasta los registros electorales de entrada. El CSV por partido es el detalle; el resumen es una vista derivada y no lo sustituye.

## Por qué separado
Permite aplicar otra elección, una actualización de escrutinio o una simulación distinta sin ejecutar M01-M06 de nuevo.
