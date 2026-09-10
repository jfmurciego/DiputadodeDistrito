# Política de versiones y conservación

**Versión:** 1.0.0 — Conservación obligatoria

## Regla inviolable

Ningún fichero funcional existente se sustituye sin conservar previamente su contenido anterior en `legacy/`. Git ya conserva el historial, pero `legacy/` constituye una segunda capa explícita de arqueología del proyecto y permite inspeccionar versiones sin reconstruir commits.

## Versionado

Se usa `MAJOR.MINOR.PATCH`:
- **MAJOR:** cambia el contrato, algoritmo fundamental o compatibilidad de entradas/salidas.
- **MINOR:** mejora funcional compatible o modificación sustancial del comportamiento.
- **PATCH:** corrección que no cambia el contrato.

Los módulos activos tendrán nombre estable (`modulo_01_...py`). La versión no se codifica en el nombre activo para que la automatización no deba cambiar rutas en cada revisión. Cada versión retirada se guarda como `legacy/modulo_XX/<nombre>_vA.B.C.py`.

## Cabecera obligatoria de código

Todo módulo debe comenzar con: nombre del módulo, versión, nombre de versión, fecha, función, entradas, salidas, razón de existencia, cambios respecto de la versión anterior y motivo del cambio. Si no existe versión anterior debe indicarse `Origen: baseline recuperado`.

## Registro de cambios

Todo cambio funcional exige simultáneamente:
1. copia anterior en `legacy/`;
2. incremento de versión;
3. actualización de cabecera;
4. entrada en `docs/REGISTRO_DE_CAMBIOS.md`;
5. actualización de `docs/MEMORIA_DEL_PROYECTO.md` si cambia estado, criterio, arquitectura o resultado;
6. commit Git identificable;
7. ejecución y resultado registrados cuando el cambio sea ejecutable.

## Resultados

Cada ejecución tendrá `run_id` inmutable y directorio lógico `runs/<ámbito>/<run_id>/` en artifacts/almacenamiento de ejecuciones. El manifiesto debe registrar commit, versiones de módulos, parámetros, hashes de entradas, semilla, entorno, tiempos, métricas, validaciones y hashes de salidas. No se sobrescribe un resultado anterior.
