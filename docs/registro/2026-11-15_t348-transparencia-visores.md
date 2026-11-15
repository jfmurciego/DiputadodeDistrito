## 2026-11-15 — T-348 — Transparencia: la frase de Cloudflare/NEL también en nacional y Congreso
- Causa: T-346 añadió la frase a V1, V3 y textos.md (V2 y sitio); nacional y Congreso, que se sirven del mismo Cloudflare, no la llevaban.
- Cambio: misma frase tras la nota de OpenStreetMap en `visor/nacional/index.html` (1.0.6) y `visor/congreso/index.html`, sin párrafo de medición de visitas (no cargan contador). No se añade la frase de OSM al pie de V2/V3/sitio: no cargan teselas (solo `app.js`, `nacional.js` y `congreso.js`, D-104).
- Pruebas: `tests/test_visor_analitica.py` 2.2.0 (frase en nacional/Congreso, sin contador; OSM solo donde hay teselas), `tests/test_visor_sin_terceros.py`, GovernanceHeaders.
- Riesgos: ninguno en motor, workflows ni huellas; no se publica. No verificado desde el entorno que esas dos páginas emitan NEL (red bloqueada); el texto dice «puede enviarle».
