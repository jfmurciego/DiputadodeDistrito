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

**P10 (preparación).** Los 71 P10 de la r3 reutilizaron un paquete registrado con id antiguo. `preparacion-fuentes.yml` 1.4.13: el selector devuelve rc 3
si el único rechazo es el id no canónico y el paso «Recuperar fuente territorial registrada» adquiere de nuevo (`::warning::`); otro rechazo sigue
fallando; cinturón que falla (rc 46) si se reutilizara un id no canónico; el resumen del job dice REUTILIZÓ/ADQUIERE y con qué paquete. La
reanudación (`validar_fuentes_reanudacion.py`) bloquea un checkpoint con id no canónico (nunca adquiere). Helper común
`politica_reutilizacion_fuentes.paquete_territory_mismatch`.

El paquete rechazado (rc 3) se borra del directorio de trabajo antes de adquirir (si no, `execute_source_policy` lo leería y devolvería REUSE).
Un paquete con id legacy y otro defecto sale con rc 2 y el P10 falla (coherente con «otro rechazo sigue fallando»). El reutilizable 1.5.3 falla en
«Aplicar puerta de preparación» (tras publicar la evidencia) si `steps.acquire` falló; el `continue-on-error` del acquire se conserva para publicar el diagnóstico.

**Hallazgos.** `preflight_preparacion_fuente.py` l.158/182 leen recibos electorales del catálogo (no alimentan al evaluador de fuentes); l.110 acepta
nombres de artefacto con variantes de id (`variantes`): no se toca aquí (el contenido del paquete manda).

**Pruebas.** `tests/test_t336_evidencia_id_canonico.py` (7; los de selector fallan sin el cambio): id legacy → rechazado/ACQUIRE, canónico → REUSE.
Batería afectada, test_t220, workflow_safety, GovernanceHeaders y guardián en verde.

**Riesgos.** Todo paquete/checkpoint con id legacy deja de reutilizarse: la 00 «Reutilizar»/«Generar desde fuente» re-adquiere (red). Sin
cambios en M04/M05/motor ni en huellas.
