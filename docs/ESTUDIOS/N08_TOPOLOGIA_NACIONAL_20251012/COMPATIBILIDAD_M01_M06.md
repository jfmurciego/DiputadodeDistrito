# Compatibilidad diagnosticada Congreso M01–M06

Versión: 0.1.0. Nombre: interfaces nacionales aisladas. Fecha: 2026-10-12.
Alcance: preflight, sin ejecutar pipeline ni generar distritos. Estado: candidato N08.
Cambios: adaptador y pruebas nuevos. Motivo: comprobar consumidores reales.
Origen: nuevo documento, sin predecesor.

`ddd_core/congreso_preflight_adapter.py` valida productos de diagnóstico sin construir una configuración ejecutable. Mantiene `generation_authorized=false`, las 52 cuotas y K=407; rechaza identidad autonómica y discrepancias de edición/hash. No modifica el motor común ni las fuentes. El hash de contacto declarado requiere reproducción geométrica independiente: su formato no demuestra contacto. Los componentes de nodos seccionales no acreditan componentes de tierra cuando una sección MultiPolygon contiene partes separadas.

| Módulo real | Entrada/salida comprobada | Evidencia | Estado y límite |
|---|---|---|---|
| M01 `01_preparar_base_territorial.py` | `CUSEC`, `POB_2025`; `normalize_section_key`; años 2025 y hashes vinculados | Prueba directa del normalizador y validación del adaptador | PASS del contrato de identidad; ejecución productiva no realizada. La unión y cobertura nacional corresponden al builder N08. |
| M02 `02_construir_adyacencias.py` | `_relation_ok`, contacto, frontera métrica y solapamiento | Geometrías sintéticas: frontera admitida, punto rechazado, solapamiento rechazado | PASS de interfaz geométrica. No se hereda el umbral autonómico. Longitud estrictamente positiva y solapamiento cero en el producto raw; sensibilidad declarada separadamente por builder. |
| M03 `03_construir_grafo.py` | `build_nodes`, `component_sets`, nodos `id/pop/CPRO/CUMUN`, aristas `u/v` | Funciones reales con dataframe sintético; componentes con aislados | PASS de contrato e identidad; prueba nacional adicional en artefactos builder. El grafo seccional no sustituye el análisis de partes físicas. |
| M04 `04_generar_semillas.py` y `ddd_core/m04_seed_engine.py` | Grafo M03 + geometría M01 + configuración; salidas `district_id/ddd_unit_id` | Función real `_atomic_population_necessary_conditions` rechaza `K_EXCEEDS_ATOMIC_UNITS`; `hard_limits` rechaza configuración sin límites; auditor de salida sintética coteja las cuotas externas | BLOCKED: mínimo atómico, disciplina municipal, límites y discontinuidades pendientes. No ejecutar semillas. |
| M05 `05_optimizar_distritos.py` y `ddd_core/m05_population_repair.py` | Grafo, partición M04, provincia, unidades y límites | `verify_partition_constraints` real: partición sintética discontinua y municipio partido rechazados; auditor aislado corrige los huecos de límites duros y K externo mediante rechazos reproducibles | BLOCKED: falta partición permitida y política Congreso. La prueba sintética no acredita optimización ni factibilidad territorial real. |
| M06 `06_consolidar_distritos.py` | `in_geojson`, `id_field`, `district_field`, `pop_field`; composición, catálogo, resumen | Prueba real sintética de `joined_unique` conserva trazabilidad administrativa; inspección del `main` exige campos, población estricta, conservación de filas/población y K; mapper declara campos | PASS del contrato de salida sintética mediante `audit_synthetic_partition`; NOT_EVIDENCED para ejecución nacional. BLOCKED por falta de partición y política. No se ejecutó consolidación ni escritura de mapas. |

## Defectos y decisiones reproducibles

`ddd_core.config.hard_limits({}, k=5, total_pop=593623)` termina con `SystemExit: El territorio no declara [...]`; no admite heredar límites de otro territorio. Además, el motor calcula target como `P_i/K_i`, mientras la referencia institucional es 120.000. Para Cantabria `593623/5=118724.6`; la diferencia es -1.062833 %. Debe decidirse expresamente si límites se expresan sobre referencia fija o promedio provincial antes de producir una configuración. No se cambia el motor para resolverlo por inferencia.

`_atomic_population_necessary_conditions(['a'], {'a':593623}, k=5, floor=1, cap=600000)` devuelve `False, K_EXCEEDS_ATOMIC_UNITS`: demuestra el contrato de rechazo mediante datos sintéticos, no una imposibilidad de Cantabria.

`verify_partition_constraints` devuelve `DISTRICT_CONTIGUITY` ante dos nodos desconectados asignados al mismo distrito, y `MUNICIPAL_INTEGRITY` ante un grupo municipal indivisible repartido en dos distritos. La misma función devuelve `valid=true` aunque existan violaciones poblacionales, registradas separadamente como `hard_limits_met=false`: un consumidor Congreso deberá exigir ambas condiciones antes de admitir una entrega. Tampoco verifica por sí sola K aprobado, porque toma como conjunto esperado los distritos presentes en el estado; el adaptador de consolidación futuro deberá contrastar cuotas provinciales explícitas y exigir población/filas conservadas.

El límite necesario `n_componentes > K_i` demuestra imposibilidad bajo contigüidad física estricta, incluso si algún componente tiene población cero, pues sus secciones deben quedar cubiertas. Si `n_componentes <= K_i`, no se demuestra factibilidad. Las partes de una misma sección discontinua carecen de población desagregada acreditada: nunca repartir población entre partes por superficie ni tratar el nodo seccional como pasarela física.

## Validación

Comando dirigido: `/usr/local/Caskroom/miniforge/base/envs/ddd_aragon/bin/python -m unittest tests.test_congreso_preflight_adapter`: **37 PASS**. `git diff --check`: PASS. Sin dependencia de pytest; descubrimiento canónico unittest. Entorno definitivo y regresiones nacionales/autonómicas se consignan en el log general N08. No se ejecutan M04–M06 ni sus entrypoints; sólo funciones puras sobre fixtures sintéticos. No se afirma compatibilidad productiva de los seis módulos ni `N08 READY`.

## Corrección aislada del contrato de salida M04–M06

`audit_synthetic_partition` sólo se invoca sobre fixtures sintéticos declarados expresamente. La salida es `SYNTHETIC_OUTPUT_AUDIT_PASS`, `institutional_policy_approved=false` y `generation_authorized=false`; conserva todos los bloqueos del contrato real. No devuelve `CONTRACT_ADMITTED` ni ejecuta los módulos. El fixture positivo usa cinco etiquetas sintéticas, cinco nodos y 593.623 habitantes; no representa una partición territorial ni cinco distritos reales de Cantabria.

El auditor exige cobertura exacta una vez por nodo, población original conservada, cuotas provinciales tomadas del contrato aprobado, barreras provinciales, contigüidad sobre las aristas físicas validadas y ausencia de pasarelas, límites numéricos explícitos finitos y positivos, mínimo atómico explícito y disciplina municipal explícita. No hereda tolerancias ni indivisibilidad; la política sintética no modifica las decisiones pendientes. Exige acreditar una sola componente de tierra por nodo y por distrito: rechaza partes físicas ausentes o múltiples, aunque el grafo seccional parezca conectado.

Las pruebas conservan los 26 casos anteriores y añaden 11 métodos. Dos reproducen los huecos reales: (1) `verify_partition_constraints` devuelve `valid=true` y `hard_limits_met=false`, pero el auditor rechaza `PARTITION_HARD_POPULATION_LIMITS`; (2) el verificador común considera válida una etiqueta única porque toma K de las etiquetas presentes, pero el auditor coteja la cuota externa cinco y rechaza `PARTITION_EXTERNAL_QUOTA_MISMATCH`. También se rechazan cobertura incompleta/duplicada/extra, población alterada, límites ausentes o infinitos, mínimo no soportado, disciplina municipal no declarada, separación municipal prohibida, evidencia física multipart ausente y partición discontinua. La interfaz de salida queda comprobada sin acreditar ejecución real ni factibilidad nacional.
