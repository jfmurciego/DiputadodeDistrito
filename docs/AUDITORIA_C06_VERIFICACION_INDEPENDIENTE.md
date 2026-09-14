# Auditoría C-06 — Verificación independiente

**Versión:** 1.0.0  
**Fecha:** 2026-09-13  
**Estado:** cerrado — recomputación independiente  
**Anterior:** ninguno — documento nuevo

El verificador `herramientas/verificar_independiente_m03_m06.py` usa solo la
biblioteca estándar. No importa módulos del productor, `ddd_core` ni
`herramientas/validar_ejecucion.py`. Desde el grafo M03 y la composición M06
recomputa por BFS universo, población, K, provincia, contigüidad, límites y
disciplina municipal.

## Resultado

- Aragón: PASS independiente, 1.463 secciones, 1.364.621 habitantes y 67 distritos.
- Castilla y León: PASS independiente, 3.506 secciones, 2.401.221 habitantes y 82 distritos.
- Extremadura: `BLOCKED_INDEPENDENT_VALIDATION`; además de dos distritos fuera
  de tolerancia, aparecen cinco municipios con más de un distrito mixto:
  `06015`, `06044`, `06153`, `06083` y `10037`.

El hallazgo no promueve ni recalcula Extremadura. La evidencia completa queda
en `docs/SALIDAS_CHATGPT/EVIDENCIAS/C06_VERIFICACION_INDEPENDIENTE.json`.
