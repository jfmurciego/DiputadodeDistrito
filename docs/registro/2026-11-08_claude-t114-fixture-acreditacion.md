## 2026-11-08 — T-114 — Planificador de acreditación histórica sobre evidencia fija

- Causa: `test_planner_reuses_both_real_m06_from_durable_sealed_evidence` leía el catálogo y la evidencia vivos;
  la 00 de Castilla y León 42521090842 registró su fuente territorial nueva antes que su M06, y la fuente viva
  (42521090842) ya no coincide con la fase 01 del manifiesto del M06 vigente (40969454399) →
  `DURABLE_LINEAGE_INCOMPATIBLE`. El resolver acierta: reutilizar ese M06 con otra fuente es un linaje roto.
- Cambio: el test se evalúa sobre una raíz mínima con la fila de catálogo, el contrato, `registro_electoral.yaml`,
  el receipt M06 y el manifiesto 00 copiados en `tests/fixtures/acreditacion_historica/planificador/`
  (Aragón M06 42497101869 de `730f9ee`; Castilla y León M06 42497104110 de `74dc873^`), verificados con sha256
  (`INDEX.json`). Mismas aserciones; ya no depende de las 00 que se lancen.
- Pruebas: `tests.test_acreditacion_historica_territorial` 14/14 en local sobre el estado de `origin/main`.
- Ampliación (Coordinador): `datos/resultados/` regenerado con `resultados_ligeros.py` (nuevos Andalucía, Aragón, Ceuta,
  Alicante, Barcelona, Málaga; runs nuevos de La Rioja, Melilla y Región de Murcia), `datos_abiertos/` con
  `generar_datos_abiertos.py` (52 provincias, `--comprobar` al día) y `orchestracion/catalogo_procedencia.json`.
- Causa raíz del desfase: la 05 de La Rioja (run 42504388624) persistió un M06 nuevo en `publicaciones_visor.json` sin
  regenerar `datos_abiertos/`; `generar_datos_abiertos.py --materializar` bloqueaba toda 05 posterior.
  Publicador 3.7.0: regenera `datos/resultados` y `datos_abiertos/` desde el registro candidato, comprueba, materializa
  y los persiste en el mismo commit que el registro.
- `resultados_ligeros.py` 1.2.0: conserva todas las claves ajenas del MANIFEST (`partidos_runs`) y solo borra los CSV que
  su MANIFEST listaba (antes borraba `contraste_2023.csv`); test del caso.
