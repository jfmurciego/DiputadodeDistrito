## 2026-11-07 — T-60 — Datos abiertos y fichas por distrito

Causa: el visor solo muestra mapas; faltaba un paquete reutilizable y una página pública por distrito.
Cambio: `herramientas/generar_datos_abiertos.py` 1.0.0 y `datos_abiertos/` (49 provincias nacionales: CSV de resultados, fichas
estáticas, `INDEX.json` con licencia CC BY 4.0, run, blob_sha y sha256 de ZIP, GeoJSON y CSV, README, `nombres.json` opcional
para T-59). El GeoJSON (~50 MB) no se versiona: el publicador del sitio 3.4.0 lo extrae del blob M06, verifica su sha256
contra el índice y publica todo en `/datos/`.
Pruebas: `tests/test_datos_abiertos.py` (8, territorio sintético, idempotencia, sha256 erróneo, materialización), hemiciclo-sitio,
workflow_safety, design A, guardián. R015 solo falla en `M05Determinism` por falta de geopandas local. PR: pendiente.
