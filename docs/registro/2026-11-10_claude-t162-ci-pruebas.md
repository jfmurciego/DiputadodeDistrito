## 2026-11-10 — T-162 — Propuesta para reducir los minutos de la CI `pruebas`

Causa: D-46 (propietario, vía Planificador): la CI `pruebas` es el mayor gasto de Actions y el tope semanal es de 15.000 min.
Cambio: `docs/ESTUDIOS/T162_CI_PRUEBAS/` con la propuesta (datos reales de 1.512 runs de 14 días; en la última semana, 25.083 min, el 72 % son pushes a `main` y el 57 % de bots), seis opciones con ahorro, riesgos, esfuerzo y orden, y los dos scripts de recogida y análisis. Solo documental.
Pruebas: no aplica (sin código ni workflows); cifras reproducibles con `recoger_runs.py` y `analisis_runs.py`.
Efectos: ninguno en motor, huellas, workflows, visor ni datos; sin cambio de modo de 00. El check `pruebas` no se modifica.
