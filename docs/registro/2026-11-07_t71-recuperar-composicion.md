## 2026-11-07 — T-71 — Composición sección→distrito recuperada por geometría INE

**Causa.** Los artefactos M06 de 47 provincias caducaron sin composición en git (T-67 recuperó 16/63; T-72 dejó 49 excepciones).

**Cambio.** Nueva `herramientas/recuperar_composicion_ine.py`: punto interior de cada sección del seccionado INE 2023 (OGC, `Secciones_2023`, solo `TIPO=SECCIONADO`) asignado al polígono del M06 publicado (blob de git, sha256 del visor) y población del INE 65034 (Total, 2023). Se valida con `composicion_m06.validar` (secciones y población por distrito idénticos al M06). Salida en `datos/composicion/<territorio>.csv` y `MANIFEST.json` con `fuente` (sha256 del seccionado y del padrón). Recuperadas 47 de 48 pendientes; votos por partido (`resultados_partidos.py`) en 30 territorios; `configuracion/excepciones_archivo_origen.json` queda solo con `ceuta`.

**No recuperado.** `ceuta`: población INE 2023 3826 ≠ 3723 del M06 → 00. Sin votos por partido (secciones del ZIP electoral 2023 ≠ secciones del M06, que el agregador rechaza por diseño): albacete, almería, ávila, badajoz, cáceres, ciudad real, córdoba, guipúzcoa, jaén, la coruña, la rioja, lugo, madrid, pontevedra, sevilla, toledo, valencia, vizcaya, zaragoza.

**Pruebas.** `tests/test_recuperar_composicion_ine.py` (sintético); `archivo_origen comprobar` en verde.

**Riesgos.** Solo datos y herramienta nueva; sin cambios en motor, contratos ni checkpoints.
