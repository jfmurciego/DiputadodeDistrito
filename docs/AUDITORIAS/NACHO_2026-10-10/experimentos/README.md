# Experimentos sintéticos sobre mecanismos históricos de Nacho

Versión 1.0.0; fecha 2026-10-10; estado: investigación aislada. Frente autonómico, sin modificación productiva, fuentes, certificados ni contratos. Autoría: implementación independiente de mecanismos descritos en el notebook; no se copia código histórico ni se presupone permiso de licencia. Origen conceptual: `nplaton/diputado-distrito`, HEAD `f5d063b`; baseline DDD `42163cd8cebd120db9ab9fd1329c32ccdd87cf36`, rama `codex/distritos-autonomicos`. Diff previo A2/A3 preservado.

## Reproducción

```sh
/private/tmp/ddd-cartografia-venv/bin/python /private/tmp/ddd-nacho-experimentos-20261010/experiments.py
```

No instalaciones, red, acciones externas ni datos territoriales. Cada benchmark se ejecuta en un subprocess nuevo con timeout de 60 segundos. Entorno concreto, fingerprint del script y resultados se registran en `results.json`. `log_N*_seed*_*.json` conserva cada ejecución medida; `run.log` contiene la primera ejecución agregada. `engine_ranking_results.json` incorpora la comprobación posterior del motor sin repetir benchmarks.

## E1: L1 puede ocultar peor desviación máxima

Grid de 4×4 cuadrados unitarios, una unidad/municipio/comarca sintéticos indivisibles por celda, una provincia; P=4000, K=4, target=1000, tolerancia dura ±20%, mismas poblaciones y mismas geometrías en ambas asignaciones. La matriz de población se encuentra en `results.json`.

| Candidato | Asignación | Poblaciones | Σ|p−target| | máx |p−target|/target |
|---|---|---|---:|---:|
| A | Filas | 1150, 950, 950, 950 | 300 | 15% |
| B | Columnas | 1100, 1100, 900, 900 | 400 | 10% |

Ambos tienen compactación idéntica (rectángulos 1×4) y retención comarcal 100%. La conservación, K, atomicidad y contigüidad se comprueban directamente. El ranking histórico por L1 prefiere A; el máximo relativo prefiere B. Se ejecuta el `assemble()` real de `ddd_ensemble/ensemble_assembler.py`: Pareto y shortlist prefieren B, y rechazan C. Los informes sintéticos prueban la selección, no validación territorial independiente.

Se ejecutan también `hard_constraint_violations`, `plan_metrics` y `select_best_state` reales de `ddd_core/m05_gerrychain_engine.py`, con geometrías/áreas/perímetros/fuentes de adyacencia sintéticas y contrato K4, provincia K4 y tolerancia 20%, sin desactivar disciplina municipal, unidades, provincias, contigüidad o preservación urbana (no hay distritos urbanos cerrados en el fixture). Seleccionan B: score B=0,5110398465 frente A=0,5235398465. El motor mide churn respecto a A, que penaliza B: esta métrica adicional no se presupone idéntica. Compactación calculada por área/perímetro/frontera coincide con las uniones Shapely a tolerancia 1e−12. No se ejecuta GerryChain/ReCom, ni la estrategia dependiente de GeoPandas/NetworkX.

C reasigna dos celdas de la segunda fila a la primera, conserva universo/K y su geometría sigue conexa, pero tiene poblaciones 2000,100,950,950. El motor rechaza `population_cap:0`, `population_floor:1`, `population_tolerance:0` y `population_tolerance:1`. Ninguna mejora de ranking acepta C.

Estos resultados no prueban que DDD siempre priorice máximo relativo: engine usa suma ponderada y strategy usa bandas/compactación, y otros ejemplos pueden producir decisiones diferentes.

## E2: pérdida de universo y K por redondeo local

Contraste analítico del mecanismo de `CELL 34` y `CELL 38` del notebook: `(target−island_pop)/island_pop > init_epsilon` elimina un nodo aislado o omite un componente. Con target1000, isla100 y epsilon0,05, el cociente es9 y el mecanismo pierde una unidad/100 habitantes/una celda geométrica de un universo de5 unidades/4100 habitantes. No se ejecuta el código de Nacho ni se utiliza esta población como una fuente DDD.

`CELL 37` calcula `round(P_component/target)` por componente. Con P_component=[1490,1490,1020], P4000 y K contractual4, da [1,1,1] y suma3; [1510,1510,980] da [2,2,1] y suma5. Con [500,500,1000], K2 y target1000, el redondeo bancario de Python da [0,0,1], suma1 y componentes sin distrito. Se exige puerta de factibilidad/contrato: la conservación de K global no garantiza que existan particiones físicamente conexas dentro de tolerancia. Estos casos no afirman que sea posible reparar componentes reales ni autorizan puentes.

## E3: aplazar uniones geométricas manteniendo ranking L1

Se comparan dos implementaciones independientes del postprocesado, no algoritmos de generación:

1. Tally poblacional y unión de geometrías para todos los S=56 estados, almacena 224 geometrías de distrito; orden estable `(L1, índice)` y top10.
2. Tally poblacional para los mismos56 estados y orden estable idéntico, unión solamente para top10, almacena40 geometrías.

N=800 (80×10) y N=3200 (160×20); K4; población100 por celda; cortes verticales perturban ±2 columnas y producen cuatro franjas rectangulares. Seed17/29/43, target P/4 y límite duro ±20%. Ambas rutas usan exactamente los mismos inputs y restricciones, S y top. Las asignaciones se preconstruyen, no resultan de una cadena Markov; algunas son duplicadas (45–46 únicas/56). No se impone diversidad artificial ni selección por compactación o comarca. Comarcas/municipios singleton permanecen intactos en todos los estados. Se verifican las poblaciones de todos los estados y BFS/Polygon/universo íntegro de todos los seleccionados fuera del intervalo de medición.

| N | Mediana speedup (3 semillas) | Tiempo todas las uniones | Tiempo tally+top10 |
|---:|---:|---:|---:|
| 800 | 5,15× | 2,34–3,06 s | 0,44–0,68 s |
| 3200 | 4,88× | 10,19–12,04 s | 1,98–2,53 s |

En las seis parejas: input SHA idéntico, mismos pasos seleccionados, igualdad exacta de población/asignación/WKB de los40 polígonos seleccionados y cero violaciones sintéticas. La firma conjunta incluye cada índice seleccionado, población y WKB de cada distrito; el hash de inputs incluye población y todas las asignaciones. Se comprueba además `equals_exact(..., 0)` respecto a reconstrucción directa y conservación de la geometría exterior completa, sin solapamientos de área.

Medición: `perf_counter` con `tracemalloc` activo. Tiempo excluye construir fixtures y validar seleccionados; incluye tally/ranking/uniones. `tracemalloc` mide asignación Python y **excluye memoria nativa de GEOS**, así que su ahorro no equivale a memoria geométrica total. RSS es pico del subprocess entero hasta la lectura (imports+fixtures+trabajo, antes de verificación), en bytes macOS; mejora modesta y dependiente del ruido (≈2–5%). No se reporta un coste real territorial ni un intervalo de confianza, y 3 semillas no bastan para inferencia estadística general.

## Correspondencia y decisión

Origen: notebook `CELL 38`, líneas475–488 en `/private/tmp/nplaton-notebook-cells.txt`: disuelve todas las iteraciones antes de calcular residual L1 y materializar top10. No se mide GeoPandas completo: se aísla `union_all`, excluye DataFrames, Excel, Kepler y generación. E3 cuantifica ahorro del mecanismo aislado sobre rejillas rectangulares.

DDD ya contiene un mecanismo mejor: `ddd_core/m05_gerrychain_engine.py:510` y `ddd_core/m05_gerrychain_strategy.py:750` calculan compactación O(n+e) sumando áreas/perímetros y restando fronteras compartidas, sin disolver cada estado. Por tanto E3 **no justifica una nueva optimización del ranking productivo** ni su sustitución por L1. Es candidato para herramientas de exportación de alternativas que hoy hicieran uniones redundantes, pendiente de localizar caller y autorización Work. Si el ranking futuro depende de geometría que no tenga una fórmula equivalente, preseleccionar con L1 podría descartar la mejor solución: requeriría equivalencia exacta, cache por assignment hash o cota admisible.

No se repiten A-OPT01/02: tratan candidatos de grafo y correspondencias M01/M02, no este postprocesado; no se tocan A1/A2/A3/N1/N2. Sin código productivo, commit, PR, push, workflows, territorios ni publicación. Esta evidencia requiere revisión separada antes de incorporarse a una recomendación; no existe GO productivo por estos resultados.

## E5: cociente exacto sección→unidad y validación de conectividad

```sh
python3 /private/tmp/ddd-nacho-experimentos-20261010/graph_contraction.py
```

Script separado stdlib, sin repetir E1–E3. Grid de16×8 municipios; cada municipio consta de q=4/8/16 secciones horizontales conexas con población100. El grafo fuente conecta vecinos ortogonales (equivale a frontera compartida positiva entre cuadrados), sin puentes. La contracción agrega sólo aristas fuente cuyos extremos pertenecen a unidades distintas y suma población de todas las secciones; no infiere adyacencia de envolventes.

Se comparan 2000 asignaciones municipales preconstruidas por cada seed17/29/43: cuatro franjas, cortes en4/8/12 columnas con desplazamiento global−1/0/+1 y permutación determinista de etiquetas. Ambas rutas usan exactamente el mismo universo, seed, K4, P, target P/4, tolerancia dura±25%, municipalidad atómica y presupuesto2000. La ruta fuente expande cada asignación a secciones y evalúa BFS/población; la otra construye una vez el cociente y evalúa BFS/población sobre las128 unidades.

| q | N fuente | E fuente | N/E cociente | Tiempo fuente, 2000 estados | Tiempo construcción+BFS cociente | Mediana speedup, 3 seeds |
|---:|---:|---:|---:|---:|---:|---:|
| 4 | 512 | 952 | 128/232 | 3,34–3,48 s | 0,75–0,81 s | 4,33× |
| 8 | 1024 | 1912 | 128/232 | 7,09–7,98 s | 0,78–0,95 s | 8,67× |
| 16 | 2048 | 3832 | 128/232 | 13,66–16,39 s | 0,74–0,94 s | 17,37× |

Construcción del cociente incluida en tiempos:0,69–0,76ms(q4),1,61–1,84ms(q8),3,54–4,21ms(q16). Cada subprocess tiene timeout60s y todos finalizan. `graph_results.json`, `graph_q*_seed*_*.json` y `graph_run.log` conservan medidas y hashes. En las9 parejas los hashes de inputs y de todos los resultados poblacionales/contigüidad son idénticos; cero violaciones en2000/2000 asignaciones preconstruidas. Esto no representa probabilidad de éxito territorial o de inicialización ni de una cadena, y los estados incluyen repeticiones.

Se comprueba cobertura exacta disjunta del universo de secciones por las128 unidades, cada unidad conexa en fuente, población preservada, aristas cociente exactamente derivadas de fuente y roundtrip `municipal→secciones→municipal` idéntico para todos los candidatos. La función sección→unidad es muchos-a-uno: **no es biyectiva**. La biyección sólo existe entre asignaciones municipales admisibles y sus expansiones atómicas.

Caso negativo: grafo fuente A1–B–A2, municipioA={A1,A2}. El cociente A–B representa A como un único nodo. Partición `{A→d0,B→d1}` parece conexa en el cociente y conserva población, pero d0 tiene dos componentes físicos en fuente. Se verifica esa divergencia y se declara REJECT de la contracción pura. La preservación del universo y de la población no bastan: mantener comprobaciones independientes por componentes poligonales/adyacencia física y excepciones acreditadas. Este caso no permite dividir automáticamente una unidad indivisible ni crear puentes.

Memoria: pico tracemalloc fuente620–807kB frente cociente≈618kB; RSS fuente17,8–20,7MB frente cociente17,3–18,1MB. Ambas rutas conservan el grafo fuente como fixture y todos los resultados para su hash, por lo que estas cifras **no miden** memoria del grafo aislado ni proyectan ahorro productivo. Construcción de fixtures y verificaciones de integridad se excluyen del cronómetro, igual en ambas rutas; construcción del cociente y expansión repetida fuente se incluyen.

La estrategia canónica DDD ya opera con `ddd_unit_id` agregado. Este experimento sólo demuestra el mecanismo equivalente para unidades conexas y candidatos ya admisibles. Para caminos de ensemble que aún proponen sobre secciones, la hipótesis sería proponer sobre unidades para evitar propuestas que rompan atomicidad, manteniendo el gate físico; medir propuestas/rechazos/mezcla requiere GerryChain real, entradas acreditadas y autorización posterior. No se ha demostrado ese beneficio de ReCom aquí.
