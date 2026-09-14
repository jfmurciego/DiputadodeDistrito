# Diseño M04 — Municipios sobredimensionados

**Versión:** 1.1.0  
**Fecha:** 2026-09-11  
**Estado:** arquitectura validada como dirección; `chunk_ratio=0.20` es candidato EXT, pendiente de cerrar el objetivo fino antes de promoción general.  
**Anterior:** `legacy/docs/DISENO_M04_MUNICIPIOS_SOBREDIMENSIONADOS_v1.0.0.md`

## Problema

M04 necesita respetar el municipio como unidad administrativa real y, al mismo tiempo, permitir que municipios cuya población equivale a varios distritos sean internamente particionables. Usar un único campo para ambos conceptos fuerza dos extremos incorrectos:

1. municipio completamente atómico, que puede hacer imposible la igualdad poblacional;
2. municipio totalmente granularizado por sección, que da demasiada libertad, multiplica splits y puede crear semillas con cadenas de articulación difíciles de reparar después.

Castilla y León demostró el primer problema con residuos monolíticos. Extremadura demostró ambos extremos: el municipio rígido bloquea M04; la sección individual desbloquea M04 pero puede dejar un mínimo topológico severo en M05. Andalucía eleva la escala: Sevilla ≈8,65 targets y Málaga ≈7,50 targets.

## Separación conceptual

### `municipality_field`
Identidad administrativa real e inmutable. Se usa para:
- auditoría;
- disciplina municipal;
- métricas de split;
- nombres y composición final;
- reglas políticas/territoriales.

### `partition_unit_field`
Identidad de trabajo de M04. Coincide con el municipio real cuando éste puede mantenerse atómico y se divide en macro-unidades internas conectas cuando su población exige varios distritos. Nunca sustituye la identidad administrativa real.

Esta separación es ya una decisión arquitectónica: evita usar un único campo para representar simultáneamente una entidad administrativa y el ladrillo algorítmico de partición.

## Regla de diseño candidata

1. Municipios por debajo de `municipality_atomicity_limit_ratio × target` permanecen como una sola unidad de partición.
2. Municipios por encima del umbral pueden producir varias macro-unidades internas conectas.
3. La granularidad interna conserva `municipality_field` original en todas las secciones.
4. Cada macro-unidad debe ser conexa en el grafo M03 y quedar completamente contenida en un municipio real.
5. M04 utiliza `partition_unit_field`; M05 y la auditoría política siguen usando `municipality_field` real.
6. La granularidad no se elige por intuición: debe ser la más gruesa que permita una semilla dura válida y suficiente capacidad de refinamiento posterior.
7. La salida debe registrar número, población, secciones y gateways externos de cada macro-unidad para permitir trazabilidad.

## Implementación experimental

`herramientas/construir_unidades_internas_m04.py` v1.0.1 construye las macro-unidades de manera determinista, sin alterar población, geometría ni `CUMUN`. Para municipios sobredimensionados estima un número de partes a partir de `chunk_ratio × target`, utiliza partición conexa y rebalanceo local y valida conectividad final y pertenencia municipal.

## Evidencia Extremadura

### EXT-03 — granularidad por sección
La granularidad extrema produjo K=65, cuotas 41/24 y `hard=0`, pero M05 terminó con dos outliers muy desiguales: distrito 32 en +36,79 % y distrito 59 en +12,22 %. Ningún movimiento simple ni ninguno de 63 swaps 1×1 válidos cruzaba el mínimo local. La auditoría de articulaciones mostró que el bloqueo era estructural y no un problema de número de iteraciones.

Conclusión: **sección individual no es una unidad de trabajo adecuada por defecto**. Da demasiados grados de libertad a M04 y transfiere deuda topológica a M05.

### EXT-04 — barrido de macro-unidades
Barrido grueso, Run `34631623662`:
- `chunk_ratio=0.25` → M04 deja 1 distrito fuera de suelo/techo;
- `0.40` → 4;
- `0.60` → 5.

Barrido fino, Run `34641091413`:
- `0.10` → descubre un bug de robustez independiente en `hybrid_partition`: tras varios peels puede llegar a `grow_partition(rem,left)` con `left > len(rem)`;
- `0.15` → macro-unidades válidas, pero M04 conserva 2 violaciones duras;
- `0.20` → **primer tamaño probado que alcanza K=65, cuotas 41/24 y `hard=0`**.

El resultado c020 construye 521 unidades de partición totales. Los siete municipios abiertos producen respectivamente 11, 47, 12, 19, 8, 30 y 13 macro-unidades internas para `06011`, `06015`, `06044`, `06083`, `06153`, `10037` y `10148`.

### M04→M05 con c020
M04 c020: min 14.050, max 18.318, `hard=0`.

M05 sin fase C:
- máximo desvío ≈13,30 % frente a 36,79 % del enfoque por sección;
- unidades alteradas: 66 frente a 134;
- cuatro outliers leves en vez de un outlier extremo;
- splits reales finales: `06011:2`, `06015:12`, `06044:4`, `06083:6`, `06153:3`, `10037:7`, `10148:3`.

La comparación no debe hacerse únicamente por número de outliers. La función objetivo canónica prioriza restricciones duras, magnitud, máximo desvío y error global; c020 es estructuralmente muy superior al enfoque por sección.

EXT-06 Run `34642098588` añadió dos swaps 1×1 deterministas y redujo los cuatro outliers a dos sin aumentar splits ni violar restricciones duras. El máximo desvío sigue en 13,30 %, por lo que c020 es candidato pero no cierre final todavía.

## Evidencia Andalucía

AND readiness Run `34626804248`: 18 municipios superan 1,12× target; Sevilla 8,652×, Málaga 7,502×, Córdoba 4,072×, Granada 2,956× y Jerez 2,701×. Esto refuerza que `partition_unit_field` no puede ser una excepción específica de Extremadura: debe convertirse, tras validación, en abstracción común del motor.

## Deuda técnica separada

El caso c010 reveló una precondición no protegida en `hybrid_partition` / `grow_partition`. Debe corregirse antes de utilizar granularidades muy finas en territorios mayores, pero **no debe mezclarse con la validación A/B de c020**, porque no es la causa del mínimo residual actual.

## Condición de promoción

La separación `municipality_field` / `partition_unit_field` puede pasar a motor común cuando:
- Extremadura produzca K=65 y cuotas 41/24 con restricciones duras PASS;
- el refinamiento posterior alcance el contrato poblacional objetivo o exista una justificación explícita y auditable para cualquier excepción;
- contigüidad y provincia permanezcan duras;
- los splits municipales observados sean explicables por población/contigüidad y no por granularidad indiscriminada;
- Aragón y Castilla y León mantengan sus baselines mediante R015;
- el comportamiento se pruebe al menos en un territorio de escala urbana mayor antes de convertir un ratio concreto en valor por defecto global.

## Decisión vigente

- La **abstracción** `municipality_field` / `partition_unit_field` queda aceptada como dirección arquitectónica.
- `chunk_ratio=0.20` queda como **candidato empírico de Extremadura**, no como constante universal.
- La granularidad por sección queda reservada a diagnóstico/fallback, no a política por defecto.
- M05 no debe transformarse en un solver de flujo multietapa para reparar semillas estructuralmente malas; la responsabilidad de una semilla territorialmente maniobrable permanece en M04.
