## 2026-11-15 — T-354 — Espejo en R2 (ARC-E) de las 4 fuentes de mesas de Galicia

**Causa.** La Xunta (abertos.xunta.gal) no se alcanza desde la nube (proxy 403); la 03 de Galicia depende de 4 CSV vivos. Mismo patrón que T-299.

**Cambio.** `comprobar_fuente_electoral_oficial.py` 1.4.0: antes de la URL oficial lee el espejo `<election_id>_<source id>.csv` del índice; sin entrada, sin sha256, sin credenciales o sin objeto sigue con la oficial; la huella (y `expected_sha256`) se exige igual. `fuente_r2.py` 1.1.0: `traer`, y entrada con sha256 null = no disponible. `fuentes_r2.json`: 4 entradas de Galicia 2024 con sha256 null (PENDIENTE). `preparacion-resultados-electorales.yml` 1.0.16: credenciales R2 en el paso «Preparar paquete electoral». `herramientas/espejo_galicia_r2.ps1` 1.0.0 (Windows del propietario: baja, sha256, sube a `arc-e/fuentes/xunta/` y escribe `espejo_galicia_r2_resultado.json`).

**Segundo paso (tras el script).** Con el JSON del propietario: rellenar clave/sha256/bytes/descargado_en en el índice (PR pequeña). Hasta entonces el espejo no se usa y la 03 va a la Xunta como hoy.

**Pruebas.** `tests.test_t354_espejo_galicia` (aut12; sin red, misma huella espejo/oficial, nombres derivados de la declaración), t299, galicia_electoral_vigente, t349_flujo, t220_renombrado.

**Riesgos.** Cambia la versión del workflow y no cambia huellas M05. No fusionar hasta terminar la r4 (57 pendientes). Solapes: #800 (workflow), #797 (índice); rebasar la que se fusione después.
