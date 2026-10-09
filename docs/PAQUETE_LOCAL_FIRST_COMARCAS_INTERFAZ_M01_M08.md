# Paquete local-first: comarcas e interfaz M01–M08

**Versión:** 1.1.0  
**Fecha:** 2026-09-16  
**Estado:** implementado; referencias operativas reconciliadas con la interfaz única  
**Anterior:** versión 1.0.0 en historial Git

## Alcance

Este paquete implementa exactamente el bloque definido en
`REENGANCHE_DDD_2026-09-14_LOCAL_FIRST`: adaptador opcional de comarcas en M01,
propagación no restrictiva por M03/M06, pruebas sintéticas, interfaz manual
institucional M01–M08 y corrección del inventario operativo de workflows.

## Contrato comarcal

- La clave es `Municipio código`, normalizada a cinco dígitos.
- M01 la compara con los cinco primeros dígitos de `CUSEC_KEY`.
- Nunca se usan nombres municipales para unir.
- Un municipio con dos asignaciones distintas aborta.
- `require_full_coverage: true` aborta si falta algún municipio.
- Con la fuente deshabilitada no se abre ni se lee su ruta.
- M03 transporta comarca como atributo del nodo; las aristas no cambian.
- M06 conserva comarca en composición y resume las presentes por distrito.

## Interfaz operativa

`.github/workflows/ejecucion-generacion-distritos.yml` es el único formulario
humano territorial. Expone únicamente inputs `choice` y `boolean`; no solicita
run IDs ni autorizaciones literales al operador.

La resolución interna transforma las selecciones humanas en IDs técnicos y
busca automáticamente la evidencia reutilizable necesaria: último checkpoint
compatible para tramos posteriores a M01 y último Aragón-10 completo y vigente
cuando se solicita su republicación.

La línea `producir-territorio-por-contrato.yml` solo acepta `workflow_call` y
la interfaz llega a ella a través de
`_reutilizable-operacion-territorial.yml`, que mantiene una sola llamada a la
cadena M01–M08 para admisión, verificación, preparación, certificación y
producción.

El antiguo `g10-ejecutar-tramo-certificado.yml` permanece únicamente como
antecedente histórico en `legacy`. Las confirmaciones humanas de ejecución y
coste son booleanas; los literales técnicos de compatibilidad se derivan dentro
de los reutilizables cuando corresponde.

## Verificación permitida

Solo suite local y validaciones estáticas/sintéticas. Queda prohibido ejecutar
Aragón, Castilla y León, Extremadura, La Rioja, Cantabria u otro territorio sin
autorización territorial explícita.

## Incidencia de certificación

La primera publicación no retiró materialmente del árbol remoto el workflow G10
sustituido; la suite lo detectó. La corrección lo eliminó, pero la segunda CI
intentó comprobar su copia legacy dentro de la imagen, donde `.dockerignore`
excluye deliberadamente `legacy/`. La prueba se ajusta al patrón de gobierno ya
vigente: ausencia activa dentro y predecesor legacy en el checkout exterior.

Esta actualización sólo reconcilia referencias documentales con el estado
operativo de la interfaz única; no modifica contratos territoriales, motores,
geometrías, umbrales ni resultados.
