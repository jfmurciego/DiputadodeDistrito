## 2026-11-09 — T-117 — El error de activo duplicado nombra las dos entradas

Causa: la 05 42538420980 (production_run_id=42531122768, Castilla y León) falló en «Construir candidato» con «Activo inmutable duplicado» sin decir qué entradas colisionaban; el blob 5143b70a no está en el registro de main, así que chocan dos entradas nuevas del mismo run.
Cambio: `registro_publicaciones_visor.py` 1.2.1; el error imprime id, kind, territorio, ejecución y sha256 de ambas. No cambia ningún criterio (inmutabilidad y sha256 intactos).
Pruebas: `tests.test_registro_escenarios` (caso nuevo). Diagnóstico de la causa de fondo: pendiente de decisión (ver cierre).
