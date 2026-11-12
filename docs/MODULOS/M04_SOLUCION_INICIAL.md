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

## Unidad flexible del residual (entrada 7.6.0)
Cuando un distrito es solo el residual monolítico de un municipio dividido (`<municipio>:R`) y los demás distritos abiertos de la provincia quedan bajo el suelo, M04 expone una unidad flexible `:F` en la frontera del residual para que M05 pueda moverla. La unidad no cambia la asignación de M04.

Desde 7.6.0, si ninguna sección fronteriza individual cubre el déficit, la unidad `:F` puede ser un bloque conexo de secciones del residual, adyacente al receptor, que cubra el déficit sin desconectar al donante, sin superar el slack del donante ni el techo del receptor y sin usar secciones de puentes topológicos. Si basta una sección, el resultado es idéntico a 7.5.9. Caso que lo motivó: Congreso Álava (residual de Vitoria, 01059:R, déficit de 14.402 habitantes).

## Alivio de residuos sobre el techo (entrada 7.6.6)
M05 mueve unidades enteras (`ddd_unit_id`) y no puede redibujar las piezas internas de un municipio dividido. Desde 7.6.6, antes del postproceso, M04 repara los distritos sobre el techo con tres movimientos, siempre dentro del mismo municipio dividido y sin tocar puentes ni pasarelas protegidas: (1) cede secciones fronterizas del residual `:R` a núcleos `:U` con margen hasta `target+tol`; (2) si el distrito no tiene residual que ceder, traslada un municipio completo al distrito del residual vecino de otro municipio dividido (su único distrito mixto) y aplica (1) sobre ese distrito, deshaciendo el traslado si no queda bajo el techo; (3) si los núcleos vecinos del residual están llenos, pasa una sección a otro núcleo del mismo municipio que siga dentro de la tolerancia. Se exige conexidad del residual, de los núcleos y de los distritos de origen y destino, y que el residual conserve una pasarela fuera del municipio. Casos que lo motivaron (T-22): Murcia (Alcantarilla y Beniel, enclaves de Murcia, empujaban el residual a 171.010) y Madrid (Pozuelo + Boadilla + Villaviciosa = 181.853; Pozuelo pasa al residual de Madrid).

## Núcleo adicional por enclaves dependientes (entrada 7.6.7)
El número de piezas de un municipio dividido se decidía solo con su población. Si un municipio vecino solo linda con él (enclave dependiente), irá forzosamente con su residual; cuando residual + enclaves supera el techo, M05 no puede repararlo. Desde 7.6.7, fuera de `closed_target_cores_plus_open_residual`, M04 reintenta la partición con un núcleo cerrado más (secuencial, equilibrada y por crecimiento) y la acepta solo si residual + enclaves cabe bajo el techo; si no, conserva la partición original. Caso que lo motivó (T-44): Elche (238.285) + Santa Pola (37.839), que solo linda con Elche; con dos piezas el residual quedaba en 144.394.
En 7.6.7 el alivio de residuos (módulo 1.1.0) admite además una cadena de dos saltos: si ningún municipio del distrito sobre el techo linda con un residual, pasa uno a un distrito vecino sin residual y desde allí traslada otro al residual, que cede el exceso a sus núcleos. Caso (T-44, Málaga con Fuengirola exenta de suelo): Benalmádena pasa con Alhaurín de la Torre y Torremolinos al residual de Málaga.

## Exención de techo de una partición atómica (entrada 7.6.8)
El preflight de población usa el techo efectivo de cada partición con `ddd_core/population_cap_exemptions.py`, la misma regla que M05, M06, el validador y motor2. Solo una partición de `validation.population_cap_exempt_partitions` con K=1 y decisión del propietario queda sin techo: su distrito es la partición entera. Sin la clave nada cambia (composiciones idénticas bit a bit en Huesca, La Rioja, Congreso La Rioja, Santa Cruz de Tenerife y Las Palmas 2025). Caso (T-235, D-83): Lanzarote y La Graciosa (35-G01) con el padrón 2025, 166.878 hab. = 1,424 de la media frente al techo 1,40.
