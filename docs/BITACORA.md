# Bitácora de progreso

**Versión:** 2.3.0  
**Fecha:** 2026-09-11  
**Anterior:** `legacy/bitacora/BITACORA_v2.2.0.md`

## R001 — Recuperación y profesionalización
Se adopta “Procedimiento de Distritación DDD” y “módulo”; se recuperan y versionan los ocho módulos, configuración única, reproducibilidad, manifiesto y puerta de calidad. Tras las correcciones de determinismo, la referencia local es: **67 distritos, 0 desconectados, 29 bajo 0,80×target, 0 sobre 1,75×target, best_max_rel_dev 0,5046**. SHA-256 del resumen: `d2d914d9f18bb7ae31db078fda046b71f75b233d1f4b79a836b214c8d92e641f`.

## R002 — Preparación de la ejecución arbitral en GitHub
**Estado:** en curso. Git LFS, Docker y Actions quedan preparados. Falta el bootstrap físico de los inputs canónicos en el remoto para efectuar la primera ejecución arbitral.

## R003 — Ejecuciones inmutables y preparación reutilizable
**Estado:** candidato. M01-M03 pasan a `.cache/ddd/preparacion/{run_name}`; M04-M08, logs, manifiesto y validación a `ejecuciones/{run_id}`. La caché depende únicamente de lo que puede alterar M01-M03. Docker deja fuera inputs/cache/ejecuciones/legacy y monta inputs como solo lectura. Versiones pre-R003 archivadas en `96ba2214`; R003 en `c665fa9a`.

## R004 — Preparación independiente de la validación algorítmica
**Estado:** candidato. Se detecta que un FAIL de M05 podía impedir consolidar la caché creada en el mismo job. El workflow v2.3.0 separa `preparar-territorio` de `ejecutar-distritacion`. El checkout no materializa LFS por defecto: los ZIP nacionales se descargan solo si falta la preparación o se fuerza modo completo. Versiones pre-R004 archivadas en `ec6232e7`.

## Ejecución GitHub #1 — run 34575702377
**Fecha:** 2026-09-11. **Rama:** `main`. **Modo:** `completo`. **Commit ejecutado:** `416b06dd1044acbad74ddc400d86ba2b99cf03f5`. **Resultado:** FAIL de infraestructura antes de M01.

Secuencia: checkout PASS; PyYAML PASS; cálculo de clave M01-M03 produjo `ParserError` por `io.cache.dir: .cache/ddd/preparacion/{run_name}` sin comillas; el workflow v2.3.0 ocultó el exit code del proceso Python al ejecutarlo dentro de `echo` y continuó con una clave vacía; caché MISS; materialización territorial FAIL porque `inputs/seccionado_2025.zip` e `inputs/65034.csv.zip` no estaban disponibles. M01-M08 no se ejecutaron. Expediente completo: `docs/EJECUCIONES/GITHUB_RUN_0001_2026-09-11.md`.

## R005 — Auditoría de ejecución y fail-fast de configuración
**Estado:** candidato. Se archivan configuración 7.1.0 y workflow 2.3.0. La configuración pasa a **7.1.1**, con rutas parametrizadas entrecomilladas y sin cambios algorítmicos. El workflow pasa a **2.3.1**, haciendo fail-fast: captura la clave fuera de `echo`, exige exactamente 64 caracteres hexadecimales y aborta con código 21 si la identidad territorial no es válida. Se formaliza el registro por ejecución en `docs/EJECUCIONES/`. Permanece pendiente, como bloqueo separado, materializar los dos ZIP territoriales para GitHub Actions. Documento de ronda: `docs/RONDAS/R005_2026-09-11_auditoria_y_fail_fast.md`.

## Regla permanente de auditoría
Cada ronda debe preservar las versiones sustituidas en `legacy/`. Cada ejecución de referencia debe conservar run ID, rama, commit, modo, versiones de configuración/workflow, fases alcanzadas, punto de fallo, clasificación del fallo, evidencia textual, acción correctiva y resultado. Una ejecución que no alcanza M01 no aporta evidencia algorítmica.

## Regla permanente de progreso
Una versión nueva solo sustituye a la referencia si mantiene todos los criterios duros ya satisfechos y mejora una capacidad o métrica explícita. Toda regresión se conserva y documenta, pero no se promociona.
