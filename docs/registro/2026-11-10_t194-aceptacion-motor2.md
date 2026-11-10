## 2026-11-10 — T-194 — Criterio automatizado de aceptación del motor 2

- **Causa**: no había un criterio escrito y ejecutable de «el motor nuevo puede relevar».
- **Cambio**: `tests/test_motor2_aceptacion.py` (huella fija en Soria, Álava y Melilla con semilla D-50 y N fijos; ganadores
  certificados con R-NUCLEO; nunca peor que el canónico en los 71 leyendo `COMPETIDOR.csv`; casos adversos; D-60 pendiente
  con `skip` hasta el corte 5.0.0) y `docs/ARQUITECTURA/ACEPTACION_MOTOR2.md`.
- **Pruebas**: `python -m unittest tests.test_motor2_aceptacion` verde (11 tests, 2 omitidos: motor real y D-60).
- **Riesgos**: solo tests y doc; no toca M04/M05/ddd_core/ddd_motor2 ni huellas. No exige 00 ni publicación. Las huellas
  (a) son de fixtures sintéticos; la del motor real queda opcional (`DDD_ACEPTACION_BATERIA`).
