# Cierre complementario F1 — resultados recuperados

**Ejecución:** [34714263877](https://github.com/jfmurciego/DiputadodeDistrito/actions/runs/34714263877)  
**Cálculo repetido:** no.  
**Nota de cierre:** las cuatro ramas terminaron correctamente; el único fallo fue el paso de consolidación. Los artefactos se recuperaron y persistieron sin relanzar ninguna rama.

| Tarea | Estado | Salida |
|---|---|---|
| Auditoría ampliada | SUCCESS | [JSON](AUDITORIA_AMPLIADA.json) |
| Salud técnica: smoke M01–M06 | SUCCESS | [log](SALUD_TECNICA_SMOKE.log) |
| Diagnóstico de Extremadura | SUCCESS | [JSON](EXTREMADURA_DIAGNOSTICO.json) |
| Preparación de visualización | SUCCESS | publicados en [resultados finales](../../finales/README.md) |

No se recalcula ningún GeoJSON existente. La ruta de consumo única es `resultados/finales/<territorio>/distritos.geojson`.
