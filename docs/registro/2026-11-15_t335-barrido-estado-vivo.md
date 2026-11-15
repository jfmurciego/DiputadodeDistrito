## 2026-11-15 — T-335 — Barrido de tests de estado vivo ante la campaña r3 (fixture congelado)

**Causa.** `main` en rojo (run 43654900207 sobre 59a6257): `test_gestor_campana_provincias::test_huesca_completa_reutiliza_su_producto` leía el estado vivo de nac22, que el P10 de r3 reescribe (`PRODUCT_REUSE_READY` → `BLOCKED`). Tercer test igual; se hace un barrido único en vez de arreglar uno a uno.

**Barrido.** (1) 123 módulos de test tocan `territorios/`, catálogos o `orchestracion/`; los que ya usan `_previo_r3`, `_raiz_congelada` o `tmp` no cuentan. (2) Batería completa en un worktree temporal con lo que escribirá cada robot: P10 de nac32–nac52 (estado `source_prepared_pending_pre_m04`, `generation_enabled=false`, recibo nuevo, sin `pre_m04_*`) y P00 de los 71 (`last_valid_checkpoint` nuevo, nueva `ejecuciones_completas`/`generaciones_m06`), frente a la misma batería sobre `main` (3241 tests; solo se compara la diferencia de fallos). (3) Resultado: rompe solo `test_gestor_campana_provincias` (ya rojo) y `test_galicia_electoral_identity_gate` (3 tests: `last_valid_checkpoint` de aut12 = run del producto electoral vivo). Los demás fallos nuevos de la simulación son artefactos (recibos sintéticos que no cuadran con su identidad en `test_design_a_catalogo`/`test_f10_derived_doors`/`test_catalogo_preparacion_cli`) o estado vivo por diseño (`test_catalogo_procedencia`: compara el catálogo vivo en main/nocturna).

**Cambio (solo tests y fixture; sin motor ni workflows).**
- `tests/fixtures/previo_r3` + MANIFEST: añade territorios/nac22 previo a su P10 (git 320f64b^, 24 ficheros, sha256 en el MANIFEST).
- `test_gestor_campana_provincias`: Huesca se prueba con `build_manifest(root=raiz_previo_r3())`.
- `test_galicia_electoral_identity_gate`: catálogo, recibos, contrato y registro de aut12 salen de la raíz congelada (`setUpModule`); el workflow sigue siendo el vivo.

**Pruebas.** `test_gestor_campana_provincias`, `test_galicia_electoral_identity_gate`, `test_t220*`, guardián y `GovernanceHeaders`, en local.

**Riesgos.** Sin efecto en huellas ni en la 00. Tests de estado vivo por diseño se quedan en main/nocturna. PR `no-automerge`.
