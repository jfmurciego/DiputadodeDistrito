## 2026-11-09 — T-118 — La 05 de un run «Reutilizar» no registraba el M08 (M06 reutilizado duplicado)

Causa: la 05 de CyL con `production_run_id=42531122768` (00 «Reutilizar») ejecuta `describe-production`, que describe M06 y M08.
El estado acumulativo del M08 lleva el M06 reutilizado (run 42521090842, mismos bytes), así que el descriptor
`m06-castilla_y_leon-42531122768` repite el blob 5143b70a… ya registrado y `validate_registry` abortaba con «Activo inmutable
duplicado» antes de llegar al M08. No se publicaron datos falsos: la 05 anterior (42535264103) usó el run del M06 y no hay
ningún `canonical_m08` de CyL en el registro; el registro actual no tiene blobs duplicados.

Cambio: `herramientas/registro_publicaciones_visor.py` 1.3.0: `make_candidate` omite un `canonical_m06` cuya ubicación
inmutable ya figura para el mismo territorio bajo otro run. Un M08 con bytes ya registrados sigue rechazado.
Test: `tests/test_registro_m06_reutilizado.py` (falla antes, pasa después). Sin cambios de workflows ni de motor.
Modo de 00: ninguno; basta relanzar la 05 (Operador, con permiso del propietario).
