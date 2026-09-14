# R010 — Outputs visibles por módulo

**Fecha:** 2026-09-11  
**Tipo:** observabilidad y experiencia operativa; no cambia el algoritmo de distritación.

## Motivo
Los outputs M01-M03 estaban ocultos en caché y los M04-M08 solo eran visibles dentro del artefacto ZIP completo de GitHub Actions. Esto dificultaba inspeccionar el procedimiento módulo a módulo.

## Decisión
Se crea `resultados/ejecuciones/{run_id}/` como índice ligero y navegable dentro del repositorio, con subcarpetas M01-M08, `VALIDACION.json`, `MANIFIESTO_EJECUCION.json` y README de la ejecución.

Los GeoJSON ZIP pesados no se incorporan a `main`: permanecen como artefactos inmutables de GitHub Actions. Así se evita añadir aproximadamente 20 MB al historial Git por cada ejecución.

## Workflow
El workflow pasa de 2.5.2 a **2.6.0**. Tras cada ejecución publica automáticamente informes JSON, CSV, logs y resúmenes ligeros por módulo en el repositorio. Los artefactos pesados siguen conservándose durante el periodo de retención configurado.

## Run #4
Se retropublican los outputs ligeros del Run #4 (`gh-34581760340-1`) en `resultados/ejecuciones/gh-34581760340-1/`.

## Resultado funcional del Run #4
M05 v7.1.0 consiguió: 67 distritos, 0 bajo suelo, 0 sobre techo, contigüidad PASS y `max_rel_dev=0.338162757278`.

## Siguiente objetivo
Mantener todos los PASS y reducir progresivamente el desvío poblacional máximo hacia ±12%.