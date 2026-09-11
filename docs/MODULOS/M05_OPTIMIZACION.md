# M05 — Optimizar distritos

## Propósito
M05 modifica fronteras de la solución M04 para mejorar equilibrio poblacional y calidad territorial sin violar ninguna regla estructural.

## Restricciones duras R012
1. exactamente 67 distritos;
2. cardinalidad provincial fija: Huesca 11, Teruel 7, Zaragoza 49;
3. ningún distrito puede cruzar una provincia;
4. contigüidad por grafo;
5. población entre 0,80×target y 1,75×target;
6. disciplina municipal: un municipio que cabe en un distrito no se fragmenta; un municipio grande ocupa como máximo `ceil(P/target)` distritos y solo uno de ellos puede ser mixto con municipios externos.

Un movimiento que viole cualquiera de estas reglas ni siquiera entra en la función objetivo: es inválido.

## Jerarquía multiobjetivo
Una vez dentro del espacio válido, M05 optimiza lexicográficamente:
1. número de distritos fuera de ±12% respecto del target;
2. magnitud total de la desviación que excede ±12%;
3. número de municipios fragmentados por encima del mínimo territorial necesario;
4. número de distritos mixtos asociados a municipios divididos;
5. máximo desvío poblacional;
6. error cuadrático poblacional global;
7. posteriormente, métricas de forma/compactación y coherencia comarcal cuando sus fuentes estén formalizadas.

## Tratamiento de municipios urbanos
M05 no debe intercambiar secciones urbanas de forma independiente si pertenecen a una unidad municipal/urbana bloqueada por M04. Los movimientos se realizan sobre unidades atómicas completas, de modo que la optimización no pueda volver a crear el problema que M04 ya resolvió.

## Entradas
Grafo M03, asignación M04, población, provincia, municipio, unidades atómicas, suelo/techo, tolerancia ±12%, iteraciones y semilla.

## Productos
`aragon_2025_m05_distritos_optimizados.geojson.zip`: asignación geográfica completa. `M05/asignacion_optimizada.csv`: las 1.463 secciones con distrito optimizado y contexto administrativo. `aragon_2025_m05_informe.json`: función objetivo inicial/final, restricciones, movimientos aceptados, municipios fragmentados, distritos mixtos, máximo desvío, iteraciones y semilla.

## Auditoría exigida
Debe poder compararse M04 y M05 sección por sección y unidad atómica por unidad atómica. Todo movimiento debe demostrar: misma provincia, contigüidad conservada, disciplina municipal conservada y mejora de la función objetivo.

## Estado actual
Run #5 demuestra que el motor previo alcanza 0 violaciones de suelo/techo, pero no es territorialmente válido bajo R012: contiene cruces provinciales y fragmentación municipal indebida. La siguiente referencia solo podrá promocionarse si conserva los antiguos PASS y añade provincia/municipio PASS.
