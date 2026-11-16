## 2026-11-16 — Hotfix T-334 — test del M06 independiente del INDEX vivo

Causa: `test_el_m06_se_busca_con_id_nuevo_aunque_el_indice_tenga_el_viejo` afirmaba sobre `datos_abiertos/INDEX.json` vivo que no traía `nac01`. Desde que la P50 de los lotes registra ids nuevos (fc259b9) el INDEX lo trae y el test fallaba en toda PR.

Cambio: solo el test. Usa un índice sintético con la clave de `id_legacy("nac01")` (sin literal viejo), comprueba que `nac01` no está y que `en_mapa` lo resuelve por el id viejo; `hc._m06("nac999", …)` sigue levantando `SystemExit`. Otros tests sobre el INDEX vivo (`test_visor_v3_ui.js`, `test_t113`) no usan ids concretos o ya usan fixture. No toca motor, workflows ni datos.

Pruebas: `test_t334_seguimiento_paso_a` y `test_t220_renombrado` en python3.11, 15 tests OK.

Alcance ampliado (T-362, por orden del Planificador): revisión de tests que leen registros vivos (`grep` de INDEX.json, publicaciones_visor, archivo_r2, registro_publicaciones, catalogo_preparacion, datos/resultados).
- Arreglado: `test_t334 · test_el_m06_se_busca_…` (INDEX sintético) y `test_t334 · test_manifiesto_clave_neutra…` (entrada histórica sintética en vez de la primera de `MANIFEST_M07.json` vivo).
- Ya independiente / invariante del formato: `test_t199` (valida el registro real, sin ids), `test_t201` (registro real sin cambios), `test_t125` (usa el registro solo como base de una entrada sintética), `test_t126` (ausencia de 350 por política; formato canónico; el Valladolid 407 es un pin de aditividad deliberado), `test_registro_escenarios`, `test_congreso_visor`, `test_numeracion_publica` (1..K sobre todo el INDEX, sin ids), `test_t113` (huellas de todos los territorios), `test_visor_v3_ui.js` (busca por provincia), `test_publicacion_multiterritorio` (pines sha256 de static-aragon/castilla_y_leon, deliberados), `test_catalogo_procedencia`, `test_ahorro_ci_pruebas` (rutas como cadenas), `test_t258` (cadenas), y los que escriben su propio registro en tmp (`test_t237`, `test_t305`, `test_t349_*`, `test_gestor_*`, `test_estado_operativo_*`, etc.).
