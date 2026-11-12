## 2026-11-11 — T-263 — Archivar a legacy el código muerto de M04 (v745–v754) y M05 (v740)

- **Causa**: T-254 §2 midió 10 motores M04 (`v745`–`v754`, 1 839 líneas) y el M05 `v740` (444) fuera del cierre de imports de producción.
- **Cambio**: los 11 ficheros pasan sin cambios a `legacy/ddd_core/t263_codigo_muerto/` (con README). `configuracion/m04_engine.json`
  deja de listarlos (`internal_components` = cadena viva v7410/v7411/v7412; copia anterior en `legacy/ddd_core/m04_engine_pre_t263.json`).
  Tests: `test_m04_oversized_municipality_hard_bounds` y `test_galicia_local_e2e_regression` usan la base viva `v7410` (mismos hashes de
  partición); se retiran los dos tests que reproducían el fallo de banda estrecha del v745 (documentaban el motor archivado; con v7410
  Alcorcón ya no falla). `test_huella_m05_motor_activo` comprueba además que v740 no está en `ddd_core/`. No se renombra nada.
- **Efecto en huellas**: huella M04 de checkpoints (`ddd_core/m04_*.py` + `m04_engine.json`) CAMBIA (20 → 10 ficheros): la próxima 00
  «Reutilizar» de cada territorio dará `CHECKPOINT_ENGINE_MISMATCH` y rehará desde M04. **La huella M04 de los checkpoints cambia; la próxima 00 de cada territorio va con «Generar desde fuente», no «Reutilizar».** Huella M05 (cierre de imports) y motor2: sin cambio.
- **Pruebas (D-89)**: `bateria_motor.py motor --m05 7.4.4` en `congreso_huesca` y `la_rioja` con `origin/main` (8e4e268) y con la rama:
  composición M06 idéntica (sha256 `524b8c68…` y `faa44f88…`), `RESULTADO.json` idéntico, validación PASS; `preparacion_unidades_internas.json`
  solo difiere en marcas de tiempo. Unittest local OK: `test_m04_oversized_municipality_hard_bounds`, `test_huella_m05_motor_activo`,
  `test_galicia_local_e2e_regression`, `test_m04_engine_contract`, `test_huella_checkpoint_motor`, `test_r015_invariantes` (33 tests).
