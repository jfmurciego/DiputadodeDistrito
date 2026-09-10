# R003 — Ejecuciones inmutables y preparación territorial reutilizable

**Fecha:** 2026-09-11  
**Estado:** candidato a validación GitHub

## Problema observado
R002 todavía escribía todas las corridas en `output/`, permitiendo sobrescritura, y la clave de caché incluía toda la configuración Aragón. Por tanto un cambio exclusivo de M05 invalidaba innecesariamente M01-M03.

## Decisión
M01-M03 constituyen la **preparación territorial**: su salida depende de cartografía, población, parámetros territoriales y versiones de esos tres módulos. M04-M08 constituyen una **ejecución**: su salida depende del experimento y debe ser inmutable.

## Cambios
- M01-M03 escriben en `.cache/ddd/preparacion/{run_name}/`.
- M04-M08 escriben en `ejecuciones/{run_id}/`.
- Logs, manifiesto y validación quedan dentro de la misma ejecución.
- Se elimina la copia de caché hacia un directorio global.
- La huella de caché ignora deliberadamente M04-M08 y sus parámetros.
- Docker excluye inputs, caché, ejecuciones y legacy; inputs se montan `read-only`.

## Razón fuerte
Una preparación territorial idéntica no debe repetirse por cambiar un algoritmo posterior. Una ejecución experimental nunca debe poder destruir la evidencia de otra. Esta separación reduce coste de E/S, tiempo y riesgo de regresión y permite decenas de corridas comparables sobre una sola base preparada.

## Criterio de aceptación
R003 queda aceptada cuando dos ejecuciones con el mismo commit/configuración/semilla generan el mismo resumen distrital y cada una conserva independientemente su manifiesto, validación, logs y resultados; además una modificación exclusiva de M05 debe reutilizar la misma preparación M01-M03.
