# Diseño M04 — Municipios sobredimensionados

**Versión:** 1.0.0  
**Fecha:** 2026-09-11  
**Estado:** diseño candidato sustentado por CYL y EXT; pendiente de promoción tras probe M04→M05.

## Problema

M04 necesita respetar el municipio como unidad administrativa real y, al mismo tiempo, permitir que municipios cuya población equivale a varios distritos sean internamente particionables. Usar un único campo para ambos conceptos fuerza dos extremos incorrectos:

1. municipio completamente atómico, que puede hacer imposible la igualdad poblacional;
2. municipio totalmente granularizado, que puede perder disciplina municipal y generar cortes innecesarios.

Castilla y León demostró el primer problema con residuos monolíticos; Extremadura demostró que un único residuo municipal conexo puede bloquear la construcción aun cuando el grafo provincial sea válido. Andalucía eleva la escala: Sevilla ≈8,65 targets y Málaga ≈7,50 targets.

## Separación conceptual propuesta

### `municipality_field`
Identidad administrativa real e inmutable. Se usa para:
- auditoría;
- disciplina municipal;
- métricas de split;
- nombres y composición final;
- reglas políticas/territoriales.

### `partition_unit_field`
Identidad de trabajo de M04. Puede coincidir con el municipio real en municipios pequeños y granularizarse dentro de municipios sobredimensionados. Nunca sustituye la identidad administrativa real.

## Regla candidata

1. Municipios por debajo de `municipality_atomicity_limit_ratio × target` permanecen como una sola unidad de partición.
2. Municipios por encima del umbral pueden producir varias unidades internas conectadas.
3. La granularidad interna debe conservar `municipality_field` original en todas las secciones.
4. M04 puede utilizar esas unidades para construir distritos; M05 sigue auditando movimientos respecto del municipio real.
5. La salida debe registrar explícitamente qué partes pertenecen al mismo municipio y cuántos distritos lo contienen.
6. No se promueve una política de granularidad hasta demostrar en Extremadura que M04→M05 llega a una solución válida sin multiplicar splits municipales no necesarios.

## Evidencia acumulada

- CYL: una micro-unidad residual flexible resolvió un bloqueo de Ávila sin relajar tolerancias.
- EXT granular-open Run 34624914889: M04 base construyó K=65 y `hard=0` en tres escenarios cuando los municipios sobredimensionados dejaron de ser residuos monolíticos.
- AND readiness Run 34626804248: 18 municipios superan 1,12× target; Sevilla 8,652×, Málaga 7,502×, Córdoba 4,072×, Granada 2,956×, Jerez 2,701×.

## Condición de promoción

La separación `municipality_field` / `partition_unit_field` solo pasa a motor común si:
- Extremadura produce K=65 y cuotas 41/24;
- M05 puede reducir el error poblacional al contrato objetivo elegido;
- contigüidad y provincia permanecen duras;
- los splits municipales observados son explicables por población/contigüidad y no por una granularidad indiscriminada;
- Aragón y Castilla y León mantienen sus baselines mediante regresión.
