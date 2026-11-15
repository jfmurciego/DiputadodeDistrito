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
