<!--
Nombre: Resultado de reproyección M02 de Comunidad Valenciana
Versión: 1.0.0
Fecha: 2026-10-19
Alcance: evaluación de M01–M03 con configuración EPSG:25830
Estado: candidato, pendiente de revisión independiente
Cambios/motivo: documentar la comparación reproducible de CRS y resultados canónicos
Anterior: no existe; primer expediente de esta prueba
-->

# Comunidad Valenciana — reproyección M02 2025

**Estado:** candidato técnico, pendiente de CI y revisión independiente.
**Base:** `main@21a4a150eb14f1abecd5d798b159d84a71df1f4a`.
**Alcance:** parámetro `working_crs` de M02 y metadatos de edición requeridos por M01. No se editan geometrías, tolerancias, población, puentes ni contratos.

## Resultado

El paquete oficial protegido `prepared_sources.zip` (SHA-256 `76ffdfc3c11291b7578560cd31b9eeab2e9b8aedc06bdfbd6c763590d6f969d9`) contiene geometría y población 2025. La configuración anterior no declaraba `source_section_year` ni `source_population_year`, por lo que el M01 actual fallaba antes de consumir el paquete (`Falta meta.source_population_year acreditado`). La configuración 1.0.1 declara ambos años como 2025.

Se ejecutó M01–M03 en `/private/tmp` sobre el mismo paquete, con la configuración anterior y la candidata. M01 produjo 3.515 CUSEC, cero filas sin población y 5.425.182 habitantes en ambos casos. La identidad y la población por CUSEC coinciden exactamente; SHA-256 de la lista ordenada de identidades: `bdece2fdc0af7e0aa5e7d03788c8b694691a98ccb567f6941280c7cd9b7d4913`.

| Métrica | EPSG:3035 anterior | EPSG:25830 candidato |
|---|---:|---:|
| M02 aristas geométricas | 9.722 | 9.724 |
| Puentes contractuales | 2 | 2 |
| M03 nodos | 3.515 | 3.515 |
| M03 aristas | 9.724 | 9.726 |
| Componentes globales | 1 | 1 |
| Nodos aislados | 0 | 0 |
| Solapamientos positivos | 74 | 68 |
| Solapamientos > 1 m² | 3 | 0 |
| Máximo solapamiento | 6,625263814 m² | 0,225482904 m² |

Las dos aristas nuevas son `4616401004/4620701007` y `4619401013/4624404012`. Ambos pares ya comparten frontera lineal en la geometría original EPSG:4326; EPSG:3035 produce solapes de 3,627476891 m² y 6,625263814 m² y los excluye según el límite de 1 m². EPSG:25830 conserva el contacto lineal y no supera el límite. No hay aristas retiradas. Una regresión con las geometrías oficiales exactas de esos cuatro CUSEC verifica que el consumidor M02 excluye ambos pares en 3035 y los admite en 25830.

Se mantienen `min_shared_border_m=1.0`, `max_precision_overlap_area_m2=1.0`, `buffer_m=0.0` y `simplify_m=0.0`. No se usaron `make_valid`, buffer, snap, densificación ni edición de vértices.

## Interpretación y límites

El cambio corrige un artefacto de reproyección y recupera dos contactos lineales presentes en la fuente. M01, M02 y M03 pasan con EPSG:25830 y mantienen identidad, población y conectividad global. No se ejecutaron M04–M06, no se promovió un producto territorial ni se emitió receipt territorial; por tanto, este resultado **no** cambia las puertas F10 ni declara Valencia `CLOSED`. Las cuatro geometrías inválidas del universo 2023 permanecen como evidencia histórica separada y no se reparan aquí.

El experimento M02 completo de 2023 se conserva en el checkpoint local F10: SHA-256 `ddc619fc771a992f05b78ebb150d18cb9765c66fddf82bdddb64f7e80b472b19`; revisión independiente acotada `PASS`. La prueba 2025 de esta entrega es adicional, separada y no cambia el estado formal de #269.
