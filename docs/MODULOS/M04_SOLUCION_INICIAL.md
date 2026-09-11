# M04 — Generar solución inicial

## Propósito
M04 produce exactamente K=67 distritos iniciales contiguos y territorialmente válidos. No es solo un semillado numérico: debe respetar desde el origen las fronteras provinciales y la disciplina municipal.

## Principio territorial R012
M04 trabaja por provincia. La cardinalidad 67 se reparte mediante Hamilton sobre población: Huesca 11, Teruel 7 y Zaragoza 49. Ningún distrito puede cruzar provincia.

Antes de ensamblar distritos, M04 debe tratar los municipios como unidades territoriales atómicas siempre que su población quepa en un distrito. Un municipio pequeño o medio no puede repartirse arbitrariamente entre varios distritos.

Los municipios cuya población exige varios distritos se dividen internamente en unidades urbanas conectadas. Se forman primero distritos exclusivamente municipales; solo la unidad residual final puede completarse con municipios menores adyacentes de la misma provincia. Como máximo un distrito que contenga partes de un municipio dividido puede ser mixto.

## Por qué existe separado de M05
Inicialización y optimización son problemas distintos. M05 no debe gastar iteraciones reparando violaciones estructurales creadas por M04. M04 debe entregar una solución ya compatible con provincia, contigüidad y disciplina municipal; M05 mejora población y calidad territorial dentro de ese espacio válido.

## Entradas
Grafo M03, geometría M01, población, provincia, municipio, K, método de apportionment y semilla.

## Productos
`aragon_2025_m04_semillas.geojson.zip`: las 1.463 secciones con `district_id` inicial. `M04/asignacion_inicial.csv`: tabla completa sección→distrito con CUSEC, municipio, provincia y población. `aragon_2025_m04_informe.json`: target, cardinalidad total y provincial, municipios divididos, distritos mixtos, mínimo/máximo poblacional y controles de asignación.

## Validaciones duras
- exactamente 67 distritos;
- 11 Huesca, 7 Teruel, 49 Zaragoza;
- cero distritos interprovinciales;
- contigüidad;
- cero secciones sin asignar;
- municipio que cabe en un distrito: máximo un distrito;
- municipio dividido: máximo `ceil(P/target)` distritos y como máximo un distrito mixto;
- determinismo con iguales datos y semilla.

## Interpretación
Una desviación poblacional inicial puede ser reparada por M05. Una violación provincial o una fragmentación municipal indebida no es reparable aceptablemente a posteriori: M04 debe impedir que nazca.
