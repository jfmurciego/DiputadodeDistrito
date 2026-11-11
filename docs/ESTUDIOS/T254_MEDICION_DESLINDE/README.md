# T-254 · Medición de Deslinde 1.0: tiempo por fase, código muerto, duplicados y reparaciones

Solo se ha medido; el motor no cambia. Este trabajo da entrada a la fase de optimización (D-85, D-89: mismos mapas bit a bit). Todas las cifras salen de los ficheros de
`resultados/` y se regeneran con los comandos de la sección 6. Máquina: sesión cloud con 4 CPU y Python 3.13.18,
commit `ee8e776`, `requirements.lock` + gerrychain 1.0.0 `--no-deps`, `PYTHONHASHSEED=0`.

**Territorios.** Se usan tres territorios pequeños cuyas entradas se reconstruyen desde fuente
(`bateria_motor.py entradas --seccionado shapefile`, 18 s en total):
- `congreso_huesca`: K=2, 202 unidades;
- `congreso_la_rioja`: K=3, 175 unidades;
- `la_rioja` (autonómica): K=33, 193 unidades. Su contrato declara `closed_target_cores_plus_open_residual` y `private_annealing`, así que pasa por esas capas del M04 y el M05.

Soria y Melilla no sirven para medir: tienen K=1 en el Congreso.

## 1. Tiempo por fase (competición de la batería = P30, 10 cadenas, D8)

Son 3 repeticiones por territorio. Cada cifra es media ± desviación típica, en segundos, y el porcentaje es sobre el total de la competición. En las 3 repeticiones salen las mismas huellas (ganador, `huella_resultado` y sha256 de cada composición): `resultados/MEDICION.json`.

| Fase | congreso_huesca | congreso_la_rioja | la_rioja |
|---|---|---|---|
| **Exhaustivo** (enumeración exacta, `_exhaustivo`) | **92,61 ± 1,94 (81,2 %)** | **124,68 ± 2,24 (86,6 %)** | **50,90 ± 0,57 (60,5 %)** |
| Cadenas ReCom (10 × `Ponderado.generar`) | 14,62 ± 0,21 (12,8 %) | 13,69 ± 0,49 (9,5 %) | 24,13 ± 0,65 (28,7 %) |
| — de ellas, clave D8 dentro de la cadena | 0,55 ± 0,01 | 0,49 ± 0,02 | 1,15 ± 0,04 |
| — de ellas, piezas finas | 0,00 | 0,00 | 0,42 ± 0,01 |
| Canónico (M04 + M05 + M06 + validación, subprocesos) | 6,05 ± 0,05 (5,3 %) | 4,90 ± 0,14 (3,4 %) | 8,36 ± 0,13 (9,9 %) |
| — M04 (semillas) | 2,40 ± 0,00 | 2,03 ± 0,06 | 2,83 ± 0,06 |
| — M05 (optimización) | 1,93 ± 0,06 | 1,37 ± 0,06 | 3,90 ± 0,10 |
| — M06 | 0,97 ± 0,06 | 0,83 ± 0,06 | 0,90 ± 0,00 |
| — validación (`validar_ejecucion`) | 0,57 ± 0,06 | 0,53 ± 0,06 | 0,57 ± 0,06 |
| Elección D8 (`juzgar` de los 12 candidatos) | 0,71 ± 0,07 (0,6 %) | 0,51 ± 0,04 (0,4 %) | 0,54 ± 0,02 (0,6 %) |
| Vigente (piezas finas + evaluación) | 0,11 ± 0,00 | 0,10 ± 0,01 | 0,14 ± 0,02 |
| **Total competición** | **114,11 ± 2,06** | **143,90 ± 1,68** | **84,08 ± 0,30** |

Tiempos de los pasos de producción y certificación (1 ejecución, `resultados/MEDICION.json` → `p30`):

| Paso | congreso_huesca | congreso_la_rioja | la_rioja |
|---|---|---|---|
| P30 `produccion competir` (competición con el canónico del run reutilizado) | 108,03 | 136,95 | 76,08 |
| P30 rehacer M06 + `verificar` | 0,97 + 0,10 | 0,86 + 0,13 | 0,90 + 0,10 |
| Certificación: auditoría geométrica (`auditar_componentes_geometricos`) | 2,83 | 2,90 | 2,85 |

En los tres territorios el P30 acaba en `P30_GANA_OTRO_PLAN`, con el mismo ganador que la batería.

**Lectura de las cifras**

1. **El exhaustivo se lleva entre el 60 % y el 87 % del tiempo y no aporta nada.** En los tres territorios agota los 200 000 nodos sin acabar («enumeración incompleta», `metodo=cadena`, 0 válidos) y no añade candidato. Bajo cProfile (`resultados/perfil_competicion_la_rioja.txt`), `podar` acumula 201 s de los 203 s del exhaustivo. Dentro de `podar`:
   - recalcula en cada nodo la población y las piezas de todos los municipios, que son constantes del problema;
   - llama a `Contexto.rango_municipal` 8,7 millones de veces, con dos divisiones de `Fraction` en cada llamada (17,7 millones de operaciones inversas de `Fraction`, `fractions.py:680 reverse`).
2. **Las cadenas ReCom son la segunda fase (10-29 %).** Dentro de `recom` (69 s bajo cProfile en La Rioja), el árbol ponderado (Kruskal con pesos en Python, `arbol_ponderado`) acumula 41 s y `nucleo`/`evaluar` 21 s.
3. **El canónico M04+M05 pesa poco (3-10 %).** Bajo cProfile, en La Rioja:
   - M04: `connected` de `m04_seed_engine_v7410` (BFS desde cero, 50 877 llamadas) acumula 3,07 s de 5,9 s (`perfil_m04_la_rioja.txt`);
   - M05: la puerta privada `_official_private_candidate_gate` acumula 2,61 s de 5,10 s, de los que 2,29 s son 3 subprocesos (M06, `validar_ejecucion`, auditoría geométrica) que la 00 vuelve a ejecutar justo después. El recocido base (`_run_base`) acumula 1,70 s (`perfil_m05_la_rioja.txt`).
4. Elección D8, vigente, P30 sin competición y certificación suman menos de 4 s por territorio.

**Experimento de caché (no es un cambio del motor).** `experimento_memo.py` memoriza `Contexto.rango_municipal`, una función pura de (p, techo, objetivo), solo dentro de su propio proceso. El resultado (`resultados/EXPERIMENTO_MEMO.json`, 1 ejecución frente a la repetición 0 de `MEDICION.json`):

| Territorio | Total con caché (s) | Total sin caché (s) | Exhaustivo con / sin caché (s) | Ganancia | Huella, composiciones y ganador |
|---|---|---|---|---|---|
| congreso_huesca | 88,38 | 115,66 | 67,49 / 93,90 | −23,6 % | idénticos |
| congreso_la_rioja | 108,76 | 145,54 | 90,23 / 126,70 | −25,3 % | idénticos |
| la_rioja | 77,18 | 83,78 | 42,40 / 50,95 | −7,9 % | idénticos |

## 2. Código muerto (`codigo_muerto.py` → `resultados/codigo_muerto.json`; vulture 2.16 → `resultados/vulture.txt`)

**Método.** Se parte de los puntos de entrada de producción:
- `modulos/0*.py`, `ddd_motor2/produccion.py` y `competir.py`;
- las herramientas y los `ddd_core/*.py` citados en `.github/workflows/*` y `procedimiento.sh`, y `ddd_ensemble`.

Desde ellos se calcula el cierre de imports, incluidos los imports por ruta (`ROOT / "ddd_core" / "x.py"`). Vivo = alcanzable desde producción. Una mención en un comentario `ANTERIOR:` no cuenta como uso.

Resultado sobre 78 módulos de `ddd_core/` y `ddd_motor2/` (23 451 líneas): 52 vivos, 7 solo herramientas, 10 solo tests, 7 solo legacy y 2 sin referencias. Fuera de producción quedan **5 849 líneas**.

| Módulo | Líneas | Estado | Quién lo usa | Retirar al archivo |
|---|---|---|---|---|
| `ddd_core/m04_seed_engine_v746`, `v748` | 117 + 296 | sin referencias | — | sí, sin tocar nada más |
| `ddd_core/m04_seed_engine_v747`, `v749`–`v754` | 290+312+69+92+115+115+115 | solo legacy | `legacy/` | sí |
| `ddd_core/m04_seed_engine_v745` | 318 | solo tests | `test_m04_oversized_municipality_hard_bounds` (import), `test_galicia_local_e2e_regression` (lee el fuente) | sí, moviendo o retirando esos 2 tests |
| `ddd_core/m05_opt_engine_v740` | 444 | solo tests | `test_huella_m05_motor_activo` (comprueba que NO está en la huella) y `herramientas/huella_checkpoint_m05.py` (solo en la cabecera) | sí, ajustando ese test |
| `ddd_motor2/naturalidad_informe` | 261 | solo tests | 1 test | decidir (informe del laboratorio) |
| `ddd_core/congreso_*` (12 módulos: candidate_certifier, cnig_receipt, ign_api_snapshot, ign_historical_wms, national_composer, product_manifest, bounded_tree_search, exact_feasibility, feasibility, readiness, topology, preflight_adapter) | 3 101 | solo tests o herramientas | herramientas y auditorías del piloto Congreso | **no** sin revisar N08: sus evidencias fijan hashes de `congreso_preflight_adapter` y `congreso_topology` (`huellas.md`) |
| `ddd_core/m06_schema`, `national_campaign_planner` | 75 + 129 | solo herramientas o tests | herramientas de catálogo y planificación | fuera del motor; no tocar |

Los 10 módulos M04 viejos (`v745`–`v754`) suman **1 839 líneas**. La cadena viva de M04 es `m04_seed_engine` → `v7412` → `v7410`, más `v7411` (postproceso) y `m04_closed_target_cores` / `m04_overcap_residual_relief` / `m04_partition_contract` / `m04_administrative_atomic_groups`.

**Funciones de nivel superior sin uso fuera de legacy o tests, dentro de módulos vivos**

| Símbolo | Líneas | Uso |
|---|---|---|
| `m05_gerrychain_engine.run_gerrychain` | 101 | solo legacy y tests |
| `m05_gerrychain_engine.select_best_state` | 20 | solo legacy y tests (`load_comarca_lookup` y `adapt_files` los usa `ddd_ensemble/runner.py`, la 07: vivos) |
| `congreso_contract.validate_production_admission` | 6 | solo legacy y tests |
| `ddd_motor2/produccion._grupos` | 5 | solo legacy |
| `m05_population_repair._province_state_key` | 2 | solo legacy |

Falsos positivos de vulture: las variables `epsilon`, `pop_target`, `region_surcharge` y `treat_unassigned_as_single_region` de `naturalidad_competicion.py:282/289` existen porque GerryChain exige esa firma.

## 3. Duplicados

La búsqueda la hizo un subagente; aquí solo entran las entradas comprobadas a mano. Ninguna cambia resultados hoy, pero todas pueden divergir.

| Tema | Implementaciones | Divergencia posible | En producción |
|---|---|---|---|
| Contigüidad / componentes (BFS copiado) | `m04_seed_engine_v7410.connected/components`, `m04_seed_engine._components`, `m04_closed_target_cores._connected`, `m05_opt_engine_v741`, `m05_swap_polish`, `m05_population_repair`, `m05_private_annealing`, `modulos/04`, `validar_ejecucion.components`, `ddd_motor2/reglas/evaluar.conexo`, `reglas/enumerar._componentes` | conjunto vacío: `conexo` devuelve True y el resto False; cada una con su adyacencia | todas |
| Fuera de tolerancia | `m05_opt_engine_v741` y `m04_seed_engine_v7410` en float sin épsilon; `reglas/evaluar` y `naturalidad_clave.fuera_regional` exactos (`Fraction`); `bateria_motor.metricas` y `banco_generadores` en float con `+1e-9`; `m05_gerrychain_strategy` con `+1e-12` | bordes exactos | M04, M05 y motor 2 |
| Límites objetivo/suelo/techo | `ddd_core/config.hard_limits` (float) frente a `reglas/modelo.Reglas.limites` (`Fraction`) | bordes exactos | las dos |
| R012 disciplina municipal | `validar_ejecucion` (mixtos fijo `>1`, `ceil` en float); `reglas/evaluar.violaciones_municipio` (`max_mixtos` del contrato); `m05_opt_engine_v741.MunicipalDiscipline` (`max_mixed_districts_per_split_municipality`) | con `max_mixed>1`, VAL rechaza lo que M05 y motor 2 aceptan | las tres |
| Puentes del contrato | `adaptadores._puentes_contrato` solo mira `cfg["modulo_02_construir_adyacencias"]` en la raíz; los contratos los tienen en `cfg["modulos"]["modulo_02_…"]`, así que la función devuelve vacío y los puentes llegan solo por `edge_type` del grafo M03. `naturalidad_competicion.puentes_contrato` recorre todo el contrato | evaluar y cadena pueden ver contigüidades distintas | las dos (motor 2) |
| Lectura de GeoJSON en ZIP | `modulos/05._raw_geojson`, `ddd_motor2/produccion._leer_geojson`, `adaptadores.leer_atributos`, `bateria_motor` | criterio de miembro del ZIP | sí |
| Puerta privada de M05 | M05 ejecuta M06 + `validar_ejecucion` + auditoría geométrica sobre su candidato (`_official_private_candidate_gate`), y la 00 ejecuta M06 y la validación otra vez | ninguna (mismo código), tiempo doble | sí |

## 4. Reparaciones del motor viejo (D-85): qué hay, quién las usa y qué depende de ellas

Se cuentan los 71 contratos `*_2025.yaml` que no son `congreso350` (`oversized_municipality_rule`, `population_repair`, `swap_polish_max`).

| Capa | Fichero | Activa en | Retirarla cambia | Depende |
|---|---|---|---|---|
| Núcleos objetivo cerrados (M04) | `m04_closed_target_cores` | 3: Castilla y León, Galicia, La Rioja (`closed_target_cores_plus_open_residual`) | el canónico de esos 3, y con él la referencia R-NUCLEO de la competición | `test_m04_structural_formation`; huella M04 (`m04_*.py`) |
| Alivio de residuos sobre techo y enclaves dependientes (M04 7.6.7) | `m04_overcap_residual_relief`, `m04_seed_engine._with_dependent_enclaves` | contratos con municipio dividido sobre techo (T-44: Elche + Santa Pola, Málaga) | el canónico de esos territorios | `test_m04_overcap_residual_relief`; huella M04 |
| Reparación de población (M05) | `m05_population_repair` | 61 de 71 (activa por omisión: 52 sin bloque y 9 con `enabled: true`) | la huella M05; los mapas solo donde actúa | **N08** (5 menciones: `test_preflight_caceres_n08`, `verificar_evidencia_n08_readonly`), `test_m05_population_repair`, `test_m05_real_repro_evidence`, `test_huella_checkpoint_motor` |
| Recocido privado (M05) | `m05_private_annealing` | 10 (`strategy: private_annealing`): Andalucía, Canarias, Cataluña, Navarra, C. Valenciana, Baleares, La Rioja, Madrid, País Vasco, Murcia; en La Rioja el informe M05 da `population_repair.result=NOT_NEEDED` | huella M05 y canónico de esos 10 | `test_m05_private_annealing` |
| Pulido por intercambios (M05) | `m05_swap_polish` | 1: Extremadura (`swap_polish_max>0`); en el resto `enabled=false`. Además da `load_geo`/`write_geo` a M05 | huella M05; mapa de Extremadura | `test_m05_population_status_integrity`, `test_motor2_exhaustivo`, `test_huella_checkpoint_motor` |
| Puerta privada M06 + VAL + auditoría dentro de M05 | `modulos/05._official_private_candidate_gate` | todos | nada en el mapa (es una comprobación), siempre que la 00 mantenga M06 + validación + auditoría después | R015 `M05Determinism`, R016 (informe de Aragón) |
| Reparación D-66 del vigente (motor 2) | `ddd_motor2/generadores.reparar` | solo si el publicado incumple R-NUCLEO (Cataluña, Ávila); en estos 3 territorios no actúa (`reparado=None`) | el candidato vigente de esos territorios | huella motor2 (todo `ddd_motor2/*.py`) |

Lo que no se puede retirar sin decidir: el canónico (M04 + M05 con sus capas) es candidato, punto de partida de las cadenas y referencia de los núcleos cerrados. Retirar cualquier capa que actúe en un territorio cambia ese canónico y, por tanto, `huella_resultado` aunque no gane. Solo se puede retirar con mapas bit a bit si la capa no actúa en ninguno de los 71; esa comprobación es la batería completa (`aceptacion` + `huella`).

## 5. Optimizaciones, ordenadas por ganancia estimada y riesgo

La ganancia sale de las mediciones anteriores. Mapas idénticos significa ganador y composición de cada candidato iguales. Las tres huellas son estas:
- **huella motor2**: sha256 de los ficheros de `ddd_motor2/` más los datos de naturalidad (`produccion.huella_motor`). Cambia con cualquier edición de `ddd_motor2/` y obliga a rehacer el P30, aunque los mapas sean iguales.
- **huella M05**: cierre de imports desde `modulos/05`. Cambia con cualquier edición de esos ficheros, `ddd_core/config.py` incluido.
- **huella M04**: `m04_*.py`.

| # | Optimización | Ganancia estimada | Mapas | Huellas que cambian | Riesgo |
|---|---|---|---|---|---|
| 1 | **Exhaustivo: `podar` incremental.** Precalcular por problema `m_tot`/`m_n` y las piezas por municipio, memorizar `rango_municipal` y mantener los acumulados por distrito al asignar y desasignar, en vez de recalcular todo en cada nodo | ya medido −8 % a −25 % del total solo con la caché de `rango_municipal`; el techo es casi todo el exhaustivo (51-127 s, 60-87 %) | idénticos (mismos nodos y decisiones; probado con la caché) | motor2 | bajo; se comprueba con `huella_resultado` en la batería |
| 2 | **Exhaustivo: no intentarlo cuando no puede acabar** (cota previa por unidades/K, o presupuesto menor) | hasta el 60-87 % del total en estos 3 | idénticos: no aporta candidato cuando no completa | motor2 **y `huella_resultado`** (en la huella entran `exhaustivo.nodos`/`metodo`, y `Criterio` en `huella_reglas`) | medio: es un cambio de criterio y hay que decidir si se acepta otra `huella_resultado` |
| 3 | **Cadenas: árbol ponderado y `nucleo` más baratos.** Pesos en vectores en lugar del bucle Python por arista; `lab.valido` incremental y `rango_municipal` en caché (también lo usa `evaluar`) | parte de 14-24 s por territorio (10-29 %); bajo cProfile, árbol 41 s y núcleo 21 s de 69 s de `recom` | idénticos solo si se conserva el orden de las llamadas a `rng.random()` | motor2 | medio: el orden del RNG fija el mapa |
| 4 | **M05: quitar la puerta privada duplicada** (M06 + VAL + auditoría dentro de M05, que la 00 repite después) | ~2,3 s por canónico (cProfile La Rioja) y ~2,8 s de auditoría | idénticos | **M05** (checkpoints M05/M06; 00 «Ejecutar desde el principio»), R015/R016 | medio: la puerta también decide si se admite el candidato |
| 5 | **M04: `connected` incremental o con caché en `find_peel`** | ≤ 3 s por M04 (cProfile La Rioja: 3,07 de 5,9 s) | idénticos si no cambia el orden de exploración | **M04** (y la evidencia pre-M04 de `physical_components` si se toca `modulos/04`) | medio |
| 6 | **Retirar al archivo el código muerto**: M04 `v745`–`v754` (1 839 líneas) y M05 `v740` (444) | ninguna en tiempo; mantenimiento | idénticos (no se ejecutan) | ninguna de motor (no están en el cierre de imports) | bajo; ajustar 3 tests |
| 7 | **Unificar duplicados** (contigüidad, límites float/`Fraction`, R012, puentes, lectura de ZIP) en un módulo común | ninguna en tiempo | riesgo de cambio en los bordes exactos | M04, M05 y motor2 | alto: hay que probar los 71 bit a bit |
| 8 | **Retirar capas de reparación** (sección 4) | canónico de 1-4 s | **cambian** donde la capa actúa | M04/M05, N08, `huella_resultado` | alto; necesita decisión del propietario |

Recomendación técnica: empezar por la 1 (bit a bit, ya probada en parte) y la 6. Para la 2 hace falta decidir si se acepta una `huella_resultado` nueva con los mismos mapas.

## 6. Cómo reproducir

```bash
pip install -r requirements.lock
pip install --no-deps gerrychain==1.0.0
pip install networkx==3.6.1 rustworkx==0.18.1 scipy==1.18.1 tqdm==4.70.1 six==1.17.0 vulture==2.16
python3 herramientas/bateria_motor.py nacionales
python3 herramientas/bateria_motor.py entradas congreso_huesca congreso_la_rioja la_rioja --seccionado shapefile
# 1. tiempos por fase (≈ 30 min): resultados/MEDICION.json
PYTHONHASHSEED=0 python3 docs/ESTUDIOS/T254_MEDICION_DESLINDE/medir.py --rep 3 --p30 congreso_huesca congreso_la_rioja la_rioja
# experimento de caché (≈ 5 min), compara con la repetición 0: resultados/EXPERIMENTO_MEMO.json
PYTHONHASHSEED=0 python3 docs/ESTUDIOS/T254_MEDICION_DESLINDE/experimento_memo.py congreso_huesca congreso_la_rioja la_rioja
# perfiles (proporciones; cProfile multiplica por ~4 el tiempo del exhaustivo)
PYTHONHASHSEED=0 python3 -m cProfile -o lr.prof -m ddd_motor2.competir --out bateria la_rioja
export DDD_RUN_ID=bateria-la_rioja-7.4.4 PYTHONHASHSEED=0 DDD_OPTIMIZATION_ALGORITHM="Canónico"
python3 -m cProfile -o m04.prof modulos/04_generar_semillas.py --params territorios/la_rioja/config/la_rioja_2025.yaml
python3 -m cProfile -o m05.prof modulos/05_optimizar_distritos.py --params territorios/la_rioja/config/la_rioja_2025.yaml
# 2. código muerto
python3 docs/ESTUDIOS/T254_MEDICION_DESLINDE/codigo_muerto.py > codigo_muerto.json
vulture ddd_core ddd_motor2 modulos/04_generar_semillas.py modulos/05_optimizar_distritos.py --min-confidence 60
```

## 7. Límites

- Hay solo 3 territorios pequeños; con K≥3 solo La Rioja autonómica, y ninguno de más de 202 unidades. En los grandes, el exhaustivo también se queda en el presupuesto, pero el peso relativo de las cadenas y del canónico crece. Antes de optimizar, hay que repetir `medir.py` en 5-6 territorios medianos.
- La reparación D-66 del vigente no actúa en estos 3 (`reparado=None`), así que su tiempo no está medido. El recocido privado se ejecuta solo en La Rioja y allí no hace falta (`NOT_NEEDED`): su coste con reparación real no está medido.
- `estado_produccion` (certificación completa) no se ha medido: necesita el estado de un run. La certificación medida es la auditoría geométrica más la validación.
- El reparto interno de M04 y M05 y el de las cadenas sale de cProfile (1 ejecución, con sobrecoste); se da como proporción, no como tiempo real.
- El experimento de caché es 1 ejecución frente a la repetición 0 de `MEDICION.json`. La desviación típica entre repeticiones es de 0,3 a 2,2 s.
- Los duplicados (sección 3) son una revisión de código, sin pruebas de divergencia con datos.
