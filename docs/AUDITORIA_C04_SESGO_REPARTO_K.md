# Auditoría C-04 — Sesgo poblacional del reparto territorial de K

**Versión:** 1.0.0  
**Fecha:** 2026-09-13  
**Estado:** cerrado — medido y publicado  
**Anterior:** ninguno — documento nuevo

## Decisión

C-04 queda cerrado con una métrica explícita y reproducible sobre evidencia ya
certificada. No se ha ejecutado M01–M06 ni se ha abierto ningún territorio.

La métrica es:

`population_load_bias = (población provincial / distritos provinciales) / (población territorial / K) - 1`

Un valor negativo indica menos habitantes por representante que la media del
territorio; uno positivo, más habitantes por representante. Es un sesgo
estructural anterior a M04: procede de convertir cuotas ideales en distritos
enteros y no de la geometría posterior.

## Resultado rector

- Aragón: máximo absoluto 4,546 %, en Teruel (`44`), con sesgo de carga −4,546 %.
- Castilla y León: máximo absoluto 9,674 %, en Palencia (`34`), con −9,674 %.
- Extremadura: máximo absoluto 0,190 %, en Cáceres (`10`), con −0,190 %; el
  territorio sigue `EXPERIMENTAL_BLOCKED` y esta medición no lo promociona.

La evidencia completa por provincia está en
`docs/SALIDAS_CHATGPT/EVIDENCIAS/C04_SESGO_REPARTO_K.json`. El cálculo se
reproduce con `herramientas/auditar_sesgo_reparto_k.py` sobre
`configuracion/auditoria_reparto_k.json`.

## Alcance

La auditoría mide el efecto del reparto dado. No recomienda cambiar K ni las
cuotas después de observar un mapa. Para un territorio nuevo, K y el método de
reparto continúan fijándose antes de M04 conforme a R036.
