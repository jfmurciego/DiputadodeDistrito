# Procedimiento por tramo certificado

**Versión:** 1.0.0

El procedimiento ya no presupone que cada intervención debe recalcular M01–M08.

## Contrato de ejecución

| Variable | Significado |
|---|---|
| `DDD_FROM_STAGE` | Primera etapa semántica a ejecutar. |
| `DDD_TO_STAGE` | Última etapa semántica a ejecutar. |
| `DDD_CHECKPOINT_MANIFEST` | `PRODUCTOS.json` del checkpoint autorizado por G10. Obligatorio si se inicia después de M01. |
| `DDD_CHECKPOINT_CACHE_DIR` | Directorio del runner donde la evidencia de base está materializada. |

El lanzador solo admite reenganche posterior a M01 cuando existen **ambas** cosas: manifiesto y grafo M03 materializado en la caché. Es deliberado: un registro en Git no equivale a una entrada disponible para el contenedor.

Una ejecución terminada antes de M08 se marca como parcial y no ejecuta la validación de producto público. Cada tramo crea `REENGANCHE.json` dentro de su run, con origen y límites de la decisión.

## Ejemplo de intención

Para modificar M05 en Aragón, G10 resolverá M04 como checkpoint; el workflow materializará M03/M04 según el adaptador de artefactos y llamará al procedimiento desde `DISTRICT_BALANCING`. Si falta cualquier pieza, el runner se detendrá antes de calcular: no existe una ruta de “seguir como sea”.
