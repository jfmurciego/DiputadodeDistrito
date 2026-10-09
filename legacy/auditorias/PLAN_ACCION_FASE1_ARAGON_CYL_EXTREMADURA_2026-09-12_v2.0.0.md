# Auditoría consolidada y plan de acción — Fase 1

**Versión:** 2.0.0  
**Fecha de cierre:** 2026-09-12  
**Estado:** CERRADA técnicamente; expansión territorial congelada  
**Anterior:** `legacy/auditorias/PLAN_ACCION_FASE1_ARAGON_CYL_EXTREMADURA_2026-09-12_v1.0.md`  
**HEAD verificado:** `aebce6ebb68b7b84cd2fa579efc276e9316ab837`

## Resultado de puertas

| Puerta | Estado | Evidencia |
|---|---|---|
| F1.1 Aragón | CERRADA / PASS | Regresión [34704363023](https://github.com/jfmurciego/DiputadodeDistrito/actions/runs/34704363023) |
| F1.2 Castilla y León | CERRADA / PASS | Regresión [34704362932](https://github.com/jfmurciego/DiputadodeDistrito/actions/runs/34704362932) y evidencia `gh-34701897922-1` |
| F1.3 Contrato común | CERRADA | Límites explícitos, YAML único de Aragón y regresiones sin degradación |
| F1.4 Extremadura | CERRADA FORMALMENTE / EXPERIMENTAL_BLOCKED | M01–M06 reproducible: K=65, 41/24, hard=0, 65/65 contiguos, 2 fuera de ±10 % |
| F1.5 Limpieza | CERRADA | Smoke M01–M06 [34704363018](https://github.com/jfmurciego/DiputadodeDistrito/actions/runs/34704363018); 13 workflows activos y 36 archivados |

## Estado factual canónico

`resultados/fase1/ESTADO_FACTUAL.json`

## Decisión

Extremadura no se promociona ni se relajan umbrales. La rama de cierre admitida por el plan —resultado reproducible y bloqueo experimental explícito— queda aplicada.

No se ejecutará ni ampliará ninguna comunidad posterior sin instrucción expresa del usuario.
