# M07 — Agregar resultados electorales

**Versión:** 1.3.0 (código M07 7.4.0, T-291)
**Estado:** vigente — R039
**Anterior:** `legacy/docs/M07_AGREGACION_ELECTORAL_v1.2.0.md`

## Propósito
M07 proyecta una elección sobre distritos ya calculados. La elección no participa en la creación de fronteras.

Antes de agregar, M07 conserva todas las filas electorales mediante un cruce izquierdo y reconcilia ambos universos. Toda sección presente solo en resultados o solo en el mapa debe estar declarada exactamente en el contrato. Una sección inesperada, una excepción obsoleta o un número de votos distinto del declarado produce `FAIL` después de escribir el informe.

## Entradas

Secciones M06 con `district_id` y un `election_contract` de familia
`ddd-election` 1.0.0. El contrato identifica convocatoria y territorio, fija la
independencia de las fronteras, declara cada fichero con SHA-256 y procedencia,
selecciona un adaptador `nested_json` o `long_csv`, enlaza un diccionario de
partidos y contiene la política de reconciliación.

La carga es cerrada: checksum incorrecto, territorio distinto, adaptador no
declarado, alias ambiguo o partido desconocido bloquean M07 antes de publicar.

## Equivalencia de seccionados (7.4.0, D-65)
Si el contrato declara `section_reconciliation.equivalence_table` (`path`, `sha256`, `source_column`,
`target_column`), M07 verifica la huella y lleva los votos de cada sección de la tabla al mapa vigente antes de
reconciliar, todas a la vez: `1:1` y `contenida` pasan enteros; `partida` se reparte por `peso_poblacion` (D-13) con
resto mayor por partido; `sin_vigente` no se toca y acaba en `ddd_unassigned_votes`. Los votos de cada partido se
conservan; el informe (`section_equivalence`) da secciones y votos por clase, destinos ausentes del mapa y votos
repartidos entre distritos distintos. Tabla de la noche del 29-11-2026: `configuracion/equivalencia_seccionado_ine_2026_a_2023.csv`
(`herramientas/equivalencia_seccionado_2026_2023.py`). Los `splits` del contrato siguen sin aplicarse.

## Productos
`M07/resultados_por_partido.csv`: votos asignados por distrito y partido. `M07/resumen_electoral.csv`: total, ganador, votos, cuota y bloque. `M07/reconciliacion.json`: votos de entrada, asignados y no asignables, más las secciones no emparejadas. El GeoJSON enriquecido conserva todas las secciones del mapa, incluidas las que carecen de resultados.

## Auditoría
Debe poder rastrearse el resultado distrital hasta las secciones que lo componen y hasta los registros electorales de entrada. El CSV por partido es el detalle; el resumen es una vista derivada y no lo sustituye.

M08 exige después igualdad exacta entre el conjunto de distritos geométricos y
el resumen electoral, y rechaza duplicados. Una ausencia ya no produce columnas
nulas silenciosas.

## Por qué separado
Permite aplicar otra elección, una actualización de escrutinio o una simulación distinta sin ejecutar M01-M06 de nuevo.
