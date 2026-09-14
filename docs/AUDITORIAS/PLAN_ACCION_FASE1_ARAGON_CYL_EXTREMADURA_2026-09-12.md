# Auditoría consolidada y plan de acción — Fase 1

**Versión:** 2.1.0  
**Fecha de cierre:** 2026-09-12  
**Estado:** CERRADA técnicamente; expansión territorial congelada  
**Anterior:** `legacy/auditorias/PLAN_ACCION_FASE1_ARAGON_CYL_EXTREMADURA_2026-09-12_v2.0.0.md`  
**HEAD auditado:** `e0585c6c3173fea6b7f12e726b1e98836bcb158c`

## Resultado de puertas

| Puerta | Estado | Evidencia |
|---|---|---|
| F1.1 Aragón | CERRADA / PASS | Regresión [34704363023](https://github.com/jfmurciego/DiputadodeDistrito/actions/runs/34704363023) |
| F1.2 Castilla y León | CERRADA / PASS | Regresión [34704362932](https://github.com/jfmurciego/DiputadodeDistrito/actions/runs/34704362932) y evidencia `gh-34701897922-1` |
| F1.3 Contrato común | CERRADA | Límites explícitos, YAML único de Aragón y regresiones sin degradación |
| F1.4 Extremadura | CERRADA FORMALMENTE / EXPERIMENTAL_BLOCKED | M01–M06 reproducible: K=65, 41/24, hard=0, 65/65 contiguos, 2 fuera de ±10 % |
| F1.5 Limpieza | CERRADA | Smoke M01–M06 [34704363018](https://github.com/jfmurciego/DiputadodeDistrito/actions/runs/34704363018); evidencia raíz duplicada eliminada |

## Hechos que deben permanecer visibles

| Territorio | Contrato población | Máximo desvío | Lectura |
|---|---|---:|---|
| Aragón | 0,80 / 1,75 / ±12 % | 9,930 % | PASS; margen: 421,620 hab. |
| Castilla y León | 0,80 / 1,75 / ±12 % | 11,984 % | PASS; margen: **4,799 hab.** |
| Extremadura | 0,85 / 1,50 / ±10 % | 13,300 % | Bloqueado; contrato tight específico c020, 2 fuera de tolerancia. |

La diferencia de Extremadura forma parte de su contrato explícito para hacer factible M04 con partición interna c020. No se hereda ni se relaja.

La compacidad Polsby–Popper queda medida en el estado factual como línea base, no como puerta de Fase 1.

## Evidencia única

Se conserva `territorios/<territorio>/resultados/ejecuciones/`. Los cinco árboles históricos de `resultados/ejecuciones/` de Aragón coincidían byte a byte con los territoriales y se han retirado de la raíz.

## Estado factual canónico

`resultados/fase1/ESTADO_FACTUAL.json`

## Decisión

Extremadura no se promociona. No se ejecutará ni ampliará ninguna comunidad posterior sin instrucción expresa del usuario.
