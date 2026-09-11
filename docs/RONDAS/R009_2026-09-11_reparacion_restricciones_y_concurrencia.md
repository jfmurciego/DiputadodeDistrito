# R009 — Reparación de restricciones poblacionales y control de concurrencia

**Fecha:** 2026-09-11

## Origen
GitHub Run #3 (`34580841510`) demuestra que R008 resuelve la infraestructura: reconstrucción local de fuentes, M01-M03, caché y M04-M08 funcionan. La única puerta fallida es algorítmica: 29 distritos bajo 0,80×target.

## Diagnóstico M05
M05 v7.0.1 aceptaba movimientos comparando únicamente `max(abs(pop-target)/target)`. Ese objetivo no representa las restricciones duras; una solución con muchos distritos bajo suelo podía seguir siendo aceptada como mejora.

## Cambio M05 v7.1.0
La función objetivo pasa a ser lexicográfica: número de violaciones suelo/techo → magnitud total de violación → máximo desvío → error cuadrático. Se añade una fase dirigida de reparación de distritos ilegales. Cada transferencia entra por frontera al receptor y solo se acepta si el distrito donante permanece conectado. Una segunda fase pule la solución sin empeorar la tupla de restricciones.

## Concurrencia
Workflow v2.5.1 añade `concurrency` únicamente al job `preparar-territorio`, grupo `ddd-preparacion-aragon-2025`, `cancel-in-progress: false`. Así nunca se reconstruye simultáneamente la misma base M01-M03, pero ejecuciones distintas pueden continuar concurrentemente en M04-M08 una vez superada su preparación.

## Versiones archivadas
- M05 v7.0.1 → `legacy/modulo05/05_optimizar_distritos_v7.0.1.py`.
- workflow v2.5.0 → `legacy/workflows/procedimiento-ddd_v2.5.0.yml`.

## Próxima validación
Ejecutar en modo `iterativo`: la caché M01-M03 del Run #3 ya es válida y un cambio exclusivo de M05 no debe forzar reconstrucción territorial. La puerta de calidad decidirá si v7.1.0 reduce/elimina los 29 distritos bajo suelo sin romper K=67 ni contigüidad.