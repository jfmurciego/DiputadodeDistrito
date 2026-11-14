## 2026-11-14 — T-314 — Respuesta: el bloqueo de linaje durable de CLM no afecta a «Generar desde fuente»

Estudio de solo lectura (`docs/ESTUDIOS/T314_LINAJE_DURABLE/RESPUESTA.md`): `CONTINUE_DURABLE_BLOCK … territorial_source→territorial_product` sale de `validate_durable_assets` y solo lo llama `build_plan` en modo `reuse`; `catalog_source` y `from_start` no llegan. Es transitorio: lo resuelve el M06 nuevo. Reproducido en copia temporal con CLM (aut08); main actual (be94b20, tras #786) ya no tiene el estado y los 2 tests de CLM pasan. Sin cambios de código ni workflows.
