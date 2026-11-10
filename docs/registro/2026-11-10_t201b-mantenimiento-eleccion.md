## 2026-11-10 — T-201b — La extracción de composición M06 elige el run por elección

- Causa: pendiente de la revisión independiente de T-201 (#667). El paso «Runs candidatos» de `mantenimiento-programado.yml` escogía el `canonical_m06` de run_id mayor por territorio sin mirar la elección: una entrada 2026 habría sustituido al run de 2023 y la composición 2023 dejaría de reponerse.
- Cambio: `mantenimiento-programado.yml` 1.0.1: solo la condición de elección de esa línea (sin `election_date` = 2023-07-23). Copia en `legacy/workflows/`. Nada más del flujo.
- Pruebas: `tests.test_t201b_mantenimiento_eleccion` (nuevo; ejecuta el script del propio workflow sobre un registro sintético: entradas 2026 con run mayor no cambian los candidatos) más `tests.test_metricas_proceso` y `GovernanceHeaders`. El flujo no se ejecuta.
- Riesgos: salida idéntica con el registro actual. Sin efecto en M04/M05 ni huellas; no requiere 00.
