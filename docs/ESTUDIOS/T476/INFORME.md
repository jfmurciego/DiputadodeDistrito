# T-476 · Datos abiertos 2: votos por partido y distrito (sin publicar)

Generado por `herramientas/datos_abiertos_votos.py` (`generar`, `--comprobar`) a partir de ficheros de git con sha256
(`votos/MANIFEST.json`). Salida fuera de `datos_abiertos/`: la P40 actual no la borra ni la publica.

## Qué contiene `votos/`
| Fichero | Contenido |
|---|---|
| `votos_partido_distrito.csv` | `territorio, eleccion, distrito, partido, votos` (distrito 1..K, como la ficha pública; solo votos > 0) |
| `doble_vuelta.csv` | por distrito y escenario (`dv_base`, `dv_A`, `dv_B`) las columnas de `doble_vuelta.py`, con bloques de 2026-11-25 y alias de `alias_partidos_generales.csv` |
| `composicion_distrito.csv` | `territorio, distrito, poblacion, secciones` del mapa vigente (`datos/composicion/runs/`) |
| `no_construible.csv` | `territorio, eleccion, motivo` de lo que no se construye |
| `MANIFEST.json` | sha256 de entradas, configuración y salidas; resumen |

## Alcance construido
- 2023-07: los 52 nac vigentes (run M08 del INDEX; en nac17, nac29, nac33 y nac38 hay dos runs en git, se usa el del INDEX).
- 2011-11, 2015-12, 2016-06, 2019-04 y 2019-11: solo en 11 nac (nac01, 05, 07, 34, 40, 42, 44, 49, 50, 51, 52), cuyo mapa
  de secciones→distrito del histórico (T-83) es idéntico al vigente (la herramienta lo comprueba sección a sección).

## No construible desde git (205 filas = 41 nac × 5 elecciones)
Histórico sobre un mapa de distritos anterior al vigente; reagregarlo exige los votos por sección (espejo T-89), que
no están en git. Se listan con motivo en `no_construible.csv`; no se inventan.

## Comprobaciones (`--comprobar`, 0 errores)
- sha256 de entradas y salidas contra el manifiesto, y de las de 2023 contra `datos/resultados/MANIFEST.json` y `MANIFEST_RUNS.json`.
- Cuadre con el BOE por provincia: ningún partido casado supera al oficial; defecto ≤ 10 % (es el voto CERA, que el ZIP
  por mesa no trae). Defecto máximo por elección: 2011-11 1,0 %; 2015-12 0,9 %; 2016-06 1,2 %; 2019-04 0,9 %; 2019-11 2,1 %;
  2023-07 7,4 % (el de VOX en Orense).
- Ganador 2023 = el de `datos/resultados/<nac>.csv` en los 52 nac. Aviso (no error): en nac46 distrito 23 los votos del
  ganador de la tabla difieren un 16,1 % de los del run (el run reparte votos de secciones del ZIP sin M06, T-103/T-104; ver
  `desajustes.json`). El ganador coincide.
- Doble vuelta: ningún partido con votos queda sin casar en la tabla de bloques (`sin_casar_doble_vuelta` vacío).

## Contraste con la Universidad de Valencia (criterio 4)
No alcanzable desde la nube: `www.uv.es` devuelve 403 del proxy (27-11). Queda pendiente para quien tenga acceso.

## Siguiente paso (integración con la P40, no hecho por la víspera de la regeneración)
`generar_datos_abiertos.py` borra con `rmtree` toda subcarpeta de `datos_abiertos/` que no sea un territorio y
`--materializar` copia el paquete entero. Para publicar: versión 1.3.2 (legacy) que conserve `datos_abiertos/votos/`
y la excluya de `--materializar` hasta que se apruebe la publicación; mover entonces la salida de esta herramienta allí.
