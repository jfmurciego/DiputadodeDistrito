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

## Resultado (fuera de tolerancia del contrato)

| Territorio | Vigente | Canónico | Ganador r3 | Ganador ahora | ¿Nunca peor que el vigente? | Unidades (M04 → finas) |
|---|---|---|---|---|---|---|
| Navarra | 11 (válido, compite) | 24 | 14 | **11** (cadena desde el vigente) | **sí** (mejora en la cola de la clave) | 288 → 442 |
| Comunidad de Madrid | 26 (válido, compite) | 24 | 21 | **14** (cadena desde el vigente) | **sí** | 269 → 3759 |
| Cataluña | 33 (**no cumple el núcleo**: R-NUCLEO, núcleo 41) | 53 | 41 | **38** | **no: 38 frente a 33** | 997 → 3359 |
| Castilla y León | no cumple el núcleo (R-MUN-MIXTOS, Ávila 05019) | 2 | 4 | 2 | no aplica (el vigente no es válido) | 2279 → 3157 |

**Cataluña.** El vigente reparte el núcleo cerrado 41 del canónico (municipio 08200, 38 secciones, 66 271 hab.):
pone 59 496 hab. en un distrito y 6775 en otro. Los núcleos cerrados salen del M04 del canónico, y el vigente se hizo
con otro M04. Juzgado con sus propios núcleos sería válido, con 33 fuera de tolerancia. Como no compite y las cadenas
solo parten del canónico, el ganador (38) queda 5 por encima del vigente.

## Opciones para Cataluña (decisión del Planificador; no hecho)

1. Vigente reparado: pasar al distrito mayoritario las secciones del núcleo que el vigente deja fuera (aquí 6775 hab.),
   juzgarlo de nuevo y, si es válido, que compita y dé semilla. Mismo criterio que el «vigente reparado» del
   laboratorio (D-66).
2. Juzgar el vigente con sus propios núcleos: es incoherente con el resto de candidatos.
3. Aceptarlo e informarlo.
