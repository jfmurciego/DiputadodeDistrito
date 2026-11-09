## 2026-11-09 — T-117 — El error de activo duplicado nombra las dos entradas y avisa de «M08 idéntico al M06»

Causa: la 05 42538420980 (production_run_id=42531122768, Castilla y León) falló en «Construir candidato» porque el M06 y el M08 del run tienen los mismos bytes (blob 5143b70a = ZIP del M06): defecto de la 00 «Reutilizar»/CyL, no de la 05. El error no decía qué entradas chocaban.
Cambio: `registro_publicaciones_visor.py` 1.2.1; el error imprime id, kind, territorio, ejecución y sha256 de ambas y, si son M06 y M08 de la misma ejecución, avisa «M08 idéntico al M06». La unicidad de ubicación NO se relaja (decisión del propietario).
Pruebas: `tests.test_registro_escenarios`, `GovernanceHeaders`.
