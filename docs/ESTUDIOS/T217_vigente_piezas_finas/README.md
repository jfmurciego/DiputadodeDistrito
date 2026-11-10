# T-217 + T-218 · El vigente compite y piezas finas con la atomicidad del contrato

Prueba en sesión: venv con `requirements.lock` y las cadenas instaladas con `--no-deps`, `PYTHONHASHSEED=0`, D8 con
10 cadenas, entradas desde fuente INE y la clave de #693. La salida completa está en `salida_sesion.txt`.

## Qué cambia

- **T-217.** El mapa publicado (`datos/composicion/<t>.csv`) se monta sobre las filas del canónico, con la población
  de la entrada, y se juzga con el núcleo.
  - Si cumple el núcleo, compite como candidato «vigente» y la mitad final de las semillas públicas parte de él.
    El ganador nunca es peor que un vigente válido, por construcción.
  - Si no cumple el núcleo o no es representable (otras secciones, o parte un municipio atómico), no compite y el
    resumen dice por qué.
- **T-218 (D-79).** Fuera del Congreso, la unidad de la cadena es la sección en los municipios de más de
  `municipality_atomicity_limit_ratio` × objetivo (el contrato los deja partir), y el municipio entero en el resto.
  - No cambian suelo, techo, K, tolerancia ni la regla de distritos mixtos.
  - No se aplica con `partitioning connected_internal_units` (Extremadura, Principado de Asturias).

## Resultado (fuera de tolerancia del contrato; aceptación frente al vigente PUBLICADO)

| Territorio | Vigente publicado | Reparación (D-66) | Canónico | Ganador r3 | Ganador ahora | ¿Nunca peor que el vigente? | Unidades (M04 → finas) |
|---|---|---|---|---|---|---|---|
| Navarra | 11, válido | no hace falta | 24 | 14 | **11** (cadena desde el vigente) | **sí** (mejora en la cola de la clave) | 288 → 442 |
| Comunidad de Madrid | 26, válido | no hace falta | 24 | 21 | **14** (cadena desde el vigente) | **sí** | 269 → 3759 |
| Cataluña | 33, R-NUCLEO (núcleo 41) | 3 secciones (6775 hab.) al distrito del núcleo → válido, 33 | 53 | 41 | **31** | **sí** | 997 → 3359 |
| Castilla y León | 2, R-MUN-MIXTOS (Ávila 05019) | 1 unidad (1918 hab.) a otro distrito de Ávila → válido | 2 | 4 | **2** | **sí** (mejora en la cola de la clave) | 2279 → 3157 |

**Cataluña.** El vigente reparte el núcleo cerrado 41 del canónico (municipio 08200, 66 271 hab.; 6775 hab. en otro
distrito), porque los núcleos salen del M04 del canónico y el vigente se hizo con otro M04. La reparación mínima
devuelve esas 3 secciones al distrito del núcleo; el vigente reparado es válido, compite y da semilla.

**Reparación (`generadores.reparar`).** Es determinista, y cada paso arregla una infracción sin crear otra:
- R-NUCLEO: el núcleo pasa al distrito con más población suya, y las unidades ajenas a ese distrito, a una vecina;
- R-MUN-MIXTOS: como el «vigente reparado» del laboratorio.

Si no hay reparación, el vigente no compite y se informa. La aceptación compara siempre con el vigente **publicado**.
