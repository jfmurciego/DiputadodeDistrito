## 2026-11-16 — Hotfix T-334 — test del M06 independiente del INDEX vivo

Causa: `test_el_m06_se_busca_con_id_nuevo_aunque_el_indice_tenga_el_viejo` afirmaba sobre `datos_abiertos/INDEX.json` vivo que no traía `nac01`. Desde que la P50 de los lotes registra ids nuevos (fc259b9) el INDEX lo trae y el test fallaba en toda PR.

Cambio: solo el test. Usa un índice sintético con la clave de `id_legacy("nac01")` (sin literal viejo), comprueba que `nac01` no está y que `en_mapa` lo resuelve por el id viejo; `hc._m06("nac999", …)` sigue levantando `SystemExit`. Otros tests sobre el INDEX vivo (`test_visor_v3_ui.js`, `test_t113`) no usan ids concretos o ya usan fixture. No toca motor, workflows ni datos.

Pruebas: `test_t334_seguimiento_paso_a` y `test_t220_renombrado` en python3.11, 15 tests OK.
