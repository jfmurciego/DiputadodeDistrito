## 2026-11-11 — T-249 — Datos abiertos con el par coherente M06/M08 y guarda contra reducciones

- Causa (P50 lote 43030563528, commit del bot `9c0cab12`): el lote registró solo `canonical_m06` de 34 runs nuevos, sin
  `canonical_m08` de esos runs. `herramientas/generar_datos_abiertos.py` 1.2.0 tomaba el M06 más reciente y exigía M08 del
  mismo run; si no, omitía el territorio en silencio y el bucle final borraba su directorio: `datos_abiertos/INDEX.json` pasó de 51 a 17.
- Cambio (1.3.0): `pares_vigentes` empareja el M08 vigente (el de `datos/resultados/`) con el M06 de su mismo run; `generar`,
  `materializar` y `comprobar` lo usan. Guarda `DATOS_ABIERTOS_REDUCCION`: falla antes de escribir INDEX o borrar si el INDEX previo
  tenía un territorio que sigue con M06 y M08 en el registro y no se regenera. Retirada explícita = sin M06 o sin M08 de la elección.
  Legacy: `legacy/herramientas/generar_datos_abiertos_v1.2.0_20261111.py`, `legacy/tests/test_datos_abiertos_v1.0.0_20261111.py`.
- Recuperación: `datos_abiertos/` restaurado desde `9c0cab12^` y regenerado con la 1.3.0: 52 territorios (los 51 previos con el
  mismo blob M06 que antes y La Rioja, con par acreditado); `--comprobar` al día. El sitio desplegado no cambia hasta la próxima P50.
- Límite: para esos 34 el mapa del visor usa el M06 nuevo y los datos abiertos el par anterior hasta que se publique el M08 de su run.
- Tests: `tests/test_datos_abiertos.py` (`ParCoherente`: M06 nuevo sin M08, reducción sin retirada, retirada explícita).
