# Naturalidad en Castilla y León, Extremadura y Principado de Asturias (T-202)

Mismo laboratorio, reglas y semillas que en las demás autonómicas (`../autonomicas/README.md`), con objetivo por
circunscripción donde hay cuotas por provincia. Estas tres necesitaban dos cosas más.

## Castilla y León: el mapa vigente incumple el núcleo (D-66)

El mapa vigente reparte Ávila (59.480 hab.) en tres distritos: uno solo de Ávila y **dos mixtos** (uno de ellos con
una única sección de Ávila). El núcleo admite como máximo un distrito mixto por municipio
(`max_mixed_districts_per_split_municipality: 1`). Por decisión del propietario (D-66):

- **A sigue siendo el mapa vigente**, marcado en la tabla como «incumple el núcleo».
- **C y D8 solo eligen entre mapas válidos.** Las cadenas parten de un «vigente reparado»: la sección de Ávila del
  distrito mixto sobrante pasa al otro distrito mixto de Ávila. Pasarla al distrito urbano rompía la contigüidad.
- **No hay infactibilidad**: la reparación cumple todas las reglas, así que no se propone ninguna excepción en el
  contrato.

## Extremadura y Principado de Asturias: unidades internas

Sus contratos parten los municipios grandes en «unidades internas» conexas (`connected_internal_units`), que se
calculan sobre el grafo M03 de producción. Ese grafo ya no está (los artefactos caducan) y, con el grafo del
laboratorio, la herramienta de producción da trozos distintos: el mapa vigente partiría 23 de ellos en Extremadura.
Por eso el laboratorio usa una aproximación, igual que el motor en lo esencial:

- municipio atómico hasta `atomicity_ratio` × objetivo (1,1 en Extremadura; 1,5 en Asturias), como en producción;
- por encima, cada sección es su propia unidad (y su clave R012): **más fina que los trozos de producción**, así que
  las cadenas pueden cortar dentro de un trozo. Afecta solo a las ciudades grandes (Badajoz, Cáceres, Oviedo, Gijón…).

## Resultado

| Territorio | Función | Fuera de tolerancia | Desvío máx. % | Suma de desvíos (personas) | Coste frente a A (personas) | Polsby-Popper medio | Convexidad media | Partidos judiciales partidos | Comarcas agrarias partidas | Cohesión de movilidad |
|---|---|---|---|---|---|---|---|---|---|---|
| Castilla y León (autonómicas) | A (incumple el núcleo) | 1 | 14.31 | 81005 | 0 | 0.184 | 0.58 | 38/41 | 53/59 | 0.235 |
| Castilla y León (autonómicas) | D8 | 1 | 14.31 | 84841 | 3836 | 0.184 | 0.581 | 37/41 | 52/59 | 0.235 |
| Castilla y León (autonómicas) | C | 1 | 14.31 | 84841 | 3836 | 0.184 | 0.581 | 37/41 | 52/59 | 0.235 |
| Extremadura (autonómicas) | A | 0 | 10.48 | 53726 | 0 | 0.271 | 0.686 | 20/21 | 20/22 | 0.141 |
| Extremadura (autonómicas) | D8 | 0 | 10.23 | 49757 | -3969 | 0.272 | 0.686 | 20/21 | 20/22 | 0.141 |
| Extremadura (autonómicas) | C | 0 | 10.88 | 56934 | 3208 | 0.275 | 0.69 | 20/21 | 20/22 | 0.144 |
| Principado de Asturias (autonómicas) | A | 4 | 37.08 | 53152 | 0 | 0.242 | 0.663 | 18/18 | 10/10 | 0.128 |
| Principado de Asturias (autonómicas) | D8 | 1 | 37.08 | 55380 | 2229 | 0.253 | 0.667 | 17/18 | 8/10 | 0.133 |
| Principado de Asturias (autonómicas) | C | 1 | 37.08 | 66651 | 13499 | 0.283 | 0.686 | 14/18 | 8/10 | 0.114 |

- **Principado de Asturias**: C baja los partidos judiciales partidos de 18 a 14 y las comarcas de 10 a 8, y los
  distritos fuera de tolerancia de 4 a 1; D8, de 18 a 17 y de 4 a 1.
- **Extremadura**: casi empate; D8 reduce la suma de desvíos (53.726 → 49.757) y C mejora algo la forma.
- **Castilla y León**: C y D8 coinciden (37 partidos judiciales partidos frente a 38; 52 comarcas frente a 53) y,
  a diferencia de A, cumplen el núcleo.
- Aparte de la suma de desvíos, ninguna empeora nada frente a A. La suma sube algo: Castilla y León +3.836 personas
  (C y D8), Extremadura +3.208 (C), Principado de Asturias +13.499 (C) y +2.228 (D8); `mapas/EMPEORA.md`.
