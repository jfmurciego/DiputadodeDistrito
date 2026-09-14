# Memoria operativa del proyecto

**Versión:** 1.1.0  
**Fecha de corte:** 2026-09-11  
**Anterior:** `legacy/memoria/MEMORIA_PROYECTO_v1.0.0.md`

## Objetivo

Construir un procedimiento reproducible, auditable y reutilizable para generar distritos uninominales a partir de unidades censales oficiales. Aragón es la primera implantación. La misma arquitectura debe admitir Castilla y León, Extremadura y, eventualmente, España completa sin duplicar el motor.

## Restricciones Aragón vigentes

- K exacto: 67 distritos.
- Contigüidad estricta medida sobre el grafo de secciones.
- Target = población total / 67.
- Suelo duro: 0,80 × target.
- Techo duro: 1,75 × target.
- Semillas deterministas.
- CUSEC único y sin nulos.
- Conservación total de población.
- La capa electoral es posterior y no condiciona la geometría.

## Estado conocido

El baseline local determinista mantiene 67 distritos y 0 desconectados, pero todavía deja 29 distritos por debajo del suelo 0,80×target. La prioridad algorítmica, una vez estabilizada la ejecución arbitral de GitHub, sigue siendo mejorar M05 sin romper cardinalidad ni contigüidad.

## Estado de GitHub Actions

La primera ejecución manual real de GitHub Actions fue el run `34575702377`, sobre `main`, modo `completo`, commit `416b06dd1044acbad74ddc400d86ba2b99cf03f5`. Terminó antes de M01 por dos defectos de infraestructura: sintaxis YAML inválida en una ruta con `{run_name}` y ausencia física de los ZIP territoriales. El workflow además ocultó inicialmente el fallo Python y generó una clave de caché vacía.

R005 corrige los dos primeros defectos de software:
- `configuracion/aragon_2025.yaml` v7.1.1: rutas parametrizadas entrecomilladas.
- `.github/workflows/procedimiento-ddd.yml` v2.3.1: cálculo de clave fail-fast y validación de SHA-256.

Sigue pendiente como bloqueo operativo independiente que GitHub Actions pueda materializar `inputs/seccionado_2025.zip` e `inputs/65034.csv.zip`. Hasta resolverlo no existe todavía una ejecución arbitral GitHub que haya alcanzado M01.

## Trazabilidad obligatoria

Cada ronda debe dejar commit, versiones internas, legacy, bitácora, memoria, manifiesto, validación y resultados identificados por commit/run. Cada ejecución de referencia debe tener un expediente en `docs/EJECUCIONES/` con run ID, rama, commit, modo, versiones, fases alcanzadas, errores, clasificación y acción correctiva. Ningún resultado generado solo dentro de una sesión de IA se considera evidencia suficiente: la referencia es una ejecución que el usuario pueda repetir en GitHub.

## Última ronda

R005 — `docs/RONDAS/R005_2026-09-11_auditoria_y_fail_fast.md`.

## Última ejecución registrada

GitHub run #1 — `docs/EJECUCIONES/GITHUB_RUN_0001_2026-09-11.md` — FAIL de infraestructura antes de M01.
