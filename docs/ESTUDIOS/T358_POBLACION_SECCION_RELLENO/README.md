# T-358 · Población por sección con relleno (D-126)

Versión: 1.0.0 · Fecha: 2026-11-15 · Solo cálculo; sin ejecuciones ni publicación.

Herramienta: `herramientas/poblacion_seccion_historica.py`. Fuentes (rutas locales, sha256 contra
`docs/ESTUDIOS/T357_PADRON_SECCION_2011_2020/SHA256SUMS.txt`; el CSV 30832 pesa 445 MB y no va al repo):

```
python -I herramientas/poblacion_seccion_historica.py --atlas <30832.csv> --censo <indicadores_seccion_censal_csv.zip> \
  --sumas docs/ESTUDIOS/T357_PADRON_SECCION_2011_2020/SHA256SUMS.txt --tabla <tabla.csv> --informe informe_provincias.csv
```

Elecciones → fuente: 2011-11 Censo 2011 (t1_1); 2015-12 Atlas 2015; 2016-06 Atlas 2016; 2019-04 Atlas 2019; 2019-11 Atlas 2020.
Relleno: misma sección, año del Atlas más cercano con dato (empate: el anterior), marcado en `origen`/`año_fuente_relleno`.

Criterio de marcadores del CSV 30832 (medido en la descarga acreditada):
- `.` = no publicado → se rellena. `..` (18 filas: 17 en 2022, 1 en 2024; no estaba en T-357) → se trata como `.`.
- `""` (comillas literales; 8 774 filas de sección en total) = sección inexistente ese año → NO se rellena y no entra en la elección.
  (El valor «vacío» de T-357 es en el fichero real `""`; hipótesis de significado sin verificar con metodología INE.)

## Salida (ejecución del 2026-11-15 sobre las fuentes con sha256 acreditado)

| Elección | Secciones | Rellenadas | Sin dato | Población | Población rellenada | Provincias MARCA (>1 %) |
|---|---|---|---|---|---|---|
| 2011-11 | 35 917 | 0 | 0 | 46 575 200 | 0 | 0 |
| 2015-12 | 36 215 | 1 320 | 0 | 46 012 253 | 119 081 (0,26 %) | 12 |
| 2016-06 | 36 191 | 1 611 | 0 | 45 916 954 | 503 290 (1,10 %) | 11 |
| 2019-04 | 36 309 | 1 428 | 0 | 46 798 561 | 107 627 (0,23 %) | 11 |
| 2019-11 | 36 333 | 0 | 0 | 46 849 376 | 0 | 0 |

`informe_provincias.csv` (sha256 en la ejecución: `644e5cdbd335b559ddba7eddba664888f616fb9c8b58dc9b0c5f6ff45b293b99`) trae por
provincia secciones, población, % rellenado y `MARCA`. Una provincia MARCA no se publica sin decisión del propietario.

Tabla completa por sección (180 965 filas, 5,4 MB; no va al repo, el propietario decide si se archiva en R2):
sha256 `6be9b9435dbcc36b6501a69363e31614d1059f45d2deadab5c04357198e09baf`, reproducible con el comando de arriba.

Límites: el universo de cada elección es el de la fuente (no el seccionado ni los votos): el casado con seccionado y votos
(T-357 §3) queda fuera de esta tarea. Los ids de sección son los códigos INE de 10 dígitos; la provincia, sus 2 primeros dígitos.

## Sevilla (41) en 2016-06: 20,9 % rellenado (403 106 de 1 927 762 personas)

Medido en el CSV 30832 (sha256 acreditado), sin interpretar la causa: en el periodo 2016 Sevilla tiene 272 secciones con «.»
(1 068 con valor, 64 vacías); en 2015, 2017, 2018, 2019 y 2020 ninguna tiene «.». Es dato real del Atlas, concentrado en ese año:
174 de ellas son del municipio 41091 (Sevilla capital, 174 de 526 secciones con dato o «.») y 98 de otros 10 municipios
(41004: 29, 41038: 15, 41039: 14, 41095: 11, …). Se rellenan 270 con 2015 y 2 con 2017.

## Revisión de #832

- `leer_atlas` ya no descarta líneas: una línea del indicador «Población» con formato inesperado o con sección/periodo no válidos
  lanza `ErrorFuente` (filas de municipio/distrito, otros indicadores y cabecera se ignoran por diseño). Las fuentes reales pasan sin error y la salida es idéntica.
- Una provincia con alguna sección `sin_dato` (población 0 en el denominador, nº en `secciones_sin_dato`) se marca `MARCA`; hoy 0 provincias lo tienen en las cinco elecciones.

## Causa del relleno alto (pedida por el Planificador): «.» real del Atlas, no cruce de códigos

Reproducible: `python -I docs/ESTUDIOS/T358_POBLACION_SECCION_RELLENO/causa_relleno.py <30832.csv> <seccionado_2015.zip> <seccionado_2016.zip> <seccionado_2019.zip> <SHA256SUMS.txt> causa_relleno_provincias.csv`
(sha256 de las 4 fuentes verificado; salida `causa_relleno_provincias.csv`, sha256 `d1ac35e2e8766803801b4ffad5c3482fba61c7f5dd27e054185f59650f4bd0ab`).
Lista de provincias MARCA con % y población rellenada: `informe_provincias.csv` (filtrar `marca=MARCA`); causa por provincia en `causa_relleno_provincias.csv`.

| Elección | Secciones rellenadas | Con «.» en el Atlas del año | Código existe en el seccionado del año | Código NO existe en el seccionado |
|---|---|---|---|---|
| 2015-12 | 1 320 | 1 320 | 1 316 | 4 |
| 2016-06 | 1 611 | 1 611 | 1 609 | 2 |
| 2019-04 | 1 428 | 1 428 | 1 428 | 0 |

Toda sección rellenada trae «.» en el Atlas de ese año (por construcción del criterio) y el 99,7-100 % existe con el mismo código en el
seccionado del año: el relleno es «.» del INE, no un cruce mal hecho. Sevilla 2016: 272 secciones, 270 con código en el seccionado 2016
y 2 sin él; tamaño medio rellenado 1 482 personas (máx. 2 864): no son secciones pequeñas; patrón: 174 en el municipio 41091 y 98 en otros 10; sin interpretar el motivo del «.» (no verificado en metodología INE).
Aparte, secciones del seccionado que no entran en la tabla (el Atlas del año las deja vacías o no las lista; ni se rellenan ni cuentan): 2015-12: 9 vacías + 36 no listadas; 2016-06: 53 + 7; 2019-04: 38 + 0 (por provincia en `causa_relleno_provincias.csv`). Es un hueco de cobertura distinto del relleno, a decidir por el propietario.
