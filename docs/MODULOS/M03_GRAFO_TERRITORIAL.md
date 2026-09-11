# M03 — Construir grafo territorial

## Propósito
M03 convierte M01+M02 en el **contrato matemático del territorio**: cada sección es un nodo con población y cada adyacencia es una arista.

## Por qué existe
Separa GIS de optimización. M04 y M05 no deberían volver a interpretar polígonos para saber conectividad; deben trabajar contra un grafo estable, pequeño, versionable y verificable.

## Entradas
Secciones con población de M01 y aristas de M02.

## Producto canónico
`aragon_2025_m03_grafo.json`, con arrays completos `nodes` y `edges`. La referencia vigente contiene 1.463 nodos, 4.293 aristas, población total 1.364.621 y 0 nodos aislados. La ejecución publica el JSON completo como `M03/grafo.json`, no solo el informe.

## Validaciones
Todos los nodos tienen CUSEC y población; todas las aristas apuntan a nodos existentes; se contabilizan aislados; se conserva la suma de población de M01.

## Por qué está antes de M04
M04 necesita una estructura de conectividad determinista para crecer distritos contiguos. Cambiar el motor de distritación no debe cambiar el territorio de entrada.
