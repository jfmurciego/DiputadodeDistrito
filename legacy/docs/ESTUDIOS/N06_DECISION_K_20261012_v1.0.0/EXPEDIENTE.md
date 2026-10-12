# N06 — Expediente definitivo para decidir K del Congreso

**Versión:** 1.0.0. **Fecha:** 2026-10-12. **Alcance:** decisión institucional del frente Congreso, edición 2025. **Estado:** propuesta técnica `WAIT_OWNER`; ninguna decisión adoptada. **Cambios y motivo:** completa N05 con comparaciones de K fijo y textos de decisión. **Origen:** expediente nuevo; no sustituye estudios, contratos ni evidencias anteriores.

**Tarea existente:** N06 del Plan Maestro `ddd-maestro-20261008`, copia viva `ddd-maestro-vivo-20261011`. Base: `1fdb75771a92be52813a6bd28894462e58a36fdd`, main con PR #237 y #239. Vinculación y hashes del Plan en [vinculo_plan.json](vinculo_plan.json). Su estado formal observado es `PENDING`, porque requiere aprobación; este expediente expresa `WAIT_OWNER` y no cambia el Plan ni crea otra tarea.

## Propuesta que se somete a decisión

Recomendar **K=350**, con **dos plazas iniciales por cada una de las 50 provincias, una fija para Ceuta y una fija para Melilla, y mayores restos sobre la población de las 50 provincias para repartir las 248 restantes**. Es la opción que conserva el tamaño legal actual y toma su regla territorial como referencia explícita para el modelo DDD. Su aprobación dentro del proyecto sería una decisión del propietario, no una inferencia automática del número de diputados.

Recomendar aprobar, si el propietario lo considera adecuado, **únicamente K y esta regla como base de planificación institucional**, sin autorizar generación ni declarar cumplidos los límites de población. No recomendar como contrato integral ninguna opción bajo la conjunción actual de barreras provinciales, representación positiva y suelo exploratorio de 96.000: esa conjunción es imposible con la población 2025. Si el propietario exige aprobar conjuntamente todas esas condiciones sin revisarlas expresamente, la recomendación es **no aprobar ninguna opción**. Los dos textos de decisión completos figuran al final.

La evidencia permite recomendar 350 por coherencia institucional, pero no demuestra que sea un óptimo geográfico ni una solución productiva factible. El expediente no convierte el objetivo 120.000 en norma ni concede excepciones a las ciudades, islas o provincias pequeñas.

## Fundamento institucional y límites de la analogía

La Constitución fija un intervalo de 300–400 diputados, la provincia como circunscripción, un representante para cada ciudad autónoma, una asignación inicial y reparto poblacional del resto. También exige criterios de representación proporcional en cada circunscripción. Estar dentro del intervalo no acredita por sí solo un modelo uninominal DDD. [Constitución, art. 68](https://www.boe.es/buscar/act.php?id=BOE-A-1978-31229#a68).

La LOREG establece 350 diputados, dos iniciales por provincia y uno por ciudad; los 248 restantes se reparten por cocientes enteros y mayores fracciones sobre la población provincial peninsular e insular. El decreto de convocatoria fija el número a elegir por circunscripción. El reparto por población calculado aquí sobre 2025 es una **aplicación analítica de esa estructura**, no el reparto oficial de una convocatoria acreditada. La distribución entre candidaturas del art. 163 es otra operación. [LOREG, arts. 161–163](https://www.boe.es/buscar/act.php?id=BOE-A-1985-11672#acientosesentaydos).

DDD propone unidades territoriales uninominales. Hacer coincidir una unidad con un diputado exige una decisión del proyecto; un cambio del sistema electoral no se produce por aprobar este expediente. Con K=350 se conserva el tamaño, no se demuestra compatibilidad jurídica del sistema uninominal con la representación proporcional. Con 383, 391, 392 o 400 se permanece en el intervalo constitucional de tamaño, pero se difiere del tamaño legal vigente; sería una propuesta de cambio institucional, no una aplicación del tamaño actual. Con 407, 409 o 435 se supera incluso ese intervalo si se pretende identificar K con diputados.

El precedente contiene **391 geometrías/IDs** coincidentes entre archivos y una incidencia documental 392/391 sin causa acreditada. Sus fuentes y ediciones demográfica y cartográfica no están acreditadas y conserva una geometría inválida. Es evidencia de existencia de material histórico, no mandato de K, mapa 2025 ni regla de reparto reconstruida. Se reutilizan los recuentos provinciales solo en un contrafactual claramente identificado; no se reparan ni generan geometrías.

## Evidencia 2025 utilizada

- Población agregada: **49.128.297**, a 1 de enero de 2025, 52 filas del estudio INE tabla 65034 ya conservado. [Fuente protegida](../modelo_nacional_2025_120000/fuente_poblacion.json), SHA-256 `6a5f16d1bf354bebb1d05ad0f9afc350d8dc1c7ea251aac3ce6002e392b16a7c`; ZIP de origen `91d3ff9a90bac1c06e26df97179daa325b65fa77c9209879d6a40333b17057f3`.
- N05: se conservan íntegros sus cinco repartos del [modelo protegido](../modelo_nacional_2025_120000/modelo.json), objetivo hipotético 120.000. Se verifica el manifiesto previo y la igualdad del universo provincial; no se sustituyen resultados.
- N07 integrado: **36.554 secciones y 52 circunscripciones**, con Ceuta 56 secciones y Melilla 44. [Evidencia N07](../N07_20261011/result/evidence.json). Este crosswalk acredita correspondencia administrativa de la edición; no acredita por sí mismo población por sección compatible, grafo, conectividad física ni overlay provincial independiente.
- [Contrato candidato](../../../territorios/congreso/contrato_congreso_2026.json): barreras provinciales duras, ciudades separadas, ninguna arista entre circunscripciones; `k_decision=WAIT_OWNER`, fuentes nulas, reglas de límites, islas, enclaves y discontinuidades pendientes; `generation_authorized=false`.
- Normativa consultada en BOE el 12 de octubre de 2026. Esta consulta documental no adquiere ni sustituye ninguna fuente demográfica o cartográfica de 2025. No se investiga ni adquiere población/geometría de 2026.

Los hashes de todas las entradas analíticas, código reusable y contrato se conservan en [comparaciones.json](resultados/comparaciones.json). Población agregada verificable no equivale a acreditación de una pareja productiva geometría/población: la decisión de referencia y su alineación a sección siguen pendientes.

## Alternativas y consecuencias comparables

Se distinguen tres familias: redondeos independientes respecto de 120.000, Hamilton puro con K global, y mínimos territoriales más residual provincial. El mismo total no hace equivalentes sus repartos. Las medias y errores son **proxies provinciales**, no poblaciones de distritos observados. El MAE se define como `Σ K_i × |P_i/K_i − 120000| / Σ K_i`; cuando hay K_i=0 se excluye esa media y se informa la población sin representación separadamente. Una puntuación menor no prevalece sobre las restricciones institucionales.

| Escenario y regla | K | Media nacional | MAE provincial ponderado frente a 120.000 | Circunscripciones fuera de límites necesarios |
|---|---:|---:|---:|---:|
| N05 inferior independiente | 383 | 128.272,32 | 7.591,33 | 4 |
| N05 más próximo independiente | 407 | 120.708,35 | 4.064,14 | 3 |
| N05 superior independiente | 435 | 112.938,61 | 7.061,39 | 10 |
| N05 Hamilton puro K derivado | 409 | 120.118,09 | 4.061,62 | 3 |
| N05 mínimos + residual K derivado | 409 | 120.118,09 | 22.345,40 | 20 |
| k300 minimos | 300 | 163.760,99 | 57.163,29 | 14 |
| k350 minimos | 350 | 140.366,56 | 36.747,28 | 17 |
| k383 minimos | 383 | 128.272,32 | 27.210,05 | 19 |
| k391 minimos | 391 | 125.647,82 | 25.030,15 | 19 |
| k392 minimos | 392 | 125.327,29 | 25.272,42 | 19 |
| k400 minimos | 400 | 122.820,74 | 22.791,56 | 19 |
| k350 hamilton puro | 350 | 140.366,56 | 20.989,97 | 3 |
| k391 hamilton puro | 391 | 125.647,82 | 7.364,94 | 3 |
| k400 hamilton puro | 400 | 122.820,74 | 5.030,40 | 3 |
| Recuentos históricos con población 2025 (contrafactual) | 391 | 125.647,82 | 8.852,70 | 3 |


Los límites necesarios de la última columna se calculan con suelo 96.000 y techo 210.000, exclusivamente como hipótesis heredada 0,80–1,75 del objetivo 120.000. No son límites nacionales aprobados. Un PASS de media provincial tampoco demuestra factibilidad de partición.

- **383 inferior independiente:** deja K=0 en Soria, Ceuta y Melilla: 260.817 habitantes sin plaza. Huesca recibe una plaza para 230.087 habitantes y supera el techo hipotético. Su suma no conserva mínimos legales. No se confunde con **383 con mínimos**, que sí representa las 52 pero produce otro reparto.
- **407 más próximo**, **409 Hamilton puro** y **435 superior**: siguen reglas diferentes; los dos primeros mantienen una sola plaza en diversas provincias y el tercero también incumple mínimos en Soria. Todos exceden 400. **409 con mínimos** es un cuarto reparto distinto y también excede 400, con Soria en 3 y media 30.061.
- **350 con mínimos**, propuesto: media nacional 140.366,56; Ceuta/Melilla 1 cada una; Soria 2 y media 45.091,50; Madrid 38 y media 187.207,53; Barcelona 32 y media 186.248,16. Las 52 tienen representación y ninguna media supera 210.000, pero **17** quedan bajo 96.000. La población por plaza en Madrid es aproximadamente 4,15 veces la de Soria. Es una consecuencia explícita de mínimos y redondeo, no una excepción aprobada.
- **350 Hamilton puro:** conserva el total pero concede una sola plaza a Ávila, Cuenca, Palencia, Segovia, Soria, Teruel y Zamora; no conserva el mínimo provincial de dos. Su menor MAE no lo convierte en la alternativa institucional recomendada.
- **391/392 con mínimos:** alternativas de tamaño reformador, no acreditación del antecedente. El recuento histórico de 391 reponderado con población 2025 tampoco equivale a Hamilton 391 ni a mínimos 391. Su columna de cuota es nula porque la regla histórica es desconocida.
- **300 y 400 con mínimos:** extremos útiles del intervalo; 300 sube la media a 163.760,99 y varias medias provinciales sobrepasan el techo. 400 baja la media a 122.820,74, pero no resuelve ciudades/Soria ni equivale al Congreso legal de 350. Para aproximarse a la media de 120.000 bajo máximo 400, 400 es el extremo aritmético más cercano; esa ventaja no decide el modelo institucional.

Hamilton puede no ser monótono en el tamaño de la cámara: con mínimos, Soria pasa de 2 plazas (391) a 3 (392) y vuelve a 2 (400). La regla y el desempate deben quedar expresos; no se supone que aumentar K solo añada distritos a todas las provincias.

## Tabla completa de la opción recomendada: K=350 con mínimos

Para las provincias, `q_i = 2 + 248 × P_i / 48.957.663`; para las ciudades, cuota fija 1. La cuota general de reparto residual es `48.957.663 / 248` habitantes por plaza residual. Primero se asignan las partes enteras de las cuotas residuales y después los mayores restos. Desempate de modelado: CPRO ascendente; **no se atribuye esta convención a la ley**. No hay empate en el corte de asignación de la opción 350, comprobado por el validador.

La media nacional de comparación es `49.128.297 / 350`. Las cuotas decimales y medias de esta tabla son presentacionales; el [CSV completo](resultados/repartos_52.csv) conserva fracciones exactas, las desviaciones relativas y las 780 filas de los 15 escenarios. Todas las desviaciones de esta tabla están expresadas en habitantes.

| CPRO | Provincia / ciudad | Población 2025 | Cuota total teórica | K provincial | Población media | Desviación de 120.000 | Desviación de media nacional |
|---|---|---:|---:|---:|---:|---:|---:|
| 01 | Álava | 341.961 | 3,73 | 4 | 85.490,25 | -34.509,75 | -54.876,31 |
| 02 | Albacete | 390.751 | 3,98 | 4 | 97.687,75 | -22.312,25 | -42.678,81 |
| 03 | Alicante | 2.033.566 | 12,30 | 12 | 169.463,83 | 49.463,83 | 29.097,27 |
| 04 | Almería | 770.554 | 5,90 | 6 | 128.425,67 | 8.425,67 | -11.940,90 |
| 05 | Ávila | 160.738 | 2,81 | 3 | 53.579,33 | -66.420,67 | -86.787,23 |
| 06 | Badajoz | 665.155 | 5,37 | 5 | 133.031,00 | 13.031,00 | -7.335,56 |
| 07 | Islas Baleares | 1.249.844 | 8,33 | 8 | 156.230,50 | 36.230,50 | 15.863,94 |
| 08 | Barcelona | 5.959.941 | 32,19 | 32 | 186.248,16 | 66.248,16 | 45.881,59 |
| 09 | Burgos | 362.663 | 3,84 | 4 | 90.665,75 | -29.334,25 | -49.700,81 |
| 10 | Cáceres | 388.190 | 3,97 | 4 | 97.047,50 | -22.952,50 | -43.319,06 |
| 11 | Cádiz | 1.261.420 | 8,39 | 8 | 157.677,50 | 37.677,50 | 17.310,94 |
| 12 | Castellón | 627.620 | 5,18 | 5 | 125.524,00 | 5.524,00 | -14.842,56 |
| 13 | Ciudad Real | 494.848 | 4,51 | 4 | 123.712,00 | 3.712,00 | -16.654,56 |
| 14 | Córdoba | 773.163 | 5,92 | 6 | 128.860,50 | 8.860,50 | -11.506,06 |
| 15 | La Coruña | 1.135.623 | 7,75 | 8 | 141.952,88 | 21.952,88 | 1.586,31 |
| 16 | Cuenca | 199.859 | 3,01 | 3 | 66.619,67 | -53.380,33 | -73.746,90 |
| 17 | Gerona | 830.429 | 6,21 | 6 | 138.404,83 | 18.404,83 | -1.961,73 |
| 18 | Granada | 945.797 | 6,79 | 7 | 135.113,86 | 15.113,86 | -5.252,71 |
| 19 | Guadalajara | 285.839 | 3,45 | 3 | 95.279,67 | -24.720,33 | -45.086,90 |
| 20 | Guipúzcoa | 733.149 | 5,71 | 6 | 122.191,50 | 2.191,50 | -18.175,06 |
| 21 | Huelva | 538.789 | 4,73 | 5 | 107.757,80 | -12.242,20 | -32.608,76 |
| 22 | Huesca | 230.087 | 3,17 | 3 | 76.695,67 | -43.304,33 | -63.670,90 |
| 23 | Jaén | 618.143 | 5,13 | 5 | 123.628,60 | 3.628,60 | -16.737,96 |
| 24 | León | 448.030 | 4,27 | 4 | 112.007,50 | -7.992,50 | -28.359,06 |
| 25 | Lérida | 458.226 | 4,32 | 4 | 114.556,50 | -5.443,50 | -25.810,06 |
| 26 | La Rioja | 326.803 | 3,66 | 4 | 81.700,75 | -38.299,25 | -58.665,81 |
| 27 | Lugo | 326.022 | 3,65 | 4 | 81.505,50 | -38.494,50 | -58.861,06 |
| 28 | Madrid | 7.113.886 | 38,04 | 38 | 187.207,53 | 67.207,53 | 46.840,96 |
| 29 | Málaga | 1.791.183 | 11,07 | 11 | 162.834,82 | 42.834,82 | 22.468,26 |
| 30 | Murcia | 1.586.989 | 10,04 | 10 | 158.698,90 | 38.698,90 | 18.332,34 |
| 31 | Navarra | 683.854 | 5,46 | 5 | 136.770,80 | 16.770,80 | -3.595,76 |
| 32 | Orense | 305.278 | 3,55 | 4 | 76.319,50 | -43.680,50 | -64.047,06 |
| 33 | Asturias | 1.015.128 | 7,14 | 7 | 145.018,29 | 25.018,29 | 4.651,72 |
| 34 | Palencia | 158.702 | 2,80 | 3 | 52.900,67 | -67.099,33 | -87.465,90 |
| 35 | Las Palmas | 1.171.547 | 7,93 | 8 | 146.443,38 | 26.443,38 | 6.076,81 |
| 36 | Pontevedra | 947.818 | 6,80 | 7 | 135.402,57 | 15.402,57 | -4.963,99 |
| 37 | Salamanca | 328.446 | 3,66 | 4 | 82.111,50 | -37.888,50 | -58.255,06 |
| 38 | Santa Cruz de Tenerife | 1.087.319 | 7,51 | 8 | 135.914,88 | 15.914,88 | -4.451,69 |
| 39 | Cantabria | 593.623 | 5,01 | 5 | 118.724,60 | -1.275,40 | -21.641,96 |
| 40 | Segovia | 158.251 | 2,80 | 3 | 52.750,33 | -67.249,67 | -87.616,23 |
| 41 | Sevilla | 1.977.664 | 12,02 | 12 | 164.805,33 | 44.805,33 | 24.438,77 |
| 42 | Soria | 90.183 | 2,46 | 2 | 45.091,50 | -74.908,50 | -95.275,06 |
| 43 | Tarragona | 875.530 | 6,44 | 6 | 145.921,67 | 25.921,67 | 5.555,10 |
| 44 | Teruel | 136.091 | 2,69 | 3 | 45.363,67 | -74.636,33 | -95.002,90 |
| 45 | Toledo | 755.081 | 5,82 | 6 | 125.846,83 | 5.846,83 | -14.519,73 |
| 46 | Valencia | 2.763.996 | 16,00 | 16 | 172.749,75 | 52.749,75 | 32.383,19 |
| 47 | Valladolid | 528.644 | 4,68 | 5 | 105.728,80 | -14.271,20 | -34.637,76 |
| 48 | Vizcaya | 1.167.233 | 7,91 | 8 | 145.904,12 | 25.904,12 | 5.537,56 |
| 49 | Zamora | 165.564 | 2,84 | 3 | 55.188,00 | -64.812,00 | -85.178,56 |
| 50 | Zaragoza | 998.443 | 7,06 | 7 | 142.634,71 | 22.634,71 | 2.268,15 |
| 51 | Ceuta | 83.567 | 1,00 | 1 | 83.567,00 | -36.433,00 | -56.799,56 |
| 52 | Melilla | 87.067 | 1,00 | 1 | 87.067,00 | -32.933,00 | -53.299,56 |


**Total:** 49.128.297 habitantes, **350 plazas** (50 provincias: 348; ciudades: 2). Los nombres de presentación están en español; la identidad es CPRO y el nombre original INE permanece en el archivo de entrada.

## Restricciones: prueba de incompatibilidad y decisiones reservadas

Para una circunscripción con población P, K_i distritos y límites L/U por distrito, son necesarias `K_i × L ≤ P ≤ K_i × U`, es decir `ceil(P/U) ≤ K_i ≤ floor(P/L)`. No son suficientes: indivisibilidad de unidades, topología o componentes pueden impedir la partición aun cumpliéndose esas desigualdades.

Con L=96.000: **Soria P=90.183**, **Ceuta P=83.567**, **Melilla P=87.067** tienen `floor(P/L)=0`. Exigir al menos uno y no cruzar provincias da simultáneamente K_i≥1 y K_i≤0. Por tanto **ningún K**, dentro ni fuera de 300–400, puede satisfacer conjuntamente ese suelo uniforme y la representación positiva de las tres con esta edición. No hace falta explorar los 101 totales del intervalo ni modificar población para demostrarlo. Dos iniciales en Soria exigirían un suelo uniforme no mayor de 45.091,50 solo como condición necesaria; no se propone ese valor como nuevo límite.

Además, mantener una media objetivo nacional exactamente 120.000 llevaría a 409,402475 plazas teóricas; el modelo redondea el total a 409. Con máximo 400, la media nacional mínima es 122.820,7425. Con 350 es 140.366,562857… . K no puede mantener a la vez el tamaño legal y el objetivo como igualdad vinculante. Una media objetivo orientativa puede conservarse para comparar, sin confundirse con condición contractual.

Decisiones y problemas concretos que condicionan la ejecución, sin impedir decidir ahora solo K y reparto:

| Materia | Hecho / evidencia | Decisión o condición pendiente |
|---|---|---|
| Tamaño y reparto | 350 + mínimos refleja la estructura legal; Hamilton puro no conserva mínimos | Aprobación expresa del propietario para DDD; 383/391/392/400 exigirían otro criterio institucional |
| Barreras | Contrato exige 52 separadas y prohíbe cruces | No usar unión entre Soria u otras provincias, ni entre ciudades, como reparación aritmética |
| Límites y ciudades | Suelo 96.000 incompatible; ciudades completas quedan por debajo | Resolver expresamente límites nacionales y cualquier trato específico; no hay excepción implícita ni tolerancia prestada del motor autonómico |
| Islas | K350 asigna 8 a Islas Baleares, 8 a Las Palmas y 8 a Santa Cruz de Tenerife | No acredita asignación por isla, puentes marítimos, mínimo por componente ni excepciones de conectividad; no importar el régimen del Senado |
| Enclaves y discontinuidades | Crosswalk identifica administración, no conectividad física | Definir contigüidad, adyacencia, tratamiento de componentes físicos y enclaves sin alterar barreras ni inventar aristas |
| Unidades y población | Secciones 2025 identificadas; población agregada provincial verificada | Aprobar unidad mínima y acreditar población compatible por unidad, cobertura y hashes; fuentes del contrato siguen nulas |
| Disciplina municipal | No hay decisión nacional aprobada | Decidir indivisibilidad o subdivisión municipal; la viabilidad no se infiere de medias |
| Histórico y N04 | 391 unidades no acreditadas; geometría inválida preservada | No usar el histórico como fuente certificada ni reparar por inferencia; N03 bloqueada y N04 mantiene diagnóstico |
| Ejecución | No se calcula mapa ni se llama al motor | N08–N10 conservan NO_GO productivo hasta condiciones y autorización separadas |

## Redacción exacta para la decisión del propietario, canalizada por Work

### Opción A — aprobación acotada de K y regla, recomendada

> Para la tarea N06 del Plan Maestro ddd-maestro-20261008, apruebo como decisión interna de planificación del modelo Congreso DDD un total K=350 y el reparto de dos plazas iniciales por cada una de las 50 provincias, una plaza fija para Ceuta y una plaza fija para Melilla, más 248 plazas distribuidas entre las 50 provincias por cocientes enteros y mayores restos de su población agregada de referencia 2025. La fórmula es q_i residual = 248 × P_i / 48.957.663, con desempate de modelado por CPRO ascendente; las ciudades no participan en el residual. El anexo repartos_52.csv, escenario k350_minimos, fija la tabla de referencia y conserva su identidad en el manifiesto del expediente.
>
> Esta elección conserva el tamaño legal actual como referencia del proyecto. No adopta el antecedente 391/392, no identifica los escenarios 383/407/409/435 con decisiones y no acredita legalmente un nuevo sistema electoral. Acepto como consecuencias aritméticas una media nacional de 140.366,562857… habitantes por plaza, Soria con dos plazas y media 45.091,50, Ceuta con una plaza y población 83.567 y Melilla con una plaza y población 87.067; reconozco que 17 medias provinciales/urbanas incumplen el suelo exploratorio de 96.000.
>
> El objetivo de 120.000 y la banda exploratoria 96.000–210.000 no quedan aprobados como límites del contrato por esta decisión. No se concede ninguna excepción implícita. Antes de generar distritos deberán aprobarse expresamente los límites nacionales y el tratamiento de provincias pequeñas y ciudades, la unidad mínima, población por unidad compatible con la edición 2025, contigüidad, disciplina municipal, islas, enclaves y discontinuidades físicas, y acreditarse sus entradas y factibilidad. Se mantienen las barreras provinciales, las ciudades separadas y la prohibición de cruces entre circunscripciones.
>
> Esta decisión aprueba únicamente K y su regla de reparto para planificación. No aprueba el contrato integral, no promociona fuentes, no autoriza M01–M08, pilotos, generación, certificación, publicación ni integración. Work registrará por separado la decisión expresa del propietario y las condiciones pendientes; cualquier modificación posterior de K o de la regla requerirá otra decisión expresa.

### Opción B — no aprobar ninguna opción

> Para la tarea N06 del Plan Maestro ddd-maestro-20261008, no apruebo por ahora ningún K ni regla de reparto. Exijo que la decisión institucional sea integral y satisfaga simultáneamente representación positiva de las 52 circunscripciones, barreras provinciales y los límites poblacionales que se decidan expresamente. Reconozco la incompatibilidad demostrada entre el suelo uniforme exploratorio de 96.000 y la población 2025 de Soria, Ceuta y Melilla, agravada por dos plazas iniciales en Soria. No autorizo a resolverla suprimiendo representación, cruzando circunscripciones, cambiando población o introduciendo excepciones.
>
> N06 permanece WAIT_OWNER, con k_decision sin total aprobado. K=350 con mínimos sigue siendo la propuesta preferida por coherencia de tamaño, pero no se convierte en contrato. La decisión reservada es si aprobar solo K y reparto conforme a la opción A o mantener la aprobación integral pendiente de resolver expresamente límites y condiciones. N08–N10 no quedan habilitadas para producción.

**Registro requerido si se adopta una opción:** identidad del propietario, fecha y texto de aprobación expresa, opción escogida, referencia al manifiesto del expediente y un identificador de decisión aportado por Work. Este documento no rellena firmas, fechas de aprobación, decision_id ni k_decision en nombre del propietario.

## Reproducción, revisión y conservación

El cálculo nuevo se limita a nueve repartos de K fijo (seis con mínimos y tres Hamilton puros); las cinco alternativas N05 se reutilizan y se añade un contrafactual de los recuentos históricos 391 sobre la misma población 2025. No se hace búsqueda geoespacial ni piloto.

```sh
python3 docs/ESTUDIOS/N06_DECISION_K_20261012/comparar.py --output /tmp/n06-reproduccion-nueva
python3 docs/ESTUDIOS/N06_DECISION_K_20261012/verificar.py
python3 -m unittest tests.test_modelo_cuantitativo_nacional tests.test_evaluacion_alternativas_nacionales tests.test_congreso_contract -v
```

El destino debe ser nuevo. Comparar los tres archivos resultantes con resultados/ mediante SHA-256. El programa valida el manifiesto N05 y las identidades de población antes de calcular. El verificador usa un oráculo entero separado para las nueve asignaciones nuevas, comprueba 52/52, totales, ciudades fijas, fracciones, límites, hashes y determinismo, y conserva la regresión de no monotonía en Soria. No considera ese oráculo una aprobación institucional independiente.

[verificacion.log](verificacion.log) y [regresiones.log](regresiones.log) registran comandos/pruebas y resultados locales. La revisión completa en sesión separada se conservará externamente y anclada al HEAD final, evitando circularidad de SHA. **CI no ejecutada para este incremento local**, conforme al límite de no push/PR; no se hereda un PASS de la PR #239.

Política de versiones: todas las rutas son nuevas, con origen/metadatos; no se sustituye ningún fichero funcional previo ni se necesita copia legacy de un predecesor inexistente. El contrato candidato permanece byte a byte intacto. La conservación local solicitada no equivale a integración ni certificación.

Resultado exigible aquí: **expediente listo para decisión**, no cierre formal de N06. No se altera el estado del Plan. Siguiente consumidor: Work y propietario para escoger A/B o redactar una decisión distinta explícita; ningún motor territorial queda habilitado. Push / PR / merge / ejecución M01–M08 / fuentes nuevas / generación / publicación: **NO**.
