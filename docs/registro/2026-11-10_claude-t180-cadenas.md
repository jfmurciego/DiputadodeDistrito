## 2026-11-10 — T-180 — Cuántas cadenas hacen falta en la competición (entrega parcial: 20 representativos)

- Causa: fijar un N oficial de cadenas GerryChain por edición en la competición del motor 2.
- Cambio: estudio nuevo `docs/ESTUDIOS/T180_CADENAS/` (`analizar_cadenas.py` 1.0.0, curva A y B, tiempos, anidamiento y
  reproducibilidad). Una sola tanda local de 20 cadenas por territorio con semillas públicas anidadas
  (`ddd-semilla-publica/1`, D-50; la D-61/6 no está aplicada en `semilla.py`). Sin cambios de motor, contratos,
  workflows, catálogo ni huellas; no se lanzó nada.
- Resultado parcial (20): con A, 10/20 mejoran al canónico; fuera de tolerancia 172 → 126 (N=5) → 125 (N=10) → 124 (N=20);
  17/20 saturados en N=10. Anidamiento sin fallos; Badajoz reproducible 6/6. Coste proyectado a los 71: 5,8 / 10,9 / 21,0 h
  de CPU para N = 5 / 10 / 20. Recomendación provisional: N = 10.
- Pendiente: 51 territorios restantes.
