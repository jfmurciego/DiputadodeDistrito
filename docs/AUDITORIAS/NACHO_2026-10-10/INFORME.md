# Aprovechamiento integral del algoritmo histórico de Nacho

Versión: 1.0.0 · Fecha: 2026-10-10 · Frente: investigación autonómica, comparación nacional sólo conceptual. Origen: encargo de Work, referencia histórica nplaton/diputado-distrito. Estado: propuesta para decisión de Work; no autoriza integración. Documento nuevo, sin predecesor sustituido. Ejecutor: sesión Codex; experimentación y revisión separadas se identifican en el expediente.

## Resultado para Work

La arquitectura híbrida de Nacho sigue siendo útil: preservar municipios pequeños y usar secciones en los grandes reduce el problema, y separar generación de exploración permite obtener alternativas. DDD ya incorpora esa arquitectura con garantías más fuertes: identidad seccional, `ddd_unit_id`, K contractual, cuotas, núcleos urbanos cerrados, fuentes vinculadas y validación posterior. No procede sustituir M04 ni el M05 canónico por el notebook.

La investigación identifica mejoras pendientes en **identidad de la reanudación del ensemble**, **coherencia de atomicidad del adaptador de laboratorio**, **diversidad física frente a permutación de etiquetas**, y una oportunidad medida de **validación sobre el cociente de unidades** para caminos que aún trabajan sobre secciones. Las primeras dos cuentan con contraejemplos ejecutados sobre funciones DDD; la última acelera una operación sintética entre 4,33× y 17,37×, sin demostrar todavía rendimiento o calidad de ReCom. La comparación L1/máximo favorece a los selectores actuales DDD en el fixture estudiado; aplazar uniones acelera otro mecanismo entre 4,88× y 5,15×, pero esa ventaja ya está incorporada en los rankings DDD.

No se ha modificado código productivo, contratos, fuentes, resultados certificados, A1/A2/A3 ni N1/N2. Las propuestas de implementación quedan pendientes de Work. El informe distingue resultados medidos, pruebas analíticas, evidencia territorial anterior e hipótesis sin medir.

## 1. Alcance, procedencia y límites verificables

DDD estudiado: rama `codex/distritos-autonomicos`, HEAD `42163cd8cebd120db9ab9fd1329c32ccdd87cf36`, con modificaciones A2 preexistentes. El HEAD **no contiene todo el estado leído**: [manifiesto-inicio.json](manifiesto-inicio.json) fija los hashes del worktree y sus nueve rutas previamente sucias. No se trata este expediente como revisión o aprobación de aquellas modificaciones. `main` remoto consultado: `2d8508a04f9b54efa05dbb0c2ee7f1d60f81dfce`; no se atribuye el comportamiento local a ese main sin contraste.

Nacho: [árbol exacto f5d063b](https://github.com/nplaton/diputado-distrito/tree/f5d063b909e33b6ce917b670d85126fa0da92887), confirmado contra GitHub. Clon completo local `/private/tmp/nplaton-diputado-distrito`, no superficial: 17 commits, ninguna etiqueta, siete archivos actuales y ocho rutas históricas contando `data.zip`. Se leyeron los siete archivos completos y todas las versiones del notebook y los demás componentes; el inventario de árboles, hashes, celdas y parámetros está en [historial.json](historial.json). No hay README, tests, CI, licencia explícita, módulos adicionales ni salidas GeoJSON versionadas en ninguno de esos árboles. Las salidas incrustadas del notebook tienen ejecuciones parciales y contadores no secuenciales; no acreditan una campaña reproducible con la configuración final.

El ZIP histórico de 3.327.122 bytes contiene un directorio y cinco Parquet **cifrados**: provincias, municipios, distritos, códigos postales y secciones. Se inspeccionaron las cabeceras y el blob, no se descifraron sus contenidos; falta la contraseña. [archivo-historico.json](archivo-historico.json) acredita nombres, tamaños, cifrado y hash. No hay fuentes actuales acreditadas dentro del repositorio histórico. No se han reutilizado sus datos como fuentes oficiales DDD ni recuperado credenciales retiradas.

No se encontró LICENSE/LICENCE/COPYING en el historial completo. Esto impide dar por autorizado el traslado de código de Nacho: se estudian mecanismos y se escriben experimentos originales, sin copiar su implementación. La dependencia GerryChain declara BSD de tres cláusulas en [PyPI 0.2.12](https://pypi.org/project/gerrychain/0.2.12/); esa licencia no se extiende al notebook de Nacho. Los requisitos de atribución de cualquier futura reutilización siguen pendientes del material concreto elegido.

No se dispone aquí del runtime GerryChain 1.0 aislado necesario para ejecutar las cadenas DDD. No se instalaron dependencias. Se reutilizó el entorno cartográfico local para Shapely; E5 utiliza sólo biblioteca estándar. No se ejecutó el notebook histórico, una cadena ReCom, una campaña territorial ni M06 territorial nuevo. No puede afirmarse un porcentaje de éxito, diversidad estadística o ahorro territorial de un algoritmo completo.

El archivo exacto distribuido de GerryChain 0.2.12 tampoco se recuperó: las referencias de GitHub no contienen una etiqueta 0.2.12. Para explicar decisiones se contrastó código contemporáneo en [commit 6fbf342, 11-07-2019](https://github.com/mggg/GerryChain/tree/6fbf342f15851832dc3d8a0b37e8d5a9e81e7cc2), anterior a la publicación de ese paquete. Sus semánticas se etiquetan como **fuente contemporánea, no wheel 0.2.12 acreditado**. No se extrapola documentación moderna a la versión antigua.

Los planes se consultaron en `~/Desarrollo/DDD-control/planes/ddd-maestro-20261008` y `ddd-direccion-20261009`. Ese directorio es de sólo lectura en esta sesión; este expediente conserva la continuidad sin modificar estados de gobierno. La comparación estática previa de siete archivos ya cubría híbrido, ReCom, borrado de componentes, L1 y ensamblado. Se reutiliza y amplía con historial completo, rutas efectivas DDD, pruebas negativas y medidas nuevas; no se repiten Madrid, Rioja, A-OPT01/02 ni campañas de semillas.

El detalle de dependencias, estructuras, fórmulas y defaults comparados se conserva en [PARAMETROS.md](PARAMETROS.md) y [dependencias.json](dependencias.json); [verificacion-remota.json](verificacion-remota.json) acredita los SHAs consultados mediante herramientas de sólo lectura.

## 2. Referencias exactas y rutas efectivas

Las referencias `Cnn:Lm` significan celda con índice **desde cero** del notebook final y línea **desde uno** dentro de su fuente, uniendo el array JSON `source`. Son estables en el SHA histórico indicado; no son números de una exportación temporal. [Notebook exacto](https://github.com/nplaton/diputado-distrito/blob/f5d063b909e33b6ce917b670d85126fa0da92887/diputado-distrito.ipynb). Las líneas Python DDD corresponden al worktree cuyos hashes fija el manifiesto.

| Alias | Componente DDD y ancla principal |
|---|---|
| D02 | [modulos/02_construir_adyacencias.py](../../../modulos/02_construir_adyacencias.py), `_relation_ok`:61, `iter_edges`:84, `write_edges_jsonl`:157 |
| D03 | [modulos/03_construir_grafo.py](../../../modulos/03_construir_grafo.py), `build_nodes`:68, `component_sets`:81, `audit_group_components`:108 |
| D04 | [ddd_core/m04_seed_engine.py](../../../ddd_core/m04_seed_engine.py), `_protected_component_gateways`:95, condiciones necesarias:132, grupos:168, exacto:219, preflight:280 |
| D04b | [ddd_core/m04_seed_engine_v7410.py](../../../ddd_core/m04_seed_engine_v7410.py), `find_peel`:61, `grow_partition`:77, `hybrid_partition`:102, `objective`:116, `rebalance`:120, `partition_oversized_municipality`:187, `main`:204 |
| D04m | [ddd_core/m04_seed_engine_v7412.py](../../../ddd_core/m04_seed_engine_v7412.py), multistart:104, fallback:124; [m04_closed_target_cores.py](../../../ddd_core/m04_closed_target_cores.py) |
| D05 | [ddd_core/m05_opt_engine_v741.py](../../../ddd_core/m05_opt_engine_v741.py), `main`:79, límites:141, objetivo:175, annealing:247 |
| R05 | [ddd_core/m05_population_repair.py](../../../ddd_core/m05_population_repair.py), límites:26, transición dura:102, frontera:342, búsqueda ampliada:559, `repair`:731; estado A2 preexistente |
| G05 | [ddd_core/m05_gerrychain_strategy.py](../../../ddd_core/m05_gerrychain_strategy.py), contrato:75, configuración:91, `prepare_problem`:332, validación:555, físico:647, forma:750, ranking:786, semillas:852/937, portfolio:972 |
| L05 | [ddd_core/m05_gerrychain_engine.py](../../../ddd_core/m05_gerrychain_engine.py), contrato:34, adaptador:153, hash:333, validación:350, comarca:467, forma:510, score:571, selección:584, cadena:629 |
| Eplan | [ddd_ensemble/ensemble_plan.py](../../../ddd_ensemble/ensemble_plan.py), semillas:22, plan:27; [runner.py](../../../ddd_ensemble/runner.py), identidad AUTO:96, `ensure_plan`:115, `_valid_existing`:215, ejecución:256 |
| Ecal | [ddd_ensemble/statistical_quality.py](../../../ddd_ensemble/statistical_quality.py), política:38, reservoir:72, diagnósticos:101, stream:191, cadena:328 |
| Esel | [ddd_ensemble/ensemble_assembler.py](../../../ddd_ensemble/ensemble_assembler.py), objetivos:17, Pareto:28, `assemble`:47; [candidate_metrics.py](../../../ddd_ensemble/candidate_metrics.py):16 |
| Top | [ddd_core/topology_preflight.py](../../../ddd_core/topology_preflight.py), vínculo fuente:87/105, componentes:208, puentes:302; [preparar_particiones_fisicas_m04.py](../../../herramientas/preparar_particiones_fisicas_m04.py), `prepare`:50 |
| Vis | [ddd_ensemble/gallery.py](../../../ddd_ensemble/gallery.py), CRS web:52, galería:72; HTML/JS generados por `build_gallery`; `visor/` |

Ruta M04 efectiva: `modulos/04_generar_semillas.py` → `m04_seed_engine.py` → `m04_seed_engine_v7412.py` → base `v7410.py`, con postprocesado `v7411.py` y sustituciones canónicas para núcleos cerrados/pasarelas/preflight. No se tomó por canónica una versión archivada `v745` sólo por su nombre. Ruta M05 predeterminada: wrapper `modulos/05_optimizar_distritos.py` → base `m05_opt_engine_v741.py` más reparación y pulido optativo. G05 es la estrategia alternativa conectada por `procedimiento.sh`; L05/Ecal forman el laboratorio/ensemble y **no comparten todas las semánticas** de G05.

## 3. Inventario completo de mecanismos y correspondencia

Clasificaciones: `YA_IMPLEMENTADO` conserva la idea; `MEJOR_IMPLEMENTADO_EN_DDD` añade garantías verificadas; `APROVECHABLE` es una idea útil sin aprobación de implementación; `REQUIERE_EXPERIMENTO` carece de prueba suficiente; `INCOMPATIBLE` viola el contrato; `OBSOLETO` es una dependencia o mecanismo técnico sustituido. Una clasificación favorable no constituye autorización funcional.

| ID | Nacho: archivo/celda/línea o mecanismo | DDD: referencia exacta | Clasificación | Justificación |
|---|---|---|---|---|
| I01 | C10–19, lectura SQL/5 Parquet por provincia | Eplan runner:83/96; bundles y M01 | MEJOR_IMPLEMENTADO_EN_DDD | Offline útil, identidad/edición/hash esenciales; Parquet no es requisito |
| I02 | C21, prefijos provincial/municipal del identificador | D03:68/93; L05:128/153 | MEJOR_IMPLEMENTADO_EN_DDD | ID oficial conservado, duplicados y campos administrativos validados |
| I03 | C23 recorta provincia; C25 usa `census_section` bruto | D03:124; G05:332 | INCOMPATIBLE | El histórico depende de caches previamente provinciales sin gate de universo |
| I04 | C25:L1, `dissolve` municipal y suma | D04b:204; G05:332 | YA_IMPLEMENTADO | Agregación por unidad contractual conservando ledger seccional |
| I05 | C26:L1 pequeño `< target`, C27 grande `>= target` | D04b:204; límites contractuales | MEJOR_IMPLEMENTADO_EN_DDD | Nacho tiene frontera distinta y no acredita que sea óptima; DDD no puede alterar umbral por tiempo |
| I06 | C29–30, mezcla municipios/secciones | D04b:204; G05:332 | MEJOR_IMPLEMENTADO_EN_DDD | `ddd_unit_id` explícito, U/R, expansión y urbano cerrado |
| I07 | C25 suma atributos junto con población | D03:68; G05:332 | INCOMPATIBLE | Sumar códigos/atributos no conserva sus semánticas; separar agregadores |
| I08 | C33:L1 Graph desde geometría disuelta | D02:84, D03:124, G05:332 | MEJOR_IMPLEMENTADO_EN_DDD | Cociente deriva del M03 acreditado, evita reconstruir autoridad topológica |
| I09 | C34:L6–11 borra isla pequeña | Top:208/302; D03:81 | INCOMPATIBLE | E2 demuestra pérdida de universo/población; no reintroduce islas en salida |
| I10 | C35:L5–12 busca componente por cada nodo | D03:81; D04b:50 | MEJOR_IMPLEMENTADO_EN_DDD | Una pasada O(V+E), sin repetir O(V(V+E)) ni orden de sets |
| I11 | C38:L12–14 omite componentes pequeños | Top:208; D04b:204 | INCOMPATIBLE | Conservación total y decisión acreditada por componente |
| I12 | C37:L3–11 K redondeado por componente | D04b:204; contrato K/cuotas | INCOMPATIBLE | E2 da K3/K5 cuando contrato K4; factibilidad conjunta imprescindible |
| I13 | C37:L6 `recursive_tree_part` | D04b:61/77/102, D04m:124 | REQUIERE_EXPERIMENTO | Sustitución de semilla no medida; contrato y núcleos cambian el espacio factible |
| I14 | Árboles aleatorios/peeling con deuda poblacional en dependencia histórica | D04b:169/187; D04:132/219 | REQUIERE_EXPERIMENTO | Intervalos de factibilidad remanente pueden ayudar A3; no prueban factibilidad global |
| I15 | C37 init amplia; C38 propuesta más estrecha | G05:91/882; L05:629 | YA_IMPLEMENTADO | Separación propuesta/límites/objetivo existe en G05; laboratorio exige banda fina |
| I16 | `node_repeats` configuración vs C37 sin pasarlo | G05:882, máximo intentos500 | REQUIERE_EXPERIMENTO | Reintentos afectan tiempo/éxito, no calidad garantizada; parámetros no idénticos |
| I17 | C7:L2 `random.random.seed(seed)` | Eplan:22; G05:852 | MEJOR_IMPLEMENTADO_EN_DDD | Expresión histórica compatible con módulo antiguo; DDD explicita seeds/hashseed |
| I18 | config.py:34, semillas manuales por provincia | Eplan:27; G05:937 | MEJOR_IMPLEMENTADO_EN_DDD | Plan determinista y cartera reproducible; robustez aún debe medirse |
| I19 | runner d2a2972 reintentos aleatorios; final:26–42 comentados | D04m:124; G05:852; Eplan:256 | REQUIERE_EXPERIMENTO | No importar reintento ciego; tipificar imposibilidad, presupuesto y fallo recuperable |
| I20 | C38:L41–47 MarkovChain | G05:852; Ecal:328 | YA_IMPLEMENTADO | Ya integrada como alternativa, no canónica predeterminada |
| I21 | C38:L33 recom selecciona arista de corte en fuente contemporánea | G05:882 `district_pairs`; L05:671 | REQUIERE_EXPERIMENTO | Probabilidad por frontera frente por pareja; no equivalencia de distribución |
| I22 | C38:L26–28 dos contigüidades y tolerancia | G05:555/647; Top:302; M06 | MEJOR_IMPLEMENTADO_EN_DDD | Excepciones acreditadas y diagnóstico causal; no confundir validación local y certificación |
| I23 | `partition_percentage=2` config:43 | G05 contrato:75/config:91; L05:350 | INCOMPATIBLE | Fuente contemporánea usa fracción ±200%, no 2%; falta wheel exacto para atribuirlo definitivamente |
| I24 | C38:L44 `always_accept` | G05:852; Ecal:191; D05:247 | YA_IMPLEMENTADO | Exploración y mejor visitado separados; annealing canónico sí pondera aceptación |
| I25 | C38 pasos56, top10; config:25/28 | G05:91; Eplan:27; Ecal:101 | MEJOR_IMPLEMENTADO_EN_DDD | Más estados configurables, diagnósticos de degeneración; pasos no prueban mezcla |
| I26 | C38 inválidos sin contador explícito | G05:852 safe proposal/counters; Ecal:101 | MEJOR_IMPLEMENTADO_EN_DDD | Fallos recuperables self-loop, intentos limitados; falta medir costo real por estado |
| I27 | C5 watchdog SIGALRM, C38:L50 120s | R05:26; G05:882; Eplan:256 | APROVECHABLE | Límite temporal tipificado útil; histórico no protege inicialización y runner limita celda90s |
| I28 | C38:L55–60 except amplios/salida parcial | G05 error baseline y fallback; Ecal:63/191 | INCOMPATIBLE | Parcial no puede aparentar cartera terminada o mapa certificado |
| I29 | C38:L54 asigna arrays por orden de nodo | L05:153/620; G05:955 | MEJOR_IMPLEMENTADO_EN_DDD | Join por identidad; orden gráfico y fila pueden diferir tras filtrado |
| I30 | C38:L77 L1 absoluto a `target` | D04b:116; D05:175; Esel:17; G05:786 | MEJOR_IMPLEMENTADO_EN_DDD | E1: L1 prefiere máximo15% frente10%; DDD elige10% en ese caso |
| I31 | C38:L78 std, no usada al ordenar | G05:538/786; Ecal:471 | MEJOR_IMPLEMENTADO_EN_DDD | RMS/distribuciones y percentiles; especificar std muestral y unidad de cada métrica |
| I32 | Sin compactación en selector histórico | L05:510; G05:750; Esel:17 | MEJOR_IMPLEMENTADO_EN_DDD | PP y geometría/comarca explícitos; microcheck exige contactos completos |
| I33 | Sin penalización comarcal | L05:467/571; G05:882; Esel:17 | MEJOR_IMPLEMENTADO_EN_DDD | G05 usa surcharge en propuesta, no objetivo comarcal en ranking; no confundir |
| I34 | Municipal pequeño intacto; grandes libremente seccionables | G05:555; L05:350; D04b:204 | MEJOR_IMPLEMENTADO_EN_DDD | Preserva unidades y cerrados; laboratorio tiene discrepancia concreta del parámetro atómico |
| I35 | Sin reparación focal, sólo nuevo árbol/ReCom | R05:397/559/731 | MEJOR_IMPLEMENTADO_EN_DDD | Cadenas preparatorias y budgets existen; problemas de poda pertenecen A2 |
| I36 | C38:L72 unión de cada estado | L05:510; G05:750; Esel measure:16 | MEJOR_IMPLEMENTADO_EN_DDD | E3 ahorro≈5× ya aprovechado; exportaciones requieren equivalencia de ranking |
| I37 | C38 todos los `flipstep` guardados | Ecal:72/191; G05:905–933 | MEJOR_IMPLEMENTADO_EN_DDD | Streaming/reservoir; hashes únicos aún O(S), no memoria totalmente constante |
| I38 | Top10 por componente sin deduplicar | G05:972; Eplan:27; Esel:47 | MEJOR_IMPLEMENTADO_EN_DDD | Hashes y Pareto; hash etiquetado no garantiza diversidad física (microcheck) |
| I39 | C39:L18–21 rellena alternativas faltantes al azar | Ecal:63; Esel:47 | INCOMPATIBLE | No inventar diez alternativas; registrar cantidad y causa de incompletitud |
| I40 | C39 `fillna(0)` y IDs locales repetidos | G05:955; Eplan candidate manifest | INCOMPATIBLE | Cero oculta ausencias; identidad debe incluir provincia/componente y ledger |
| I41 | runner:17 parámetros Papermill/cuaderno por provincia | Eplan:256; G05:1023 | APROVECHABLE | Manifest legible por ejecución y notebook diagnóstico opcional, no nueva dependencia |
| I42 | runner:80/84 Excel/pickle sólo al final | Eplan:215/256; manifiestos JSON | MEJOR_IMPLEMENTADO_EN_DDD | Resultado por candidato reanudable; identidad de configuración completa pendiente |
| I43 | runner:54 secuencial | Eplan plan/shards; campañas existentes | YA_IMPLEMENTADO | Sharding existe; paralelismo local no medido, debe mantener budgets totales |
| I44 | map_assembler:18 sustituye 52 provincias por Burgos | N1/N2 inventarios; manifiestos DDD | INCOMPATIBLE | Configuraciones presentes no acreditan mapa completo |
| I45 | config_assembler selección `map_iteration` | Esel:47; Vis:72 | APROVECHABLE | Selección explícita provincia/candidato/config; ya hay selection.json con justificación |
| I46 | map_assembler:31–36 añade provincia/iteración | Eplan:256; ensamblado conceptual N1 | YA_IMPLEMENTADO | Metadatos útiles; completarlos con hashes/ediciones y ledger |
| I47 | map_assembler:44–45 reetiqueta por fila | M06; N1/N2 comparadores | INCOMPATIBLE | Renumerar filas no certifica distritos, secciones, K o cuotas nacionales |
| I48 | map_assembler:48 simplifica .0005 sin CRS explícito | Vis:52; geometría oficial/M06 | INCOMPATIBLE | Sólo derivado visual aislado si aprobado; nunca reemplazar geometría certificada |
| I49 | C40 Kepler multilayer, C41:L3 GeoJSON top | Vis:72; visor MapLibre | YA_IMPLEMENTADO | Comparación A/B y capas sin añadir Kepler |
| I50 | map_assembler:65 Excel estadísticas | informes M06/JSON/CSV; N1 workbooks | APROVECHABLE | Exportación tabular por manifest, Excel optativo; no prueba territorial |
| I51 | pyproject Python^3.6.8/Gerry^0.2.12/Geo^0.8.1 | runtime aislado G05:149 | OBSOLETO | Pins de 2020 no sustituibles sin adaptar APIs y medir; Papermill falta en pyproject |
| I52 | requirements.txt 104 dependencias congeladas | aislamiento runtime/código actual | OBSOLETO | No importar stack completo; sólo mecanismos necesarios |
| I53 | Notebook con outputs parciales, sin suite | tests actuales/M06; expediente sintético | MEJOR_IMPLEMENTADO_EN_DDD | Prueba dirigida, cadena, campaña y certificación son evidencias distintas |
| I54 | Falta checkpoint mitad de cadena | Eplan:215; G05:972 | REQUIERE_EXPERIMENTO | DDD reanuda candidatos completos, no RNG/estado intermedio; checkpoint exige contrato adicional |
| I55 | Híbrido previo a construir grafo | G05:332 ya unitario; Ecal:328/L05:629 seccionales | REQUIERE_EXPERIMENTO | E5 cuantifica validación, no ley de propuestas; portarlo al laboratorio debe preservar expansión física |
| I56 | Sin fuentes electorales en delimitación estudiada | contrato territorial, M01–M06 | YA_IMPLEMENTADO | Mantener separación; M07/M08 posteriores no retroalimentan límites |

## 4. Qué cambió a lo largo del historial

- **48fe0a3 → 8fcfa0f (noviembre2020):** notebook monolítico y dependencia del entorno. **7ab762c / 1874aff:** retirada de credenciales/configuración SQL. Se examinó su contexto sin reproducir secretos; no son un recurso para DDD.
- **d80000b (23-11-2020):** ZIP cifrado y requisitos. **e3fbbc9 / 5f60615 / 6093d82 / f777bab / 497e024:** instalación/adaptación Colab y cambios de dependencias. Implican entorno interactivo frágil, no garantías nuevas de partición.
- **a860e41 (24-11-2020):** muestra todas las iteraciones en Kepler, precursor útil de comparar alternativas; no hay test ni selección multifactorial acreditada.
- **0ee6465 (10-02-2021):** elimina ZIP y parametriza ejecución; su runner contiene referencias ETL no definidas. **eb789a6:** corrige runner Papermill, captura errores y permite seguir provincias. Parámetros anteriores incluyen target33000/init.4/propuesta.3/56 pasos; no deben mezclarse con los finales de120000.
- **4215064 (27-03-2021):** amplía parametrización, incluyendo porcentaje poblacional. **61ed9bc:** fija requisitos; el pyproject no es un lock equivalente al requirements.
- **d2a2972 (08-04-2021):** 52 configuraciones provinciales y reintentos aleatorios hasta10, usando configuración mutable/global; arranque desde índice5, por lo que aquella ejecución no cubre las52 entradas.
- **f5d063b (último, abril2021):** componentes desconectados, watchdog y ensamblado de alternativas; quita el slice de provincias, pero comenta el manejo de errores/reintentos (hasta15 sólo en comentarios). Introduce ensamblador cuya lista real vuelve a limitarse a Burgos. Más mecanismos no implican una campaña nacional completa.

Parámetros **realmente usados por runner final**: 52 registros, target120000, `node_repeats=3`, `epsilon=.1`, `partition_percentage=2`, `total_steps=56`, `top_iteration=10`. `init_epsilon=.2` en46; Barcelona/Málaga.3, Soria.36, Toledo.25, Ceuta.42 y Melilla.39. Quince registros usan seed42; los demás semillas individuales. Defaults globales `INIT_EPSILON=1`, `EPSILION=1` (nombre distinto de `epsilon`) no describen esos registros. C4 es un ejemplo Murcia33000 y C6 contiene placeholders para Papermill; ejecutar el notebook sin inyección no equivale al runner.

## 5. Diferencias algorítmicas por ámbito

### A. Unidades, granularidad, municipios y componentes

Nacho cambia municipio→sección en el umbral target, agregando geometría antes del grafo. Eso puede disminuir V/E, pero no hay búsqueda de una granularidad óptima ni medición en el repositorio. No conserva explícitamente una función oficial sección→unidad→distrito en los GeoJSON disueltos. Municipalidades grandes admiten cualquier partición de secciones; no tienen el concepto DDD de núcleo U cerrado y residual R.

DDD conserva M03 seccional como evidencia y contrae después por `ddd_unit_id`. Para dos unidades distintas u/v hay arista cociente si existe una arista M03 entre sus secciones; cada unidad suma población exacta y mantiene lista completa de secciones. El mapa final expande asignación de unidad hacia secciones originales. Esta estrategia ya aprovecha la aceleración híbrida **sin perder atomicidad** cuando sus precondiciones se cumplen.

La precondición crítica es conectividad física/operativa de la unidad o tratamiento acreditado de sus componentes. A1–B–A2 contraído a A–B conserva población y universo, pero convierte el distrito A en un nodo aparentemente conexo aunque sus piezas sean disjuntas. E5 verifica esa falsa contigüidad. No se soluciona eliminando A2, uniendo por distancia o dividiendo arbitrariamente una unidad contractual. Top/preparación física y los contratos existentes son la puerta. Las excepciones acreditadas no autorizan conexiones nuevas por una geometría multiparte no relacionada.

DDD no necesita alterar M02/M03 para obtener un grafo menor en optimización: G05 ya prepara el cociente. Ecal/L05 aún construyen grafo de secciones y rechazan después fracturas de unidades; ahí hay oportunidad de propuestas unitarias. El beneficio potencial es menos propuestas inviables y validación más barata, pero cambia la ley de ReCom. E5 mide **sólo** validación de asignaciones ya admisibles. No demuestra equilibrio, exploración ni éxito de propuestas.

M02 mantiene riesgos previamente identificados por A-OPT01: truncar candidatos espaciales a50 puede requerir oracle de completitud; usar `iloc` repetidamente y repetir pares no aceptados cuesta. No se realizaron benchmarks nuevos de ese frente. La exactitud de PP aditivo también depende de contactos completos; el microcheck nuevo aporta un consumidor concreto para esa investigación pendiente, sin demostrar que falte ninguna arista productiva.

### B. Inicialización y K

Nacho obtiene `round(P_componente/target)` y ejecuta `recursive_tree_part` con target fijo. P/K real puede diferir del target configurado, lo que separa objetivo de inicialización, objetivo de propuesta y media empleada por el validador. Su fuente contemporánea de GerryChain combina árboles máximos sobre pesos aleatorios, cortes balanceados y deuda poblacional para las piezas siguientes; ese árbol no es una muestra uniforme de todos los spanning trees. Los reintentos de bipartición pueden no terminar cuando no hay corte; no hay presupuesto de inicialización en C37. `node_repeats` sólo se pasa a propuesta, no a inicialización.

DDD fija K y cuotas antes de particionar, deriva target=P/K y calcula rangos de distritos por componente con floor/cap y suma conjunta exacta. El redondeo local q de piezas de un municipio sobredimensionado en D04b:187 **no decide K global**. Usa peeling BFS, crecimiento con semillas distantes, rebalanceo, protección de gateways y fallback multistart determinista; añade preflight de condiciones necesarias y búsqueda exacta acotada en grupos pequeños. `UNKNOWN` por presupuesto agotado no es prueba de imposibilidad.

Hay una idea útil de la deuda histórica: antes de cerrar una pieza, exigir que población y número de piezas remanentes puedan satisfacer sus intervalos; mejor aún considerar demanda exterior del residual. DDD ya tiene parte de esa contabilidad y A3 cubre la demanda exterior de Rioja. El testigo existente Calahorra/Rincón/Aldeanueva no es prueba global. No se reimplementa aquí ni se vuelve a ejecutar. Una prueba futura debe conservar exactamente unidades/K/budgets e incluir contraprueba de municipio con gateway único, resto insuficiente y componente sin solución.

### C. ReCom, transiciones y aceptación

Nacho usa partición inicial, `contiguous` más BFS, propuesta ReCom, población y `always_accept`. El ranking se aplica al archivo de estados visitados; no existe aceptación dirigida por L1. En la fuente contemporánea, elegir una arista de corte pondera las parejas por cantidad de frontera; G05 declara `pair_selection="district_pairs"`. Ni parejas uniformes ni pesos comarcales garantizan mejor solución, mezcla o imparcialidad territorial; deben compararse con semillas emparejadas y costo real igual.

La fuente contemporánea `within_percent_of_ideal_population` multiplica media por1±percent. Con percent2 resulta una banda de±200%, mientras la propuesta final usa±10% y la inicialización generalmente±20%. No se debe interpretar2 como2% por su nombre. Como falta el wheel exacto, esto es una alarma semántica fundamentada, no una ejecución acreditada de aquel paquete. DDD distingue floor/cap, epsilon de propuesta, banda objetivo y tolerancia contractual, evitando importar ese valor.

G05 protege K/cuotas, provincia, atomicidad mediante unidades, cerrados y disciplina municipal. La banda fina es objetivo y no transición dura. L05/Ecal, en cambio, exigen banda fina en cada estado; una semilla M04 fuera de ella puede ser inadmisible aunque respete floor/cap. Es una diferencia funcional ya tratada por PR73/78, no un motivo para relajar el laboratorio. G05 añade reintentos limitados, captura fallos concretos de propuesta como self-loop, contadores, hashseed0 y manifest; Ecal separa calidad de la cadena de calidad del mejor mapa y exige políticas de degeneración. G05 no aplica exactamente esa puerta de degeneración del ensemble.

La contigüidad **no es idéntica entre caminos**: G05 usa el grafo territorial acreditado como autoridad dura y reporta geometría física causalmente; L05 incorpora una puerta física cuando hay geometrías. PR105 explica por qué una segunda puerta puede contradecir pasarelas declaradas. Esto no suprime M06 ni certifica automáticamente toda geometría de G05. Las doce reglas del encargo requieren controles independientes posteriores y excepciones acreditadas; no se propone cambiar esa política aquí.

El histórico guarda todos los estados válidos observados y puede consumir intentos inválidos sin incrementar el contador de pasos en la fuente contemporánea. Por eso comparar56 versus3000 pasos sin medir intentos/tiempo es inválido. Además watchdog120s no incluye C37 y Papermill90s por celda puede terminar antes. DDD limita ciertas búsquedas/intentostree, pero no se ha medido tiempo máximo real de cadena/semilla en este expediente. Un presupuesto futuro debe contar propuestas, self-loops, estados válidos, tiempo y memoria, y terminar con estado tipificado; no etiquetar una cadena truncada como completa.

### D. Evaluación, búsqueda y reparación

Para poblaciones p_d, objetivo T=P/K: absoluto a_d=|p_d−T|; relativo r_d=a_d/T; L1=Σa_d; máximo=max r_d; RMS=√(Σr_d²/K). A target común, L1/T es desviación relativa total; al comparar provincias con distinto T no se pueden sumar objetivos sin declarar ponderación. Nacho usa target configurado y calcula std muestral de los absolutos, pero ordena sólo L1. E1 muestra que concentrar error en un distrito puede reducir L1 y empeorar máximo.

M04/M05 canónicos ordenan primero infracciones duras y su magnitud, después outliers, máximo y error cuadrático. La reparación usa su propio objetivo y transición dura no regresiva; hard0 puede ser distinto de todos dentro de banda fina. El laboratorio usa un score ponderado; el ensemble incorpora Pareto multidimensional; G05 ordena `(outliers, ceil(max_rel/band), penalización_forma, max_rel, RMS, cortes, churn, hash)`. Dentro de una misma banda, forma puede preceder máximo: no se afirma que DDD siempre priorice máximo absoluto. E1 sólo prueba los dos selectores ejecutados sobre ese fixture.

Fragmentación municipal se controla estructuralmente además de métricas. Comarca tiene retención/fragmentación/entropía en L05 y Pareto en Esel; G05 aplica surcharge a árboles, pero **no incluye retención comarcal explícita en candidate_rank**. Si Work exige ese objetivo, comparar Pareto/profiles existentes antes de añadir otro selector. La suma agregada de objetivos de Esel puede ser sensible a escalas y exige decisión de pesos; aquí no se demostró un ranking alternativo superior.

La poda A2 limita qué estados preparatorios sobreviven: selección lexicográfica local no equivale a una búsqueda completa. La entrega anterior del09-10 acreditó un candidato válido podado (rango34 y47 seleccionados) y un presupuesto exploratorio incompatible con el aprobado. **Ese resultado es de la implementación fechada**, no del diff A2 actual: hoy `_select_expanded_frontier`:342 selecciona una frontera global ordenada por rank/ceiling. No se repite ni se emite un NO_GO sobre el trabajo en curso. La recomendación ya cubierta es retener diversidad de estados alcanzables, contar todos los candidatos y preservar hard monotone bajo180s/400k/depth96/640MiB. L1 histórico no corrige la poda ni prueba que exista una ruta dentro del presupuesto.

La evidencia Rioja anterior acredita que, bajo ciertas unidades fijas, no hay solución en la banda fina: más iteraciones no resuelven una imposibilidad atómica. La formación A3 debe preceder a la optimización A7 cuando la semilla/unidades son el bloqueo.

### E. Ensamblado provincial y Nacional

El runner conserva configuraciones y produce cuadernos/mapas por provincia; el assembler selecciona `map_iteration`, adjunta provincia, concatena y exporta mapa/Excel. Es útil como patrón de **catálogo de alternativas y ensamblado cartográfico**, con ledger de configuración. El código final sólo selecciona Burgos, resetea índices como distrito y simplifica .0005 sin CRS explícito. No comprueba cobertura nacional, universo, K, cuotas, fuentes ni consistencia de IDs locales. No certifica un algoritmo nacional ni una asignación legal.

En N1/N2 ya hay herramientas de inventario, comparación cartográfica, evaluación cuantitativa, workbooks, manifests y geometrías históricas: en el worktree nacional leído, `inventariar_cartografia_historica.py`:40/73 incorpora referencias; `comparar_cartografia_nacional.py`:61/92/147 compara estadísticas/geometrías; `evaluar_alternativas_nacionales.py`:30/59/93/115 valida el modelo y sensibilidad. Se consultaron como concepto, sin ejecutar ni cambiar ese frente. N1 requiere catálogo/evidencia de ensamblado y N2 relaciones sección–unidad–distrito/componentes según su propio contrato; no heredan automáticamente el autonómico. target120000 histórico es exploratorio, no una decisión de K nacional.

La entrega de gobierno anterior registra divergencia392/391 y44 geometrías discontinuas y correcciones pendientes; son estados fechados que se dejan a sus responsables, no resultados actuales certificados por esta investigación. Propuesta documental: ledger `(provincia, id_local, componente, candidato, config_hash, source_hash, secciones)` y suma de invariantes antes de mapa. No se implementa ni se transforma la geometría Nacional.

### F. Rendimiento, memoria y reproducibilidad

| Operación | Histórico | DDD / oportunidad | Evidencia disponible |
|---|---|---|---|
| Componentes | BFS por nodo + deduplicación de listas | BFS única O(V+E) | Estática, ya mejor en D03 |
| Grafo geométrico | Construye tras dissolve | M02/M03 seccional + cociente auditable | E5 mide validación, no construcción GIS completa |
| Árbol ReCom | Kruskal sobre E, BFS/cortes repetidos | Intentos limitados y unidades en G05 | Complejidad dependiente de versión; tiempo real no medido |
| Ranking población | Agrupación/dissolve en cada estado | Tallies, métricas streaming | E1 y E3; ahorro de E3 ya existente |
| Forma | Uniones para todos los estados | Área/perímetro/fronteras O(U+E_u) | Microcheck exactitud condicionada a contactos |
| Estados | O(S·N) columnas más geometrías O(S·K) | Mejor estado + reservoir métrico; hashes O(S) | Código Ecal/G05; no memoria territorial medida |
| Validación de unidades | Grafo híbrido | Algunos callers aún expanden secciones | E5 4,33–17,37× sintético |
| Reanudación | Persistencia global al final, sin checkpoint | Candidato completo retomable | Microcheck: config completa no vinculada en Eplan |
| Paralelismo | Provincias secuenciales | Shards/candidatos independientes | No benchmark nuevo; mantener budget global |
| Fallos | except amplio/reintento aleatorio/inertes en final | Errores tipificados y baseline válido antes de fallback | Fuente actual, no campaña ejecutada |

Semilla fija no basta: también hashes de fuentes/contrato/código/configuración, orden determinista, versiones, CRS, hashseed y esquema de serialización. G05 prepara geometría una vez, aunque reconstruye grafo de propuestas por semilla y ciertas validaciones recalculan adyacencia. Cache inmutable y memoización de estados repetidos son hipótesis; se deben perfilar antes de tocar. No se cuantifica ahorro que no se midió.

Eplan AUTO liga bundle a bytes M03/M04/comarca. Eso no sustituye la identidad **completa de ejecución**: `ensure_plan` no incorpora pasos ni tolerancia y `_valid_existing` no recibe configuración actual. El microcheck crea un artefacto mock autoconsistente, cambia56→1000 pasos y tolerancia.2→.01 y obtiene mismo plan hash y cache aceptada. Es prueba causal de las funciones de identidad, no una cadena inválida o certificación ficticia. Corregir exige invalidación explícita por execution fingerprint sin borrar un producto certificado anterior.

### G. Visualización y diagnóstico

Kepler facilitó capas de provincia/municipio/CP/sección/híbrido y las iteraciones; GeoJSON permite inspección y Excel resume poblaciones/configuraciones. DDD ya ofrece MapLibre, galería A/B, perfiles/Pareto, métricas y `selection.json` con responsable/justificación; gallery reproyecta a WGS84 para navegador. No hay beneficio demostrado de añadir Kepler.gl ni de sustituir el visor.

Ideas pendientes útiles: capa de unidades/residuales y componentes físicos con ledger de sección; histograma/tabla de desviaciones por alternativa; semillas, configuración y algoritmo efectivo visibles en diagnóstico; distinguir selección técnica, validación y certificación. Incorporar sólo métricas ya acreditadas y derivados de visualización, sin editar fuente ni exponer implementación irrelevante al ciudadano. Simplificación cartográfica sólo como derivado etiquetado, nunca en geometría oficial ni en cálculo de contigüidad/compactación certificada. Excel opcional para revisión, conservando JSON/CSV e IDs; su existencia no acredita una configuración nacional.

## 6. Experimentos ejecutados y resultados reales

[README detallado](experimentos/README.md), [E1–E3](experimentos/results.json), [ranking motor real](experimentos/engine_ranking_results.json), [E5](experimentos/graph_results.json), [microchecks](microchecks.json). Scripts originales y logs quedan junto a los resultados. Mismos inputs/seeds/K/límites/presupuestos en cada par; no hay datos electorales. Los fixtures sin núcleos urbanos cerrados verifican un caso vacuo de esa condición: no se presentan como regresión de su preservación en casos reales.

| Ensayo | Comparación / presupuesto | Resultado | Métricas y límites |
|---|---|---|---|
| E1 | Grid4×4, P4000,K4,T1000,±20%, filas vs columnas | L1 A300 vs B400; máximo A15% vs B10%; Esel y L05 reales eligen B | PP idéntico≈.502655, retención100%, C inválido rechazado; no cadena |
| E2 | Isla100/T1000/init.05; redondeos por3 componentes | Borrado pierde100habitantes/1unidad; K3 o5 vs contrato4; ties.5 pueden producir0 | Prueba analítica, no demuestra factibilidad física de una reparación |
| E3 | N800/3200,K4,56 estados,top10,seeds17/29/43,±20% | Mediana5,15×/4,88× al unir sólo seleccionados;224→40 uniones | Six pares, shortlist/pop/asignación/WKB exactos, cero violaciones sintéticas seleccionadas; RSS ahorro≈2–5% |
| E5 | 128municipios×q4/8/16, K4,2000estados×3seeds,±25% | N512/1024/2048→128; speedup4,33×/8,67×/17,37× | Nueve pares,2000/2000 resultados iguales; población/conexión/universo/roundtrip exactos; construcción incluida |
| E5 negativo | A1–B–A2, unidadA discontinua | Cociente da falso positivo de contigüidad | Contraejemplo rechaza contracción pura; no permite romper atomicidad |
| E4a | L05 real,4secciones×10,K2,T20,atomicidad1.75 | Municipio30≤35 dividido en2; validador devuelve[] | Parámetro no usado; secciónsin geometría en este fixture, hallazgo contractual del adaptador |
| E4b | Mismo distrito físico, etiquetas0/1 permutadas | 2hashes de asignación,1partición sin etiquetas | Diversidad etiquetada distinta de física; preservar IDs oficiales |
| E4c | Eplan real + artefactos mock, cambia pasos/tolerancia | plan_sha igual y cache aceptada antes/después | Prueba de identidad, no tasa de cadenas ni producto certificado |
| E4d | 3rectángulos válidos,2aristas operativas vs3contactos | PPcache.502655 vs unión.785398; añadiendo contacto coincide | Condicional: no acredita pérdida real de aristas M03 |

E3 cronometra tally/ranking/uniones, excluye construcción de fixtures y validación final por igual. E5 cronometra construcción cociente y validación repetida, incluye expansión en ruta seccional y excluye fixtures/verificación por igual. Todos los subprocess tienen timeout60s. Datos completos de tiempo, `tracemalloc` y RSS están en los logs. `tracemalloc` excluye GEOS nativo; RSS incluye imports/fixtures y no es memoria aislada del grafo. E5 registra fuente620–807kB vs cociente≈618kB Python y RSS17,8–20,7MB vs17,3–18,1MB, pero ambas rutas mantienen fixture fuente/resultados: **no demuestra ahorro productivo de memoria**.

Los2000/2000 estados válidos de E5 fueron construidos para ser admisibles, con repeticiones y etiquetas permutadas. No equivalen a100% éxito de inicialización/ReCom. Se usan3semillas, sin intervalos de confianza ni generalización estadística. No se mide mejora comarcal/geometría exploratoria en E3/E5: se conserva en fixtures rectangulares/singleton; E1 mide igualdad explícita. La diversidad física, robustez de cadenas y comparación a tiempo fijo quedan sin ejecutar.

Evidencias anteriores reutilizadas, **sin reejecución**: auditoría C01 Aragón50,15/50 cumplen banda fina y49hashes etiquetados; informe Rioja/Cantabria08-10 (reparación Cantabria hard1→0, outliers6→11); entregas A1/A2/A3 del09-10. Sirven para límites/priorización, no para atribuir efectos a propuestas de este expediente.

## 7. Deficiencias y mejoras existentes, separadas por alcance

**Histórico:** puede perder secciones/población; K no contractual; target de propuesta/media de aceptación no alineados; sensibilidad manual sin robustez; ejecución dependiente de SQL/caches sin identidad; falta ledger oficial y cerrados; inicialización sin límite; timeouts incompatibles; errores y parcialidad ambiguos; ranking sóloL1; costos geométricos redundantes; IDs por orden; relleno aleatorio de alternativas; assembler final parcial; simplificación no acreditada; sin licencia/tests/resultados reproducibles. Son problemas específicos, no una valoración por antigüedad.

**DDD ya mejor:** identidad oficial completa, grafo acreditado y tipado, componente/preflight, K/cuotas, unidades/cerrados, crecimiento/multistart, reparación acotada, hard primero, portfolio/semillas/hash deterministas, métricas de forma/comarca, streaming/reservoir, fallback con baseline válido, galería A/B, manifests y validación independiente posterior. Esas garantías no se deben sustituir por los mecanismos incompatibles del histórico.

**DDD con evidencia nueva:** identidad de reanudación incompleta (E4c), parámetro de atomicidad declarado sin uso en laboratorio (E4a), hashes etiquetados que sobrecuentan diversidad física (E4b), y necesidad de completitud de contactos para perímetro cacheado (E4d). Los dos últimos son límites métricos/condicionales, no errores certificados observados. **Pendiente de experimentar:** contracción en propuestas del ensemble, ranking comarcal explícito G05, cache de validación por hash, límite temporal completo de cadena, calidad estadística equivalente de portfolios, checkpoint intermedio y estrategias de árbol/deuda.

## 8. Oportunidades, encaje con Plan Maestro y prueba de aceptación

| Propuesta | Problema y adaptación | Restricciones/riesgo | Prueba pendiente y encaje |
|---|---|---|---|
| P01 Fingerprint de ejecución | Reanudación histórica pobre; DDD reusa candidato sin config completa | Cache obsoleta; conservar producto previo, nunca recertificar por cache | Misma config reusa; cambia pasos/tol/pesos/CRS/runtime/código/fuentes invalida. Nueva autorización Work, relacionado PR116 |
| P02 Atomicidad coherente laboratorio | Híbrido histórico protege municipios pequeños; L05 declara ratio pero no lo aplica | Usar unidad municipal **contractual** con particiones acreditadas; no imponer CUMUN contradictorio | Caso30≤35 falla si se divide; sobredimensionado permitido por reglas; excepciones/internal units iguales validador común. PR107/91 ya cubren semántica, evitar duplicación |
| P03 Cociente en ensemble | Evitar proponer sobre secciones indivisibles que luego se rechazan | Cambia distribución de árboles; discontinuidad puede fingir conexión | E5 demuestra equivalencia de validación; siguiente comparar propuestas reales y M06 en idéntico budget. A07 trasA3, no modificar G05 ya contraído |
| P04 Diversidad física adicional | Top histórico y hashes etiquetados pueden aparentar variedad | No renumerar distritos ni romper identidad; diversidad no prueba mezcla | Hash suplementario sin etiquetas, baseline permutado=1, partición distinta=2, cuotas/componentes preservados. A07/ensemble, aprobación nueva |
| P05 Oráculo de forma/contactos | Métricas rápidas exigen todas las fronteras internas | Diferente política operativa/geométrica; CRS métrico obligatorio | Comparar fórmula contra uniones exactas en triángulo/multipart/overlap/bridge. Contactos físicos cache aparte de aristas operativas. A-OPT01 ya cubre M02; no abrir frente paralelo |
| P06 Semilla con demanda remanente | Deuda/intervalos históricos evitan algunos residuos inviables | K/gateways/cerrados/integridad; beneficio no medido | TestigoA3 + casos imposibles + presupuesto exacto; salida global validada independiente. A03/A3, ya asignado |
| P07 Exploración preparatoria y poda | L1 local no representa alcanzabilidad; A2 tiene poda limitada | Monotonía dura/180s400k96/640MiB; no prometer completitud | Evidencia de cada rechazo/poda/budget, diversidad frente estados, suite actual A2. PR144/47 y A2: sólo transmitir conocimiento |
| P08 Pareto/comarca/perfiles | G05 no rankea comarca explícitamente; Esel sí | Tradeoff forma/máximo/comarca, pesos deben ser previos | Mismos seeds/inputs/budget, Pareto multidimensional y estabilidad, no elegir pesos por resultado. PR96 barrido preparado, A07; no duplicarlo |
| P09 Límite/reanudación por semilla | Watchdog útil pero incompleto; DDD sólo candidato completo | RNG/versión/hashseed, partial distinto de complete | Interrumpir/reanudar produce mismo estado/bytes o declarar no bitexact; contador propuestas/tiempo/memoria. A07 o nuevo mandato |
| P10 Diagnóstico visual/ledger | Kepler/Excel hacen alternativas inspeccionables | Geometría derivada nunca fuente; no intervenir Nacional | Usar MapLibre/catálogo/JSON existentes, unidades/componentes/curva poblacional. N1/N2 sólo recomendación y Vis bajo Work |

Búsquedas GitHub de sólo lectura: [prs-relacionadas.json](prs-relacionadas.json). Se limitaron a12 resultados por tema; no acreditan ausencia de otras PR ni su estado de merge. Correspondencias positivas: [PR78](https://github.com/jfmurciego/DiputadodeDistrito/pull/78) estrategia alternativa/unidades/banda objetivo; [PR84](https://github.com/jfmurciego/DiputadodeDistrito/pull/84) selector/portfolio; [PR105](https://github.com/jfmurciego/DiputadodeDistrito/pull/105) grafo operativo/diagnóstico/fallback; [PR107](https://github.com/jfmurciego/DiputadodeDistrito/pull/107) disciplina municipal contractual; [PR116](https://github.com/jfmurciego/DiputadodeDistrito/pull/116) ensemble/semillas/manifests/hashes; [PR96](https://github.com/jfmurciego/DiputadodeDistrito/pull/96) barrido comarcal preparado; [PR151](https://github.com/jfmurciego/DiputadodeDistrito/pull/151) multistart M04; [PR218](https://github.com/jfmurciego/DiputadodeDistrito/pull/218) discontinuidades acreditadas; [PR144](https://github.com/jfmurciego/DiputadodeDistrito/pull/144) cadenas preparatorias. Sólo se toman declaraciones de esas PR como trazabilidad de trabajo existente; su implementación local se contrasta en los archivos citados, no se supone por el título.

## 9. Pseudocódigo original para candidatos pendientes

Estos esquemas no son traslaciones de código Nacho ni integraciones autorizadas.

```text
P01 identidad de ejecución:
  resolver contrato, configuración, dependencias y fuentes efectivas
  fingerprint = hash(canonical_json(
      esquema, contrato_completo, parametros_motor, perfiles/pesos,
      seeds, CRS, hashseed, runtime/versiones, codigo_SHA,
      hashes_bytes_fuentes, ledger_unidades))
  al retomar candidato:
      exigir fingerprint_actual == fingerprint_manifest
      verificar hashes de artefactos y validaciones/quality requeridas
      si difiere: declarar INCOMPATIBLE_CACHE, preservar producto previo
      nunca tratar un resultado parcial como COMPLETE

P02 atomicidad:
  resolver campo de disciplina municipal desde contrato acreditado
  calcular población por entidad contractual, una sola vez
  para cada entidad que deba ser indivisible:
      exigir un único distrito para todas sus secciones
  exigir además unidad_atómica, cerrados, K, cuotas, piso/techo y contigüidad
  usar mismo resolvedor que validación común; no crear otra disciplina

P03 cociente exacto:
  exigir ledger cubra cada sección exactamente una vez
  construir nodos sumando poblaciones oficiales por unidad
  derivar aristas sólo de M03, conservando tipos/procedencia
  acreditar conectividad interna/componentes/excepciones de cada unidad
  proponer asignaciones de unidades respetando provincia y cerrado
  expandir por ID; comprobar universo y todas las puertas independientes
  comparar rendimiento/calidad a igual presupuesto con ruta seccional

P04 diagnóstico de diversidad:
  por cada asignación válida: guardar hash etiquetado existente
  hash_fisico = hash(lista ordenada de conjuntos ordenados de secciones
                    agrupados por distrito, con ámbito provincial)
  reportar ambos conteos, self_loops y distancia entre particiones
  conservar IDs de salida; no interpretar conteo como convergencia

P06 factibilidad remanente (dentro de A3):
  antes de fijar núcleo: calcular unidades/población/K que quedarían
  comprobar intervalos necesarios por componente y gateways residuales
  si imposible: descartar candidato antes de cerrarlo
  si búsqueda acotada no concluye: UNKNOWN, nunca IMPOSSIBLE por timeout
  expandir solución global y pasar validación independiente
```

## 10. Riesgos, orden recomendado y tabla final

Prioridad propuesta: primero P01/P02 por defectos causales pequeños y aislables, **sólo después de decisión Work** y contraste con PR107/116. Después P04/P05 como diagnóstico/exactitud de métricas. Respetar que A3 resuelva formación y A2 termine reparación; transmitir P06/P07 a sus responsables sin nueva implementación. Luego P03/P08/P09 en A07 con runtime y presupuesto aprobados, semillas emparejadas y M06. Visualización/ledger al final, reutilizando herramientas; Nacional decide en su propio frente.

Beneficio/esfuerzo/riesgo son estimaciones cualitativas salvo medidas expresamente indicadas. No se prometen speedups productivos ni porcentajes de éxito. Adoptar una propuesta exige cero pérdida/duplicación seccional o poblacional, K/cuotas exactos, floor/cap contractual, atomicidad/municipalidad/cerrados, contigüidad y excepciones acreditadas, fuente/edición idénticas, determinismo y M06 independiente. Ninguna métrica puede compensar una violación dura. Los experimentos carecen de datos electorales y no modifican el contrato.

| MEJORA | ORIGEN NACHO | COMPONENTE DDD | BENEFICIO | EVIDENCIA | COSTE | RIESGO | DECISIÓN |
|---|---|---|---|---|---|---|---|
| Híbrido municipal/seccional | C25–30 | M04/G05 | Menos unidades sin romper ledger | Código actual, E5 validación | Ya asumido | Medio si discontinuidad | CONSERVAR lo existente |
| Cociente en laboratorio ensemble | C33 híbrido | L05/Ecal | Validación4,33–17,37× en sintético; menos propuestas inválidas por medir | E5 + negativoA–B–A | Medio | Alto, ley ReCom/física | PROPONER A07, no integrar |
| Identidad completa de reanudación | runner pickle/configs | Eplan runner | Evitar reuso con pasos/tolerancia distintos | E4c funciones reales/mock | Bajo–medio | Bajo–medio compatibilidad cache | PRIORIDAD1, pedir decisión Work mediante entrega |
| Atomicidad contractual consistente | Municipio pequeño íntegro | L05 validador | Cerrar discrepancia ratio declarado/no aplicado | E4a, PR107/91 | Bajo–medio | Medio particiones internas | PRIORIDAD1, contrastar contrato antes de corregir |
| Diversidad sin etiquetas adicional | Top10 alternativas | Ecal/G05/Esel | Distinguir mapas físicos de renumeración | E4b doshashes/unmapa | Bajo | Bajo si sólo diagnóstico | PRIORIDAD2, pendiente Work |
| Oráculo contactos/CRS para PP | Dissolve exacto | D02/G05/L05 | Evitar sesgo de forma con contactos incompletos | E4d condicional | Medio | Medio interpretación puente | REMITIR A-OPT01, no duplicar |
| Unión sólo seleccionados | C38 dissolve todos | Rankings G05/L05 |≈5× mecanismo sintético | E3 exactitudWKB | Ya asumido | Alto si preselección elimina criterio | YA MEJOR EN DDD |
| Máximo/distribución frente L1 | C38 residuals | D05/Esel/L05 | Evita15% cuando hay10% en fixture | E1 motor/assembler reales | Ya asumido | Pesos/bandas aún tradeoff | CONSERVAR, no otro selector |
| Demanda exterior/deuda remanente | recursive_tree_part | M04/A3 | Evitar residuales inviables | Estática, testigo previo; mejora no medida | Medio–alto | Alto congelación/gateway | YA CUBIERTO A3 |
| Retención diversa en poda | Exploración sin ranking online | R05/A2 | Mayor alcanzabilidad a budget fijo | Entrega09-10, no reaprobación diff | Medio–alto | Alto presupuesto/monotonía | YA CUBIERTO A2 |
| Pareto/comarca/perfiles | Alternativas top | G05/Esel | Tradeoffs explícitos/retención por medir | Código + PR96; sin barrido nuevo | Medio | Medio sesgo ranking | A07, no repetir barrido |
| Semillas/presupuesto/quality | seed/retry/watchdog | G05/Ecal | Fallos claros/robustez verificable | Código, C01 anterior, falta chain nueva | Medio | Medio terminación/diversidad | A07 después de A3 |
| Checkpoint por semilla | runner final-only | Eplan/G05 | Reanudar largas ejecuciones sin repetir | Falta checkpoint real, no ahorro medido | Medio–alto | Alto RNG/bytes | CANDIDATO posterior P01 |
| Ledger ensamblado | config_assembler | N1/N2 conceptual | Trazabilidad sin confundir certificación | Revisión archivos/planes | Medio | Alto si K implícito | RECOMENDAR, no tocar Nacional |
| Comparación visual y tabla | Kepler/GeoJSON/Excel | galería/visor | Diagnóstico unidades/componentes/alternativas | A/B ya presente | Bajo–medio | Bajo derivado, alto geometríafuente | REUTILIZAR, pendiente mandato |
| Borrado/islas/redondeo/relleno | C34/37/38/39 | Ninguno | Inaceptable con contrato | E2 y lectura completa | No aplicable | Viola universo/K | RECHAZAR |
| Copia directa/stack antiguo | Notebook/requisitos | Ninguno | Sin ventaja demostrada | Licencia ausente/API distinta | Alto | Licencia/regresión | NO REUTILIZAR sin permiso/licencia |

La revisión separada, los hashes finales y el control de preservación se anexan al expediente. La entrega permite a Work decidir próximas implementaciones; no cambia prioridades ni estados del Plan Maestro por su cuenta.
