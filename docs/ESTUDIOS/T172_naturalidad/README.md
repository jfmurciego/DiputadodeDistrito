# Distritos más naturales: cinco formas de elegir el mapa

Mismos datos (población y secciones del INE), mismas reglas (contigüidad, municipios, tolerancia del contrato) y las
mismas semillas públicas. Solo cambia cómo se elige el mapa ganador entre el mapa del motor actual y 20 cadenas:

- **A · solo población**: la función de calidad vigente (menos distritos fuera de tolerancia y, después, el menor desvío).
- **D5 · como C, con desvío máximo ≤ 5 %**: entre los mapas de C, el más natural que no pase del 5 % de desvío.
- **D8 · como C, con desvío máximo ≤ 8 %**: igual, con el 8 %.
- **C · como B, cortando por donde hay menos vínculo**: las cadenas prefieren cortar entre partidos judiciales,
  comarcas agrarias y áreas de movilidad distintas, y por fronteras largas.
- **B · población y luego naturalidad**: primero que nadie quede fuera de tolerancia; a igualdad, menos partidos
  judiciales y comarcas agrarias partidos y menos frontera cortada; el desvío solo desempata al final.

El tope de D5/D8 **solo sirve para elegir** entre candidatos: no es una regla nueva (suelo, techo, K y tolerancia no
cambian). Se mide en los distritos dentro de tolerancia; un distrito ya fuera (el municipio exento de Cádiz, el de
Barcelona) no cuenta. Si ningún candidato cumple el tope, gana el de menor exceso.

Mapas lado a lado en `mapas/` (paneles A, D5, D8, C y B; mismos colores y escala; línea discontinua: partidos
judiciales). Sin ríos ni relieve: aún no hay fuente oficial descargada. Tablas completas en `mapas/TABLA.csv` y, por
distrito, `mapas/DISTRITOS.csv`.

## Resultado

| Territorio | Función | Fuera de tolerancia | Desvío máx. % | Suma de desvíos (personas) | Coste frente a A (personas) | Polsby-Popper medio | Convexidad media | Partidos judiciales partidos | Comarcas agrarias partidas | Cohesión de movilidad |
|---|---|---|---|---|---|---|---|---|---|---|
| Asturias | A | 0 | 4.79 | 22454 | 0 | 0.247 | 0.611 | 8/18 | 4/10 | 0.548 |
| Asturias | D5 | 0 | 6.89 | 43034 | 20580 | 0.241 | 0.62 | 3/18 | 4/10 | 0.586 |
| Asturias | D8 | 0 | 6.89 | 43034 | 20580 | 0.241 | 0.62 | 3/18 | 4/10 | 0.586 |
| Asturias | C | 0 | 14.36 | 70312 | 47858 | 0.261 | 0.628 | 3/18 | 2/10 | 0.585 |
| Asturias | B | 0 | 14.54 | 73087 | 50633 | 0.227 | 0.6 | 3/18 | 3/10 | 0.555 |
| Badajoz | A | 0 | 1.41 | 5261 | 0 | 0.14 | 0.521 | 13/14 | 9/12 | 0.638 |
| Badajoz | D5 | 0 | 4.41 | 18551 | 13290 | 0.227 | 0.632 | 5/14 | 5/12 | 0.692 |
| Badajoz | D8 | 0 | 7.7 | 34177 | 28916 | 0.218 | 0.657 | 3/14 | 3/12 | 0.662 |
| Badajoz | C | 0 | 14.7 | 36733 | 31472 | 0.223 | 0.66 | 3/14 | 3/12 | 0.668 |
| Badajoz | B | 0 | 13.5 | 52433 | 47172 | 0.23 | 0.611 | 7/14 | 5/12 | 0.718 |
| Barcelona | A | 1 | 22.31 | 217168 | 0 | 0.208 | 0.593 | 21/25 | 10/10 | 0.459 |
| Barcelona | D5 | 1 | 22.31 | 388224 | 171057 | 0.261 | 0.656 | 19/25 | 9/10 | 0.481 |
| Barcelona | D8 | 1 | 22.31 | 388224 | 171057 | 0.261 | 0.656 | 19/25 | 9/10 | 0.481 |
| Barcelona | C | 1 | 22.31 | 509890 | 292722 | 0.277 | 0.666 | 18/25 | 8/10 | 0.498 |
| Barcelona | B | 1 | 22.31 | 512776 | 295608 | 0.262 | 0.656 | 20/25 | 9/10 | 0.523 |
| Cádiz | A | 1 | 17.54 | 56220 | 0 | 0.267 | 0.671 | 5/13 | 4/5 | 0.632 |
| Cádiz | D5 | 1 | 17.54 | 75123 | 18903 | 0.299 | 0.702 | 3/13 | 4/5 | 0.625 |
| Cádiz | D8 | 1 | 17.54 | 75123 | 18903 | 0.299 | 0.702 | 3/13 | 4/5 | 0.625 |
| Cádiz | C | 1 | 17.54 | 75123 | 18903 | 0.299 | 0.702 | 3/13 | 4/5 | 0.625 |
| Cádiz | B | 1 | 17.54 | 80475 | 24255 | 0.282 | 0.686 | 3/13 | 4/5 | 0.633 |
| León | A | 0 | 0.6 | 1813 | 0 | 0.227 | 0.606 | 4/7 | 6/10 | 0.637 |
| León | D5 | 0 | 4.44 | 16963 | 15150 | 0.213 | 0.581 | 2/7 | 2/10 | 0.658 |
| León | D8 | 0 | 7.52 | 22545 | 20732 | 0.25 | 0.631 | 1/7 | 2/10 | 0.598 |
| León | C | 0 | 13.67 | 42997 | 41184 | 0.301 | 0.687 | 1/7 | 2/10 | 0.637 |
| León | B | 0 | 14.87 | 60829 | 59016 | 0.254 | 0.647 | 2/7 | 4/10 | 0.622 |
| Madrid | A | 0 | 13.49 | 466868 | 0 | 0.259 | 0.662 | 19/19 | 6/6 | 0.394 |
| Madrid | D5 | 0 | 13.55 | 376926 | -89942 | 0.243 | 0.64 | 18/19 | 6/6 | 0.392 |
| Madrid | D8 | 0 | 13.55 | 376926 | -89942 | 0.243 | 0.64 | 18/19 | 6/6 | 0.392 |
| Madrid | C | 0 | 14.82 | 491236 | 24368 | 0.272 | 0.676 | 18/19 | 5/6 | 0.386 |
| Madrid | B | 0 | 14.79 | 536344 | 69476 | 0.253 | 0.657 | 18/19 | 5/6 | 0.388 |

«Coste frente a A»: cuántas personas más suman los desvíos de todos los distritos respecto a la población objetivo
(negativo: menos que A). Polsby-Popper y convexidad: 1 = forma ideal; más alto, menos anguloso.

## Lectura

- D5 y D8 recogen gran parte de la mejora de naturalidad con mucho menos coste en población. Badajoz: partidos
  judiciales partidos 13 (A) → 5 (D5) → 3 (D8 y C), con desvío máximo 1,4 % → 4,4 % → 7,7 % → 14,7 %. León: 4 → 2 → 1 → 1.
  Asturias: 8 → 3 ya con D5 (6,9 %: ningún candidato bajó del 5 %, gana el de menor exceso).
- En Cádiz los tres coinciden (el mejor de C ya está por debajo del 5 % en los distritos dentro de tolerancia).
- En Madrid y Barcelona la ganancia sigue siendo pequeña: casi todos los partidos judiciales quedan partidos por el
  tamaño de las ciudades. En Madrid el mapa vigente ya roza el 13,5 % y D5/D8 no pueden bajarlo, pero reducen la suma
  de desvíos frente a A.

## Distritos urbanos minúsculos en superficie (no es un error)

En los mapas hay distritos de capital que apenas se ven. Son **núcleos cerrados**: todas sus secciones están en un
solo municipio, mayor que la población objetivo, que la regla municipal permite partir por secciones. Tienen la misma
población que los demás (dentro de tolerancia), pero en la densidad de una ciudad:

| Territorio | Distrito más pequeño | A | C | B |
|---|---|---|---|---|
| León | núcleo de León | 24,6 km², 112.547 hab. | 19,6 km², 103.170 hab. | 16,3 km², 95.466 hab. |
| Asturias | núcleo de Gijón | 13,4 km², 129.398 hab. | 5,6 km², 135.305 hab. | (Oviedo) 82,5 km², 107.474 hab. |
| Badajoz | núcleo de Badajoz | 194,5 km², 111.238 hab. | 192,7 km², 94.686 hab. | 105,5 km², 109.823 hab. |
| Cádiz | núcleo de Cádiz / Jerez | 12,3 km², 112.077 hab. | 12,3 km², 112.077 hab. | (Jerez) 12,0 km², 108.579 hab. |
| Madrid | distrito de Madrid capital | 2,9 km², 104.808 hab. | 3,4 km², 114.245 hab. | 2,7 km², 101.144 hab. |
| Barcelona | distrito de Hospitalet / Barcelona | 2,6 km², 115.995 hab. | 2,6 km², 100.189 hab. | 2,5 km², 102.508 hab. |

Ya existen en A (el motor actual); en B y C a veces encogen más, por tres razones:

1. **Los partidos judiciales y las comarcas se cuentan por municipio.** La capital está entera en un partido y una
   comarca, así que cortar *dentro* de la ciudad no parte ninguna demarcación: es el corte «gratis».
2. **La frontera cortada se mide en kilómetros.** Entre secciones urbanas la frontera es de cientos de metros; entre
   pueblos, de kilómetros. Minimizarla lleva los cortes al casco urbano.
3. **B y C no miran la población hasta el final.** El distrito urbano puede bajar hasta el borde de la tolerancia
   (León B: −14 %), con solo las secciones más densas; las secciones periféricas de la capital van con el distrito
   que rodea la ciudad y que así conserva enteros sus partidos judiciales.

Las reglas lo validan todo (contigüidad, municipio que solo se parte si supera el objetivo, tolerancia). D5/D8, al
limitar el desvío, devuelven al núcleo urbano parte de esa población (León D5: 29,5 km², 116.314 hab.).

## Cómo se ha hecho

Laboratorio sobre las secciones del INE (seccionado 2023, sha256 del .shp en `datos/naturalidad/MANIFEST.json`) y el
mapa vigente: los municipios que no se pueden partir son una pieza; las cadenas parten del mapa vigente y cada paso se
valida con las reglas completas del motor nuevo. 20 cadenas de 300 pasos por función; D5 y D8 eligen entre los mismos
estados que recorren las cadenas de C. Reproducible bit a bit con el mismo entorno (`RESULTADO.json` lleva la huella y
las versiones de shapely/GEOS, geopandas y gerrychain): con otra GEOS cambia alguna frontera y, con ella, las cadenas
(Badajoz, Madrid y Barcelona difieren de la primera entrega, #651). Tiempos por territorio: de 1 a 6 minutos.
Código: `ddd_motor2/naturalidad*.py`.
