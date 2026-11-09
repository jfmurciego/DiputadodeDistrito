## 2026-11-09 — T-128 (paso 2) — Fase `ensemble_25` en el 06 «Escenarios y Ensembles»

Autorización: Planificador (09-11): turno y OK para `leer_config_ensemble.py` y el gate del 06. No se lanza ni se publica nada; no se toca el Gestor (T-130).
Causa: la fase `ensemble_25` no existía: `TERRITORIAL_STAGES` solo tenía `ensemble_10` y el gate del 06 acababa en «Fase no admitida» (exit 20).
Cambio: `herramientas/leer_config_ensemble.py` 1.1.0 y `generar-alternativas-territoriales.yml` 2.5.0 admiten `ensemble_25` (territorios, 25 candidatas, 5 lotes de 5; el plan ya lo soportaba). Aragón y el lote de 50 no cambian. Test en `tests/test_ensemble_workflow_generico.py`.
Riesgos: sin efecto en huellas ni motor. El Gestor sigue rechazando el 25 hasta que haya una corrida válida. Republicación de 25 no incluida (solo ensemble_10).
