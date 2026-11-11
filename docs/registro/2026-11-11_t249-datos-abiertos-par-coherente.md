## 2026-11-11 — T-249 — Par M06/M08 por linaje en la P50 y en datos abiertos, con guarda contra reducciones

- Causa (P50 lote 43030563528, commit del bot `9c0cab12`): el lote registró solo `canonical_m06` de 34 runs territoriales,
  sin el `canonical_m08` de su cadena. `herramientas/generar_datos_abiertos.py` 1.2.0 tomaba el M06 más reciente y exigía M08 del
  mismo run; si no, omitía el territorio en silencio y el bucle final borraba su directorio: `datos_abiertos/INDEX.json` pasó de 51 a 17.
- Decisión del Planificador: publicar un territorio = registrar el PAR; emparejamiento por LINAJE (criterio del dashboard, #354).
- `herramientas/linaje_m06_m08.py` 1.0.0 (nuevo): un M08 es del linaje de un M06 si comparten run o si el manifiesto
  `territorios/<t>/evidencia/ejecuciones_completas/<run M08>.json` da 02 = run del M06 y 04 = propio run en success.
- `herramientas/registro_publicaciones_visor.py` 1.8.0: `candidate` (CLI, el que llama la P50) rechaza todo el lote con
  `PAR_INCOMPLETO` si en un territorio tocado el M08 vigente falta o no es del linaje del M06 vigente. `make_candidate` no cambia;
  el workflow no cambia. Legacy: `legacy/herramientas/registro_publicaciones_visor_v1.7.0_20261111.py`.
- `herramientas/generar_datos_abiertos.py` 1.3.0: `pares_vigentes` = M08 vigente + M06 de su linaje; `generar`, `materializar` y
  `comprobar` lo usan. Guarda `DATOS_ABIERTOS_REDUCCION`: falla antes de escribir INDEX o borrar si se pierde un territorio que
  sigue con M06 y M08 en el registro (retirada explícita = sin M06 o sin M08 de la elección).
  Legacy: `legacy/herramientas/generar_datos_abiertos_v1.2.0_20261111.py`, `legacy/tests/test_datos_abiertos_v1.0.0_20261111.py`.
- Recuperación en git: `datos_abiertos/` restaurado desde `9c0cab12^` y regenerado: 52 territorios (los 51 previos con el mismo
  blob M06 y La Rioja); `--comprobar` al día. El sitio desplegado no cambia hasta la próxima P50.
- Pendiente (Operador, con frase del propietario): publicar el M08 de la cadena de los 35 territorios con M06 sin par (runs
  electorales «Reutilizar» del bot); hasta entonces el mapa del visor usa el M06 nuevo con resultados del par anterior.
- Avisos `::warning::` del generador: territorio omitido (MANIFEST de resultados que no acredita el M08, o ZIP del M06 ausente)
  y «par antiguo en uso» (M06 vigente más nuevo que el del par: hoy 35, p. ej. congreso_alicante 42940331557 frente a 42495067503).
  `origen` del INDEX.json: «canonical_m08 vigente + canonical_m06 de su linaje».
- Tests: `tests/test_datos_abiertos.py` (`ParCoherente`; `test_m06_nuevo_sin_m08_conserva_el_par_anterior` reproduce el caso real:
  M06 nuevo sin M08 con el INDEX previo, que se conserva entero), `tests/test_t249_par_linaje.py`.
