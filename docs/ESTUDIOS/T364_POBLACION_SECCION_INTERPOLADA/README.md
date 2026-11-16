# T-364 · Población por sección: interpolación y ajuste municipal (D-128)

Versión: 1.1.0 de `herramientas/poblacion_seccion_historica.py` (1.0.0 en `legacy/herramientas/`) · 2026-11-16 · Solo cálculo; sin ejecuciones ni publicación.
Sustituye la regla de relleno de D-126 (año más cercano). Entrada de T-365 (distritos por época).

## Regla
0. **Secciones no listadas (D-128 ampliada).** El seccionado INE del año de la fuente (2015-12→2015, 2016-06→2016, 2019-04→2019,
   2019-11→2020; sha256 verificado) define qué secciones existen. Una sección del seccionado que el Atlas de ese año no trae con valor
   —no listada **o listada como vacío `""`**— se estima como una «.» y lleva `origen=no_listada` (el método está en `años_fuente`);
   nunca población 0 ni fusión de secciones. Un vacío sin sección en el seccionado sigue siendo sección inexistente (no aparece).
   Hallazgo medido: en el CSV 30832 las 28 secciones que el seccionado 2020 tiene y T-365 no casaba para 2019-11 están como `""` (no
   «no listadas»), y las 28 tienen dato en otros años; por eso `no_listada` cubre ambos casos. Falla cerrado si falta o no se lee el
   seccionado, o si > 1 % de las secciones de un lado no tiene pareja en el otro. Las secciones de la fuente que el seccionado no
   tiene (p. ej. 52 en 2019-11) se MANTIENEN con su población y se cuentan en `secciones_sin_seccionado` (decisión pendiente). 2011-11
   no usa seccionado (el Censo 2011 es el universo; seccionado a la fecha de esa elección NO VERIFICADO).
1. «.» (no publicado) y secciones no listadas → **interpolación lineal** entre el año anterior y el siguiente más próximos con dato
   de ESA misma sección (redondeo half-up entero); solo dato en un lado → año más cercano con dato (`mas_cercana`, o `no_listada` si
   venía del seccionado); ninguno → `sin_dato` (población vacía, nunca 0).
   `..` = «.».
2. **Ajuste proporcional por municipio** (solo elecciones con fuente Atlas): residuo = población oficial del municipio − suma de secciones de dato publicado.
   Con residuo > 0 las secciones ESTIMADAS (interpoladas, más cercanas y no listadas) se reescalan para sumar exactamente el residuo (restos mayores; empate: sección
   ascendente) y quedan `ajustada=sí`; las de dato publicado no se tocan. Si el residuo ya iguala la suma estimada: `cuadra`. **Aviso y sin ajuste**
   (`informe_municipios.csv`, `estado=aviso_*`) si residuo ≤ 0, el municipio tiene `sin_dato` (también si no tiene otras estimadas), o no figura en la fuente oficial.
3. Informe por provincia sobre población estimada (interpolada + más cercana + no listada, ya ajustada); MARCA si > 1 % o si hay `sin_dato`.

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
  --seccionados <dir con seccionado_AAAA.zip> --sumas docs/ESTUDIOS/T357_PADRON_SECCION_2011_2020/SHA256SUMS.txt docs/ESTUDIOS/T364_POBLACION_SECCION_INTERPOLADA/SHA256SUMS.txt --salida <dir>
```
**Interfaz para T-365 (estable)**: un CSV por elección, `poblacion_seccion_<AAAA-MM>.csv` (UTF-8, `\n`, orden por sección), columnas:
`sección` (10 dígitos INE) · `población` (entero; vacío si `sin_dato`) · `origen` (`dato`/`interpolada`/`mas_cercana`/`no_listada`/`sin_dato`) ·
`ajustada` (`sí`/`no`) · `años_fuente` (`dato`: año de la fuente; `interpolada`: `AAAA-AAAA`; `mas_cercana`: `AAAA`; `no_listada`: `AAAA-AAAA` o `AAAA` según el método; `sin_dato`: vacío).
**T-365 debe ejecutar la herramienta con `--estricto`**: si algún municipio de cualquier elección tiene aviso (residuo ≤ 0, `sin_dato` u ausente del
oficial, o secciones `sin_dato`) sale con código 2 y NO escribe las tablas por elección (solo los informes); así una tabla presente significa «0 avisos» (ejecución actual: 0).
Sin `--estricto` las tablas se escriben igualmente y los avisos solo constan en `informe_municipios.csv`/`municipios_aviso`.
Además `informe_provincias.csv` (en esta carpeta) e `informe_municipios.csv` (fuera del repo). Salida determinista (dos ejecuciones idénticas byte a byte).

## Resultado (ejecución del 2026-11-16, fuentes con sha256 de T-357/T-364 verificado; 2 corridas idénticas byte a byte)
Seccionados 2015, 2016, 2019 y 2020 descargados de `https://www.ine.es/prodyser/cartografia/seccionado_AAAA.zip` (sha256 de T-357 coinciden).

| Elección | Secciones | Interp. | Más cerc. | No listadas | Ajustadas | Sin dato | Sin seccionado | Población | Estimada | Prov. MARCA | Municipios aj./cuadran/aviso | Desajuste medio (personas) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2011-11 | 35 917 | 0 | 0 | 0 | 0 | 0 | — | 46 575 200 | 0 | 0 | sin ajuste (censo) | — |
| 2015-12 | 36 260 | 0 | 1 320 | 0 | 1 265 | 45 | 31 | 46 019 896 | 126 724 (0,28 %) | 25 | 1 237 / 55 / 36 | 12,9 |
| 2016-06 | 36 251 | 319 | 1 292 | 53 | 1 600 | 7 | 36 | 45 964 430 | 550 766 (1,20 %) | 14 | 1 307 / 62 / 4 | 41,9 |
| 2019-04 | 36 347 | 167 | 1 261 | 38 | 1 354 | 0 | 30 | 46 821 039 | 130 105 (0,28 %) | 12 | 1 337 / 99 / 3 | 20,6 |
| 2019-11 | 36 361 | 0 | 0 | 28 | 25 | 0 | 52 | 46 886 644 | 37 268 (0,08 %) | 0 | 22 / 0 / 3 | 1 409,5 |

(«Más cerc.» y «No listadas» son excluyentes: las no listadas llevan origen `no_listada` aunque se estimen por el año más cercano. «Ajustadas» incluye las no listadas ajustadas.)

**`--estricto` hoy FALLA (rc=2) y no escribe tablas: 46 municipios con aviso** — a decidir por el propietario:
- `aviso_sin_dato` 38 municipios (2015-12: 36; 2016-06: 2): 45 secciones de 2015 y 7 de 2016 existen en el seccionado y el Atlas no trae NINGÚN valor en ningún año (sin fuente
  para estimarlas; no se pone 0). Opción a valorar (no hecha): estimarlas con el Censo 2011 (`t1_1`).
- `aviso_residuo_no_positivo` 8 municipios (2016-06: 36016, 41059; 2019-04: 08245, 15041, 15061; 2019-11: 18116, 18135, 33016): la suma de las secciones de dato publicado ya iguala o
  supera la población oficial del municipio (p. ej. 33016: oficial 22 273, publicada 22 275); las estimadas (1 a 11 secciones por municipio) quedan sin ajustar.
- 2019-11 (la del piloto de T-365) tiene solo estos 3 avisos y 0 `sin_dato`: las 28 secciones antes sin población ya están estimadas.
Sin `--estricto` las tablas se escriben igualmente (los hashes de abajo son de esa ejecución sin `--estricto`).
Las 52 secciones de 2019-11 de la fuente sin sección en el seccionado 2020 se mantienen con su población (T-365 las verá como población sin geometría).

`informe_provincias.csv` (en esta carpeta) trae por provincia las columnas nuevas `secciones_no_listadas` y `secciones_sin_seccionado`.

Tablas completas (fuera del repo, reproducibles con el comando de arriba; el propietario decide R2): sha256
2011-11 `45aa3552592a8819beab26b2a885551fbe1e8ccba0ec68ac3ccbb7621f0496a3` · 2015-12 `34c0a1dd1407288a9219d78ccdaf15a69cdb0b023b88cd123718174726df0b34` ·
2016-06 `2654f579cd23f26c882b62fade93606b76d3652c922bfe685fd413ffe7c99f82` · 2019-04 `270061aea7f41f040657674d6b725811cf61e304e3d4a4e14100340fff06ed11` ·
2019-11 `c6eb6f8a839e2af650ee6d28cc0f69d38c05b2dd84305566f371b22684281555` · informe_provincias `62c941d3fe26d57b1fc4d7c3aaa30ae5caacc263423041ee2404ae4c9f472f5c` ·
informe_municipios `0a6748994667e5fc4e806d4a928ec9371a4c1a8f12da88aa0a89fedba1524b8e`.

Nota: `docs/ESTUDIOS/T358_POBLACION_SECCION_RELLENO/causa_relleno.py` es histórico: solo corre con la herramienta 1.0.0 (en `legacy/`); con la 1.1.0 aborta con un aviso.
