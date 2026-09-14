# Bitácora de progreso

**Versión:** 2.20.0
**Fecha:** 2026-09-11
**Anterior:** `legacy/bitacora/BITACORA_v2.19.0.md`

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

## Reglas permanentes
Un informe no sustituye al producto. GitHub reproducible manda sobre memoria/chat. Toda versión nueva preserva su predecesor. Los resultados electorales nunca condicionan geometría. Un nuevo territorio no justifica un fork: cualquier cambio del motor debe ser una generalización reusable.
