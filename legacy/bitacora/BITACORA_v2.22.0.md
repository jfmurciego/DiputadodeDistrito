# Bitácora de progreso

**Versión:** 2.22.0
**Fecha:** 2026-09-11
**Anterior:** `legacy/bitacora/BITACORA_v2.21.0.md`

## R001–R013 — recuperación y profesionalización
Se recuperó el procedimiento Aragón y se formalizaron M01–M08, fuentes congeladas, caché territorial, validación, outputs auditables, manifiestos, versionado, continuidad y reglas de contigüidad/municipio/provincia. Run #7 consiguió estructura R012 PASS pero dejó un distrito fuera de ±12 %.

## R014 — escape de mínimo local
M05 v7.3.0 añadió recocido reproducible. Run #8 `34592470470` consiguió `fuera_12=0`, máximo desvío 11,943 %, con todas las restricciones duras PASS.

## R015 — pruebas y gobernanza
Se creó la suite automática de regresión/determinismo y se normalizó `legacy/`. Desde R015, una referencia activa a un predecesor inexistente es error de CI. El código probado no se reescribe solo para cambiar una etiqueta de promoción.

## R016 — refinamiento post-factibilidad
M05 v7.4.0 dejó de detenerse al primer `fuera_12=0`. Run #9 `34599224954` continuó desde iteración 9.038 hasta 20.000 y redujo el máximo desvío a **9,930 %** y el error cuadrático a `0.161271162560`, manteniendo 67 distritos, 1.463 secciones, 1.364.621 habitantes, 11/7/49 y todas las restricciones PASS. Run #9 es el baseline territorial vigente.

Se limpiaron las ramas históricas/temporales y quedó únicamente `main`.

## R018 — arquitectura multi-territorio

### Motivo
Seguir afinando Aragón entra ya en grano fino. La siguiente prueba de madurez es incorporar Castilla y León sin clonar el motor. El proyecto pasa de una implantación implícitamente aragonesa a un producto multi-territorio.

### Decisiones
- un solo repositorio;
- una sola rama permanente `main`;
- un solo motor común en `ddd_core/`, `modulos/`, `herramientas/`;
- cada territorio vive en `territorios/<id>/` con configuración, inputs, docs y tests;
- Aragón pasa a `territorios/aragon/` como referencia validada;
- Castilla y León se crea como segundo paquete y prueba de generalización;
- Extremadura será la siguiente prueba de reutilización;
- rutas raíz históricas de Aragón se mantienen temporalmente como compatibilidad hasta generalizar el workflow.

### Cambios técnicos
`procedimiento.sh` pasa a v2.2.0 y deriva `run_name` desde el YAML; elimina la caché codificada como `aragon_2025` y acepta cualquier `DDD_PARAMS` compatible. No cambia ningún algoritmo territorial.

Se crean `docs/ARQUITECTURA_MULTI_TERRITORIO.md`, `docs/CONTRATO_TERRITORIO.md` y `docs/CONTINUIDAD_CASTILLA_Y_LEON.md`.

### Limpieza documental
Se retiran del árbol activo documentos ya sustituidos o redundantes: `MEMORIA*`, `ARQUITECTURA.md`, `MODULOS.md`, el expediente candidato R016 ya superado y una copia duplicada de deuda histórica. Se preservan en `legacy/docs/retirados_r018/` cuando aportan arqueología; los documentos canónicos y expedientes útiles se conservan.

### Estado al cierre
Aragón no cambia de baseline. R017 de calidad territorial queda pendiente en su hilo. El nuevo hilo de Castilla y León debe empezar por inventario de fuentes, contrato territorial, generalización del workflow y M01–M03; no por optimización.

## R019 — Extremadura: separación municipio real / unidad de partición y diagnóstico del mínimo local

### Problema estructural
Extremadura confirmó que usar el municipio real como única unidad de trabajo de M04 es demasiado rígido en municipios sobredimensionados, mientras que abrirlos completamente a sección genera fragmentación y un espacio de búsqueda excesivo. Se formaliza la separación entre:
- `municipality_field`: identidad administrativa real e inmutable, usada para auditoría, disciplina municipal, nombres y métricas de split;
- `partition_unit_field`: unidad interna de trabajo de M04, que puede subdividir únicamente municipios sobredimensionados manteniendo intacta su identidad administrativa.

El diseño queda recogido en `docs/DISENO_M04_MUNICIPIOS_SOBREDIMENSIONADOS.md` v1.1.0.

### EXT-03 / EXT-04 — granularidad interna
Los barridos iniciales mostraron que la factibilidad de M04 no es monotónica respecto del tamaño de las macro-unidades. Los tamaños gruesos 0,25 / 0,40 / 0,60 dejaron respectivamente 1 / 4 / 5 distritos fuera de suelo/techo. En el barrido fino, 0,15 falló, mientras que **0,20 fue el primer candidato que produjo K=65, cuotas provinciales 41/24 y `hard=0`**.

El intento c010 expuso además una deuda técnica real del constructor `hybrid_partition`: tras sucesivos peels puede quedar `left > len(rem)` y alcanzarse `max(empty)`. No se corrige dentro de R019 para no contaminar la comparación territorial; queda como deuda separada antes de Andalucía.

### c020 — candidato M04 reproducible
Con `chunk_ratio=0.20` se construyen 521 unidades de partición sobre las 964 secciones, manteniendo 7 municipios sobredimensionados internamente divisibles. M04 v7.4.5 obtiene:
- 65 distritos;
- Badajoz 41 / Cáceres 24;
- `hard=0`;
- mínimo 14.050;
- máximo 18.318.

Frente al enfoque abierto por sección, el estado entregado a M05 reduce fuertemente el churn y la fragmentación municipal.

### EXT-05 / EXT-06 — swap-polish 1×1
EXT-05 demostró que el estado c020 después del motor M05 v7.4.0 estaba en un mínimo de movimientos simples pero todavía tenía swaps 1×1 válidos. Se creó `ddd_core/m05_swap_polish.py`, fase C determinista y opt-in.

M05 wrapper evoluciona a v7.5.2 manteniendo el motor base v7.4.0. El informe distingue explícitamente `version=7.4.0` del motor y `wrapper_version=7.5.2`. R015 vuelve a PASS completo tras esta corrección semántica.

EXT-06 Run `34642635707` aplica dos swaps 1×1 válidos y reduce los outliers de 4 a 2 sin romper restricciones duras. Resultado post-polish:
- `outside_10=2`;
- máximo desvío absoluto **13,3000 %**;
- error cuadrático `0.131455334058`;
- mínimo 14.050;
- máximo 17.813;
- distritos residuales: 14 = 14.050 (−13,30 %) y 25 = 14.212 (−12,30 %);
- splits municipales: 06011=2, 06015=12, 06044=4, 06083=6, 06153=3, 10037=7, 10148=3.

### EXT-07 / EXT-08 — límite de la optimización local compuesta
EXT-07 Run `34643074456` prueba 43 intercambios 1↔2 / 2↔1 y encuentra **0 mejoras válidas**. La causa dominante es topológica: 39 candidatos desconectan el distrito vecino y 26 desconectan también el distrito deficitario.

EXT-08 Run `34645870892` prueba el siguiente operador mínimo, 2↔2: 39 candidatos, **0 mejoras válidas**.

Decisión: se detiene la escalada combinatoria de M05. No se añaden 2↔3, 3↔3 ni búsqueda bruta para compensar una discretización previa. El problema residual se considera topológico y se devuelve a M04.

### EXT-09 — ventana de factibilidad M04
Se crea un barrido homogéneo c017–c024. EXT-09 v1.0.0 falló antes de M04 por no pasar `LABEL`/`CFG` al contenedor de configuración; la versión quedó preservada en `legacy/workflows/` y v1.0.1 corrigió exclusivamente la orquestación Docker.

Run `34646270990` demuestra una **isla de factibilidad en c020**:
- c017: M04 FAIL;
- c018: M04 FAIL;
- c019: M04 FAIL, 2 distritos fuera de suelo/techo;
- **c020: M04 PASS → M05 PASS**;
- c021: M04 FAIL;
- c022: M04 FAIL;
- c023: M04 FAIL;
- c024: M04 FAIL.

c020 reproduce exactamente el resultado EXT-06: 65 distritos, `outside_10=2`, máximo desvío 13,3000 %, error cuadrático `0.131455334058`, dos swaps aceptados.

### Decisión arquitectónica al cierre de R019
1. **c020 se congela como mejor discretización M04 probada para Extremadura.** No se interpreta como constante universal; es un candidato territorial reproducible.
2. La separación `municipality_field` / `partition_unit_field` queda confirmada como arquitectura necesaria del motor multi-territorio.
3. M05 v7.4.0 sigue siendo el motor optimizador validado; wrapper v7.5.2 añade normalización y swap-polish opt-in sin alterar el baseline.
4. No se amplía M05 con operadores combinatorios de orden superior mientras el bloqueo residual sea topológico.
5. El siguiente frente de ingeniería debe mejorar **cómo M04 construye las macro-unidades internas alrededor de articulaciones y fronteras**, manteniendo c020 como baseline A/B.
6. El bug c010 del constructor debe corregirse como deuda técnica independiente y pasar R015 antes de probar Andalucía.

## R020 — Extremadura: fragilidad topológica explícita y pulido protegido M04

### EXT-10 — el `seed` de M04 no genera variantes
Run `34646703254` prueba ocho semillas M04 sobre el mismo c020 manteniendo M05 en seed 12345. Todas producen la misma solución hasta el último decimal. La inspección de `m04_seed_engine_v745.py` confirma que la configuración `seed` no se consume: los desempates son deterministas por población, grado e identificador.

Decisión: no se implanta un falso multistart. Antes de introducir aleatoriedad hay que definir variantes reales y una función explícita para compararlas.

### EXT-11 — métrica global de fragilidad
Se crea `herramientas/auditar_fragilidad_topologica.py`. La firma topológica es:
`[distritos_con_articulaciones, unidades_articulacion, suma_lobulos_minimos/target, max_lobulo_minimo/target]`.

Run `34647283785` mide:
- M04 c020: `[53, 122, 15.444507734883, 0.455591472879]`, 250.283 habitantes acumulados en lóbulos mínimos y máximo lóbulo mínimo 7.383;
- M05 baseline: `[52, 128, 17.257123734389, 0.478917163892]`, 279.657 habitantes acumulados y máximo 7.761.

Conclusión: M05 mejora el equilibrio poblacional, pero su objetivo actual puede **empeorar la robustez topológica**. La topología no debe seguir siendo una restricción binaria de conectividad únicamente; necesita una métrica de calidad secundaria.

El auditor v1.0.0 falló inicialmente porque OGR descartaba `ddd_unit_id` con tipo no soportado. Se preservó y v1.0.1 recupera `ddd_unit_id` desde el GeoJSON crudo por `CUSEC_KEY`, patrón que queda recomendado para herramientas diagnósticas.

### EXT-12 — existen movimientos M04 que compran robustez sin romper población
Run `34647432729` enumera movimientos unitarios de frontera en M04 que preservan provincia, suelo/techo y contigüidad y reducen estrictamente la firma de fragilidad:
- 123 movimientos topológicamente mejores;
- 70 protegidos por `hard=0`, mismo o menor número de outliers y mismo o menor máximo desvío;
- 0 que además no empeoren el error cuadrático completo.

El mejor candidato mueve la unidad `10:10059:P` del distrito 61 al 44, población 354. M04 pasa de `[53,122,15.4445,0.4556]` a `[52,120,15.3798,0.4556]`, conservando 5 outliers y máximo desvío 13,3000 %, a costa de un pequeño aumento del error cuadrático.

### EXT-13 A/B — un solo movimiento topológico
Run `34647645087` aplica únicamente `10:10059:P` y ejecuta después M05. Resultado final:
- `outside_10=2`;
- máximo desvío 13,3000 %;
- error cuadrático `0.132011051243` frente a `0.131455334058` baseline;
- fragilidad `[50,122,16.125580887553,0.465341364890]` frente a `[52,128,17.257123734389,0.478917163892]` baseline.

Conclusión: una intervención topológica mínima sobre M04 sobrevive a M05 y mejora claramente robustez, pero no resuelve los dos outliers y paga una pequeña penalización poblacional.

### EXT-13 iterativo — pulido topológico protegido antes de M05
Se crea `herramientas/pulir_topologia_m04.py` v1.0.0 como herramienta experimental, fuera del motor productivo. Aplica iterativamente solo movimientos que:
- preservan provincia y contigüidad;
- mantienen `hard=0`;
- no aumentan el número de outliers;
- no aumentan el máximo desvío;
- reducen estrictamente la firma de fragilidad.

Run `34650575053`, con límite 50, acepta los 50 movimientos y por tanto **no alcanza convergencia natural**. Antes de M05:
- outliers M04: 5 → 4;
- máximo desvío: permanece 13,3000 %;
- error cuadrático M04: `0.166604116639` → `0.251709268807`;
- fragilidad: `[53,122,15.4445,0.4556]` → `[44,76,8.9155,0.4277]`.

Después de M05 v7.5.2:
- `outside_10=2`;
- máximo desvío 13,3000 %;
- error cuadrático **`0.123144479940`**, mejor que el baseline `0.131455334058`;
- máximo poblacional 17.699 frente a 17.813 baseline;
- fragilidad **`[47,95,12.998765836454,0.452444355838]`**, mejora fuerte frente al baseline `[52,128,17.257123734389,0.478917163892]`.

Conclusión provisional: el preacondicionamiento topológico de M04 no elimina aún los dos outliers, pero crea un estado desde el que M05 obtiene simultáneamente **menor error cuadrático y mucha menor fragilidad**. Es la primera mejora estructural posterior a c020 que gana en ambos ejes finales.

### Decisión al cierre provisional de R020
1. No se promueve todavía `pulir_topologia_m04.py`: el run de 50 movimientos llegó al límite configurado y no a convergencia.
2. Se crea EXT-14 para medir la curva 5/10/20/30/40/50 y localizar un punto de Pareto reproducible.
3. Si el patrón se confirma, la solución productiva deberá usar evaluación topológica incremental; recalcular todas las articulaciones para cada candidato es aceptable en diagnóstico pero demasiado caro como diseño final.
4. Los dos outliers siguen siendo el criterio de cierre territorial; una mejora de fragilidad no sustituye el objetivo ±10 %.
5. R015 permanece como guardarraíl obligatorio y ha seguido pasando durante los experimentos topológicos realizados hasta este punto.

## Reglas permanentes
Un informe no sustituye al producto. GitHub reproducible manda sobre memoria/chat. Toda versión nueva preserva su predecesor. Los resultados electorales nunca condicionan geometría. Un nuevo territorio no justifica un fork: cualquier cambio del motor debe ser una generalización reusable.


## R021 — Auditoría y continuidad persistente
La auditoría de 2026-09-12 fijó el estado real y creó `docs/SALIDAS_CHATGPT/`.

## R022 — M03 observable, Cataluña y España
M03 v7.2.0 desacopla diagnóstico de bloqueo. CAT-02 Run `34688104014` certificó Llívia; CAT-03 Run `34688242964` cerró M03. Run nacional `34688010656` completó Madrid y otros 13 territorios, con resúmenes ligeros y artefactos pesados separados.

## R023 — diagnóstico topológico continental
Se abre una matriz de siete territorios para explicar discontinuidades antes de declarar pasarelas. Baleares y Canarias quedan separados como archipiélagos.
