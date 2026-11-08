## 2026-11-08 — T-106 — Limpieza reversible de la lista de Workflows de Actions

**Causa.** La lista de Actions mezcla interfaces (00-06) con 19 workflows internos y uno de pruebas de infraestructura. Orden del propietario (11-08, D-23): limpiar sin ninguna acción irreversible.

**Cambio (solo reversible).**
- `r2-test.yml` → `legacy/workflows/r2-test_v0.0.0_20261108.yml` (sin `uses:` ni dependientes; era una prueba manual de humo). Retirado de las listas de `test_design_a_matriz_sintetica` y `test_codauto_preparation_contract`.
- Solo el `name:` visible, con prefijo «_Interno — », en 19 workflows (6 `_reutilizable-*` y auto-merge, forense-00, metricas-proceso, notificar-finalizacion, numerar-registro, orquestacion-control, orquestacion-durable, revisor-pr, catalogo-procedencia, resultados-ligeros, validar-contratos, validar-documentacion, validar-productos). Ficheros sin renombrar. Cada uno sube VERSIÓN (+0.0.1) y deja copia en `legacy/workflows/<nombre>_v<ant>_20261108.yml`.
- Tests ajustados: `test_workflow_safety` (nombres de control y durable), `test_publicacion_multiterritorio` (nombre del publicador).

**No se hace (y por qué).**
- `orquestacion-durable`, `producir-territorio-por-contrato`, `recuperar-producto-electoral-durable`: NO archivados; los referencian `uses:` vivos (`_reutilizable-operacion-territorial` y la 00) y su cabecera no los marca retirados. Durable solo cambia de nombre visible.
- «Pruebas de la Plataforma» NO renombrada: `auto-merge` (`workflow_run`), `metricas_proceso.py` y varios tests la fijan por nombre; renombrarla rompería la fusión automática. «00 Ejecución Completa…» tampoco (la usa `forense-00`).
- `gestor-campanas.yml` no se toca (T-105).
- **Historial de runs: no se borra nada.** Pendiente de decisión futura: los 12 workflows desactivados sin fichero (lista a extraer con `gh api repos/<r>/actions/workflows` filtrando `state=disabled_manually` cuyo `path` ya no exista en `main`).

**Efectos.** Cambia el nombre en la lista y en los run-name de los workflows internos; los runs históricos conservan su nombre anterior. Reversión: `git revert` de la PR. Sin invalidar checkpoints ni huellas; no requiere 00.
