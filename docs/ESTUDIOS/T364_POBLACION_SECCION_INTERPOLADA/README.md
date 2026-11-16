# T-364 · Población por sección: interpolación y ajuste municipal (D-128)

Versión: 1.1.0 de `herramientas/poblacion_seccion_historica.py` (1.0.0 en `legacy/herramientas/`) · 2026-11-16 · Solo cálculo; sin ejecuciones ni publicación.
Sustituye la regla de relleno de D-126 (año más cercano). Entrada de T-365 (distritos por época).

## Regla
1. «.» (no publicado) en el Atlas 30832 del año de la elección → **interpolación lineal** entre el año anterior y el siguiente más próximos con dato
   de ESA misma sección (redondeo half-up entero) → `interpolada`; solo dato en un lado → año más cercano con dato → `mas_cercana`; ninguno → `sin_dato`.
   `..` = «.»; `""` = sección inexistente ese año (no se estima ni aparece).
2. **Ajuste proporcional por municipio** (solo elecciones con fuente Atlas): residuo = población oficial del municipio − suma de secciones de dato publicado.
   Con residuo > 0 las secciones ESTIMADAS del municipio se reescalan para sumar exactamente el residuo (restos mayores; empate: sección ascendente) y
   quedan `ajustada=sí`; las de dato publicado no se tocan. Si el residuo ya iguala la suma estimada: `cuadra`, nada cambia. **Aviso y sin ajuste**
   (`informe_municipios.csv`, `estado=aviso_*`; `--estricto` sale con 2) si residuo ≤ 0, el municipio tiene `sin_dato`, o no figura en la fuente oficial.
3. Informe por provincia sobre población estimada (interpolada + más cercana, ya ajustada); MARCA si > 1 % o si hay `sin_dato`.

## Fuente oficial del municipio (medida)
INE tabla 29005 «Cifras oficiales del padrón por municipio» (padrón, 1 de enero; Sexo = Total; 1996-2025):
`https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/29005.csv` · 27 348 525 bytes · sha256 `8d568dbb14ba1e6cd9d5d3f7db6516842806ce3ba4bdf52938482d2adca50635`
(`SHA256SUMS.txt` de esta carpeta; servicios.ine.es no se usó). Años usados: 2015, 2016, 2019, 2020 (el de la fuente Atlas de cada elección);
`""` en la tabla = municipio inexistente ese año (19, 13, 7 y 7) → sin oficial.
**2011-11 no se ajusta**: la fuente es el Censo 2011 (1-nov-2011), no el padrón a 1 de enero; fichero oficial de población municipal censal: NO VERIFICADO.
En la descarga acreditada esa elección no tiene «.» (nada que estimar).

## Uso y salida
```
python -I herramientas/poblacion_seccion_historica.py --atlas <30832.csv> --censo <indicadores_seccion_censal_csv.zip> --oficial <29005.csv> \
  --sumas docs/ESTUDIOS/T357_PADRON_SECCION_2011_2020/SHA256SUMS.txt docs/ESTUDIOS/T364_POBLACION_SECCION_INTERPOLADA/SHA256SUMS.txt --salida <dir>
```
**Interfaz para T-365 (estable)**: un CSV por elección, `poblacion_seccion_<AAAA-MM>.csv` (UTF-8, `\n`, orden por sección), columnas:
`sección` (10 dígitos INE) · `población` (entero; vacío si `sin_dato`) · `origen` (`dato`/`interpolada`/`mas_cercana`/`sin_dato`) ·
`ajustada` (`sí`/`no`) · `años_fuente` (`dato`: año de la fuente; `interpolada`: `AAAA-AAAA`; `mas_cercana`: `AAAA`; `sin_dato`: vacío).
**T-365 debe ejecutar la herramienta con `--estricto`**: si algún municipio de cualquier elección tiene aviso (residuo ≤ 0, `sin_dato` u ausente del
oficial) sale con código 2 y NO escribe las tablas por elección (solo los informes); así una tabla presente significa «0 avisos» (ejecución actual: 0).
Sin `--estricto` las tablas se escriben igualmente y los avisos solo constan en `informe_municipios.csv`/`municipios_aviso`.
Además `informe_provincias.csv` (en esta carpeta) e `informe_municipios.csv` (fuera del repo). Salida determinista (dos ejecuciones idénticas byte a byte).

## Resultado (ejecución del 2026-11-16, fuentes con sha256 de T-357 verificado)
| Elección | Secciones | Interpoladas | Más cercanas | Ajustadas | Sin dato | Población | Estimada | Prov. MARCA | Municipios (ajustados/cuadran/aviso) | Desajuste medio por municipio ajustado |
|---|---|---|---|---|---|---|---|---|---|---|
| 2011-11 | 35 917 | 0 | 0 | 0 | 0 | 46 575 200 | 0 | 0 | sin ajuste (censo) | — |
| 2015-12 | 36 215 | 0 | 1 320 | 1 265 | 0 | 46 019 896 | 126 724 (0,28 %) | 12 | 1 237 / 55 / 0 | 12,9 personas |
| 2016-06 | 36 191 | 319 | 1 292 | 1 549 | 0 | 45 930 326 | 516 662 (1,12 %) | 12 | 1 273 / 62 / 0 | 24,9 personas |
| 2019-04 | 36 309 | 167 | 1 261 | 1 329 | 0 | 46 801 502 | 110 568 (0,24 %) | 12 | 1 314 / 99 / 0 | 7,6 personas |
| 2019-11 | 36 333 | 0 | 0 | 0 | 0 | 46 849 376 | 0 | 0 | — | — |

Cero avisos de municipio. 2015-12 no tiene interpoladas porque 2015 es el primer año del Atlas (no hay dato anterior). El desajuste relativo medio por
provincia está en `informe_provincias.csv` (`desajuste_medio_pct`). Sevilla 2016-06: 270 interpoladas + 2 más cercanas, 11 municipios ajustados, 21,22 % estimado (MARCA);
La Rioja (26) pasa a 1,0005 % tras el ajuste (MARCA marginal). Las MARCA siguen sin publicarse sin decisión del propietario.
(Las cifras de población difieren de T-358 porque el ajuste reescala las estimadas al padrón oficial.)

Tablas completas (fuera del repo, reproducibles con el comando de arriba; el propietario decide R2): sha256
2011-11 `45aa3552592a8819beab26b2a885551fbe1e8ccba0ec68ac3ccbb7621f0496a3` · 2015-12 `2410b02c0bd6ea297f38dead86193e1d62991ac713417b84d93206d431ba61c5` ·
2016-06 `663c18af448f26cc2e13ffaa42812d73dab67e0f3d2b8734ff77a234aeca8aa4` · 2019-04 `9103d1b62fa05bfc1d3de454d9db10c7b2dad184740241e5bb66ef9df1458771` ·
2019-11 `8968bea2ba87630c0d98d3fc5165d09b95d9fc5184c6f5a5cb7fc70dd78f3c18` · informe_provincias `db2af10f0bee2a8ded732d33b14e959c30b84f2b9315025def0eb00234bd683c` ·
informe_municipios `fb444fc5f67c891397bb5bd63dd904632f08819fef0dfd66f8c9d61c57edcb40`.

Nota: `docs/ESTUDIOS/T358_POBLACION_SECCION_RELLENO/causa_relleno.py` es histórico: solo corre con la herramienta 1.0.0 (en `legacy/`); con la 1.1.0 aborta con un aviso.
