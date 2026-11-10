# T-180 · ¿Cuántas cadenas hacen falta en la competición? (71 territorios)

Fecha: 2026-11-10. Motor 2 (`ddd_motor2/competir.py`, orquestador 1.1.0, función A): canónico M05 7.4.4 + N cadenas
GerryChain de producción (`m05_gerrychain_strategy`, ReCom), juzgadas por el núcleo de reglas. Entradas de la batería
T-132 (`bateria_motor.py entradas`, adquisición oficial; ENTRADAS.json con sha256) en local; no se lanzó nada en Actions.

**Semilla.** La semilla pública definitiva de la tabla maestra (D-61/6) **no está aplicada** en `ddd_motor2/semilla.py`
(no aparece en el repo). Se usó la vigente: `ddd-semilla-publica/1` (semilla.py 1.0.1, ancla D-50: sha256 del padrón y
del seccionado del contrato + territorio). Las semillas son anidadas (semilla_i depende solo de i), así que **una sola
tanda de 20 cadenas** basta: el ganador con N cadenas se calcula a posteriori entre el canónico y las cadenas 1..N.

**Método.** `analizar_cadenas.py` (este directorio). N = 1, 2, 3, 5, 10, 15, 20.
- Función A (vigente): violaciones duras, distritos fuera de tolerancia, desvío máximo, ECM, huella.
- Función B (naturalidad, `naturalidad_competicion.py`), a posteriori sobre los mismos candidatos: violaciones duras,
  fuera de tolerancia, partidos judiciales + comarcas agrarias partidos, frontera cortada (km), desvío máximo.
- N de saturación: el menor N de la rejilla a partir del cual el ganador ya no cambia (0 = gana el canónico). Cuenta
  todo cambio de ganador, también por ECM, centésimas de desvío o solo por el desempate de huella con métricas
  iguales, aunque no mejore el número de distritos fuera de tolerancia (p. ej. Congreso Cáceres: gana una cadena en
  N = 15 con las mismas métricas que el canónico, `A_mejora_20` = False, saturación 15).

## Resultado (71 territorios)

Todos los candidatos válidos (21/21 en los 71). Agregado (`todos_71/AGREGADO.csv`):

| N | A: mejoran al canónico | A: fuera de tolerancia (canónico 270) | A: saturados | B: mejoran | B: saturados |
|---|---|---|---|---|---|
| 1 | 18 | 217 | 42 | 44 | 22 |
| 2 | 22 | 210 | 44 | 49 | 25 |
| 3 | 23 | 206 | 45 | 51 | 28 |
| 5 | 26 | 204 | 48 | 51 | 34 |
| 10 | 28 | 203 | 53 | 52 | 45 |
| 15 | 29 | 202 | 61 | 53 | 60 |
| 20 | 30 | 201 | 71 | 53 | 71 |

- Con A, 41 de 71 nunca mejoran al canónico. La mejora en distritos fuera de tolerancia está casi toda en las comunidades
  (Cataluña 53 → 27, Navarra 24 → 12, Andalucía 20 → 15, Madrid 24 → 21).
- De 270 a 201 distritos fuera de tolerancia hay 69 de mejora: N = 5 da 66 (96 %); N = 10, 67 (97 %). De 10 a 20 solo
  se ganan 2 (Cataluña 28 → 27; Castilla y León 1 → 0, que además baja 4,1 puntos de desvío máximo).
- N de saturación con A (`todos_71/TERRITORIOS.csv`): 0 en 40; 1 en Congreso Alicante y Guadalajara; 2 en Baleares y
  Madrid; 3 en C. Valenciana; 5 en Cantabria, Congreso Barcelona y La Coruña; 10 en 5 territorios; 15 en 8; 20 en 10.
  Percentiles: p50 0, p75 10, p90 20. Los que saturan en 15–20 ganan casi siempre solo ECM o centésimas de desvío.
  El único caso sustancial es Castilla y León (arriba).
- Con B el ganador se estabiliza más tarde (p50 10, p75 15): a igualdad de tolerancia casi siempre aparece un plan algo
  «más natural»; partidos + comarcas partidos bajan de 1.075 (N = 1) a 1.010 (5), 998 (10) y 994 (20).
- El desvío máximo de las comunidades lo marca un distrito ya fuera de tolerancia (p. ej. un municipio exento), por eso
  apenas se mueve. La métrica útil es el número de distritos fuera de tolerancia.

## Anidamiento y reproducibilidad

- Anidamiento: que el ganador con 10 no sea peor que con 5 es **cierto por construcción**. El ganador es el mínimo sobre
  un conjunto que crece, porque las semillas 1..5 son las mismas en una tanda de 5 y en una de 20. La columna
  `*_monotono` solo comprueba la coherencia de las tablas; la prueba real es la de reproducibilidad.
- Reproducibilidad: Congreso Badajoz repetido con `--cadenas 5` en otra carpeta. Las 5 semillas son las 5 primeras de la
  tanda de 20, y los 6 candidatos (canónico + 5) dan la misma huella de plan y el mismo sha256 de composición M06 (6/6).
  Artefactos: `datos/reproducibilidad/congreso_badajoz/COMPETICION.json` y `todos_71/REPRODUCIBILIDAD.csv`.

## Datos versionados y cómo regenerar

`datos/competicion/<t>/COMPETICION.json` lleva todos los candidatos con semilla, estado, métricas, huellas y tiempos
(~40 KB por territorio; 2,7 MB en total). `datos/NATURALIDAD_B.csv` lleva, por candidato, los partidos y comarcas
partidos y la frontera cortada, con el sha256 del seccionado INE usado. Con ellos,
`analizar_cadenas.py --out datos --naturalidad-b datos/NATURALIDAD_B.csv` regenera AGREGADO, CURVA, TERRITORIOS y
TIEMPOS sin la tanda ni la geometría. Lo comprobé en local (no hay prueba en la CI): ejecutar
`python docs/ESTUDIOS/T180_CADENAS/analizar_cadenas.py --out docs/ESTUDIOS/T180_CADENAS/datos --naturalidad-b
docs/ESTUDIOS/T180_CADENAS/datos/NATURALIDAD_B.csv --salida /tmp/x` y `cmp /tmp/x/<f>.csv todos_71/<f>.csv` para los
cuatro ficheros: iguales. Las composiciones M06 de cada candidato no se
versionan; su sha256 está en COMPETICION.json. Un territorio sin B sale con `B_estado` ≠ OK en TERRITORIOS.csv y queda
fuera de la curva B (en esta tanda, 71/71 OK).

## Tiempos y coste (medidos en los 71)

Medidos en local con 3–4 territorios a la vez en 4 CPU (contención incluida). `todos_71/TIEMPOS.csv` por candidato.
- Por cadena (media por territorio): de 4 s a 329 s (Madrid autonómica). Cataluña 283 s, Congreso Madrid 229 s,
  Murcia 228 s, C. Valenciana 187 s.
- CPU acumulada en los 71, con el canónico (0,6 h) incluido: **N = 5: 5,9 h; N = 10: 10,9 h; N = 20: 20,8 h**. La
  proyección de la entrega parcial (5,8 / 10,9 / 21,0 h, tiempos de T-132 × 0,96) queda sustituida por lo medido.
- El 44 % del tiempo de cada cadena se va en rehacer unidades, M04 y la comprobación de la semilla, que son idénticos en
  todas las cadenas del territorio; el M05 GerryChain es el 38 %. Hacerlos una vez por territorio reduciría el coste a
  cerca de la mitad (cambio de `generadores.py`; no se ha hecho aquí).

## Recomendación

**Recomendación PROVISIONAL (D-67): N = 10 por edición** con la función A. Da el 97 % de la mejora en distritos fuera de tolerancia (67 de 69) y
28 de los 30 territorios que llegan a mejorar con 20. Pasar a 20 casi duplica el coste (10,9 → 20,8 h) por 2
distritos. N = 5 cuesta la mitad, pero deja sin mejorar 4 territorios más (26 frente a 30). Esta curva es con las cadenas de
A (GerryChain de producción). B y D8 usan cadenas ponderadas distintas (`naturalidad_competicion`, generador
«ponderado»), que no se han medido aquí: la selección con B sobre estos candidatos satura más tarde (p75 15), pero que
B o D8 necesiten 15–20 cadenas es una conjetura, a medir con la batería D8 arreglada (T-196).
