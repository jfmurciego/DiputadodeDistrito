# M06 — Consolidar y describir distritos

## Propósito
M06 transforma la asignación interna de M05 en **entidades distritales auditables**. Un distrito no es un número y una población: es una unidad territorial compuesta por secciones, municipios, provincias y geometría, con métricas demográficas y espaciales.

## Productos geográficos
`aragon_2025_m06_secciones.geojson.zip`: las 1.463 secciones con distrito final. `aragon_2025_m06_distritos.geojson.zip`: 67 geometrías disueltas, una por distrito.

## Catálogo distrital auditable
`M06/catalogo_distritos.csv` contiene por distrito: `district_id`, población, target, diferencia absoluta, desviación relativa, ratio población/target, suelo, techo, cumplimiento, número de secciones, número y nombres de municipios, número y nombres de provincias, superficie km², perímetro km, compacidad Polsby–Popper, centroide ETRS89/UTM30 y bounding box.

## Composición territorial
`M06/composicion_distritos.csv` contiene una fila por sección con distrito, CUSEC, municipio, provincia, CUDIS y población. Permite reconstruir y auditar exactamente de qué está hecho cada distrito sin abrir GIS.

## Por qué estas métricas
Población mide equilibrio; composición permite trazabilidad; municipios/provincias describen coherencia administrativa; área/perímetro/compacidad permiten detectar formas territorialmente aberrantes; centroide y bbox facilitan inspección GIS y automatización posterior.

## Evolución prevista
La denominación humana del distrito debe añadirse cuando exista la capa fiable de barrios/toponimia. No se inventarán nombres a partir de «ejes». También podrán incorporarse comarca, cabecera, población por municipio, densidad, continuidad municipal y métricas adicionales de forma sin cambiar la identidad básica del distrito.
