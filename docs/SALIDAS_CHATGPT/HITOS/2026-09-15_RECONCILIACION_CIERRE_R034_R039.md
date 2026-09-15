# Reconciliación canónica del cierre R034–R039

**Fecha:** 2026-09-15
**Estado:** documentación reconciliada
**Alcance:** documentación y continuidad; cero ejecución territorial y cero cambios de visor.

## Problema

La evidencia histórica y el punto de reenganche ya certificaban R036, R037, R038 y R039, pero `docs/CIERRE_INGENIERIA_PRODUCCION.md` todavía los mostraba como pendientes y `docs/CONTINUIDAD_AUDITORIA_PLATAFORMA.md` conservaba un orden de trabajo anterior que podía provocar la repetición de C-05/C-09 y otros paquetes ya cerrados.

## Decisión

Se armonizan las fuentes canónicas:

- R034–R039 quedan cerrados.
- La auditoría crítica previa queda tratada como evidencia cerrada, no como cola de ejecución.
- C-01 conserva su resultado `FAIL_ROBUSTNESS`; no se reejecuta por defecto.
- R040 queda como único hito territorial abierto y exige autorización explícita.
- Publicación y visor quedan desacoplados de la autorización de cálculo territorial.

## Efecto operacional

Ninguno sobre resultados. No se ejecuta M01–M08, no se abre ninguna comunidad, no se recalculan Aragón/Castilla y León, no se modifica Extremadura y no se toca el visor.
