# DDD — Validación experimental de tres oportunidades de Nacho

Versión 1.0.0 · 10-10-2026 · Ejecutor técnico; Work decide la integración.

Esta entrega añade mediciones a la investigación histórica ya cerrada. No repite su inventario. Se ejecutaron los tres experimentos, con seis mediciones de construcción, doce ejecuciones de motores existentes, una comprobación negativa de inicialización y pruebas aisladas del ensamblador y de las funciones de visualización. No se modificó producción ni se autoriza ninguna integración con este informe.

| Experimento | Decisión | Alcance demostrado |
|---|---|---|
| 1. Contracción municipal | **SIN_VENTAJA_DEMOSTRADA** | DDD obtiene 193 nodos frente a 320 con el esquema histórico adaptado; éste subdivide unidades indivisibles actuales. |
| 2. ReCom frente a canónico | **MEJORA_DEMOSTRADA** | En los fixtures y configuraciones ensayados, ReCom mejora población en B y compactación mediana en A/B; consume bastante más tiempo. |
| 2. Aplicación a reparación A2 | **SIN_VENTAJA_DEMOSTRADA** | Todos los casos comparados parten de soluciones duramente válidas; A2 no necesita activarse. ReCom rechaza la baseline negativa. |
| 3. Diagnóstico de alternativas | **MEJORA_DEMOSTRADA** | El ejemplo añade límites, causas por distrito y explicación de selección a candidatos existentes. No demuestra mejora del ranking ni usabilidad del visor. |
| 3. Renderizado y usabilidad | **NO_EVALUABLE** | Chrome no pudo arrancar por `bootstrap EPERM` del sandbox; JavaScriptCore comprobó lógica y HTML, con DOM/MapLibre simulados. |

## Identidad, entorno y alcance

Worktree `/Users/macbookpro/Desarrollo/DDD-distritos-autonomicos`, rama `codex/distritos-autonomicos`, HEAD `42163cd8cebd120db9ab9fd1329c32ccdd87cf36`. El HEAD por sí solo **no identifica todo el código ejecutado**: ya existían cambios locales A2 y otros nueve paths. [baseline.json](mediciones/baseline.json) fija su estado y bytes iniciales; los resultados de cada ejecución identifican los SHA de las fuentes realmente cargadas. Esos cambios se conservaron.

Se utilizó el entorno **ya existente** `/private/tmp/madrid-gerrychain-venv/bin/python`: Python 3.11.4, macOS 11.7.11 x86_64, GerryChain 1.0.0, GeoPandas 1.1.4, Shapely 2.1.2, NetworkX 3.6.1, pandas 3.0.5, PyYAML 6.0.2, pyproj 3.7.2. [entorno.json](mediciones/entorno.json) conserva el sondeo. No se instaló ninguna dependencia. `PYTHONHASHSEED=0` y `PYTHONDONTWRITEBYTECODE=1` se aplicaron sólo a los procesos de prueba. JavaScriptCore procede del framework instalado de macOS.

Todas las escrituras de experimentación se hicieron en `/private/tmp`; esta carpeta contiene copias de la evidencia y la documentación nueva. No hubo commits, push, PR, workflows, publicación, descargas de fuentes, ejecuciones `00`/`01`, M04/M05 territoriales completos ni cambios de contratos o resultados certificados. La comprobación final de conservación y el manifiesto de entrega se adjuntan separadamente. La revisión independiente se refiere exclusivamente a esta entrega.

**Resultados nuevos** son los tiempos, memoria, conteos, integridad y salidas de los motores registrados aquí. **Evidencia histórica reutilizada** son los fixtures, asignaciones y reportes anteriores y el diseño de contracción y visualización de Nacho ya documentado. **Hipótesis** son las extrapolaciones a territorios mayores y las propuestas de integración. El 28,6 % histórico de Murcia no se usa como medición nueva.

## Experimento 1 — Contracción municipal

### Fixture y SHA-256

Se reutiliza el archivo ya disponible `/private/tmp/ddd-rioja-M05.zip`, procedente de la ejecución histórica DDD `37473252569`, commit de fuente `b9244a523d54016e4364fc0eab19200571aeb336`. Su referencia está en `tests/fixtures/m05_rioja_37473252569.json`. Sólo se extrajeron entradas congeladas; no se ejecutó aquel territorio.

| Entrada | SHA-256 |
|---|---|
| Archivo histórico completo | `a949dd2a2ac6e187ccf30f4952073f9490dfa76cca09180c8cb46cf1c3c30fd4` |
| [M03 graph.json](mediciones/fixture-e1/graph.json) | `24d58f7a853fc8ed99a0f7b4b482cb6cb2726747f34b35e07899a6c42ffbf90f` |
| [M04 m04.zip](mediciones/fixture-e1/m04.zip) | `576b36dc5066fdfefbc64b7bc42d58dfba4b5145709867ddf55bd3bc4cd174ae` |
| [M04 m04-report.json](mediciones/fixture-e1/m04-report.json) | `24ab5caebb55b9edb9635fc2cb35346f49949c606e048ca1dcb40e85f39faada` |

Universo: 343 secciones, 174 municipios, población 322.282, K33, provincia26; 193 unidades DDD y 19 distritos urbanos cerrados. Se conserva la población M03 y el campo `POP_2023` del M04, aunque el nombre histórico del artefacto aluda a 2025. No se presenta como fuente oficial actual. Objetivo T=9.766,121212; floor=7.812,896970; cap=17.090,712121; tolerancia fina=1.171,934545. Ambas alternativas usan el mismo universo, población y K.

### Algoritmos y medición

[contraccion.py](mediciones/contraccion.py) implementa de forma independiente la **regla conceptual** ya acreditada de Nacho: municipio con P<T se agrega; municipio con P≥T conserva secciones. No copia código histórico ni elimina islas, ni recalcula K por redondeo. Agrega población/geometría y conserva una relación sección→nodo. Construye el grafo con `Graph.from_geodataframe(adjacency='rook')` de GerryChain **1.0.0**, no con la versión histórica 0.2.12; por tanto mide el esquema adaptado, no el rendimiento del entorno original de Nacho.

DDD ejecuta la función actual `ddd_core/m05_gerrychain_strategy.py::prepare_problem` sobre el `ddd_unit_id` congelado: cociente del grafo M03, caché geométrica, componentes y validación de baseline. Contrato derivado exactamente del reporte M04, disciplina municipal/provincial y preservación urbana activadas; EPSG:3035 y borde compartido mínimo 1 m. No se reconstruye M02/M04.

Tres procesos nuevos por alternativa, timeout30 s/proceso, umbral observado de RSS640 MiB. Importación, lectura y reproyección comunes preceden al cronómetro. La verificación independiente sucede después. `tracemalloc` mide asignaciones Python del tramo; el pico RSS incluye importaciones, fixture y bibliotecas nativas. **640 MiB no es un límite duro aplicado a la memoria GIS**: se registra y verifica el pico. Ninguna ejecución lo superó.

### Resultados nuevos

| Métrica | Esquema Nacho adaptado | DDD actual |
|---|---:|---:|
| Secciones originales | 343 | 343 |
| Nodos resultantes | 320 | 193 |
| Reducción frente a secciones | 6,706 % | 43,732 % |
| Aristas | 863 | 509 |
| Municipios conservados | 174 | 174 |
| Municipios con varios nodos | 6 | 5 |
| Tiempo mediano del tramo medido | 3,152183 s | 1,579897 s |
| Rango del pico RSS por proceso | 116.96–118.54 MiB | 119.04–121.10 MiB |
| Pico Python mediano | 1.269.387 B | 4.558.064 B |
| Unidades DDD subdivididas por el nuevo esquema | 24 | 0 |
| Unidades urbanas cerradas entre las subdivididas | 19 | 0 |
| Error poblacional máximo por nodo | 0 | 0 |
| Diferencia geométrica por nodo y global | 0 m² | 0 m² |
| Aristas extra frente al cociente M03 del esquema | 1 | 0 |
| Aristas M03 ausentes en el grafo del esquema | 0 | 0 |

[e1-results.json](mediciones/e1-results.json) conserva las seis mediciones, RSS exacto, configuración y comandos. Universo completo, población total y relación municipio→sección→nodo se conservaron en todas. Geometría verificada mediante diferencia simétrica y concordancia con área/perímetro de la caché DDD. Varios nodos municipales **no equivalen** a municipios divididos entre distritos; este experimento no genera distritos. Tampoco afirma que se hayan dividido realmente los 19 distritos cerrados: demuestra que la regla histórica separa sus unidades en nodos proposables y necesita otra protección.

Los tiempos no son etapas homólogas: DDD reutiliza M03 y añade preflight/cachés; Nacho recompone la adyacencia geométrica. El coste previo de construir M03 no se mide. La arista adicional tiene causa no determinada. No se puede afirmar equivalencia topológica, una aceleración del pipeline completo ni ahorro de memoria: DDD utiliza más memoria Python en esta prueba.

**Decisión: SIN_VENTAJA_DEMOSTRADA.** No aparece una granularidad útil ausente de DDD en este fixture. DDD ya agrega con mayor reducción y conserva unidades/urbanos cerrados. Adoptar directamente la regla P<T degradaría la indivisibilidad, aunque conserve población y superficie. Recomendación: mantener `ddd_unit_id`; cualquier futura optimización de construcción/caché debe operar sobre esas mismas unidades y aristas acreditadas. No hay integración nueva que recomendar a partir de esta medición.

## Experimento 2 — ReCom y M05 canónico

### Fixtures congelados y SHA-256

Se utilizan **dos asignaciones iniciales existentes** A (filas) y B (columnas), con la misma matriz poblacional del experimento anterior de selección. No son dos territorios distintos. Fuente `docs/AUDITORIAS/NACHO_2026-10-10/experimentos/results.json`, SHA `3ef8b107c33fa923301fd56df1be83a82d0e8a726069fd54efa678d2a152e684`.

```text
950 100  50  50
 50 800  50  50
 50 150 700  50
 50  50 100 750
```

Dieciséis cuadrados de 1.000×1.000 m en EPSG:3035, anclados en (4.320.000,3.210.000), 24 aristas ortogonales, una provincia01; cada sección es también municipio, unidad y comarca. P4000, K4, T1000. No hay geometrías multipartes, islas ni distritos urbanos cerrados. Esas restricciones se conservan en el motor pero **este fixture no ejercita sus casos difíciles**; comarca y fragmentación son controles triviales, no pruebas de mejora.

| Entrada | SHA-256 |
|---|---|
| Grafo común A/B | `be5bc9c070499f24d610ee68778c2eb3f29e6ad028e69952aaeaf6c069f7f909` |
| A initial.geojson | `f7d85941a22d0671030c87f587dd8931391adeb63d3f99e991b0ccb05083e53d` |
| A frozen.json | `009d8a8a861cf8bf71da6fc9311ebce63b1235f4fc46c05badf1b37a9d74028f` |
| B initial.geojson | `e642ea246895d44afe6b771a33f93260573313837312b34b0cc977d570b6ae37` |
| B frozen.json | `4e9bdb7be6b1e5c69e5a3263aa87a158c7b53f345a5cc96fb3f7056bb7e79cf8` |

Entradas completas en [fixture-e2](mediciones/fixture-e2/); se verifica la identidad de las asignaciones históricas antes de congelar los GeoJSON métricos. El cambio de escala/CRS corresponde a un fixture sintético explícito; no utiliza fuentes territoriales nuevas.

### Motores, contrato y presupuestos exactos

Canónico: wrapper actual `modulos/05_optimizar_distritos.py::main`, motor real `ddd_core/m05_opt_engine_v741.py::main`. Se carga el código local actual, incluido el módulo A2, pero no se altera. ReCom: `ddd_core/m05_gerrychain_strategy.py::run_from_paths`, portfolio y `_run_seed` reales, selección/materialización existentes; no es una reimplementación de ReCom.

Contrato idéntico en cada pareja: K4, P4000, floor800, cap1750, reparto provincial01→4, contigüidad topológica y física, unidades indivisibles y disciplina municipal. La banda ±12 % es objetivo fino, **no restricción dura** en estos motores; no se ha cambiado el contrato de producción. Ambas salidas están además dentro de esa banda. El laboratorio visual del experimento3 conserva su banda dura anterior ±20 % y no se confunde con ésta.

Semillas17/29/43, seis parejas. Por ejecución: máximo10 s en motor mediante alarma, timeout20 s de subprocess y verificación de pico RSS≤640 MiB después de ejecutar. Canónico: `greedy_moves_limit=100`, `anneal_iters=1000`, `anneal_seed_offset=0`, `swap_polish_max=0`; pesos originales out0,01/max0,05/churn0,0016, temperatura0,02→0,0005. No se sobrescriben parámetros de reparación poblacional A2. Los YAML efectivamente consumidos están junto a cada resultado.

ReCom: `steps_per_seed=1001` (inicial+1000 transiciones), `seed_count=1`, `seed_base=seed−1`, `proposal_epsilon=.12`, `population_band=.005`, `max_bipartition_attempts=50`, `comarca_surcharge=0`, `metric_crs='EPSG:3035'`, `min_shared_border_m=1`, `require_pythonhashseed_zero=True`. Cada `params.json` guarda el resto de valores efectivos.

**Se igualan topes y entradas, no trabajo ni tiempo consumido.** Un intento SA no cuesta lo mismo que ReCom; canónico añade hasta100 movimientos greedy. Ninguno se fuerza a agotar los10 s. No se demuestra superioridad por segundo/CPU ni se usa una ejecución territorial externa como control.

[comparar_m05.py](mediciones/comparar_m05.py) observa el canónico con `sys.settrace` en sus incrementos reales y ReCom mediante llamadas al ranking, devolviendo su valor original. No cambia selección, aceptación ni código fuente. Se conserva la traza y se contrasta el conteo con los informes de los motores. Tiempo incluye I/O e instrumentación; RSS incluye imports y baseline preparada común; pico Python incluye retención de trazas, excluye memoria GEOS nativa. Estos picos no son una estimación limpia de memoria de producción.

### Resultados nuevos por semilla

Tabla numérica completa insertada a continuación a partir de [e2-results.json](mediciones/e2-results.json). “Únicos” cuenta estados observados; la segunda cifra elimina permutaciones de etiquetas. Son estados explorados, no candidatos finales todos exportados. Hold SA y self-loop ReCom tienen denominadores distintos; SA sin intentos se muestra como no aplicable.

| Baseline | Motor | Semilla | Máx. desv. | RMS | PP mediana | Únicos etiquetados / físicos | Hold SA o self-loop / transiciones | Tiempo s | RSS MiB |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | Canónico | 17 | 0.0 % | 0.000 % | 0.469494 | 47/47 | 944/1000 SA | 0.606944 | 108.32 |
| A | ReCom | 17 | 0.0 % | 0.000 % | 0.663225 | 711/314 | 207/1000 ReCom | 7.556245 | 103.32 |
| A | Canónico | 29 | 0.0 % | 0.000 % | 0.469494 | 45/45 | 935/1000 SA | 0.613664 | 108.24 |
| A | ReCom | 29 | 0.0 % | 0.000 % | 0.663225 | 674/311 | 222/1000 ReCom | 7.731357 | 103.25 |
| A | Canónico | 43 | 0.0 % | 0.000 % | 0.565487 | 54/54 | 932/1000 SA | 0.607222 | 108.16 |
| A | ReCom | 43 | 0.0 % | 0.000 % | 0.663225 | 658/279 | 218/1000 ReCom | 7.543765 | 103.30 |
| B | Canónico | 17 | 10.0 % | 6.124 % | 0.502655 | 3/3 | NO_APLICA (0 intentos) | 0.300211 | 108.51 |
| B | ReCom | 17 | 0.0 % | 0.000 % | 0.663225 | 695/293 | 204/1000 ReCom | 7.397688 | 103.28 |
| B | Canónico | 29 | 10.0 % | 6.124 % | 0.502655 | 3/3 | NO_APLICA (0 intentos) | 0.296488 | 108.32 |
| B | ReCom | 29 | 5.0 % | 5.000 % | 0.726057 | 670/280 | 231/1000 ReCom | 7.572411 | 103.32 |
| B | Canónico | 43 | 10.0 % | 6.124 % | 0.502655 | 3/3 | NO_APLICA (0 intentos) | 0.298715 | 108.63 |
| B | ReCom | 43 | 0.0 % | 0.000 % | 0.663225 | 677/273 | 202/1000 ReCom | 7.461407 | 103.33 |

En las **12/12 ejecuciones**: cero infracciones duras finales e intermedias observadas; K4 y P4000 exactos; 16 secciones/geometrías originales conservadas; 4/4 distritos contiguos topológica y físicamente; cero municipios divididos y retención comarcal1. La validación independiente del harness comprueba universo, geometría exacta, límites y conectividad, además del hard gate común. No sustituye M06 territorial ni certificación. Con sólo tres semillas por baseline se acredita repetición del beneficio en este fixture, no robustez territorial general ni reproducción bit a bit en otro runtime.

Medianas de tiempo: A canónico0,607222 s/ReCom7,556245 s; B canónico0,298715 s/ReCom7,461407 s. ReCom consume aproximadamente12,4× y25,0× el tiempo respectivo. Picos Python medianos: canónico1.618.020/1.617.958 B; ReCom2.089.307/2.090.273 B (A/B). El RSS máximo canónico es113.909.760 B y ReCom108.347.392 B, con el alcance de memoria antes descrito. No se demuestra aceleración ni ventaja de memoria del algoritmo aislado.

En A ambos alcanzan desviación máxima0 %; ReCom alcanza PP mediana0,663225 en las tres semillas frente a0,469494/0,469494/0,565487. En B el canónico queda en máximo10 % y RMS6,124 %; ReCom obtiene máximos0/5/0 % y RMS0/5/0 %. PP mediana de ReCom0,663225/0,726057/0,663225 frente a0,502655. El mínimo PP generalmente permanece0,436332: la mejora de la mediana **no significa mejora uniforme de cada distrito**.

La causa observada en B es concreta: el canónico ejecuta dos movimientos greedy y **cero intentos SA**, con `active_provinces=[]`, al partir dentro de ±12 %. Su activación por provincias fuera de tolerancia está en `m05_opt_engine_v741.py:247` y el bucle observado en295. ReCom sigue explorando una baseline válida y encuentra mayor equilibrio. No se atribuye el resultado a un defecto demostrado de A2.

### Límite de aplicación a A2: prueba negativa ejecutada

[baseline_invalida.py](mediciones/baseline_invalida.py) reutiliza también C, ya existente y duramente inválido. GeoJSON SHA `fa19cf5a27e9ce64cb5a70738260adb386d5429a1c19814ed02db80b4f920c40`; grafo común anterior; configuración SHA `aa859d92531163dff6cc5efc3bdb77599cb92b5c249cf8c40bec4abf8e956bdc`. El `prepare_problem` real rechaza C en0,186370 s con `BaselineValidationError: Formación inicial viola restricciones duras: population_cap:0, population_floor:1`. **No se ejecutó cadena**. [e2-negative-baseline.json](mediciones/e2-negative-baseline.json) registra la prueba.

En las doce ejecuciones comparadas, `population_repair.activation=NOT_NEEDED` y cero infracciones duras iniciales. Esta comparación no mide búsqueda, poda, reparación ni presupuesto original A2. ReCom existente requiere baseline válida y no es una solución demostrada para su problema de factibilidad.

**Decisión del experimento: MEJORA_DEMOSTRADA**, limitada al refinamiento de soluciones duramente válidas en estos fixtures, configuraciones y topes. **Decisión para cambiar A2: SIN_VENTAJA_DEMOSTRADA**. Recomendación a Work: considerar una fase opcional de refinamiento posterior a factibilidad, utilizando el motor ReCom ya existente o estudiando la activación canónica dentro de banda. Primero autorizar un control con tiempo realmente gastado comparable y un fixture congelado más rico, sin alterar A2/A3; después exigir las validaciones independientes correspondientes. No sustituir por defecto el motor ni ampliar presupuestos A2 por esta evidencia.

## Experimento 3 — Selección y visualización de alternativas

### Entradas y configuración

Se reutilizan A/B/C y los reportes de selección **existentes**. No se generan nuevas soluciones ni se repite su benchmark algorítmico. Fuente `results.json` y SHA anterior; plan SHA `b8e840f6e2acfbc5f0bdd72c5fe08057e3351305b777dcee8177af4dbbb94441`; resumen original SHA `93b1cff2b8c5a2a1e5e78f5fdd6316a8fdb558ebd69100eccc0b2556796d6712`.

Asignaciones originales, convención SHA de lista JSON del laboratorio: A `b2589fa8b94eb36ba57f00fdcdb5cab38248f11b760f4848e191fe7a5ec87f83`; B `06bd071b587ce8bea12912663ad6392c76d22b87c9aa5d4d73adbca29c67979e`; C `2b212d9089dbb303e0f5c343e3508122d35126665b3f26faaf83283b21ab8987`. [provenance.json](visualizacion/provenance.json) registra SHA de cada reporte original y configuración completa. Esta convención no se confunde con SHA de archivos ni con hash normalizado sin etiquetas del experimento2.

Contrato visual original: K4/P4000/T1000, floor800/cap1750, **banda dura±20 % del laboratorio**, municipios indivisibles, perfil`controlled`, semilla metadata0. Copias de reportes enriquecidas sólo con assets y campos diagnósticos; no cambian objetivos, hard gate ni asignaciones. Se llama a `ddd_ensemble.ensemble_assembler.assemble` y `gallery.build_gallery` existentes. Se reconstruyen16 cuadrados locales por alternativa. El embedding web de1 m/unidad cerca de(−3,7;40,4) se documenta como ilustración sintética, nunca como geografía oficial de Madrid. Las métricas conservan el plano local original.

### Capacidades comprobadas y aportación

| Capacidad | Galería DDD actual | Visor productivo actual | Ejemplo aislado |
|---|---|---|---|
| Varias soluciones | Dos mapas A/B, filtro perfil/Pareto | Selector cambia la alternativa en un único mapa | Dos SVG A/B del mismo universo |
| Población/desviación | Métrica agregada por candidato | Población, objetivo y desviación por distrito | Tabla de los12 distritos A/B/C |
| Límites | No floor/cap estructurados visibles | No consumidos en `districtHtml` | Floor, cap y banda explícitos |
| Municipios | Sin lista ni conteo de splits | Lista de municipios cuando existe el campo | Conteo acreditado0; coincide municipio/unidad/sección |
| Incumplimientos | C inválido en JSON, sin causas visibles en tarjetas | Estado auditado y motivos **globales** ya visibles | Causas poblacionales por distrito de C |
| Ranking | Pareto y shortlist, selección responsable y justificación | Sin explicación de dominancia A/B en la ficha probada | Explicación B/A y trazabilidad de objetivos |

Referencias: `ddd_ensemble/gallery.py:15–18,29`; `visor/app.js:69–77` para población/objetivo/desviación/lista y `87–90` para motivos globales; `visor/index.html:16,20,25–26` para selector/mapa/ficha/estado. El complemento [VISOR_COMPARACION.md](visualizacion/VISOR_COMPARACION.md) conserva líneas, SHA y la prueba pura del visor. **No se afirma que DDD carezca de población, selección responsable o auditoría.**

De Nacho se reutiliza el concepto histórico ya acreditado de capas simultáneas provincia/municipio/sección/unidad y seguimiento del residuo poblacional por iteración. La carencia útil aquí es unir esos datos con tablas, límites y explicación de selección. No se reanalizó su repositorio ni se incorporó Kepler/Excel como dependencia. Códigos postales y capas oficiales adicionales no están disponibles en este fixture y no se fabricaron.

### Resultados nuevos y límites de ejecución

El ensamblador mantiene exactamente Pareto[B], shortlist[B], inválidos[C]. Dos candidatos admisibles, dos assets de16 secciones; C queda excluido de selección y de assets promocionables. Su rechazo sólo aparece en el diagnóstico. B reduce el máximo del15 % al10 % frente a A; los demás objetivos usados en la comparación de dominancia mantienen valores congelados iguales. L1 preferiría A (300 frente400), pero ese criterio no es el ranking vigente. El `assignment_delta=0` congelado del reporte no es una medición de churn real de una cadena.

La evidencia funcional añade12 filas poblacionales, ambos límites, las cuatro causas de incumplimiento originales de C (`population_cap:0`, `population_floor:1`, `population_tolerance:0`, `population_tolerance:1`), cero splits acreditados y explicación de la elección sin cambiar scores. [diagnostico.html](visualizacion/diagnostico.html) funciona como artefacto SVG/HTML sin CDN; [comparison.csv](visualizacion/comparison.csv) permite exportar los mismos datos.

Python: ensamblado0,001143 s, construcción galería0,002677 s, ejecución total0,073120 s, RSS43.626.496 B. JavaScriptCore:0,017930 s, RSS4.599.808 B, dos tarjetas, filtro Pareto[B], selección simulada B y lectura de dos assets16; prueba pura `districtHtml` para12 casos:0,039 s, RSS≈5,20 MB. Los campos población/objetivo/desviación/lista aparecen; floor/cap/conteo de splits/causas por distrito suministrados no aparecen. Detalle numérico y aserciones en [validation_results.json](visualizacion/validation_results.json), [dom_simulation_results.json](visualizacion/dom_simulation_results.json) y [visor_check_results.json](visualizacion/visor_check_results.json).

Las pruebas JS usan el código real con DOM/MapLibre simulados o funciones puras. Timeout60 s, CPU55 s y límite DATA640 MiB en esos procesos; no acceso a red. Una solicitud de selección se captura en memoria del harness; no se escribe en el registro productivo ni se promueve ningún territorio. No equivalen a render WebGL, accesibilidad, CSS o usabilidad.

El intento inicial de Chrome138 terminó por `crashpad/bootstrap EPERM`; el log [gallery_dom.stderr.log](visualizacion/gallery_dom.stderr.log) documenta el bloqueo real. No se reintentó ni se escaló. **Render y usabilidad: NO_EVALUABLE**. Procedimiento posterior, en un entorno con navegador autorizado: servir exclusivamente la copia de galería/assets, cargar MapLibre ya disponible conforme a la política del entorno, ejecutar los mismos controles A/B/Pareto/selección y capturar mapa/DOM; abrir el diagnóstico offline y verificar tablas y toggles. El [README](README.md) incluye el comando exacto para la captura del diagnóstico sin CDN. No se requieren nuevos territorios ni instalar nada en este worktree.

**Decisión: MEJORA_DEMOSTRADA exclusivamente de información diagnóstica.** Ranking existente: SIN_VENTAJA_DEMOSTRADA para sustituirlo; ya selecciona y excluye correctamente. [ESPECIFICACION.md](visualizacion/ESPECIFICACION.md) define campos, ledger, causas, comparación y aceptación. Recomendación: autorizar primero un export diagnóstico aislado con explicación y límites, después considerar su presentación en visor/galería con prueba real de navegador. No introducir otra biblioteca cartográfica para los campos demostrados.

## Propuesta a Work y riesgos

| MEJORA | ORIGEN NACHO | COMPONENTE DDD | BENEFICIO | EVIDENCIA NUEVA | COSTE | RIESGO | DECISIÓN |
|---|---|---|---|---|---|---|---|
| Tabla de alternativas, límites, causas y ledger | Comparación por capas/estadísticas | Diagnóstico ensemble; después visor | Explicar selección y rechazo | E3:12 filas, C excluido, pruebas JS reales sin render | Bajo diagnóstico; medio UI | Confundir límite duro/fino, promover inválido | MEJORA_DEMOSTRADA informativa; proponer primero, pendiente Work |
| Refinamiento opcional ReCom de baseline válida | ReCom y exploración | G05/ensemble existentes | Mejor población B y PP mediana A/B | E2:6 parejas, cero fallos duros | Mayor CPU:12,4–25× tiempo observado | Extrapolar sintético, cambiar prioridades, mezclar etiquetas | MEJORA_DEMOSTRADA acotada; ampliar evaluación sólo con autorización |
| Refinar canónico aun dentro de banda | Búsqueda continuada histórica | Estrategia de refinamiento posterior a factibilidad | Evitar parada temprana observada en B | SA0 en B; ReCom mejora3/3 | Medio; beneficio por CPU no medido | Interferir A2/A3 si se ubica mal | Hipótesis; propuesta fuera de producción, pendiente Work |
| Contracción P<T histórica | Agregación híbrida | M02/M03/M04, `ddd_unit_id` | Ningún beneficio nuevo acreditado | E1:320 vs193 nodos;24 unidades subdivididas | Coste sin beneficio demostrado | Atomicidad y19 unidades cerradas | SIN_VENTAJA_DEMOSTRADA; mantener DDD |
| ReCom como reparación A2 | Inicialización válida histórica | A2 | No demostrado | NOT_NEEDED en12; C rechazado antes de cadena | No estimable aquí | Baseline inválida, duplicación del frente | SIN_VENTAJA_DEMOSTRADA; no tocar A2 |

Orden recomendado: diagnóstico aislado → autorización de evaluación de refinamiento con coste realmente comparable y fixture con municipios multisección/urbanos/discontinuidades → decisión de integración y validación independiente. La contracción actual debe permanecer; A2/A3 y N1/N2 quedan fuera. Las tres oportunidades están evaluadas con las limitaciones concretas anteriores, sin convertir las hipótesis restantes en resultados.

## Reproducción y trazabilidad

Los comandos están en [README.md](README.md). Se copian los scripts y entradas a otra carpeta temporal para no sobrescribir evidencia congelada. Los JSON registran comandos ejecutados, semillas, configuraciones efectivas, trazas y hashes. `sumarizar.py` deriva las tablas y decisiones de los doce resultados sin volver a ejecutar motores.

Se conservan también fallos iniciales del **harness**, corregidos antes de las mediciones válidas: tipo de `province_districts`, acceso a un atributo inexistente de `PreparedProblem`, convención SHA lista/dict y alcance lexical de helpers JS. No son fallos de producción ni resultados negativos de los algoritmos. El bloqueo Chrome permanece como tal. No se repitieron los experimentos históricos ya acreditados: se ejecutaron la comparación controlada y los checks de visualización nuevos.
