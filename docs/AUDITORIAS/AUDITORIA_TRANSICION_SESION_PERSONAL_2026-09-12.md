# Auditoría de transición — sesión personal posterior

**Fecha de corte:** 2026-09-12  
**HEAD auditado:** `2143204` ([commit](https://github.com/jfmurciego/DiputadodeDistrito/commit/2143204))  
**Ámbito:** cambios desde `1563f20` (cierre F1.3 de workflows) y estado actual de GitHub Actions.  
**Naturaleza:** lectura y conciliación; no altera motor, datos ni resultados.

## Dictamen

El proyecto avanzó de forma material tras F1.3: Aragón y Castilla y León permanecen en **PASS**; Extremadura está correctamente preservada como **EXPERIMENTAL_BLOCKED** y la expansión posterior sigue congelada.

No hay ejecuciones en curso. La última ejecución autónoma completa disponible, [34708518702](https://github.com/jfmurciego/DiputadodeDistrito/actions/runs/34708518702), terminó **SUCCESS** para Aragón, Castilla y León y la auditoría de deuda F1. Las tres validaciones de cierre anteriores también están verdes: [smoke](https://github.com/jfmurciego/DiputadodeDistrito/actions/runs/34704363018), [Aragón](https://github.com/jfmurciego/DiputadodeDistrito/actions/runs/34704363023) y [Castilla y León](https://github.com/jfmurciego/DiputadodeDistrito/actions/runs/34704362932).

## Progreso conciliado

| Bloque | Estado comprobado | Evidencia |
|---|---|---|
| F1.3 Aragón | PASS; configuración canónica territorial y predecesor conservado | commits [5b90d1e](https://github.com/jfmurciego/DiputadodeDistrito/commit/5b90d1e), [b6ee6c8](https://github.com/jfmurciego/DiputadodeDistrito/commit/b6ee6c8) |
| F1.3 Castilla y León | PASS; evidencia durable y regresión posterior verde | [VALIDACION](../../territorios/castilla_y_leon/resultados/ejecuciones/gh-34701897922-1/VALIDACION.json) |
| F1.4 Extremadura | reproducible, pero no promovida: 2 distritos fuera de ±10 % | [VALIDACION](../../territorios/extremadura/resultados/ejecuciones/gh-34703213474-1/VALIDACION.json) |
| F1.5 | smoke M01–M06 añadido y workflows cerrados archivados | commit [d585009](https://github.com/jfmurciego/DiputadodeDistrito/commit/d585009) |
| Orquestación | lote paralelo con persistencia y notificación preparado; la última repetición quedó exitosa | commits [fcf02a7](https://github.com/jfmurciego/DiputadodeDistrito/commit/fcf02a7), [20a599e](https://github.com/jfmurciego/DiputadodeDistrito/commit/20a599e), [2143204](https://github.com/jfmurciego/DiputadodeDistrito/commit/2143204) |
| Auditoría ampliada | workflow manual de 40 controles preparado; no consta ejecución todavía | [workflow](../../.github/workflows/auditoria-integral-f1-40-controles.yml) |

## Hechos vigentes

- Aragón: 67 distritos, 1.463 secciones, desviación máxima 0,099299365905.
- Castilla y León: 82 distritos, 3.506 secciones, desviación máxima 0,11983611670895764.
- Extremadura: 65 distritos, 964 secciones, `hard_outliers=0`, pero desviación máxima 0,1330001091760059; continúa bloqueada.
- Se conservan 13 workflows activos y 36 archivados; los territorios posteriores no se han reactivado.
- El lote exitoso generó GeoJSON de Aragón y Castilla y León y verificó los contratos explícitos.

## Deuda visible que queda registrada

1. **Documentos maestros desfasados.** `SALIDA_MAESTRA.md` y `ESTADO_MAESTRO_PROYECTO.md` declaran corte `aebce6e`, mientras el HEAD es `2143204`; no invalidan resultados, pero deben actualizarse antes de usar esos documentos como punto único de reenganche.
2. **Auditoría de 40 controles pendiente de lanzar.** Está preparada y es manual; no debe confundirse con el lote ya completado.
3. **Duplicación de evidencia de Aragón.** El último lote cuantificó 135 ficheros idénticos entre `resultados/ejecuciones` y la copia territorial. Es deuda de almacenamiento/trazabilidad, no un fallo de cálculo. No se elimina evidencia sin una migración validada.
4. **Compacidad.** El lote la mide, pero no la convierte aún en criterio de promoción: Aragón 17, Castilla y León 40 y Extremadura 7 distritos por debajo de 0,15 de Polsby–Popper. La decisión de umbral debe ser explícita antes de endurecer el motor.
5. **Pruebas locales.** La ejecución local de los tests geométricos no es reproducible en este entorno porque falta `geopandas`; las ejecuciones CI documentadas arriba son la evidencia operativa válida.

## Punto de reenganche

1. Actualizar los dos documentos maestros a este corte, sin recalcular.
2. Lanzar manualmente `Auditoría integral F1 — 40 controles` y persistir su resultado.
3. Revisar únicamente las deudas que esa auditoría confirme.
4. Sólo entonces preparar la visualización del GeoJSON final de Aragón.

No se debe lanzar ninguna comunidad adicional.
