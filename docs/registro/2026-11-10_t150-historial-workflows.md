## 2026-11-10 — T-150 — Historial de workflows desactivados y lista de borrado de runs

Causa: 12 workflows `disabled_manually` sin fichero en `main` ensucian la lista de Actions (222 runs, D-23).
Cambio: `docs/HISTORIAL_WORKFLOWS.md` (ficha de cada uno: fechas, nº de runs, función, sustituto, evidencia) y `docs/HISTORIAL_WORKFLOWS_BORRADO_RUNS.csv` (workflow_id, run_id, fecha, evidencia, ruta@sha, verificada). Solo documentación; no se borra ni lanza nada.
Pruebas: rutas de evidencia comprobadas con `git rev-parse origin/main:<ruta>` (8 con evidencia en git: SI; 4 checks de PR: no aplica). R2 no comprobado.
Riesgos: la asignación workflow→evidencia es por nombre/fecha/herramienta; revisar antes del borrado, que es irreversible.
