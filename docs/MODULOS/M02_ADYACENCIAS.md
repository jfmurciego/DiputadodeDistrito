# M02 — Construir adyacencias territoriales

## Propósito
M02 transforma la cartografía de M01 en una relación explícita de vecindad entre secciones. El producto son **todas las aristas CUSEC↔CUSEC**, no un contador.

## Por qué existe
La contigüidad de un distrito no puede decidirse por apariencia visual ni por proximidad de centroides. Debe existir una relación topológica reproducible que indique qué unidades pueden transferirse entre distritos y qué conjunto permanece conectado.

## Entrada
GeoJSON canónico de M01.

## Criterio vigente
Predicado `touches`, CRS métrico ETRS89/UTM 30N, sin buffer ni simplificación y sin longitud mínima de frontera configurada. El índice espacial limita candidatos antes de comprobar topología.

## Producto canónico
`aragon_2025_m02_adyacencias.jsonl`. Cada línea es una arista real `{u, v}`. En la base vigente contiene 4.293 relaciones. La ejecución publica el JSONL completo en `M02/adyacencias.jsonl` y su identidad en `PRODUCTOS.json`.

## Validaciones
CUSEC de ambos extremos debe existir en M01; no se permiten auto-aristas; la pareja se canonicaliza para no duplicar A-B/B-A; el número de aislados se verifica en M03.

## Reutilización
Solo debe recalcularse si cambia la geometría, el conjunto de secciones o el criterio de adyacencia. No depende del algoritmo de distritación ni de las elecciones.
