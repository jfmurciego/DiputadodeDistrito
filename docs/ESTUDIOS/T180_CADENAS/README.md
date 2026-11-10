# T-180 · ¿Cuántas cadenas hacen falta en la competición? (entrega parcial: 20 representativos)

Fecha: 2026-11-10. Motor 2 (`ddd_motor2/competir.py`, orquestador 1.1.0): canónico M05 7.4.4 + N cadenas GerryChain de
producción (`m05_gerrychain_strategy`, ReCom), juzgadas por el núcleo de reglas. Entradas de la batería T-132
(`bateria_motor.py entradas`, adquisición oficial; ENTRADAS.json con sha256) en local; no se lanzó nada en Actions.

**Semilla.** La semilla pública definitiva de la tabla maestra (D-61/6) **no está aplicada** en `ddd_motor2/semilla.py`
(no aparece en el repo). Se usó la vigente: `ddd-semilla-publica/1` (semilla.py 1.0.1, ancla D-50: sha256 del padrón y
del seccionado del contrato + territorio). Las semillas son anidadas (semilla_i depende solo de i), así que **una sola
tanda de 20 cadenas** basta: el ganador con N cadenas se calcula a posteriori entre el canónico y las cadenas 1..N.

**Método.** `analizar_cadenas.py` (este directorio). N = 1, 2, 3, 5, 10, 15, 20.
- Función A (vigente): violaciones duras, distritos fuera de tolerancia, desvío máximo, ECM, huella.
- Función B (naturalidad, `naturalidad_competicion.py`), a posteriori sobre los mismos candidatos: violaciones duras,
  fuera de tolerancia, partidos judiciales + comarcas agrarias partidos, frontera cortada (km), desvío máximo.
- N de saturación: el menor N de la rejilla a partir del cual el ganador ya no cambia (0 = gana el canónico).

Territorios (20): Congreso Soria, Teruel, Segovia, León, Badajoz, Cádiz, Zaragoza, Alicante, Valencia, Madrid y
Barcelona; La Rioja, Asturias, Navarra, Cantabria, Madrid, Cataluña, Andalucía, Islas Baleares y Canarias.

## Resultado (20 representativos)

Todos los candidatos válidos (21/21 en los 20). Agregado (`representativos_20/AGREGADO.csv`):

| N | A: mejoran al canónico | A: fuera de tolerancia (canónico 172) | A: saturados | B: mejoran | B: saturados |
|---|---|---|---|---|---|
| 1 | 6 | 133 | 11 | 12 | 5 |
| 2 | 7 | 130 | 13 | 13 | 5 |
| 3 | 7 | 128 | 13 | 14 | 5 |
| 5 | 8 | 126 | 15 | 14 | 7 |
| 10 | 10 | 125 | 17 | 15 | 12 |
| 15 | 10 | 124 | 19 | 15 | 16 |
| 20 | 10 | 124 | 20 | 15 | 20 |

- Con A, 10 de 20 nunca mejoran al canónico (los K = 1 y Congreso Madrid, Zaragoza, León, Cádiz, La Rioja, Asturias,
  Canarias). La mejora está en las comunidades con muchos distritos fuera de tolerancia (Cataluña 53 → 27,
  Navarra 24 → 12, Andalucía 20 → 15, Madrid 24 → 21) y en Badajoz, Valencia, Alicante, Barcelona, Cantabria y Baleares.
- Saturación A por territorio (`TERRITORIOS.csv`): 0 en 10; 1 Alicante; 2 Madrid y Baleares; 5 Cantabria y
  Barcelona; 10 Badajoz y Valencia; 15 Andalucía y Cataluña; 20 Navarra. De N = 10 a 20 solo se gana **1 distrito**
  fuera de tolerancia en total (125 → 124) y el desvío máximo medio no cambia (0,3417).
- Con B el ganador tarda más en estabilizarse (mediana 10; 8 territorios siguen cambiando entre 10 y 20): la
  naturalidad sigue mejorando con más cadenas porque, a igualdad de tolerancia, casi siempre hay un plan algo «más
  natural».
- El desvío máximo de las comunidades lo marca un distrito ya fuera de tolerancia (p. ej. un municipio exento), por
  eso apenas se mueve: la métrica útil es el número de distritos fuera de tolerancia.

## Anidamiento y reproducibilidad

- Anidamiento: que el ganador con 10 no sea peor que con 5 es **cierto por construcción** (el ganador es el mínimo
  sobre un conjunto que crece, porque las semillas de 1..5 son las mismas en una tanda de 5 y en una de 20); la columna
  `*_monotono` solo comprueba la coherencia de las tablas. La prueba real es la de reproducibilidad.
- Reproducibilidad: Congreso Badajoz repetido con `--cadenas 5` en otra carpeta: las 5 semillas son las 5 primeras
  de la tanda de 20 y los 6 candidatos (canónico + 5) dan la misma huella de plan y el mismo sha256 de composición
  M06 (6/6). Artefactos: `datos/reproducibilidad/congreso_badajoz/COMPETICION.json` y `representativos_20/REPRODUCIBILIDAD.csv`.

## Datos versionados y cómo regenerar

`datos/competicion/<t>/COMPETICION.json` (todos los candidatos con semilla, estado, métricas, huellas y tiempos; ~40 KB
por territorio) y `datos/NATURALIDAD_B.csv` (partidos + comarcas partidos y frontera cortada de cada candidato, con el
sha256 del seccionado INE usado). Con ellos, `analizar_cadenas.py --out datos --naturalidad-b datos/NATURALIDAD_B.csv`
regenera AGREGADO, CURVA, TERRITORIOS y TIEMPOS idénticos byte a byte sin la tanda ni la geometría (comprobado).
Las composiciones M06 de cada candidato no se versionan (su sha256 está en COMPETICION.json). Un territorio sin B sale
con `B_estado` ≠ OK en TERRITORIOS.csv y fuera de la curva B.

## Tiempos y coste

Medidos con 4 territorios a la vez en 4 CPU (contención incluida). `TIEMPOS.csv` por candidato.
- Por cadena (media por territorio): de 7 s (Soria) a 329 s (Madrid autonómica); Cataluña 283 s, Congreso Madrid 229 s.
- 20 representativos, CPU acumulada: N = 5: 2,9 h; N = 10: 5,4 h; N = 20: 10,3 h (canónico incluido, 0,4 h).
- Proyección a los 71 (tiempo por cadena de T-132, `T132_BATERIA_MOTOR/BANCO.csv`, por territorio, multiplicado por
  0,96 = media medida aquí / media de T-132 en los mismos 20; el canónico, como fracción medida de una cadena): **N = 5: 5,8 h; N = 10: 10,9 h;
  N = 20: 21,0 h** de CPU. Pendiente de sustituir por lo medido cuando acaben los 51 restantes.
- El 44 % del tiempo de cada cadena es rehacer unidades + M04 + comprobación de semilla, idénticos en todas las cadenas
  del territorio; el M05 GerryChain es el 38 %. Hacerlos una vez por territorio reduciría el coste a cerca de la mitad
  (cambio de `generadores.py`; no se ha hecho aquí).

## Recomendación provisional (se confirmará con los 71)

**N oficial = 10 por edición.** Con 10 se alcanza el 98 % de la mejora (47 de 48 distritos) en distritos fuera de tolerancia (125 frente a
124 con 20) y 17/20 territorios ya están saturados con A; con 5 quedan sin mejorar 2 territorios (Badajoz y
Valencia: mejoran el desvío desde la cadena 6-7) y 1 distrito fuera de tolerancia más. Pasar a 20 duplica el coste por 1 distrito. Si la función oficial acabara siendo B, 10 sigue dejando
cambios (mediana de saturación 10, p75 15): entonces, 15–20.

## Pendiente

Los 51 territorios restantes (misma tanda, en curso) y la tabla con los 71.
