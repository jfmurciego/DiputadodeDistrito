# Auditoría C-10 — Contrato único del catálogo M06

**Versión:** 1.0.0  
**Fecha:** 2026-09-13  
**Estado:** cerrado — esquema único y compatibilidad histórica explícita  
**Anterior:** ninguno — documento nuevo

## Decisión

El nombre canónico de la métrica es `polsby_popper`. El contrato completo de
fila se publica en `schemas/m06-district-catalog.schema.json` y se resuelve en
`ddd_core/m06_schema.py`. Ningún consumidor debe volver a elegir campos por
territorio.

Los catálogos certificados no se reescriben: forman parte de runs históricos
con identidad propia. La divergencia histórica se absorbe mediante un registro
cerrado de alias, que informa `PASS_LEGACY_ADAPTED`; una salida nueva debe usar
los nombres canónicos y no puede introducir aliases nuevos silenciosamente.

## Alcance verificado

- Aragón: 67 filas, adaptando `compactness_polsby_popper` y otros nombres v7.
- Castilla y León: 82 filas, adaptando el vocabulario inicial de M06.
- Extremadura: 65 filas, misma adaptación, sin cambiar su estado bloqueado.
- Productor M06 vigente: emite `polsby_popper`.

La evidencia reproducible queda en
`docs/SALIDAS_CHATGPT/EVIDENCIAS/C10_ESQUEMA_M06.json`. La validación no ejecuta
M01–M06 ni modifica los productos certificados.
