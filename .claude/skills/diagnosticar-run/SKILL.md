---
name: diagnosticar-run
description: Da la causa de un run fallido o bloqueado de DDD en cinco líneas, con el catálogo de causas raíz. Úsala cuando el propietario o el planificador pasen un run id, una 00 en PARADA o un error de CI.
---

# Diagnosticar un run

Salida: cinco líneas — territorio y run · paso que falla · mensaje · causa (del catálogo o nueva) · siguiente acción.

1. Territorio: `TERRITORY:` en el log del job «Planificar» (nunca por el orden).
2. Error sin descargar logs: `gh api repos/jfmurciego/DiputadodeDistrito/check-runs/<job_id>/annotations`.
   Si hace falta el log: `get_job_logs` guardado en fichero y filtrado (`::error|Traceback|Error`).
3. Los artefactos dan 403 desde la nube y caducan a los 14 días: para el motor usa los volcados de `diagnostico/*`
   (M01 + grafo M03) y reproduce en local (`.claude/rules/diagnostico-local.md`). Si faltan, pídelos al Mac del propietario.
4. Mira `CHECKPOINT_RUN_ID` en el paso M04: «Reutilizar» puede haber restaurado un checkpoint anterior a los arreglos.

Delega en el subagente `forense` (`.claude/agents/forense.md`, Sonnet, solo lectura) pasándole el run id o el
síntoma, y devuelve sus cinco líneas. El catálogo de causas raíz (FRAMEWORK §9 y `CLAUDE.md`, con `causa_id`) vive en
su memoria: `.claude/agent-memory/forense/MEMORY.md`. Calibración en `evals/oro/`
(`python herramientas/evaluar_oro.py --preparar DIR --agente forense`, luego `--salidas … --anotar`).

Bloqueo de población: comprueba antes si es estructural (vecinos municipales en el grafo M03); más presupuesto de
reparación no ayuda. Causa nueva: añádela a la memoria del forense en la PR del arreglo.
