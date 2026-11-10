# T-211 · Por qué el Ponderado de la competición no baja los fuera de tolerancia del laboratorio en las autonómicas

Prueba en sesión (venv con `requirements.lock` + cadenas `--no-deps` como `bateria-motor.yml`, `PYTHONHASHSEED=0`,
D8, 10 cadenas, entradas desde fuente INE). Salida completa en `salida_sesion.txt`; scripts en `scripts/`.

## Resultado

1. **Reproduce r3 bit a bit** (misma `huella_resultado` que el run 42886114842) en Comunidad de Madrid, Navarra,
   País Vasco y Canarias. El entorno (shapely 2.1.1) y la reconstrucción del grafo M03 no explican la diferencia.
2. **La hipótesis no se cumple.** Madrid, Navarra, Melilla y Murcia tienen una sola circunscripción. Donde hay varias
   (País Vasco: 3; Canarias: 8), `natural_desde_m06` ya da a cada unidad el objetivo de su circunscripción
   (0 unidades sin objetivo) y `cadena` ya corta por la mitad del par (`_bip_mitad`): el Ponderado y la elección
   D8 ya miden como el laboratorio.
3. **Causas medidas:**
   - **(a) El laboratorio parte municipios que el contrato declara atómicos.** `naturalidad_competicion.unidades_de`
     solo deja entero el municipio de hasta 1 × objetivo; el contrato lo deja entero hasta
     `municipality_atomicity_limit_ratio` × objetivo, que da cada contrato (1,75 en casi todas las autonómicas, 1,5 en la
     Comunidad Valenciana, 1,15 en la mayoría de provincias del Congreso). El D8 del laboratorio parte 6 en
     Madrid (códigos INE 28013, 28014, 28022, 28045, 28047 y 28080; de 55 000 a 73 000 hab.), 2 en Navarra (31097 y 31907), 7 en Canarias (el fichero lista los 6 primeros), 4 en
     Castilla-La Mancha, 2 en Murcia; en total, 16 territorios (`atomicos_laboratorio.txt`). La competición los
     respeta (unidad «M» del M04). Parte de la mejora del laboratorio no es alcanzable con el contrato.
   - **(b) Granularidad.** El laboratorio trabaja por secciones dentro de los municipios grandes (Madrid: 4150
     unidades); la competición, con las unidades M04 (Madrid: 269; 90 internas, todas ≥ 0,5 × objetivo; Pamplona:
     15 unidades de unos 14 000 hab., casi un distrito cada una). Con 300 pasos, las cadenas de Madrid ven de 3 a 7
     planes distintos (el laboratorio, de 103 a 143 en Navarra y de 191 a 224 en Madrid: `salida_sesion.txt`): apenas se mueven.
   - **(c) Punto de partida.** El laboratorio parte del mapa publicado (Navarra: «GerryChain 50», 11 fuera de
     tolerancia); la competición, del canónico M05 7.4.4 (Navarra 24, Madrid 24). Las cadenas bajan a 14 y 21.
   - **(d) La clave D8 no contaba como el contrato (corregido en esta PR).** Con varias circunscripciones, el primer
     término de la clave eran los fuera de tolerancia contra el objetivo de cada circunscripción. El contrato, el
     núcleo (`reglas.evaluar`) y el M04 (`outside_target_tolerance`) los cuentan contra el objetivo regional, sin
     exenciones. Por eso r3 dejó ganar mapas con más fuera de tolerancia que el canónico: Aragón 0→2, Castilla-La
     Mancha 5→8, Castilla y León 2→4, Galicia 6→8 (en `CANDIDATOS.csv` de T-196, el ganador empata con el canónico
     en `clave_fuera_tol`: 1/1, 5/5, 1/1, 6/6). No venía de los exentos (ninguna de las dos medidas los descuenta)
     ni del tope (`exceso_tope` igual al del canónico en los cuatro): venía del objetivo.
     **Exenciones:** el recuento del contrato (`reglas.evaluar`) es sobre todos los distritos; las exenciones solo
     relajan el suelo y el tope del 8 % solo ordena, no entra en el recuento. En Aragón, Castilla-La Mancha, Castilla
     y León y Galicia el contrato no tiene exentos. En Canarias, 14 de los 20 o 21 distritos fuera de tolerancia
     contienen una partición exenta: el recuento del contrato los cuenta (`salida_sesion.txt`, `scripts/exentos.py`).
     **Medidas cruzadas:** los dos recuentos no van siempre en el mismo sentido. En Canarias, el canónico tiene 21
     por circunscripción y 20 por el objetivo regional; el ganador de r3, 20 y 21. La cifra publicada puede subir o
     bajar según el candidato.
   - **(e) Sin frontera en la batería (no corregido).** El grafo M03 que rehace la batería no trae `shared_border_m`
     (0 de 11 290 aristas en Madrid). La frontera cortada vale 0 km en todos los candidatos de r3 y el recargo por
     frontera corta es el mismo en todas las aristas: el término de forma de D8 no actúa.

## Cambio

- `ddd_motor2/naturalidad_clave.py` 1.1.0: en la competición (`natural_desde_m06`), el primer término de la clave es
  el recuento del contrato (objetivo regional). El resto de la clave (tope del 8 %, demarcaciones, frontera y
  desvío) sigue midiéndose por circunscripción. El laboratorio no cambia.
- `ddd_motor2/competicion.py` 1.3.1: el `fuera_tolerancia` publicado es ese mismo recuento; los valores por
  circunscripción quedan en `extra.metricas_circunscripcion`.
- El Congreso (una sola circunscripción) no cambia: las HUELLAS_FIJAS siguen iguales.

## Antes y después en los 4 territorios (D8, 10 cadenas, fuera de tolerancia del contrato)

Antes: r3 (`CANDIDATOS.csv` de T-196). Después: la competición en sesión con esta PR (el canónico sale igual que en r3).

| Territorio | Canónico | Ganador r3 (antes) | Ganador ahora | Clave del ganador ahora (fuera, exceso, demarcaciones) |
|---|---|---|---|---|
| aragon | 0 (r3 0) | ponderado-s677079344: 2 | ponderado-s1768655224: 0 | 0, 0.0332, 35 |
| castilla_la_mancha | 5 (r3 5) | ponderado-s214103641: 8 | ponderado-s547221014: 5 | 5, 0.0227, 53 |
| castilla_y_leon | 2 (r3 2) | ponderado-s999727098: 4 | ponderado-s999727098: 2 | 2, 0.0383, 88 |
| galicia | 6 (r3 6) | ponderado-s1167476498: 8 | ponderado-s1167476498: 6 | 6, 0.0394, 51 |

## Opciones (decisión del Planificador o del propietario; nada de esto está hecho)

- (e) Que el M03 de la batería traiga `shared_border_m` (en la batería, el M03 sale del motor de producción: no es de este turno).

- (a) Que el laboratorio respete `municipality_atomicity_limit_ratio` (naturalidad_competicion 1.6.0) y rehacer
  T-179 en las autonómicas: dará la cifra comparable de verdad.
- (b) Cadenas a nivel de sección dentro de las unidades internas del M04: toca la atomicidad de la unidad M04, que
  no se cambia sin decisión del propietario.
- (c) Más pasos o partir también del mapa publicado como candidato inicial: más coste por territorio.
