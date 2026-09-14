# F1.3 — Contrato de límites poblacionales estricto

**Fecha:** 2026-09-12  
**Alcance:** motor común y herramientas de diagnóstico de Aragón, Castilla y León y Extremadura.

## Acción

- Se centraliza el cálculo de objetivo, suelo, techo y tolerancia en `ddd_core.config.hard_limits()`.
- Se eliminan los valores por defecto territoriales de 18 consumidores en `ddd_core/`, `modulos/` y `herramientas/`.
- Una configuración que omita cualquiera de los tres ratios falla explícitamente conforme a `CONTRATO_TERRITORIO.md §5`.

## Verificación previa al push

- `python -m compileall -q ddd_core modulos herramientas`: PASS.
- Búsqueda de defaults `0.8 / 1.75 / 0.12` mediante `.get(..., default)`: 0 resultados.
- Gobernanza y evidencia publicada R016: 8 tests PASS.

## Criterio remoto

El cambio solo se promueve si las regresiones completas de Aragón y Castilla y León terminan SUCCESS sin variación de sus trinquetes.
