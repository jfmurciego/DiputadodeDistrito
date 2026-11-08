## 2026-11-08 — T-94 — El escritor PENDING ya no esconde su error (01, Ceuta)

Causa: en la 00 de Ceuta (run 42427122612) el paso «Persistir diagnóstico» salió con 54 sin mensaje: `main()` imprimía `::error::` en stdout y el workflow lo captura con `source_ref="$(…)"`. Causa de fondo probable (no confirmada en el log, que no conserva el texto): reintentos de push agotados; el escritor usaba 4 intentos con espera de 0,2–0,6 s frente a las fusiones #500-#502.
Cambio: `persistir_evidencia_pre_m04_operacional.py` envía el error a stderr, usa 10 intentos y `shared_state_backoff` (exponencial con jitter, como el estado compartido); `preparacion-fuentes.yml` 1.4.9 vuelca `.ddd-generation-pending-persistence.json` (status/reason) y conserva el código de salida. Tests en `PreM04ErrorVisibilityTests`.
Efectos: ninguno en M04/M05 ni huellas; no cambia el contrato. Para Ceuta basta relanzar la 00 cuando el Operador lo decida.
Pruebas: `tests.test_pre_m04_persistencia_concurrente`, `test_workflow_safety`, `test_credencial_registro`, `test_operational_concurrency_gerrychain50`, `test_design_a_catalogo`, `comprobar_guardian_main.py todo`.
Riesgos: bajos; un push que antes fallaba en ~1 s puede tardar hasta unos 2-3 min en agotarse.
