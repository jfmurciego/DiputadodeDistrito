# Blindaje de workflows automáticos

**Versión:** 1.0.0
**Fecha:** 2026-09-14
**Estado:** candidato local-first
**Anterior:** ninguno — documento nuevo

## Decisión

Los workflows que calculan, exportan o publican quedan exclusivamente bajo
`workflow_dispatch`: C‑01, las dos regresiones M06, exportación Flourish y los
dos despliegues web. Ningún push puede volver a activarlos.

Siguen automáticos solo los controles sin cálculo territorial: suite general,
puerta contractual, control G10, validación de productos y notificaciones.

## Incidencia que origina el cambio

La restauración del árbol del commit `636f732` hizo que GitHub considerara
reintroducidas varias rutas y activara sus disparadores `push`. C‑01 terminó
`FAIL`, coherente con el resultado ya conocido de 15/50 semillas válidas. No
modificó productos certificados, pero consumió cálculo sin orden y por ello el
disparador automático queda prohibido mediante prueba de regresión.

## Comarcas verificadas sin territorio

`COMARCAS.csv` de Drive contiene las seis columnas declaradas, 731 filas, 731
códigos municipales únicos, 33 comarcas, cero códigos municipales inválidos y
cero asignaciones contradictorias. Esta verificación es tabular: no ejecuta
M01–M08 ni habilita `comarcas.enabled`.
