## 2026-11-19 — T-400 (D-180 1 y 2) — K por partición insular y exención de suelo en el histórico 2011-11

**Causa.** `contrato_provincia` escribía `validation.province_districts={provincia: K}`; en 07, 35 y 38 M04 reparte por partición insular y fallaba «need=K > unidades abiertas=0». Además Fuerteventura (35-C02, 102.810 hab.) queda bajo el suelo (115.523) con K=1.

**Cambio (decisión del propietario D-180, 19-11, «sí a todo» vía Planificador).** `herramientas/contrato_historico_epoca.py` 1.3.3: en contratos base con `hard_partition_mode`, `_reparto_particiones` reutiliza `component_hamilton` y `component_apportionment_audit` de `materializar_contrato_generacion` (el criterio del contrato 2025) con la población de la época: cuota por partición, exención de suelo de una partición de un distrito bajo el suelo, `partition_populations`, `partition_apportionment_audit` y el motivo en `meta.historico_epoca.reparto_particiones`. Exenciones (1) y (2) salen de la misma llamada, por eso van en una PR. Suelo, techo, K y atomicidad, intactos.

**Pruebas.** `tests/test_t365_historico_epoca.py` 1.4.3, clase `RepartoParticiones` (3 tests; nac35 6/1/1 con 35-C02 exenta). Cadena local M01-M08 con el motor real y las fuentes con sha256: nac35 PASS (8 distritos, 0 votos sin asignar, contraste BOE ok) y nac07 PASS (8 distritos, 0 sin asignar).

**Riesgos / efectos.** Apilada sobre #932 (T-400 a). Solo yaml de la época; sin 00. **nac38 falla cerrado**: 38-G01 (115.715 hab.) queda bajo el suelo (120.634) y la política de nac38 no gobierna una excepción de suelo; no estaba en D-180: pregunta al propietario. `no-automerge`.
