## 2026-11-14 — T-301 — La P50 versiona la composición vigente de cada M06 que publica

- Causa: 36 de los 71 territorios publicados salen SIN_VIGENTE en la competición y la batería (D-66, «nunca peor que el
  vigente»): el M06 del visor (blob de git) solo trae polígonos y totales por distrito; la asignación sección→distrito vive
  en artefactos de Actions que caducan y no se descargan desde la sesión cloud.
- Cambio (decisión del Planificador, sin workflow nuevo): `_reutilizable-publicar-sitio.yml` 3.15.0 llama, por run del lote
  y tras describirlo, a `composicion_m06.py --descriptores` (1.2.0): extrae la composición de los artefactos ya descargados,
  la valida contra el M06 que se publica y la escribe en `datos/composicion/runs/<id>_<run>.csv` (lo que lee
  `ddd_motor2.vigente`) con su sha256 en `datos/composicion/MANIFEST_RUNS.json`. Se persiste en el mismo commit que el
  registro. Si un territorio del lote no se recupera, el lote se rechaza antes de crear blobs (`COMPOSICION_NO_RECUPERADA`).
  Copias previas en `legacy/`.
- Efectos: toda publicación futura deja su vigente versionado. Los 36 actuales se rellenan republicando los mismos runs en
  una P50 por lotes (la lanza el Operador). La huella motor2 cambia al entrar los CSV (esperado).
- Riesgos: la descarga selectiva `ddd-state-<run>-M06*` debe traer el CSV de composición; si no, el lote se rechaza con el
  territorio nombrado (no se publica sin vigente).
- Pruebas: `tests/test_t301_composicion_p50.py` (escribe y no pierde territorio, escenarios ignorados, id viejo reutilizado,
  orden de pasos del workflow). `test_recuperar_composicion_ine` y otros fallan en local sin pyproj, también en main.
