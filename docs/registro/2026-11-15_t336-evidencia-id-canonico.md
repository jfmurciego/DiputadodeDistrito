## 2026-11-15 — T-336 — Evidencia de fuentes restaurada solo con el id canónico (r3 aut11)

**Causa.** P00 aut11 (run 43669468142) restauró un paquete de fuentes anterior al renombrado T-220 (`acquired_at` 2026-11-10) con
`territory_id` legacy en declaración, inventario y procedencia. Entró porque `seleccionar_paquete_fuentes.py` comparaba con
`mismo_territorio` (alias), mientras `evaluar_preparacion_territorial.py` compara estricto → BLOCKED. Además `cp source_execution.json`
daba «Permission denied» (docker escribe `.ddd-sources` como root y el cp corre como runner) y el paso es `continue-on-error`, así que el
evaluador leía los documentos viejos.

**Cambio.** (1) `seleccionar_paquete_fuentes.py` y `compatibilidad_poblacion_seccionado.py`: igualdad exacta con el id canónico (sin alias ni
reescritura). (2) `ejecutar_fuentes_workflow.py`: `checkpoint_territory_mismatch`; un checkpoint con id distinto se descarta y se adquiere de
nuevo (ACQUIRE) con `::warning::`. (3) `_reutilizable-generacion-territorial.yml` 1.5.3: `sudo chown` de la evidencia antes del cp y cp que falla
con `::error::` y rc 1.

**Pruebas.** `tests/test_t336_evidencia_id_canonico.py` (7; los de selector fallan sin el cambio): id legacy → rechazado/ACQUIRE, canónico → REUSE.
Batería afectada, test_t220, workflow_safety, GovernanceHeaders y guardián en verde.

**Riesgos.** Todo paquete/checkpoint con id legacy deja de reutilizarse: la 00 «Reutilizar»/«Generar desde fuente» re-adquiere (red). Sin
cambios en M04/M05/motor ni en huellas.
