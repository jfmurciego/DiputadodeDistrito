# M08 — Integrar producto electoral territorial

## Propósito
M08 une la entidad territorial consolidada de M06 con el resultado electoral agregado de M07. No recalcula ni fronteras ni votos.

## Entradas
GeoJSON distrital M06 y resumen electoral M07.

## Productos
`aragon_2025_m08_distritos_resultados.geojson.zip`: producto geográfico final, una feature por distrito con geometría y atributos electorales. `M08/distritos_resultados.csv`: todos los atributos no geométricos del producto final para inspección tabular.

## Auditoría
El `district_id` es la clave de unión. Deben existir exactamente 67 entidades y la geometría debe ser idéntica a M06; M08 solo añade atributos electorales. La validación final se conserva separadamente en `VALIDACION.json`.

## Uso
Es el producto consumible por GIS, cartografía web, análisis electoral y publicación. La separación permite distinguir con precisión qué parte procede de la distritación y qué parte del escrutinio.
