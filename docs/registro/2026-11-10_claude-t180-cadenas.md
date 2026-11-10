## 2026-11-10 — T-180 — Cuántas cadenas hacen falta en la competición del motor 2 (71 territorios)

- Causa: fijar un N oficial de cadenas GerryChain por edición en la competición del motor 2.
- Cambio: estudio nuevo `docs/ESTUDIOS/T180_CADENAS/` (`analizar_cadenas.py` 1.0.0: curva con la función A y con la B
  de naturalidad a posteriori, saturación, tiempos y reproducibilidad; datos versionados con los que se regeneran las
  tablas). Una sola tanda local de 20 cadenas por territorio con semillas públicas anidadas (`ddd-semilla-publica/1`,
  D-50; la D-61/6 no está aplicada en `semilla.py`). Sin cambios de motor, contratos, workflows, catálogo ni huellas;
  no se lanzó nada.
- Resultado (71): 21/21 candidatos válidos en todos. Con A, distritos fuera de tolerancia 270 → 204 (N=5) → 203 (N=10)
  → 201 (N=20); mejoran al canónico 26 / 28 / 30 territorios. Badajoz reproducible 6/6. CPU medida en los 71:
  5,9 / 10,9 / 20,8 h para N = 5 / 10 / 20. Recomendación provisional (D-67): N = 10 por edición; para B o D8 (cadenas ponderadas, no medidas aquí), por medir.
