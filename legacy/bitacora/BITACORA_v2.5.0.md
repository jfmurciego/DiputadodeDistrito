# Bitácora de progreso

**Versión:** 2.5.0  
**Fecha:** 2026-09-11  
**Anterior:** `legacy/bitacora/BITACORA_v2.4.0.md`

## R001 — Recuperación y profesionalización
Se adopta “Procedimiento de Distritación DDD” y “módulo”; se recuperan y versionan los ocho módulos, configuración única, reproducibilidad, manifiesto y puerta de calidad. Tras las correcciones de determinismo, la referencia local es: **67 distritos, 0 desconectados, 29 bajo 0,80×target, 0 sobre 1,75×target, best_max_rel_dev 0,5046**. SHA-256 del resumen: `d2d914d9f18bb7ae31db078fda046b71f75b233d1f4b79a836b214c8d92e641f`.

## R002 — Preparación de la ejecución arbitral en GitHub
Se prepara Docker/Actions y la trazabilidad de inputs.

## R003 — Ejecuciones inmutables y preparación reutilizable
M01-M03 pasan a `.cache/ddd/preparacion/{run_name}`; M04-M08, logs, manifiesto y validación a `ejecuciones/{run_id}`. La caché depende únicamente de lo que puede alterar M01-M03.

## R004 — Preparación independiente de la validación algorítmica
El workflow separa `preparar-territorio` de `ejecutar-distritacion` para que un FAIL algorítmico no impida conservar una preparación territorial válida.

## Ejecución GitHub #1 — run 34575702377
**Resultado:** FAIL de infraestructura antes de M01. YAML inválido por ruta con `{run_name}` sin comillas; el workflow ocultó el error Python dentro de `echo`; después faltaron los ZIP territoriales. Expediente: `docs/EJECUCIONES/GITHUB_RUN_0001_2026-09-11.md`.

## R005 — Auditoría de ejecución y fail-fast
Configuración 7.1.1 corrige las rutas YAML; workflow 2.3.1 hace fail-fast y valida la clave territorial. Se formaliza `docs/EJECUCIONES/`.

## R006 — Adquisición automática de fuentes oficiales
Se implementa `herramientas/adquirir_fuentes_ine.py` para materializar población INE 65034 y cartografía INE `Secciones_2025` directamente desde servicios oficiales. Configuración 7.2.0; workflow 2.4.0. Se conserva como mecanismo de validación/final.

## R007 — Continuidad autosuficiente
Se crea `docs/ESTADO_MAESTRO_PROYECTO.md` v1.0.0 con objetivo, arquitectura, restricciones, historia técnica, baselines, fuentes y siguiente acción.

## R008 — Fuentes congeladas para desarrollo rápido
**Estado:** candidato. Para evitar varios minutos de espera del INE en cada iteración, el usuario sube a `inputs/partes/` los fragmentos de los dos ZIP canónicos y su manifiesto. El workflow 2.5.0 reconstruye los ZIP localmente cuando hay que recalcular M01-M03, valida los fragmentos y después los SHA-256 canónicos. La configuración 7.3.0 vuelve a consumir `inputs/seccionado_2025.zip` y `inputs/65034.csv.zip`. R006 no se elimina: queda reservado para contraste/validación final. Documento: `docs/RONDAS/R008_2026-09-11_fuentes_congeladas_desarrollo.md`.

Hashes canónicos de desarrollo:
- seccionado: `55c9da7e34d3bb3cb725400c35b58e72f4db2ea8321ef91237a89e708d2dbcc4`;
- población: `91d3ff9a90bac1c06e26df97179daa325b65fa77c9209879d6a40333b17057f3`.

## Regla permanente de auditoría
Cada ronda preserva versiones sustituidas en `legacy/`. Cada ejecución de referencia conserva run ID, rama, commit, modo, versiones, fases alcanzadas, fallo/métricas, acción correctiva y resultado.

## Regla permanente de continuidad
Toda ronda que cambie objetivo, restricciones, baseline, fuentes, arquitectura, estado de ejecución o siguiente acción debe actualizar `docs/ESTADO_MAESTRO_PROYECTO.md`.

## Regla permanente de progreso
Una versión nueva solo sustituye a la referencia si mantiene todos los criterios duros ya satisfechos y mejora una capacidad o métrica explícita. Toda regresión se conserva y documenta, pero no se promociona.
