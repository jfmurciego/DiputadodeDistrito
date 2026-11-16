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

## Provincias MARCA por elección (tabla generada de `informe_provincias.csv` y `causa_relleno_provincias.csv`)

(a) = «.» en el Atlas del año y código EXISTE en el seccionado del año; (b) = rellenada cuyo código NO existe en el seccionado del año. «No figura en el Atlas» no puede darse en una rellenada (solo se rellenan las «.» del Atlas del año); las no listadas están en `causa_relleno_provincias.csv` (columna `seccionado_fuera_de_tabla_*`).

| Elección | Prov. | Secc. rellenadas | Población rellenada | % rellenado | (a) | (b) | Municipio con más rellenadas (secc.) |
|---|---|---|---|---|---|---|---|
| 2015-12 | 05 | 87 | 5 080 | 3.1306 | 87 | 0 | 05015 (1) |
| 2015-12 | 09 | 158 | 8 306 | 2.3309 | 158 | 0 | 09001 (1) |
| 2015-12 | 14 | 6 | 8 017 | 1.0243 | 5 | 1 | 14030 (6) |
| 2015-12 | 16 | 73 | 3 907 | 1.9487 | 73 | 0 | 16001 (1) |
| 2015-12 | 18 | 8 | 12 525 | 1.3769 | 7 | 1 | 18022 (8) |
| 2015-12 | 19 | 174 | 8 108 | 3.2517 | 174 | 0 | 19001 (1) |
| 2015-12 | 34 | 69 | 3 903 | 2.4041 | 69 | 0 | 34001 (1) |
| 2015-12 | 37 | 76 | 5 064 | 1.5151 | 76 | 0 | 37004 (1) |
| 2015-12 | 40 | 72 | 3 640 | 2.3666 | 72 | 0 | 40002 (1) |
| 2015-12 | 42 | 114 | 4 718 | 5.3405 | 114 | 0 | 42003 (1) |
| 2015-12 | 44 | 90 | 4 902 | 3.6353 | 90 | 0 | 44001 (1) |
| 2015-12 | 49 | 27 | 1 808 | 1.0091 | 27 | 0 | 49002 (1) |
| 2016-06 | 05 | 90 | 5 463 | 3.4287 | 90 | 0 | 05015 (1) |
| 2016-06 | 09 | 161 | 8 690 | 2.4551 | 161 | 0 | 09001 (1) |
| 2016-06 | 16 | 71 | 3 648 | 1.8493 | 71 | 0 | 16001 (1) |
| 2016-06 | 19 | 180 | 8 876 | 3.5486 | 180 | 0 | 19001 (1) |
| 2016-06 | 34 | 72 | 4 287 | 2.6582 | 72 | 0 | 34001 (1) |
| 2016-06 | 37 | 78 | 5 318 | 1.6041 | 78 | 0 | 37004 (1) |
| 2016-06 | 40 | 76 | 4 152 | 2.7179 | 76 | 0 | 40002 (1) |
| 2016-06 | 41 | 272 | 403 106 | 20.9106 | 270 | 2 | 41091 (174) |
| 2016-06 | 42 | 116 | 4 974 | 5.6844 | 116 | 0 | 42003 (1) |
| 2016-06 | 44 | 92 | 5 158 | 3.8600 | 92 | 0 | 44001 (1) |
| 2016-06 | 49 | 27 | 1 808 | 1.0253 | 27 | 0 | 49002 (1) |
| 2019-04 | 05 | 100 | 6 289 | 4.0106 | 100 | 0 | 05015 (1) |
| 2019-04 | 09 | 171 | 9 705 | 2.7498 | 171 | 0 | 09001 (1) |
| 2019-04 | 16 | 78 | 4 362 | 2.2353 | 78 | 0 | 16001 (1) |
| 2019-04 | 19 | 182 | 8 830 | 3.4074 | 182 | 0 | 19001 (1) |
| 2019-04 | 22 | 33 | 2 649 | 1.2064 | 33 | 0 | 22036 (1) |
| 2019-04 | 34 | 76 | 4 487 | 2.8368 | 76 | 0 | 34001 (1) |
| 2019-04 | 37 | 87 | 6 077 | 1.8549 | 87 | 0 | 37004 (1) |
| 2019-04 | 40 | 79 | 4 298 | 2.8190 | 79 | 0 | 40002 (1) |
| 2019-04 | 42 | 118 | 5 150 | 5.8627 | 118 | 0 | 42003 (1) |
| 2019-04 | 44 | 96 | 5 459 | 4.1184 | 96 | 0 | 44001 (1) |
| 2019-04 | 49 | 32 | 2 383 | 1.4034 | 32 | 0 | 49002 (1) |

Total (b) en provincias MARCA: 4. Causa del «.» en el INE: NO DETERMINADO (el CSV no la da).
### Sevilla-2016: qué es (medido)

Las 272 secciones «.» en 2016 tienen valor en 2015 y 2017 en el mismo CSV del Atlas (que usa una única lista de códigos para todos los años) en 270 casos,
y esos 270 códigos existen en el seccionado 2015 y en el 2016. Por tanto NO es desajuste de códigos en 270: el INE dejó «.» en el Atlas 2016 para esas
secciones (patrón: 174 en el municipio 41091 y 98 en otros 10). Los 2 restantes (4106003007, 4109505012): código ausente del seccionado 2015 y 2016, presente en el 2019,
vacío en el Atlas 2015 y con valor en 2017 (sección nueva entre 2016 y 2019): se rellenan con 2017. Motivo del «.»: NO DETERMINADO.
