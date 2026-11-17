## 2026-11-17 — T-397c — Fusión automática sin botón + inventario de workflows retirados

**Causa.** D-159: los workflows sin botón llevan «_». `auto-merge.yml` quedó pendiente de T-379 (turno liberado).
**Cambio.** (a) `auto-merge.yml` 1.3.2: solo `name:` → «_P90 Automático — Fusión automática»; copia 1.3.1 en `legacy/workflows/`. Jobs, permisos y concurrencia intactos. `tests/test_t397_nombres_workflows.py`: pasa de PENDIENTES_2A a SIN_BOTON. (b) `docs/INVENTARIO_WORKFLOWS_RETIRADOS.md`: 16 workflows con id y 8 862 ejecuciones (solo lectura; no se borra nada).
**Comprobado (grep).** Ningún `workflow_run.workflows`, test ni `herramientas/` usa el nombre viejo (`decidir_auto_merge.py` y el ruleset usan check-runs `pruebas`/`veredicto`); solo históricos generados (`metricas_proceso.json`, dashboard, estudios, legacy).
**Pruebas.** `tests.test_t397_nombres_workflows`, `tests.test_auto_merge`, `tests.test_t366_p90_equivalencia`, `tests.test_corte_5_0_0_equivalencias`, gobernanza.
**Riesgos.** Los runs previos quedan bajo el nombre viejo. «Pruebas de la Plataforma» sigue `active` en la API: revisar antes de borrar. El borrado queda para el Operador con permiso.
