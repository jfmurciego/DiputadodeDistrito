# G10 v2 — Semántica y reenganche durable

**Versión:** 2.0.0 · **Fecha:** 2026-09-12  
**Estado:** operativo inicial, sin autorización para recalcular M01–M08.

## Decisión arquitectónica

G10 es el plano de control: registra, admite, ejecuta, conserva evidencia y cierra un lote. No es un módulo territorial y no altera una asignación.

Las etapas territoriales se identifican por `stage_id` y nombre humano. `M01–M08` se preservan como identificadores históricos de scripts, productos y baselines. El catálogo canónico es `CATALOGO_ETAPAS_SEMANTICAS_V2.json`.

## Garantía de no repetición

Un producto histórico existente no pasa automáticamente a `REUSED`: primero se verifica como evidencia canónica histórica. Al cerrar el lote se guarda una huella SHA-256 de las entradas declaradas en `orchestracion/estado_tareas.json`. Sólo una ejecución posterior con la misma huella se omite como `REUSED`.

## Lote inicial

`plan_lote_g10_fase1_cierre.json` no ejecuta M01–M08. Verifica en paralelo la evidencia canónica de Aragón, Castilla y León y Extremadura, además del controlador G10 y del catálogo semántico. Extremadura conserva su carácter experimental bloqueado; verificar la evidencia no la promueve.

Se lanza desde **Actions → G10 — Operar lote durable → Run workflow**. El cierre publica un único comentario en la issue #5 y conserva un artefacto de lote. La siguiente conversación sólo necesita: **«revisa G10»**.

## Límite deliberado de esta versión

Los checkpoints M01–M06 aún no autorizan reanudar una regresión territorial: requieren manifiestos por etapa con checksum y contrato de salida. La siguiente entrega implementará ese adaptador sobre los scripts existentes, sin renombrarlos ni usar la caché como evidencia.
