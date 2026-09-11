# Bitácora de progreso

**Versión:** 2.4.0  
**Fecha:** 2026-09-11  
**Anterior:** `legacy/bitacora/BITACORA_v2.3.0.md`

## R001 — Recuperación y profesionalización
Se adopta “Procedimiento de Distritación DDD” y “módulo”; se recuperan y versionan los ocho módulos, configuración única, reproducibilidad, manifiesto y puerta de calidad. Tras las correcciones de determinismo, la referencia local es: **67 distritos, 0 desconectados, 29 bajo 0,80×target, 0 sobre 1,75×target, best_max_rel_dev 0,5046**. SHA-256 del resumen: `d2d914d9f18bb7ae31db078fda046b71f75b233d1f4b79a836b214c8d92e641f`.

## R002 — Preparación de la ejecución arbitral en GitHub
Se prepara Docker/Actions y la trazabilidad de inputs. El bloqueo inicial de grandes fuentes remotas se elimina posteriormente en R006 mediante adquisición oficial automática.

## R003 — Ejecuciones inmutables y preparación reutilizable
M01-M03 pasan a `.cache/ddd/preparacion/{run_name}`; M04-M08, logs, manifiesto y validación a `ejecuciones/{run_id}`. La caché depende únicamente de lo que puede alterar M01-M03. Versiones pre-R003 archivadas en `96ba2214`; R003 en `c665fa9a`.

## R004 — Preparación independiente de la validación algorítmica
El workflow separa `preparar-territorio` de `ejecutar-distritacion` para que un FAIL algorítmico no impida conservar una preparación territorial válida. Versiones pre-R004 archivadas en `ec6232e7`.

## Ejecución GitHub #1 — run 34575702377
**Fecha:** 2026-09-11. **Rama:** `main`. **Modo:** `completo`. **Commit:** `416b06dd1044acbad74ddc400d86ba2b99cf03f5`. **Resultado:** FAIL de infraestructura antes de M01. YAML inválido por ruta con `{run_name}` sin comillas; el workflow ocultó el error Python dentro de `echo`; después faltaron los ZIP territoriales. M01-M08 no se ejecutaron. Expediente: `docs/EJECUCIONES/GITHUB_RUN_0001_2026-09-11.md`.

## R005 — Auditoría de ejecución y fail-fast
Configuración 7.1.1 corrige las rutas YAML; workflow 2.3.1 hace fail-fast y valida la clave territorial. Se formaliza `docs/EJECUCIONES/`.

## R006 — Adquisición automática de fuentes oficiales
**Estado:** candidato pendiente de ejecución arbitral. Se elimina el bootstrap manual/Git LFS de los dos inputs territoriales grandes. `herramientas/adquirir_fuentes_ine.py` materializa población INE 65034 y cartografía INE `Secciones_2025` para 22/44/50, exige 1.463 secciones y registra URL, fecha, tamaño y SHA-256 en `FUENTES_ADQUIRIDAS.json`. Configuración 7.2.0; workflow 2.4.0; herramienta 1.0.0. Commit funcional R006: `d92296e472a6dde0e8ba7c1c188643d9dfeed789`.

## R007 — Continuidad autosuficiente
**Estado:** documental. La auditoría detecta conocimiento histórico importante disperso o ausente de la documentación canónica. Se crea `docs/ESTADO_MAESTRO_PROYECTO.md` v1.0.0 con objetivo, arquitectura, restricciones, Zaragoza CUDIS→CUSEC, split≤3, historia H≈61, fallos V2, baselines, diferencia poblacional, referencias de grafo, defectos ya resueltos, fuentes, estado GitHub, orden de lectura y siguiente acción. Documento: `docs/RONDAS/R007_2026-09-11_continuidad_autosuficiente.md`.

## Regla permanente de auditoría
Cada ronda preserva versiones sustituidas en `legacy/`. Cada ejecución de referencia conserva run ID, rama, commit, modo, versiones, fases alcanzadas, fallo/métricas, acción correctiva y resultado. Una ejecución que no alcanza M01 no aporta evidencia algorítmica.

## Regla permanente de continuidad
Toda ronda que cambie objetivo, restricciones, baseline, fuentes, arquitectura, estado de ejecución o siguiente acción debe actualizar `docs/ESTADO_MAESTRO_PROYECTO.md`.

## Regla permanente de progreso
Una versión nueva solo sustituye a la referencia si mantiene todos los criterios duros ya satisfechos y mejora una capacidad o métrica explícita. Toda regresión se conserva y documenta, pero no se promociona.
