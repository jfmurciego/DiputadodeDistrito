# Oleada C — C1 Fundaciones

**Fecha:** 2026-09-21  
**Estado:** diseño implementado en rama aislada; sin integración productiva.

C1 fija contratos de datos para tres capacidades posteriores: comunidades de interés/comarcas, campañas multi-territorio y dashboard/control plane.

## Seguridad

C1 no modifica la lógica de los workflows productivos 00–05, no activa comarcas en producción, no cambia parámetros territoriales ni publica Pages. La única modificación de workflow de esta PR es la puerta de CI que verifica que todos los `tests/test_*.py` aporten tests descubribles por `unittest`.

## Fuente de verdad comarcal

El YAML territorial vigente es la única autoridad para parámetros ya existentes:

- fuente comarcal;
- activación;
- `comarca_surcharge` u otro peso de búsqueda.

La configuración candidata de C1 no repite esos valores. Solo declara semántica y métricas todavía ausentes. Para Aragón, el read model obtiene del contrato vigente `inputs/COMARCAS.csv` y `comarca_surcharge: 0.30`. La huella canónica de la fuente es `ac750499cc180c1241465a42b089044cd3095850b078113bc900b1a33538899a`, ya fijada en `inputs/MANIFEST.sha256`.

La semántica candidata es `SOFT_OBJECTIVE`. Las métricas incluyen las cuatro históricas y dos normalizadas:

- `avoidable_split_communities`;
- `retention_over_structural_max`.

Para Aragón se registra como dato metodológico candidato un techo estructural de retención 0,352 y 11 de 33 comarcas estructuralmente sobredimensionadas. C1 no activa ese criterio como puerta productiva.

## Campañas

La campaña solo selecciona territorios, fases, entorno, modo, publicación y paralelismo. No puede sobrescribir el algoritmo de optimización: cada territorio hereda su método del contrato territorial vigente.

## Read model y linaje

El read model agrega estado durable sin consultar APIs vivas durante la generación. Por territorio expone:

- `source_commit`;
- `artifact_sha256`;
- `release_tag`;
- `doi`;
- `attestation_verified`;
- `osf_registration`.

Las publicaciones se leen de `configuracion/publicaciones.yaml`, no se fijan a una lista vacía. El catálogo inicial refleja la prerelease técnica existente `cyl-m06-checkpoint-temp`; una fase posterior podrá sincronizar automáticamente este catálogo con GitHub Releases.

## Pruebas

Los tests C1 usan `unittest.TestCase`. La CI ejecuta además `herramientas/verificar_descubrimiento_tests.py` dentro de la imagen reproducible y falla si cualquier `tests/test_*.py` aporta cero tests descubribles.

La prueba de ausencia de efectos crea un árbol temporal mínimo, calcula hashes de todos sus ficheros antes y después de construir el read model y exige identidad exacta.
