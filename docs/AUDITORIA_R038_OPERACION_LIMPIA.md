# R038 — Operación limpia e interfaz manual

**Versión:** 1.1.0
**Fecha:** 2026-09-14
**Estado:** cerrado y certificado — CI 34830677071 SUCCESS
**Anterior:** `legacy/docs/AUDITORIA_R038_OPERACION_LIMPIA_v1.0.3.md`

## Decisión operativa

La única interfaz humana para procesar territorios es
`.github/workflows/operacion-territorial.yml`. Su nombre visible es **Operación
territorial DDD — M01 a M08** y ofrece seis operaciones institucionales:
admitir, verificar, preparar M01–M03, diagnosticar topología, certificar M01–M06
o producir M01–M08.

La producción sigue protegida por contrato completo y por la frase literal
`EXECUTE_WITH_EXPLICIT_USER_AUTHORIZATION`. Los contratos bootstrap no pueden
atravesar M04. Extremadura conserva su bloqueo. Todos los productos del run se
publican como artefacto descargable junto con la decisión contractual.

## Workflows retirados

Se trasladan íntegros a `legacy/workflows/r038/` diez workflows sustituidos:
tres falsos genéricos acoplados a Castilla y León, tres líneas específicas de
Extremadura, el procedimiento específico de Aragón y tres lotes históricos de
Fase 1. No se borra evidencia.

Permanecen activos únicamente la interfaz institucional, sus componentes reutilizables,
la línea común M01–M08, G10 por lote, validaciones, regresiones manuales, publicación y
auditorías reproducibles. Las herramientas experimentales conservadas no son
seleccionables desde la interfaz; solo los módulos canónicos y los componentes
reutilizables forman parte de la ruta operativa.

El inventario activo queda en 17 workflows: una interfaz territorial manual,
cuatro componentes/motores reutilizables o automáticos de operación, dos
regresiones territoriales exclusivamente manuales y diez puertas, auditorías o
flujos de publicación. Ese recuento sustituye inventarios históricos previos.

La línea contractual pierde su `workflow_dispatch` y el antiguo formulario G10
por tramo se retira a `legacy/workflows/local_first/`. Así no quedan tres botones
capaces de expresar el mismo recorrido territorial.

## Defectos adicionales corregidos

`procedimiento.sh` contenía secuencias literales `\\n` y no superaba
`bash -n`; por tanto, el modo `execute` de R035 era formalmente invocable pero
no ejecutable. También fijaba `ejecuciones/<run>` aunque el contrato declarase
otra ruta. R038 corrige ambos defectos y obliga a comprobar el shell antes de
construir la imagen.

R038 no demuestra todavía la prueba ciega R040: prepara y protege el botón que
deberá ejecutarla.

## Incidencia de certificación

El run general `34825103970` falla dos veces en el paso de unittest, aunque la
misma suite completa pasa localmente con Python 3.11 y las dependencias fijadas:
71/71 pruebas. El workflow general v1.2.0 conserva desde ahora su salida como
artefacto incluso al fallar. Esta instrumentación no ejecuta territorios y evita
modificar R038 sin conocer la excepción exacta.

El artefacto del run `34830251652` identifica la causa: `.dockerignore` excluye
correctamente `legacy/`, pero la prueba intentaba validarlo dentro de la imagen.
La comprobación de workflows activos se mantiene siempre; la existencia de
predecesores se verifica en el checkout, donde CI ya ejecuta la puerta de
gobernanza. No se relaja ninguna garantía.

El commit `7a02dba` supera la suite general `34830677071`. Fue el único
workflow activado y no se ejecutó ningún territorio. R038 queda cerrado.
