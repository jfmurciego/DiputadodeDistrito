## 2026-11-07 — T-53 — Resultados electorales ligeros en git

Causa: los análisis tenían que descargar los ZIP M08 para ver los ganadores por distrito.
Cambio: `herramientas/resultados_ligeros.py` escribe `datos/resultados/<territorio>.csv` (distrito, población, votos totales, ganador, votos y porcentaje del ganador) y `MANIFEST.json` (run, blob_sha, sha256 de origen y de cada CSV) desde los `canonical_m08` vigentes, con sha256 verificado; el workflow `resultados-ligeros.yml` lo regenera con la app de registro cuando cambia `publicaciones_visor.json`; `generar_hemiciclo.py` 1.1.0 lee estos CSV (blobs como respaldo). Limitación: el M08 solo trae el ganador, no los votos de cada partido, así que hay una fila por distrito y no por partido. Generados los 49 CSV de provincias (63 territorios).
Pruebas: `tests/test_resultados_ligeros.py` (M08 sintético, idempotencia byte a byte, sha256 erróneo, lectura de ganadores) y `tests/test_generar_hemiciclo.py`.
Riesgos: ninguno para 00; no cambia checkpoints ni huellas.
