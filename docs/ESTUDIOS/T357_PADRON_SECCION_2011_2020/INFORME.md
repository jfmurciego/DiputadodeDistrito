# T-357 — Población por sección censal 2011-2020 y casado con seccionado y votos

Versión: 1.0.0
Fecha: 2026-11-15
Estado: medido (solo lectura; sin ejecuciones ni publicación). Decisión D-125 (opción A).

Todo medido en la sesión cloud el 2026-11-15. Descargas hechas de verdad desde `www.ine.es` (HTTP 200; `servicios.ine.es`
rechazado por el proxy, no hace falta). Bytes, sha256, fecha y comandos de las 8 descargas del INE en `SHA256SUMS.txt` (medidos en esta sesión, sin contraste externo). No se sube ninguna descarga: solo hashes y `resultados.json` (salida de `medir_casado.py`,
que reproduce todas las cifras). Observatorio: los 520 ficheros usados coinciden en bytes y sha256 con `orchestracion/fuente_nazioenbehatokia.json` (script `contrastar_observatorio.py`, salida en `contraste_observatorio.txt`: 520 contrastados, 0 discrepancias).

## 1. Qué población por sección existe

| Fuente INE | URL oficial | Bytes (Content-Length) | sha256 | Periodo |
|---|---|---|---|---|
| Censo 2011, indicadores por sección (CSV, `t1_1` = población) | https://www.ine.es/censos2011_datos/indicadores_seccion_censal_csv.zip | 4 575 186 | `305a19f11b87d4e13d2ea4267774b9b0e3a69a3b7b1ff8e483aad90867628fe7` | 1-nov-2011 (censo, no padrón) |
| Cartografía Censo 2011 | https://www.ine.es/censos2011_datos/cartografia_censo2011_nacional.zip | 64 103 930 | `d0151e0cc126695933bc30a922c803ab09af03fdfb622238b22f769c7a883acc` | secciones a 1-nov-2011 |
| Atlas de Distribución de Renta, tabla 30832 «Indicadores demográficos» (indicador «Población»), CSV | https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/30832.csv | 445 592 835 (sin Content-Length, chunked: tamaño descargado) | `37716cba8cda50a492f52e2bae91a1c543bafb4263110e5aa5da18107ef68311` | 2015…2024 (una columna por año) |
| Padrón continuo por sección anterior a 2015 | — | — | — | **No existe** en las páginas del INE revisadas (ver §4) |

El Atlas usa **una sola lista de 37 229 secciones para todos los años** (el mismo conjunto en los 10 periodos): no es el seccionado
de cada año, es una lista única. En cada año las 37 229 filas son: valor, «.» o vacío (`atlas_30832_clasificacion_filas` en `resultados.json`). 2019: 34 881 con valor, 1 428 «.» y 920 vacías; 2020: 36 333 con valor y 896 vacías, ninguna «.». Significado de «.» (dato no publicado, probable secreto estadístico) y de vacío (sección inexistente ese año): HIPÓTESIS, no verificadas en metodología. Provincias con más «.» en 2019 (códigos INE): 19 Guadalajara 182, 09 Burgos 171, 42 Soria 118, 05 Ávila 100, 44 Teruel 96, 50 Zaragoza 88, 37 Salamanca 87, 40 Segovia 79. Secciones con valor: 2015 = 34 895, 2016 = 34 580, 2019 = 34 881, 2020 = 36 333. La referencia exacta («1 de enero» o 31-dic del año) NO VERIFICADA. Suma nacional con valor: 2015 = 45 893 172, 2016 = 45 413 664, 2019 = 46 690 934, 2020 = 46 849 376.

## 2. Seccionado del INE por elección (descargado)

| Elección | Seccionado | URL | Bytes | sha256 | Campo |
|---|---|---|---|---|---|
| 2011-11 | 2012 (1-ene-2012) | https://www.ine.es/prodyser/cartografia/seccionado_2012.zip | 63 966 805 | `772ad76b84e1b3bb9293a5595d2ccafa06f21a3a58ccc96a9ec5dadd99e46c4a` | CUSEC |
| 2015-12 | 2015 | …/seccionado_2015.zip | 63 901 341 | `50dda58ed4afb57c7f1f38e6b6b8150768efaa225bfc3a523b9c210a2a218c03` | CUSEC |
| 2016-06 | 2016 | …/seccionado_2016.zip | 64 043 263 | `3410af763bfe58d1b0f9c0d0038cbdd6417e0f3f6d0fce6a3e70bef64c84b3e1` | CUSEC |
| 2019-04 | 2019 | …/seccionado_2019.zip | 72 059 641 | `656119dadadb57ef3fa9d20a8ba33399fe606e553c9fef3fc338786e52fae967` | CUSEC |
| 2019-11 | 2020 | …/seccionado_2020.zip | 65 901 199 | `07544bb49256e9e9f290b6f459a0a833e69c97900eb840c3f5bbe863914ede6e` | CUSEC |

`orchestracion/fuentes_r2.json` solo trae seccionado_2023/2024/2025: estos cinco no están en R2 (hay que archivarlos si se sigue con A).

## 3. Casado (códigos de sección de 10 dígitos; «A vs B»: casan / sobran en A / faltan en A)

| Elección | Seccionado INE | Votos Observatorio | Seccionado vs votos | Población (mejor periodo) | Población vs seccionado | Población vs votos |
|---|---|---|---|---|---|---|
| 2011-11 | 35 978 | 35 957 | 35 944 / 34 / 13 | Censo 2011: 35 917 secciones con valor | 35 873 / 105 / 44 | 35 885 / 72 / 32 |
| 2015-12 | 36 229 | 36 217 | 36 202 / 27 / 15 | Atlas 2015: 34 895 con valor | 34 868 / 1 361 / 27 | 34 883 / 1 334 / 12 |
| 2016-06 | 36 215 | 36 193 | 36 190 / 25 / 3 | Atlas 2016: 34 580 | 34 546 / 1 669 / 34 | 34 549 / 1 644 / 31 |
| 2019-04 | 36 317 | 36 317 | 36 317 / 0 / 0 | Atlas 2019: 34 881 | 34 851 / 1 466 / 30 | 34 851 / 1 466 / 30 |
| 2019-11 | 36 309 | 36 302 | 36 294 / 15 / 8 | Atlas 2020: 36 333 (sin «.») | 36 281 / 28 / 52 | 36 266 / 36 / 67 |

Geometría del Observatorio (`geo/sekzioak/<año>`) casa al 100 % con el seccionado INE del mismo año en las cinco (columna `ine_vs_geo` de `resultados.json`).
Otros periodos del Atlas por elección (2017, 2018, 2021) en `resultados.json`. Muestras de códigos que no casan, también.

## 4. Límites

- Sin población por sección anterior a 2015 salvo el Censo 2011 (1-nov-2011, no padrón). No se encontró padrón por sección 2011-2014 en `ine.es`; NO VERIFICADO que no exista en otro sitio del INE (no se rastreó INEbase entero).
- La lista de secciones del Atlas es única para todos los años: se casa por código, pero una sección que cambió de límites entre años no es la misma geometría (el 2020 trae 82 códigos que el seccionado 2019 no tiene).
- Periodo de referencia exacto del Atlas y causa de los vacíos: NO VERIFICADOS (arriba).

## Conclusiones

1. 2019-11: opción A viable con el Atlas 2020: sin «.», pero 28 de las 36 309 secciones del seccionado 2020 y 36 de las 36 302 de votos quedan sin valor (hay que cubrirlas).
2. 2019-04: seccionado y votos casan al 100 %, pero la población del Atlas 2019 deja 1 466 secciones vacías (≈4 %, rurales): hace falta Atlas 2020 (sin «.»; casa 36 251 de 36 317) o rellenar los vacíos; decisión del propietario.
3. 2015-12 y 2016-06: seccionado y votos casan (≥99,9 %), pero la población del Atlas 2015/2016 tiene ~1 300-1 700 secciones vacías: opción A solo con relleno o con otra fuente; no se ha encontrado otra.
4. 2011-11: solo Censo 2011 (nov-2011; trae valor en las 35 917 secciones, pero 105 secciones del seccionado 2012 no aparecen en él): serviría como población «de la época» pero no es padrón.
5. Ninguna elección casa al 100 % entre las tres fuentes salvo seccionado-votos de 2019-04; las diferencias (decenas de códigos) requieren una regla de reconciliación antes de generar distritos.
6. Cualquier uso exige archivar en R2 los cinco seccionados, el CSV 30832 y el ZIP del Censo con estos sha256.
