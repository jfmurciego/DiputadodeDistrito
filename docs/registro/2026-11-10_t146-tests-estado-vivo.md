## 2026-11-10 — T-146 — Tests de Extremadura no fijan el estado vivo del catálogo

Causa: main en rojo (run 42725626761). La preparación territorial de Extremadura (run 42720735134) dejó el catálogo en
`source_prepared_pending_pre_m04` y 3 tests exigían `generation_ready`.
Cambio: `tests/_estados_vivos.py` (`ESTADOS_PREPARADO`, estados válidos del ciclo) y los 3 tests aceptan el conjunto
(`test_extremadura_preparacion_declarativa` x2, `test_promocion_automatica_catalogo::test_master_catalog_matches_extremadura_promotion`).
No se toca el catálogo vivo. Pruebas: ambos módulos en verde (18 tests). Riesgos: ninguno en producción; solo tests.
Pendiente general: otros tests leen estado vivo (`configuracion/catalogo_*`, `territorios/*/evidencia`); la solución de fondo es
`tests/_raiz_congelada.py` (fixture fija) o el conjunto de `_estados_vivos.py`.
