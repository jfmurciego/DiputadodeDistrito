## 2026-11-11 — T-247 — Tests de `pruebas` independientes del estado que reescribe la campaña

- Causa (PR #713, HEAD 65afefa, suites 2-5; reproducido en `origin/main` 09ba9a2): cuatro tests leían estado vivo que
  reescriben los commits del bot, que no ejecutan `pruebas`, así que `main` quedó rojo sin tocar código:
  - `test_t113_gestor_historico.Plan` (7 + markdown): leía `datos_abiertos/INDEX.json`; `9c0cab12` («registrar activos
    persistentes del visor», 13:46) lo dejó en 17 territorios (antes 51-52, sin Huesca) → «sin M06 publicado».
  - `test_bateria_motor…test_comparacion_con_publicado_ignora_etiquetas`: construía la partición desde la canónica
    `datos/composicion/congreso_huesca.csv`, pero la función compara con `runs/<t>_<run>.csv` del canonical_m06 del visor
    (run 42991551418), que es otra partición.
  - `test_ejecucion_completa.CastillaLaMancha…` y `test_continuar…castilla_la_mancha_m08_reuse_follows_m06_lineage`:
    exigían M06 y M08 del mismo run; la cadena 00 43025652192 (M06, `384a9e71`) → 00 «Reutilizar» 43031565452 (M08,
    `248bce79`/`56b214f8`) deja runs distintos con linaje válido (fase 02 del run del M08 = run y sha256 del M06).
- Cambio (solo tests): T-113 sobre una raíz enlazada con INDEX congelado de 52 circunscripciones
  (`tests/fixtures/t247_m06_publicados_52.json`, del INDEX de b7917e6e) y un test nuevo de omisión sin M06; batería
  sobre raíz sintética (y comprueba que otra partición da `igual=False`); CLM comprueba el invariante de linaje real
  (fase 02 del run del M08 → M06 vigente) en vez de «mismo run». Legacy: `legacy/tests/test_t113_gestor_historico_v1.0.0_20261111.py`.
- Mutaciones: Huesca fuera del INDEX congelado → falla; manifiesto con fase 02 rota + resolver sin la comprobación de
  linaje → fallan los dos de CLM.
- El INDEX de 17 territorios tras `9c0cab12` es una regresión real de la P50 por lotes (salen los 34 del lote): el rojo de
  T-113 era una alarma verdadera. El fixture congelado es el INDEX bueno (52, con Huesca), no el de 17. T-113 deja de
  vigilar el INDEX vivo: esa comprobación (no menos territorios que el registro del visor sin retirada explícita) la
  hace T-249, en su propio test.
