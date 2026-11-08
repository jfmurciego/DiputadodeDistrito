## 2026-11-08 — T-85 — Equivalencia de seccionados INE 2012-2024 con el vigente 2025

Causa: D-9, D-10 y D-11 (6 generales 2011-2023 sobre los distritos vigentes) exigen llevar los votos de cada sección
histórica a las del seccionado INE 2025; D-13 fija el peso por población (el área solo si falta).
Cambio: `herramientas/equivalencia_seccionados.py` 1.0.0 (nuevo): intersección de la cartografía INE detallada de cada
año con la de 2025, 1:1 al 95 %, reparto por población (padrón 65034 de 2025) con el área como respaldo, traslación
sistemática corregida (Melilla 2012, 63 m) e informe de cobertura y prueba del censo en
`docs/AUDITORIAS/T85_EQUIVALENCIA_SECCIONADOS/` (fuentes con sha256). La geometría simplificada del espejo T-89 no vale
para la equivalencia (hasta un 35 % de falsos repartos urbanos); del espejo se toman votos y censo.
Resultado: votos no 1:1 del 23,3 % (2011) al 1,6 % (2023); en la prueba del censo el error es del 18-22 % con población
y del 28-32 % con área. Sin motor, contratos, workflows ni publicación.
Pruebas: `tests/test_equivalencia_seccionados.py` (9, sintéticos con valores a mano), guardián y `GovernanceHeaders`.
Riesgos: el padrón 2025 se parece al censo de 2023 de referencia (la prueba favorece algo a la población); las tablas
(11 MB) no se versionan y se regeneran desde las fuentes con sha256.
