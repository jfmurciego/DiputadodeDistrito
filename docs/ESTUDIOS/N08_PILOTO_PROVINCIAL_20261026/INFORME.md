# N08 — Piloto analítico provincial: León y Cáceres

**Alcance:** auditoría y candidato analítico vinculado a entradas INE/N08 existentes. No ejecuta M04–M06, no certifica producto, no autoriza generación ni publicación. Fecha de trabajo: 2026-10-26.

## Base, artefacto y linaje

- Base `main` observada: `9efc672972c6d9f16f24de633bdf0e9f04aaf0c2`.
- PR #298 existente observada en `80dd2fd1256b49439dd11b017cff2d56f776e49a`; no se reconstruyó su entrega.
- Candidato histórico examinado: run `39448134186`, artifact `12275919036`, HEAD productor `9f96bed70cfa8fed1f520b745274e2e852da60db`.
- SHA-256 del ZIP original recuperado: `9bc7edf8f6a76b1f706c692c6f71972c1f6eff01c3a1c18758ff5a1324aa9c15`. SHA-256 del JSON candidato: `237f7a73218347aab56964fe2b1ae918d5b2516f8bb33f842be15459637ed8c9`.
- El candidato liga checkpoint, contrato, preflight, manifiesto topológico y unidad provincial por los hashes que constan en `FUENTES.json`. La evaluación actual (`evaluate_unit`) no devuelve errores.
- El ZIP del run más reciente `39454218489` no pudo recuperarse por el enlace temporal inaccesible. Su log registra el mismo SHA del JSON (`237f7a…ed8c9`); no se atribuye al audit actual la geometría empaquetada que no se inspeccionó.

## León — candidato original

| Requisito | Estado | Evidencia |
|---|---|---|
| CUSEC íntegra, sin pérdidas ni duplicados | DEMOSTRADO | 444/444, enlazadas a la unidad N08 CPRO24 |
| Población y edición de fuente | DEMOSTRADO | 448.030; binding N08/INE 2025 exacto |
| K y cuotas | DEMOSTRADO | K=4, tomado del contrato; no se recalculó |
| Banda poblacional | DEMOSTRADO | target 112.007,5; suelo 95.207; techo 128.808; distritos 115.740 / 95.570 / 115.280 / 121.440 |
| Conectividad del grafo seccional | DEMOSTRADO | los cuatro grupos conectados en el grafo acreditado de 1.245 aristas lineales |
| Conectividad física de partes originales | PENDIENTE | no ejecutable en el Mac; runtime local no dispone de Shapely/GeoPandas funcionales. Hay auditor geoespacial aislado y CI fijada, aún no ejecutada sobre este HEAD |
| Disciplina municipal | INCUMPLIDO | seis municipios divididos; cinco divisiones evitables por consolidación local válida y una división de León sin necesidad demostrada |
| Acreditación administrativa externa | PENDIENTE | CNIG/IGN efectiva 01-01-2025 no recibida/acreditada |
| Excepciones nominales | PENDIENTE | no se aplicó ninguna; falta determinar contra la fuente externa si procede una excepción |
| Trazabilidad geometría por partes | PENDIENTE | falta ejecutar auditoría física y vincular el reporte al candidato final |

### Municipios y fragmentos del original

| CUMUN | Municipio | Población | Fragmentos originales | Resultado tras reparación analítica |
|---|---|---:|---|---|
| 24056 | Cistierna | 2855 | LEON-01=1514 hab. (1 CUSEC); LEON-02=1341 hab. (1 CUSEC) | No se conserva la división en el candidato corregido |
| 24089 | León | 124091 | LEON-02=44509 hab. (33 CUSEC); LEON-04=79582 hab. (68 CUSEC) | No se conserva la división en el candidato corregido |
| 24115 | Ponferrada | 63112 | LEON-01=616 hab. (1 CUSEC); LEON-03=62496 hab. (45 CUSEC) | No se conserva la división en el candidato corregido |
| 24163 | Sariegos | 5482 | LEON-02=4348 hab. (3 CUSEC); LEON-04=1134 hab. (1 CUSEC) | No se conserva la división en el candidato corregido |
| 24170 | Torre del Bierzo | 1923 | LEON-01=974 hab. (1 CUSEC); LEON-03=949 hab. (1 CUSEC) | No se conserva la división en el candidato corregido |
| 24202 | Villablino | 7587 | LEON-01=5986 hab. (6 CUSEC); LEON-03=1601 hab. (2 CUSEC) | No se conserva la división en el candidato corregido |

El original falla el validador N08/M05 con `MUNICIPAL_SPLIT_NOT_MINIMAL`. El candidato corregido conserva todas las CUSEC y K=4 y elimina las seis divisiones. Cinco consolidaciones fueron aceptadas manteniendo conectividad seccional y cotas. Para el municipio de León (124.091 hab., inferior al techo), la reparación trasladó sus CUSEC al distrito LEON-04 y evacuó CUSEC no leonesas de dicho distrito; estas se reasignaron a LEON-02 junto con Benavides (CUMUN 24015, 2 CUSEC/2.319 hab.) para recuperar el suelo poblacional. Las poblaciones finales son 113.841 / 124.091 / 113.346 / 96.752. El M05 vigente declara `valid=true`, `hard_limits_met=true`, cero divisiones y cero infracciones.

`LEON/municipios-divididos-original.csv` enumera CUSEC y población de cada fragmento de los seis municipios originales.

**Límite:** es un testigo constructivo de reparación y necesidad cero de divisiones **en el grafo seccional examinado**, no una prueba sobre partes poligonales ni una prueba de que León sea factible frente a límites administrativos externos. No se inició búsqueda global ni se afirma optimalidad fuera de la asignación fija usada por el certificado local.

- Candidato corregido SHA-256: `bbc7c8b638d02b9c7100c83d7faa449f77161d1c1b49b5a3999dd93ff606bdc3`.
- Witness del candidato original: `e3717b106b5d297d854e7900763d84f2310f5b79b69822fbf778f8b8bf318f05`.
- Witness del nuevo conjunto de asignaciones corregido: `1e4bcce54b64327aa19ccd9215fc4b2f1933020a9367d95f25e1878696b2984b`. El vínculo al testigo histórico se conserva como `source_witness_sha256`.
- Reproducción exacta del JSON corregido desde el original: comprobada byte a byte en la prueba `test_leon_repair_is_byte_deterministic_and_keeps_gates_closed`.

## Cáceres — reutilización del procedimiento

- CPRO10, K=3 obtenido del contrato; unidad enlazada: 411 CUSEC, 388.190 habitantes, 1.125 aristas físicas lineales.
- Se recuperó el resultado previo `NAC_K_MULTIPLE_BOUNDED_20261020_final.json`: `TREE_WITNESS_FOUND_CONDITIONAL`, entrada SHA `38c4ae7c5720645698e0fe90cf3ea95f8ba90e18bd761d1693c5c4b658a18910`, witness original `f387c48696abbedf7dc1cc6084fef863a8e8eea9251ad084c4f566db94063ce2`, 839 estados/426 transiciones. La reproducción obtuvo exactamente el mismo input y witness; solo materializó ahora las asignaciones.
- Reparación acotada: 23 ensayos, seis consolidaciones municipales; K=3, poblaciones 147.674 / 130.354 / 110.162, dentro de 109.988–148.806.
- Queda dividido Cáceres (CUMUN10037), 96.598 hab., en dos grupos de 19.799 y 76.799. El certificado M05 prueba que, **con las demás asignaciones fijas**, no existe un único distrito conectado con bandas válidas (105 asignaciones examinadas); no prueba minimalidad global de divisiones al reasignar otros municipios.
- Candidate SHA-256: `0e176071730bd2b8b5a0293d52fd1c10d2bc2b9c0835a41a2fca946238caad9a`; candidate witness final `5fcaa25e9f28abccccaf9029edf88a1d8461a001976d7076daa103da60add3d2`, y digest histórico preservado como `source_witness_sha256`.
- Cobertura, suma de población, K, cotas y conectividad seccional demostradas; disciplina municipal válida para este testigo según M05 con certificado local acotado. Conectividad por partes originales, acreditación externa y excepciones siguen pendientes.

## Versiones y reproducibilidad

El entorno local informa CPython 3.11.4 macOS 11.7.11, sin Shapely/GeoPandas; pyogrio 0.13.0 no carga por faltar `libgdal.38.dylib`. No se declara ejecutada localmente la auditoría de partes ni el visor. La CI fija Ubuntu 24.04, CPython 3.12.12, GeoPandas 1.2.0, NumPy 2.5.4, pandas 3.0.6, pyogrio 0.13.0, pyproj 3.8.0 y Shapely 2.2.0; registra GDAL/PROJ/GEOS efectivos. La reproducción exige igualdad byte a byte de los JSON candidatos y reporte de contacto geométrico determinista; no equipara bytes de empaquetado ZIP ni la representación de visualización con la identidad del candidato.

## Puertas y estado

`generation_authorized=false`; `product_certification=NOT_PERFORMED`; `publication_authorized=false`. La geometría física y las decisiones administrativas exteriores no se infieren del grafo seccional. No hay distritos electorales certificados ni autorizados para producción.

## Pruebas y verificación de integración

- Local: 21 pruebas del piloto/topología acotada; 17 PASS y 4 SKIP por ausencia de Shapely. Incluye re-reproducción byte a byte de León y Cáceres, rechazo de duplicados, población/K/gates inválidos, y las regresiones existentes del buscador.
- Local: `py_compile` de los cuatro módulos, `git diff --check` y parseo YAML: PASS.
- Las suites `test_congreso_contract` y `test_congreso_candidate_certifier` se intentaron en este checkout sparse: 28 PASS, 3 errores de entorno porque faltan los artefactos históricos `legacy/n06_contrato...`, `legacy/n08_nac...` y el manifiesto de entrega completo de 74 ficheros. No son cambios de esta rama; la CI de checkout completo las ejecutará.
- CI del HEAD candidato aún no existe: esta rama no se ha publicado. Por tanto, contigüidad de partes originales permanece PENDIENTE, y el expediente no queda `READY_FOR_INTEGRATION`.

## Revisión independiente del snapshot

La sesión revisora separada encontró cero defectos P0/P1 y tres observaciones P2.
Se aplicaron dos correcciones en el candidato local: el adaptador ya no admite
una estructura arbitraria como acreditación topológica física (esa evidencia
permanece separada y pendiente de revisión), y el consumidor del visor rechaza
claves JSON duplicadas y valores no finitos. Se amplió el filtro de rutas de CI
para incluir el visor y sus dependencias directas. Se añadieron regresiones
negativas. La revisión independiente posterior examinó el merge commit
`023d41d98a6a630991d1bd08f02e45cc230ec246` y emitió `GO_ACOTADO`, sin P0/P1.
Sus tres P2 se corrigieron en ese árbol. Esta revisión no acredita CI ni
conectividad física: ambas siguen pendientes antes de considerar integración.
