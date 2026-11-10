# Naturalidad en las autonómicas: C y D8 frente a A (2.ª parte)

Mismo laboratorio, reglas y semillas que en las 52 provincias del Congreso (`../README.md`), ahora en las 12
autonómicas cuyo mapa vigente cumple el núcleo. Castilla y León, Extremadura y Principado de Asturias, en `../t202/README.md`.

**Objetivo por circunscripción.** Donde el contrato reparte escaños por provincia o isla (`province_districts`:
Canarias, Castilla-La Mancha, Cataluña, Comunidad Valenciana, Galicia y País Vasco), el desvío de cada distrito se
mide contra la población de su circunscripción dividida por su cuota, y las cadenas cortan cada par de distritos
por la mitad de su población. Con una sola circunscripción es el objetivo regional de siempre.

## Resumen (12 autonómicas)

| | A (vigente) | D8 | C |
|---|---|---|---|
| Partidos judiciales partidos | 216 de 237 | 208 | 207 |
| Comarcas agrarias partidas | 128 de 146 | 121 | 118 |
| Polsby-Popper medio | 0,263 | 0,277 | 0,288 |
| Distritos fuera de tolerancia | 166 | 113 | 113 |
| Suma de desvíos (personas) | 3.166.115 | 2.972.911 | 2.994.713 |

- Aquí lo que más mejora es la población, no las demarcaciones: C y D8 reducen los distritos fuera de tolerancia
  en 10 de 12 autonómicas (Comunidad de Madrid, de 26 a 6; Castilla-La Mancha, de 5 a 1; Melilla, de 6 a 0) y
  empatan en Galicia y La Rioja.
- Partidos judiciales y comarcas agrarias: C mejora en 5 y empata en 7; D8 mejora en 3 y empata en 9. Con distritos
  de 30.000 a 60.000 habitantes casi todos los partidos judiciales quedan partidos de todos modos.
- Siguen fuera de tolerancia, sobre todo, municipios enteros mayores que el objetivo que ni el mapa vigente ni las
  cadenas llegan a partir (p. ej. Pozuelo de Alarcón, 88.504 hab., o Lérida, 72.480), comarcas rurales por debajo
  del objetivo y, en Melilla, secciones grandes para distritos de unos 3.400 habitantes.

## Dónde C o D8 empeoran algo frente a A

| Territorio | Función | Qué empeora frente a A |
|---|---|---|
| Cataluña (autonómicas) | D8 | Polsby-Popper medio 0.233 → 0.232 |
| Melilla (autonómicas) | D8 | Polsby-Popper medio 0.404 → 0.366 |

Ninguna autonómica se queda sin candidato válido.

## Tabla

| Territorio | Función | Fuera de tolerancia | Desvío máx. % | Suma de desvíos (personas) | Coste frente a A (personas) | Polsby-Popper medio | Convexidad media | Partidos judiciales partidos | Comarcas agrarias partidas | Cohesión de movilidad |
|---|---|---|---|---|---|---|---|---|---|---|
| Canarias (autonómicas) | A | 22 | 67.9 | 343041 | 0 | 0.261 | 0.67 | 15/18 | 0/0 | 0.151 |
| Canarias (autonómicas) | D8 | 15 | 65.23 | 223385 | -119656 | 0.275 | 0.683 | 15/18 | 0/0 | 0.133 |
| Canarias (autonómicas) | C | 15 | 65.23 | 223385 | -119656 | 0.275 | 0.683 | 15/18 | 0/0 | 0.133 |
| Cantabria (autonómicas) | A | 9 | 72.3 | 65100 | 0 | 0.259 | 0.685 | 7/7 | 5/6 | 0.107 |
| Cantabria (autonómicas) | D8 | 6 | 72.3 | 67581 | 2480 | 0.277 | 0.694 | 7/7 | 5/6 | 0.115 |
| Cantabria (autonómicas) | C | 6 | 72.3 | 70041 | 4940 | 0.278 | 0.699 | 6/7 | 4/6 | 0.116 |
| Castilla-La Mancha (autonómicas) | A | 5 | 40.86 | 191095 | 0 | 0.175 | 0.567 | 27/31 | 26/32 | 0.45 |
| Castilla-La Mancha (autonómicas) | D8 | 1 | 14.06 | 130297 | -60798 | 0.231 | 0.617 | 20/31 | 21/32 | 0.431 |
| Castilla-La Mancha (autonómicas) | C | 1 | 14.06 | 130297 | -60798 | 0.231 | 0.617 | 20/31 | 21/32 | 0.431 |
| Cataluña (autonómicas) | A | 33 | 67.9 | 794078 | 0 | 0.233 | 0.629 | 45/49 | 31/35 | 0.309 |
| Cataluña (autonómicas) | D8 | 32 | 67.9 | 767781 | -26297 | 0.232 | 0.627 | 45/49 | 31/35 | 0.309 |
| Cataluña (autonómicas) | C | 32 | 67.9 | 772817 | -21261 | 0.234 | 0.629 | 45/49 | 31/35 | 0.31 |
| Navarra (autonómicas) | A | 11 | 67.04 | 83096 | 0 | 0.281 | 0.698 | 5/5 | 7/7 | 0.062 |
| Navarra (autonómicas) | D8 | 8 | 67.04 | 77409 | -5687 | 0.301 | 0.709 | 5/5 | 7/7 | 0.068 |
| Navarra (autonómicas) | C | 8 | 67.04 | 84059 | 962 | 0.309 | 0.72 | 5/5 | 7/7 | 0.066 |
| Comunidad Valenciana (autonómicas) | A | 29 | 69.55 | 617513 | 0 | 0.263 | 0.712 | 33/34 | 22/25 | 0.335 |
| Comunidad Valenciana (autonómicas) | D8 | 27 | 69.55 | 612689 | -4825 | 0.269 | 0.72 | 33/34 | 22/25 | 0.333 |
| Comunidad Valenciana (autonómicas) | C | 27 | 69.55 | 612689 | -4825 | 0.269 | 0.72 | 33/34 | 22/25 | 0.333 |
| Galicia (autonómicas) | A | 6 | 54.8 | 185428 | 0 | 0.203 | 0.597 | 38/45 | 15/15 | 0.227 |
| Galicia (autonómicas) | D8 | 6 | 54.8 | 192665 | 7238 | 0.204 | 0.599 | 37/45 | 14/15 | 0.231 |
| Galicia (autonómicas) | C | 6 | 54.8 | 192665 | 7238 | 0.204 | 0.599 | 37/45 | 14/15 | 0.231 |
| La Rioja (autonómicas) | A | 1 | 41.78 | 21501 | 0 | 0.32 | 0.746 | 3/3 | 6/6 | 0.041 |
| La Rioja (autonómicas) | D8 | 1 | 41.78 | 20275 | -1226 | 0.343 | 0.758 | 3/3 | 6/6 | 0.038 |
| La Rioja (autonómicas) | C | 1 | 41.78 | 22259 | 758 | 0.407 | 0.801 | 3/3 | 4/6 | 0.038 |
| Comunidad de Madrid (autonómicas) | A | 26 | 73.87 | 514781 | 0 | 0.228 | 0.635 | 19/19 | 6/6 | 0.202 |
| Comunidad de Madrid (autonómicas) | D8 | 6 | 73.87 | 558330 | 43548 | 0.258 | 0.676 | 19/19 | 6/6 | 0.187 |
| Comunidad de Madrid (autonómicas) | C | 6 | 73.87 | 558330 | 43548 | 0.258 | 0.676 | 19/19 | 6/6 | 0.187 |
| Melilla (autonómicas) | A | 6 | 74.99 | 31560 | 0 | 0.404 | 0.842 | 1/1 | 0/0 | 0.024 |
| Melilla (autonómicas) | D8 | 0 | 45.04 | 21030 | -10530 | 0.366 | 0.821 | 1/1 | 0/0 | 0.013 |
| Melilla (autonómicas) | C | 0 | 50.0 | 20770 | -10789 | 0.43 | 0.848 | 1/1 | 0/0 | 0.011 |
| País Vasco (autonómicas) | A | 8 | 23.52 | 159105 | 0 | 0.237 | 0.642 | 14/14 | 4/8 | 0.152 |
| País Vasco (autonómicas) | D8 | 6 | 23.52 | 152965 | -6140 | 0.238 | 0.645 | 14/14 | 4/8 | 0.154 |
| País Vasco (autonómicas) | C | 6 | 23.52 | 152965 | -6140 | 0.238 | 0.645 | 14/14 | 4/8 | 0.154 |
| Región de Murcia (autonómicas) | A | 10 | 66.76 | 159817 | 0 | 0.291 | 0.695 | 9/11 | 6/6 | 0.156 |
| Región de Murcia (autonómicas) | D8 | 5 | 66.76 | 148504 | -11312 | 0.332 | 0.728 | 9/11 | 5/6 | 0.168 |
| Región de Murcia (autonómicas) | C | 5 | 66.76 | 154436 | -5380 | 0.328 | 0.723 | 9/11 | 5/6 | 0.172 |

Láminas de Canarias, Galicia y Cataluña en `mapas/`; por distrito en `mapas/DISTRITOS.csv`.
