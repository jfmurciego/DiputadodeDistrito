## 2026-11-10 — T-170 — Plan de migración de ids AUT/NAC (D-54)

- Causa: el propietario pidió, para el corte 5.0.0, el plan de migración de los identificadores internos AUT01-19 / NAC01-52.
- Cambio: solo documentación, `docs/ESTUDIOS/T170_MIGRACION_IDS/PLAN_MIGRACION_IDS_AUT_NAC.md`: orden por capas, alias y compatibilidad, huellas que cambian y las que no, pruebas de equivalencia, puntos de no retorno y reversión, variantes de 350 (sufijo propuesto, decide el propietario), duplicados AUT/NAC (incluye Baleares, no citada en la orden) y riesgos. Sin cambios en código, claves, workflows ni huellas.
- Pruebas: no aplica (documentación); `GovernanceHeaders` y la guardia de conflictos en verde.
