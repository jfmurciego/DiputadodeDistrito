# T-196 · Batería r3 del motor 2 (71 territorios, D8, N = 10) frente al canónico y al laboratorio T-179

Run 42886114842 de `bateria-motor.yml` (`motor=motor2`, D8, 10 cadenas, entorno de producción: shapely 2.1.1, pandas 2.3.2).
Aceptación SÍ: 71/71 válidos, 0 `FALLO_GENERADOR`, ninguno peor que el canónico, huellas reales correctas. Cada territorio
evalúa 11 candidatos (canónico + 10 cadenas; 60 territorios) o 12 (con exhaustivo; 11 territorios). Datos y cálculo:

- `datos/filas.json`: la fila de `ddd_motor2.competir` de cada job (sacada de los logs por job: los artefactos dan 403 desde la nube).
  `extraer_filas.py` las regenera con `gh` (ids de job en `datos/JOBS_run42886114842.tsv`).
- `analizar.py` → `datos/COMPARACION.csv` y todas las cifras de este informe (solo ficheros versionados, sin red).

## Qué significa «mejora / empata / empeora»

Lo calcula `competir.comparar`: clave de naturalidad del **ganador** frente a la del **canónico**, en este orden:
evaluable, violaciones duras, distritos fuera de tolerancia, exceso sobre el tope del 8 %, demarcaciones partidas
(partidos judiciales + comarcas agrarias), frontera cortada (km), desvío máximo. **Mejora** = la clave del ganador es
estrictamente menor (gana una cadena); **empata** = igual (gana el canónico por desempate); **empeora** no puede darse
porque el canónico compite. Quien decide es la primera componente que difiere: una «mejora» puede ser de población
(menos distritos fuera de tolerancia), de demarcaciones o de forma. La fila solo trae fuera de tolerancia y desvío del
ganador: **no hay en los logs ni los partidos y comarcas ni los fuera de tolerancia del canónico** (están en
`COMPETICION.json`, artefacto no accesible desde la nube), así que aquí no se puede desglosar por qué componente mejora cada territorio.

## Resultado

| Ámbito | Territorios | Mejora | Empata | Empeora | Con más de un distrito: mejora / empata | Gana una cadena | Fuera de tolerancia del ganador |
|---|---|---|---|---|---|---|---|
| Congreso (52) | 52 | 40 | 12 | 0 | 40 / 4 (de 44) | 41 | 7 |
| Autonómicas (19) | 19 | 15 | 4 | 0 | 15 / 2 (de 17) | 16 | 236 |
| Total | 71 | 55 | 16 | 0 | 55 / 6 (de 61) | 57 | 243 |

Los 10 territorios de un solo distrito (Ávila, Ceuta, Melilla, Palencia, Segovia, Soria, Teruel, Zamora en el Congreso;
Ceuta y Melilla autonómicas) empatan siempre. Empatan además Álava, Baleares, Valencia y Zaragoza (Congreso) y País Vasco y Región de Murcia (autonómicas).
(Los 16 empates incluyen 2 donde una cadena iguala la clave del canónico.) Tiempo de competición: 201 min en total (Congreso 109, autonómicas 92),
mediana 130 s por territorio, máximo Castilla y León 628 s; el run entero costó ~502 min de Actions (71 jobs con instalación y entradas).

## Comparación con el laboratorio (T-179, D8 frente a A)

Se compara con `T179_naturalidad_nacional/**/TABLA.csv` (67 territorios con dato; sin dato: Andalucía, Aragón, Ceuta, Illes Balears).
Clave del laboratorio aproximada con las mismas componentes que hay en la tabla (sin el exceso sobre el tope).

**Congreso: reproduce el laboratorio.**
- Fuera de tolerancia: ganador r3 = 7 en los 52; A = 7 y D8 = 6 en el laboratorio. La única diferencia es Las Palmas (1 frente a 0).
- El canónico de r3 coincide con el mapa vigente (A) en el desvío máximo de los 51 territorios del Congreso salvo Las Palmas (65,85 % frente a 41,93 %).
- Mejora en 40 de 44 provincias con más de un distrito (laboratorio: 40 mejora, 3 empata, 1 empeora). Distinto frente: Álava,
  Baleares, Valencia y Zaragoza empatan en r3 y mejoran en el laboratorio; Alicante mejora en r3 y empeora en el laboratorio.
- La cadena ganadora es la misma que en el laboratorio solo en 2 de 54 casos (el laboratorio eligía entre 20 cadenas; aquí entre 10).

**Autonómicas: NO reproduce el laboratorio en población.** En las 15 autonómicas con dato:

| | r3 (ganador) | Laboratorio A (vigente) | Laboratorio D8 |
|---|---|---|---|
| Distritos fuera de tolerancia | 187 | 171 | 115 |

El laboratorio reduce 56 distritos fuera de tolerancia frente a A; r3 queda 16 por encima de A. Por territorio (r3 / D8 laboratorio):
Madrid 21 / 6, Melilla 6 / 0, Castilla-La Mancha 8 / 1, Navarra 14 / 8, Cataluña 41 / 32, Murcia 10 / 5, Canarias 21 / 15,
País Vasco 9 / 6, Cantabria 9 / 6, Castilla y León 4 / 1, Extremadura 1 / 0, Galicia 8 / 6, Asturias 3 / 1, Comunidad Valenciana 31 / 27.
En estos territorios la «mejora» que cuenta r3 (15 de 19) no viene de la población. Causa probable, **no verificada**: el laboratorio de
autonómicas (T-179, 2.ª parte) mide el desvío de cada distrito contra el objetivo de su circunscripción (`province_districts`) y corta cada par
de distritos por la mitad de su población, y el generador `Ponderado` que usa la batería no lo hace en esas autonómicas. Otras diferencias
(shapely 2.1.1 frente a 2.1.2, grafo M03 reconstruido desde fuente, 10 frente a 20 cadenas) no explican por sí solas una diferencia tan grande.

## Límites

- Sin `COMPETICION.json`: no se recalculan partidos judiciales ni comarcas, ni el desglose de la clave, ni los fuera de tolerancia del canónico.
  Para ello hace falta bajar los artefactos del run (el host de descarga está bloqueado en el entorno cloud por defecto).
- La comparación de población frente al laboratorio usa el ganador de r3, no la mejora frente al canónico; en Congreso ambos coinciden con A.
