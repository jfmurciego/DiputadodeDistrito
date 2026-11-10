## 2026-11-10 — T-136 — Certificador exacto 1.1.0 sobre el núcleo de reglas (fallos F1 y F2)

- **Causa:** T-132 encontró dos fallos en la 1.0.0:
  - **F1:** en Canarias daba una infactibilidad falsa. Tomaba la provincia y el municipio del M01, sin `DDD_PARTITION`,
    y no aplicaba la exención por partición.
  - **F2:** en Cádiz partía unidades M04, porque agrupaba las unidades dentro de cada municipio.
  Además, T-160 pidió usar el núcleo único `ddd_motor2.reglas`.
- **Cambio:** `herramientas/certificador_exacto.py` 1.1.0. Toma las reglas de `Reglas.desde_contrato` (límites exactos),
  el criterio de `Criterio` (perfiles `nucleo` y `produccion`) y el veredicto de `evaluar()`. Las secciones se leen del
  M04 con los campos del contrato. Las unidades M04 se unen con unión-búsqueda y se comprueba su integridad. Se quitan
  las reglas propias y las contigüidades de flujo y cortes. Copias de la 1.0.0 en `legacy/herramientas/` y `legacy/tests/`.
- **Pruebas:** `tests.test_certificador_exacto` (7 tests, con casos de F1 y F2), `tests.test_motor2_reglas` y
  `tests.test_r015_invariantes` en verde. Casos reales con el motor 7.4.4 de la batería:
  - Canarias: FACTIBLE en 1,5 s y el canónico da PASS.
  - Cádiz: 46 átomos, sin unidades partidas; techo mínimo 1,15919× (óptimo); con techo 115 %, infactible.
  - Álava: 1 plan.
- **Modo de 00:** ninguno (herramienta de diagnóstico).
