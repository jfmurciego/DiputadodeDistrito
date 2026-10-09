# Bitácora de progreso

**Versión:** 2.2.0  
**Fecha:** 2026-09-11  
**Anterior:** `legacy/bitacora/BITACORA_v2.1.0.md`

## R001 — Recuperación y profesionalización
Se adopta “Procedimiento de Distritación DDD” y “módulo”; se recuperan y versionan los ocho módulos, configuración única, reproducibilidad, manifiesto y puerta de calidad. Tras las correcciones de determinismo, la referencia local es: **67 distritos, 0 desconectados, 29 bajo 0,80×target, 0 sobre 1,75×target, best_max_rel_dev 0,5046**. SHA-256 del resumen: `d2d914d9f18bb7ae31db078fda046b71f75b233d1f4b79a836b214c8d92e641f`.

## R002 — Preparación de la ejecución arbitral en GitHub
**Estado:** en curso. Git LFS, Docker y Actions quedan preparados. Falta el bootstrap físico de los inputs canónicos en el remoto para efectuar la primera ejecución arbitral.

## R003 — Ejecuciones inmutables y preparación reutilizable
**Estado:** candidato. M01-M03 pasan a `.cache/ddd/preparacion/{run_name}`; M04-M08, logs, manifiesto y validación a `ejecuciones/{run_id}`. La caché depende únicamente de lo que puede alterar M01-M03. Docker deja fuera inputs/cache/ejecuciones/legacy y monta inputs como solo lectura. Versiones pre-R003 archivadas en `96ba2214`; R003 en `c665fa9a`.

## R004 — Preparación independiente de la validación algorítmica
**Estado:** candidato. Se detecta que un FAIL de M05 podía impedir consolidar la caché creada en el mismo job. El workflow v2.3.0 separa `preparar-territorio` de `ejecutar-distritacion`. El checkout no materializa LFS por defecto: los ZIP nacionales se descargan solo si falta la preparación o se fuerza modo completo. Versiones pre-R004 archivadas en `ec6232e7`.

## Regla permanente de progreso
Una versión nueva solo sustituye a la referencia si mantiene todos los criterios duros ya satisfechos y mejora una capacidad o métrica explícita. Toda regresión se conserva y documenta, pero no se promociona.
