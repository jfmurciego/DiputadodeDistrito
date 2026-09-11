# Continuidad — Extremadura

**Proyecto:** Diputado de Distrito  
**Versión:** 2.0.0  
**Fecha:** 2026-09-11  
**Estado:** EXT-02 cerrado; EXT-03 ha demostrado M04 granular pero mantiene 2 outliers en M05; diagnóstico causal en curso.
**Anterior:** `legacy/territorios/extremadura/CONTINUIDAD_v1.0.0.md`

## Baseline certificado
- Secciones: **964**.
- Población total: **1.053.345**.
- Badajoz: **553 / 665.155**.
- Cáceres: **411 / 388.190**.
- K: **65**.
- Hamilton DDD: **41 Badajoz / 24 Cáceres**.

## EXT-02 — cerrado
- M02 `contact` v7.2.0.
- Pasarelas Don Benito: `0604405005↔0604405003`, `0604405006↔0604405004`.
- M02: 2.607 aristas = 2.605 geométricas + 2 administrativas.
- M03: 964 nodos, 0 aislados, 0 provincias y 0 municipios desconectados.

## EXT-03 — hallazgo arquitectónico
El modelo de un único residuo municipal conexo para municipios sobredimensionados bloquea M04 en Extremadura aunque M03 sea correcto. Las versiones M04 7.5.0/7.5.1 probaron políticas de puertas topológicas y no resolvieron el problema de forma general.

La prueba `granular-open` Run `34624914889` separó identidad administrativa real (`CUMUN`) de una identidad de partición por sección solo para los siete municipios sobredimensionados. El motor base M04 produjo **K=65, cuotas 41/24 y hard=0** en tres escenarios.

El escenario tight (suelo 0,85 / techo 1,50 / ±10% / atomicidad 1,10) fue el mejor candidato inicial: M04 outside=2, min=15.031, max=22.168.

## M05 robusto
M05 v7.4.0 está congelado como motor validado. El wrapper activo v7.4.2 añade únicamente robustez de lectura de `ddd_unit_id` y resolución canónica de rutas; R015 Run `34627885700` pasó completo, por lo que no altera el baseline protegido.

Probe EXT-03 Run `34627885668`:
- M04: K=65, hard=0, outside=2.
- M05 v7.4.2 ejecutó 30.000 iteraciones sobre 705 unidades normalizadas.
- Resultado: **outside ±10%=2**, max dev **36,7947%**, min=15.193, max=22.168.
- M05 redujo error cuadrático pero no pudo reducir el número de outliers ni el máximo desvío.
- Splits observados en municipios grandes: 06011=3, 06015=13, 06044=5, 06083=6, 06153=4, 10037=8, 10148=3.

Conclusión: granularizar por sección desbloquea M04, pero **no se promueve todavía**. Debemos identificar causalmente los dos outliers y decidir si falta una micro-unidad de borde, un operador compuesto de M05 o unidades internas de partición más coherentes que una sección individual.

## Diagnóstico en curso
Herramienta: `herramientas/auditar_bloqueos_m05.py`.
Workflow: `EXT-03 — M05 granular JSON` v1.1.0.
Debe informar por outlier:
- distrito, población y desviación;
- composición municipal/unidades;
- unidades fronterizas;
- cada movimiento unitario candidato y motivo de rechazo;
- si existe alguna mejora unit-step bajo las reglas de M05.

## Regla de promoción
Una nueva política M04 solo podrá promocionarse si:
1. K=65 y cuotas 41/24;
2. contigüidad/provincia duras;
3. cero hard;
4. contrato poblacional objetivo alcanzado tras M05;
5. splits municipales explicables por población/contigüidad, no granularidad indiscriminada;
6. R015/Aragón y Castilla y León mantienen sus baselines;
7. evidencia y outputs quedan persistidos en GitHub.
