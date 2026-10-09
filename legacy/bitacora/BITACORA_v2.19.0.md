# Bitácora de progreso

**Versión:** 2.19.0
**Fecha:** 2026-09-11
**Anterior:** `legacy/bitacora/BITACORA_v2.18.0.md`

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

## Reglas permanentes
Un informe no sustituye al producto. GitHub reproducible manda sobre memoria/chat. Toda versión nueva preserva su predecesor. Los resultados electorales nunca condicionan geometría. Un nuevo territorio no justifica un fork: cualquier cambio del motor debe ser una generalización reusable.
