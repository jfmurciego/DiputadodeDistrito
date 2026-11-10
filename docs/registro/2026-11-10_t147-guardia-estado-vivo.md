## 2026-11-10 — T-147 — Guardia contra tests que fijan el estado vivo del ciclo de preparación

Causa: main rojo por tests que exigían `generation_ready` sobre catálogo/contratos que el bot reescribe (T-146, #597).
Cambio: `tests/test_guardia_estado_vivo.py` falla si un test (fuera de 4 ficheros con fixture en tmpdir, revisados) hace
assertEqual/== de `status` contra `generation_ready` o `source_prepared_pending_pre_m04`. Único test vivo que lo hacía y se migra:
`test_estado_produccion_y_visor` (contrato de Aragón) → `ESTADOS_PREPARADO`. Pruebas: guardia y módulo migrado en verde.
Riesgos: solo tests. Para recuentos/receipts exactos, `tests/_raiz_congelada.py`.
