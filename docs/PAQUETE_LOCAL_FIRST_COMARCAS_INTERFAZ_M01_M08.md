# Paquete local-first: comarcas e interfaz M01–M08

**Versión:** 1.0.0  
**Fecha:** 2026-09-14  
**Estado:** implementado localmente; pendiente certificación CI  
**Anterior:** ninguno — documento nuevo

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

`.github/workflows/picadora-territorial.yml` es el único formulario territorial.
La línea `producir-territorio-por-contrato.yml` solo acepta `workflow_call`.
El antiguo `g10-ejecutar-tramo-certificado.yml` queda en legacy. La autorización
literal sigue siendo obligatoria para cualquier operación que ejecute módulos.

## Verificación permitida

Solo suite local y validaciones estáticas/sintéticas. Queda prohibido ejecutar
Aragón, Castilla y León, Extremadura, La Rioja, Cantabria u otro territorio.

## Incidencia de certificación

La primera publicación no retiró materialmente del árbol remoto el workflow G10
sustituido; la suite lo detectó. La corrección lo eliminó, pero la segunda CI
intentó comprobar su copia legacy dentro de la imagen, donde `.dockerignore`
excluye deliberadamente `legacy/`. La prueba se ajusta al patrón de gobierno ya
vigente: ausencia activa dentro y predecesor legacy en el checkout exterior.
