# Bitácora de progreso

**Versión:** 2.6.0  
**Fecha:** 2026-09-11  
**Anterior:** `legacy/bitacora/BITACORA_v2.5.0.md`

## R001 — Recuperación y profesionalización
Se adopta “Procedimiento de Distritación DDD” y “módulo”; se recuperan y versionan los ocho módulos, configuración única, reproducibilidad, manifiesto y puerta de calidad. Referencia local previa: **67 distritos, 0 desconectados, 29 bajo 0,80×target, 0 sobre 1,75×target, best_max_rel_dev 0,5046**.

## R002-R005 — Infraestructura, caché y auditoría
Se separan preparación y motor iterativo, se formalizan ejecuciones inmutables, validación y fail-fast.

## R006 — Adquisición automática INE
Se conserva como mecanismo de validación/final.

## R007 — Continuidad autosuficiente
Se crea `docs/ESTADO_MAESTRO_PROYECTO.md`.

## R008 — Fuentes congeladas para desarrollo rápido
Workflow 2.5.0 reconstruye desde `inputs/partes/` los ZIP canónicos y permite preparar M01-M03 sin latencia del INE. Configuración 7.3.0 consume `inputs/seccionado_2025.zip` y `inputs/65034.csv.zip`.

## GitHub Run #3 — 34580841510
**Resultado:** infraestructura PASS; M01-M08 PASS técnico; puerta de calidad FAIL algorítmico. M01=1.463 secciones/0 población ausente; M02=4.293 aristas; M03=1.463 nodos/4.293 aristas/0 aislados; M04 K=67; M05 `best_max_rel_dev=0.5046`; M06-M08 PASS; validación final: **29 distritos bajo 0,80×target**. Expediente: `docs/EJECUCIONES/GITHUB_RUN_0003_2026-09-11.md`.

## R009 — Reparación de restricciones poblacionales y concurrencia
M05 pasa a **v7.1.0**. La función objetivo deja de ser únicamente `max_rel_dev` y pasa a priorizar lexicográficamente: número de violaciones de suelo/techo, magnitud total de violación, máximo desvío y error cuadrático. Añade fase dirigida de reparación preservando la conectividad del donante. Workflow pasa a **2.5.1** y serializa únicamente `preparar-territorio`; M04-M08 mantienen capacidad de concurrencia entre ejecuciones. Documento: `docs/RONDAS/R009_2026-09-11_reparacion_restricciones_y_concurrencia.md`.

## Regla permanente de auditoría
Cada ronda preserva versiones sustituidas en `legacy/`. Cada ejecución de referencia conserva run ID, rama, commit, modo, versiones, fases alcanzadas, fallo/métricas, acción correctiva y resultado.

## Regla permanente de continuidad
Toda ronda que cambie objetivo, restricciones, baseline, fuentes, arquitectura, estado de ejecución o siguiente acción debe actualizar `docs/ESTADO_MAESTRO_PROYECTO.md`.

## Regla permanente de progreso
Una versión nueva solo sustituye a la referencia si mantiene todos los criterios duros ya satisfechos y mejora una capacidad o métrica explícita. Toda regresión se conserva y documenta, pero no se promociona.
