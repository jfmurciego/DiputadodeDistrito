# Política de versiones y conservación

**Versión:** 1.3.0 — Multi-territorio y compatibilidad controlada
**Fecha:** 2026-09-11
**Anterior:** `legacy/docs/POLITICA_DE_VERSIONES_v1.2.2.md`

## Regla inviolable

Ningún fichero funcional/versionado existente se sustituye sin conservar previamente su contenido anterior en `legacy/`. Las copias históricas son evidencia y no se reescriben para satisfacer reglas posteriores.

## Versionado

SemVer:
- MAJOR: cambia contrato o arquitectura incompatible;
- MINOR: mejora funcional compatible;
- PATCH: corrección compatible, metadatos o trazabilidad.

## Cabecera obligatoria

Código, configuración, workflows y documentos versionados deben declarar versión, nombre, fecha, alcance, estado, cambios, motivo y predecesor/origen cuando el formato lo permita. Una ruta `Anterior` debe existir; si no existe, declarar explícitamente predecesor histórico no recuperado.

## Promoción

Un artefacto ya probado no se reescribe solo para cambiar `candidato` por `vigente`. La promoción se registra en documentación canónica y expediente de run.

## Arquitectura multi-territorio

El repositorio contiene un único motor y múltiples paquetes `territorios/<id>/`. Queda prohibido usar repositorios o ramas permanentes como mecanismo de separación por territorio.

Un paquete territorial puede contener configuración, inputs, docs, tests y referencias de resultados. No puede contener una copia de `ddd_core/` o `modulos/`.

Si una nueva implantación descubre una diferencia, primero debe intentarse expresar como:
1. parámetro;
2. rol genérico del contrato territorial;
3. estrategia reusable del motor.
Solo después puede considerarse una extensión específica, siempre documentada y sin romper otros territorios.

## Compatibilidad temporal

Rutas históricas pueden mantenerse temporalmente si son necesarias para reproducir un baseline validado. Deben marcarse como compatibilidad, no como arquitectura canónica. Su retirada exige demostrar que la nueva ruta/workflow reproduce el baseline protegido.

## Procedimiento de cambio

Todo cambio funcional exige:
1. preservar predecesor;
2. incrementar versión;
3. actualizar metadatos;
4. registrar cambio;
5. ejecutar CI;
6. si afecta comportamiento territorial, ejecutar nuevo run reproducible;
7. comprobar regresiones de todos los territorios validados, no solo del territorio nuevo.

## Ramas

`main` es la única rama permanente. Cualquier rama técnica temporal debe integrarse y eliminarse. Las versiones históricas viven en `legacy/`.

## Resultados

Cada run usa identidad inmutable y manifiesto. Los resultados por territorio deben poder asociarse inequívocamente a `territory_id`, configuración, commit y hashes de inputs.

## Estado canónico

Documentos vigentes: `README.md`, `docs/ESTADO_MAESTRO_PROYECTO.md`, `docs/CONTINUIDAD_NUEVO_CHAT.md`, `docs/BITACORA.md`, `docs/REGISTRO_DE_CAMBIOS.md`, `docs/ARQUITECTURA_MULTI_TERRITORIO.md` y `docs/CONTRATO_TERRITORIO.md`. Los antiguos `MEMORIA*` no son fuentes activas.
