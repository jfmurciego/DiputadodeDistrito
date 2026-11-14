## 2026-11-14 — T-322 — aut11 y aut12 a la raíz congelada y linaje fijado (continuación de #793)

**Causa.** Cada P10 nuevo de la campaña r3 reescribe `territorios/<aut>/evidencia` y el catálogo; los tests que leían el estado vivo de aut08/aut01 fallaban en `main` (`CONTINUE_DURABLE_BLOCK … DURABLE_LINEAGE_INCOMPATIBLE territorial_source→territorial_product`).

**Cambio (solo tests; sin motor, contratos ni workflows).** Fixture `tests/fixtures/previo_r3/` (160 ficheros, sha256 en `MANIFEST.json`, verificado al montar): estado de aut08 (M06 43025652192 + M08 acreditado), aut11 (M06 40656175842), aut12 y receipt territorial de aut01 en git `cc34b0c` (previo a r3). Helper nuevo `tests/_previo_r3.py` 1.0.0. Tests movidos al fixture (cabecera y `legacy/tests/` actualizados):
- `test_reanudacion_m08_huerfano` 1.0.5: `test_castilla_la_mancha_m08_is_reused_only_with_its_exact_m06`; añade el caso explícito: con un P10 nuevo (sha del M06 distinto) `build_plan` da `DURABLE_LINEAGE_INCOMPATIBLE`.
- `test_continuar_ultimo_resultado_valido` 1.0.4: `test_castilla_la_mancha_m08_reuse_follows_m06_lineage`.
- `test_ejecucion_completa` 1.0.6: `CastillaLaManchaReuseCurrentDurableInputsTests`.
- `test_t244_andalucia_receipt_vigente` 1.0.2: receipt 253f/40946875467 de aut01.
- `test_00_reuse_real_regressions` (Extremadura/aut11, 36472516474) y `test_gestor_campana_nacional` 0.0.8 (2 casos de aut12: ruta y linaje) y `_test_gestor_campana_core` (`first_generation_preflight_is_structural`, aut12): a la raíz congelada.
- Los tres casos de Castilla-La Mancha fijan con `assertTrue(enlazado/same_lineage)` la rama del fixture (sin ramas `if/else` que probarían la contraria con otros datos).
- `test_f10_receipt_contract` ya usaba `frozen_root()` (aee8215e), no el estado vivo: sin cambios.

**Barrido.** Suite completa (3232 pasan) sobre `main` con r3 tandas ya aplicadas (aut06–aut10 con P10 nuevo): solo esos 4 fallaban por estado vivo (más `tests/legacy/*`, que no corre en CI, y `test_0000_integration_loader`, preexistente por ruta de importación). Rojo antes (4 fallos en `origin/main`), verde después.

**Simulación de P10 nuevo (aut11…aut20).** En copia temporal se cambió para 9 territorios el `preparation_evidence` (run_id+7, nuevo sha, receipt copiado a la ruta nueva) y se corrieron: `test_extremadura_preparacion_declarativa`, `test_galicia_*`, `test_f10_asturias_galicia_receipt_candidates`, `test_preparacion_legislatura_vigente`, `test_territorial_only_selector`, `test_gestor_campana_nacional`, `test_gestor_campana`, `test_f10_receipt_contract`, `test_ejecucion_completa`, `test_00_reuse_real_regressions`: antes 3 fallos (aut12 en gestor nacional ×2 y gestor_campana ×1); después 205 pasan. `test_catalogo_procedencia` falla en la simulación solo porque el catálogo de procedencia se regenera aparte (derivado, no estado).

**Vivos por ser invariantes** (no leen run_id/sha fijos de P10; resuelven por linaje o estructura): `test_baleares_36573474139…` (manifiesto de run fallido inmutable), `test_f10_*`/`test_galicia_*`/`test_castilla_y_leon_electoral_reuse` (raíz `_raiz_congelada` o linaje), `test_catalogo_procedencia`, `test_gestor_campana`, `test_dashboard_*` (sintéticos o por regla).

**Riesgos.** Una nueva tanda P10 puede romper un test no cubierto por la suite actual; la regla: fixture congelado o invariante de linaje (`package_sha256` + `compatibility_identity_sha256`), nunca `run_id` vivo. Sin efecto en huellas ni 00.
