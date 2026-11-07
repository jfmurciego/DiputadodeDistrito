## 2026-11-07 — T-52 — Cadenas 00 territorial → Activación → 00 electoral en GitHub, sin el Mac

Causa: la cadena 00 territorial → «Activación de Legislatura» `prepare_one` → 00 electoral «Reutilizar» corría en el Mac
del propietario (`lanzadores-mac/lanzar_resto.sh`, fase B); la 00 solo encadenaba sola cuando la 04 se saltaba por falta
de par, sin comprobar duplicados ni dejar estado. Cambio: `ejecucion-completa-proyecto.yml` 1.6.0 con dos entradas
compatibles (`cadena_electoral`, por defecto false, y `cadena_origen_run_id`) y `run-name` con territorio y modo. El job
«Encadenar par de fuentes y 04» también corre en una 00 `territorial_only` con `cadena_electoral`; antes de cada dispatch
comprueba que el territorio no tenga ya una activación o una 00 en cola o en curso (`CHAIN_DUPLICATE_SKIPPED`; si la
activación ya corre, espera a esa); si la activación falla (paquete caducado o par incompatible) para con la causa. El
eslabón electoral sale siempre con `publish_result=false` (publicar sigue aparte, con permiso del propietario) y lleva
`cadena_origen_run_id`, que `escribir_manifest_ejecucion_completa.py` guarda en `chain` del manifiesto; el estado de cada
eslabón queda en el artefacto `ddd-cadena-<run>` y en el resumen. Los dispatch del bot no esperan al environment
`produccion` (T-41). Skill `operador` actualizada. Pruebas: `tests/test_cadena_electoral.py` (7), encadenado, elección,
manifiesto, ejecución completa y tests de workflows en verde.
