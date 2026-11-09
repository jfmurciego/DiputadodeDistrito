## 2026-11-09 — T-120 — Barcelona entra en los ensembles con su exención (08073)
- Causa: decisión B2 del propietario (09-11). El generador (1.1.0) dejaba fuera las exenciones distintas de Cádiz.
- Cambio: `generar_config_ensemble.py` 1.2.0 (APROBADOS_PROPIETARIO admite la exención 08073 de Barcelona; la decisión se copia del contrato, límites del molde); nueva `configuracion/ensemble/congreso_barcelona.json`; tests (reproduce la config, rechaza exenciones no gobernadas).
- Pruebas: `tests.test_generar_config_ensemble`, `test_ensemble_configs_territorios`, `test_ensemble_exencion_suelo` (18 OK; la cadena con exención es la sintética del motor). Cadena corta con datos de Barcelona no posible en local: no hay M03/M05 (sin volcado `diagnostico/*`); la primera 00/ensemble real la valida.
- Riesgos: ninguno en motor ni contrato; no cambia huellas M04/M05. El ensemble de Barcelona lo lanza el Operador con permiso del propietario.
