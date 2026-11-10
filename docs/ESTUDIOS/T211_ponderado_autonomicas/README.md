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
     `municipality_atomicity_limit_ratio` × objetivo (1,75 en las autonómicas). El D8 del laboratorio parte 6 en
     Madrid (códigos INE 28013, 28014, 28022, 28045, 28047 y 28080; de 55 000 a 73 000 hab.), 2 en Navarra (31097 y 31907), 7 en Canarias, 4 en
     Castilla-La Mancha, 2 en Murcia; en total, 16 territorios (`atomicos_laboratorio.txt`). La competición los
     respeta (unidad «M» del M04). Parte de la mejora del laboratorio no es alcanzable con el contrato.
   - **(b) Granularidad.** El laboratorio trabaja por secciones dentro de los municipios grandes (Madrid: 4150
     unidades); la competición, con las unidades M04 (Madrid: 269; 90 internas, todas ≥ 0,5 × objetivo; Pamplona:
     15 unidades de unos 14 000 hab., casi un distrito cada una). Con 300 pasos, las cadenas de Madrid ven de 3 a 7
     planes distintos (el laboratorio, más de 100 en Navarra): apenas se mueven.
   - **(c) Punto de partida.** El laboratorio parte del mapa publicado (Navarra: «GerryChain 50», 11 fuera de
     tolerancia); la competición, del canónico M05 7.4.4 (Navarra 24, Madrid 24). Las cadenas bajan a 14 y 21.
   - **(d) Medida publicada (corregida en esta PR).** Con varias circunscripciones, COMPETICION.json y la batería
     publicaban los fuera de tolerancia contra el objetivo regional, pero elegían con los de la circunscripción
     (País Vasco: elige con 8 y publica 9; Canarias: el ganador tiene 20, y se publicaban 21). La tabla de T-196
     comparaba, en esas autonómicas, cifras medidas de otra forma.

## Cambio

`ddd_motor2/competicion.py` 1.3.1: con C/D5/D8 y varias circunscripciones, `fuera_tolerancia` y `desvio_max`
publicados salen de los desvíos de la clave; los regionales quedan en `extra.metricas_regionales`. No cambia la
elección ni la huella (las HUELLAS_FIJAS siguen iguales); el Congreso tampoco cambia (una sola circunscripción).
No se toca el generador: lo que pedía la tarea ya lo hacía.

## Opciones (decisión del Planificador o del propietario; nada de esto está hecho)

- (a) Que el laboratorio respete `municipality_atomicity_limit_ratio` (naturalidad_competicion 1.6.0) y rehacer
  T-179 en las autonómicas: dará la cifra comparable de verdad.
- (b) Cadenas a nivel de sección dentro de las unidades internas del M04: toca la atomicidad de la unidad M04, que
  no se cambia sin decisión del propietario.
- (c) Más pasos o partir también del mapa publicado como candidato inicial: más coste por territorio.
