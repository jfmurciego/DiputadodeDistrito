# R005 — Auditoría de ejecución y fail-fast de configuración

**Fecha:** 2026-09-11  
**Motivación:** primera ejecución manual real de GitHub Actions (`run 34575702377`) sobre `main`.

## Hallazgos
La ejecución reveló dos defectos de infraestructura antes de M01: una ruta parametrizada inválida para PyYAML y un control de shell que permitía continuar con una clave de caché vacía. Después apareció un segundo bloqueo independiente: los dos ZIP territoriales no estaban disponibles en GitHub/LFS.

## Cambios
1. `configuracion/aragon_2025.yaml` pasa de 7.1.0 a 7.1.1.
2. Se entrecomillan todas las rutas/plantillas que contienen `{...}` para evitar ambigüedad sintáctica YAML.
3. `.github/workflows/procedimiento-ddd.yml` pasa de 2.3.0 a 2.3.1.
4. El step de identidad territorial usa `set -euo pipefail`, captura primero la salida Python, valida `^[0-9a-f]{64}$` y solo después escribe en `$GITHUB_OUTPUT`.
5. Se crea un registro permanente de la ejecución en `docs/EJECUCIONES/GITHUB_RUN_0001_2026-09-11.md`.
6. Las versiones sustituidas se conservan en `legacy/` antes de la promoción.

## No cambia
- K=67.
- Semilla=12345.
- Iteraciones M05=20000.
- Suelo=0,80×target.
- Techo=1,75×target.
- Contigüidad estricta.
- Ningún criterio o algoritmo de distritación.

## Estado al cierre
El defecto YAML y el defecto de fail-fast están corregidos. Permanece como bloqueo operativo independiente la materialización de `inputs/seccionado_2025.zip` e `inputs/65034.csv.zip` en GitHub Actions. No procede interpretar R005 como validación de M01-M08 porque la ejecución #1 no llegó a M01.

## Regla de auditoría reforzada
Toda ejecución manual de referencia debe conservar, como mínimo: run ID de GitHub, rama, commit, modo, versiones de workflow/configuración, punto exacto de terminación, estado de cada fase alcanzada, error textual suficiente para reproducir el diagnóstico, acción correctiva y clasificación del resultado (infraestructura / datos / algoritmo / validación).
