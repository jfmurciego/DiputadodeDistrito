# Auditoría C-07 — Caso sintético adversarial

**Versión:** 1.0.0  
**Fecha:** 2026-09-13  
**Estado:** candidato a certificación CI  
**Anterior:** ninguno — documento nuevo

El caso C-07 usa un grafo camino de cuatro secciones con poblaciones
`60/40/30/70`, K=2 y objetivo 100. Las tres divisiones contiguas posibles dan
`60/140`, `100/100` y `130/70`; por tanto, existe una única solución óptima
calculable a mano: `{60,40} | {30,70}`.

La prueba ejecuta M01–M06 exclusivamente sobre estos datos sintéticos y exige la
asignación exacta, no solo cardinalidades. Además inyecta una partición
plausible pero errónea y prueba que el oráculo la rechaza. Así demuestra
capacidad real para detectar un motor que ignore población o asigne al azar.

No se leen ni recalculan datos territoriales certificados y C-01 queda intacto.
