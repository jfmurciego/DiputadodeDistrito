# R038 — Operación limpia y picadora manual

**Versión:** 1.0.0
**Fecha:** 2026-09-14
**Estado:** implementado; pendiente de CI
**Anterior:** ninguno — documento nuevo

## Decisión operativa

La única interfaz humana para procesar territorios es
`.github/workflows/picadora-territorial.yml`. Desde ella el propietario elige un
territorio del catálogo y una de cinco operaciones: admisión sin cálculo,
bootstrap M01-M03, diagnóstico topológico, promoción estricta M01-M03 o
producción M01-M06.

La producción sigue protegida por contrato completo y por la frase literal
`EXECUTE_WITH_EXPLICIT_USER_AUTHORIZATION`. Los contratos bootstrap no pueden
atravesar M04. Extremadura conserva su bloqueo. Todos los productos del run se
publican como artefacto descargable junto con la decisión contractual.

## Workflows retirados

Se trasladan íntegros a `legacy/workflows/r038/` diez workflows sustituidos:
tres falsos genéricos acoplados a Castilla y León, tres líneas específicas de
Extremadura, el procedimiento específico de Aragón y tres lotes históricos de
Fase 1. No se borra evidencia.

Permanecen activos únicamente la picadora, sus tres componentes reutilizables,
la línea común M01-M06, G10, validaciones, regresiones manuales, publicación y
auditorías reproducibles. Las herramientas experimentales conservadas no son
seleccionables por la picadora; solo los módulos canónicos y los componentes
reutilizables forman parte de la ruta operativa.

## Defectos adicionales corregidos

`procedimiento.sh` contenía secuencias literales `\\n` y no superaba
`bash -n`; por tanto, el modo `execute` de R035 era formalmente invocable pero
no ejecutable. También fijaba `ejecuciones/<run>` aunque el contrato declarase
otra ruta. R038 corrige ambos defectos y obliga a comprobar el shell antes de
construir la imagen.

R038 no demuestra todavía la prueba ciega R040: prepara y protege el botón que
deberá ejecutarla.
