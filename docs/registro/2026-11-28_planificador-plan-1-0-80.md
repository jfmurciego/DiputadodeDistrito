## 2026-11-28 — T-555 — Plan 1.0.80 y traspaso del Planificador

- Causa: el propietario aprueba («sí a todo») los siete bloques de la investigación profunda T-509; el chat del Planificador supera el umbral de relevo.
- Cambio: `docs/PLAN.md` 1.0.80 (D-217; T-506 a T-555; estados de T-503 a T-505 y de la tanda 2). Copia en `legacy/docs/PLAN_v1.0.79_20261126.md`. `docs/TRASPASO_PLANIFICADOR_2026-11-28.md`.
- Pruebas: `tests/test_r015_invariantes.py` en local (el fallo de `M05Determinism` es del entorno, también en `main`).
- Riesgos: ninguno de producto; solo documentación. El informe de T-509 sigue en su rama, sin PR, a la espera de la orden del propietario.
- PR: esta.
