# T-364 · Población por sección: interpolación y ajuste municipal (D-128)

Versión: 1.2.0 (T-364b) de `herramientas/poblacion_seccion_historica.py` (1.0.0 y 1.1.0 en `legacy/herramientas/`) · 2026-11-16 · Solo cálculo; sin ejecuciones ni publicación.
Sustituye la regla de relleno de D-126 (año más cercano). Entrada de T-365 (distritos por época).

## Regla
0. **Secciones no listadas (D-128 ampliada).** El seccionado INE del año de la fuente (2015-12→2015, 2016-06→2016, 2019-04→2019,
   2019-11→2020; sha256 verificado) define qué secciones existen. Una sección del seccionado que el Atlas de ese año no trae con valor
   —no listada **o listada como vacío `""`**— se estima como una «.» y lleva `origen=no_listada` (el método está en `años_fuente`);
   nunca población 0 ni fusión de secciones. Un vacío sin sección en el seccionado sigue siendo sección inexistente (no aparece).
   Hallazgo medido: en el CSV 30832 las 28 secciones que el seccionado 2020 tiene y T-365 no casaba para 2019-11 están como `""` (no
   «no listadas»), y las 28 tienen dato en otros años; por eso `no_listada` cubre ambos casos. Falla cerrado si falta o no se lee el
   seccionado, o si > 1 % de las secciones de un lado no tiene pareja en el otro. Las secciones de la fuente que el seccionado no
   tiene (52 en 2019-11) se tratan en el paso 4. 2011-11 no usa seccionado (el Censo 2011 es el universo; seccionado a la fecha de
   esa elección NO VERIFICADO).
1. «.» (no publicado) y secciones no listadas → **interpolación lineal** entre el año anterior y el siguiente más próximos con dato
   de ESA misma sección (redondeo half-up entero); solo dato en un lado → año más cercano con dato (`mas_cercana`, o `no_listada` si
   venía del seccionado); ninguno → `sin_dato` (población vacía, nunca 0).
   `..` = «.».
2. **Ajuste proporcional por municipio** (solo elecciones con fuente Atlas): residuo = población oficial del municipio − suma de secciones de dato publicado.
   Con residuo > 0 las secciones ESTIMADAS (interpoladas, más cercanas y no listadas) se reescalan para sumar exactamente el residuo (restos mayores; empate: sección
   ascendente) y quedan `ajustada=sí`; las de dato publicado no se tocan. Si el residuo ya iguala la suma estimada: `cuadra`. **Aviso y sin ajuste**
   (`informe_municipios.csv`, `estado=aviso_*`) si residuo ≤ 0, el municipio tiene `sin_dato` (también si no tiene otras estimadas), o no figura en la fuente oficial.
   **(a) T-364b: el aviso NO bloquea**: las estimadas del municipio conservan el valor interpolado (nunca 0) y salen con `ajustada=sin_ajuste_municipal`.
   Las `reasignada` cuentan como población real (fija) en el residuo.
4. **Secciones de la fuente que no existen en el seccionado del año (c)**: su población pasa ENTERA a la sección sucesora y la sucesora sale con
   `origen=reasignada` (con dato propio: suma; si era estimada o sin_dato: la sustituye, porque manda el dato real de la zona). La sucesora es la de
   mayor peso de población según `herramientas/equivalencia_seccionados.equivalencia` (a(h∩v)/a(v)·pob(v), no el área) con la geometría de la sección
   tomada del seccionado MÁS CERCANO en años que la tenga (empate: el anterior) y las del seccionado del año; peso de población = la población de la
   propia tabla. **Sin sucesora única** (empate de pesos, sin geometría en ningún seccionado, sin sección vigente o sucesora fuera del seccionado) →
   provincia APARTADA. La sección original desaparece de la tabla. **Condiciones y contabilidad declaradas:**
   - La sucesora debe ser de la MISMA provincia (si no, provincia APARTADA). Si es de otro MUNICIPIO (segregaciones: el seccionado del año es anterior
     al municipio nuevo; en la ejecución actual 7 secciones de 2015-12 y 6 de 2016-06, de las que solo 1 cae en una provincia no apartada: la 10 de 2015-12) se acepta y se cuenta en `reasignadas_otro_municipio`: la suma
     de la provincia se conserva y la del municipio no (el municipio receptor suma de más; si su residuo sale ≤ 0 es el aviso `sin_ajuste_municipal`).
   - **Conservación**: con sucesora de dato propio se conserva la suma por municipio y provincia; con sucesora ESTIMADA (o `sin_dato`) la
     estimación se DESCARTA y entra el dato real de la sección desaparecida, así que la suma cambia en (dato real − estimación). Si ese municipio acaba con
     residuo ≤ 0 (`sin_ajuste_municipal`) su suma puede no cuadrar con la oficial: queda registrado en `informe_municipios.csv`.
   - **Criterio conservador del 1 %**: una sucesora con dato propio pasa a `reasignada` y cuenta ENTERA como estimada (no se prorratea la parte de dato real).
   Limitación: si una sección vieja se fusiona con otras, solo la de mayor peso recibe la
   población y las demás siguen con su estimación (el ajuste municipal acota la suma).
5. **Provincias APARTADAS (b y c)**: provincia-elección con alguna sección `sin_dato` (sin valor en NINGÚN año del Atlas; no se inventa) o con una sección
   sin sucesora única. Sus filas NO van en `poblacion_seccion_<AAAA-MM>.csv` (el consumidor las ve como provincia sin filas → `BLOQUEADA_SIN_DATO`)
   y `informe_provincias.csv` las marca `estado=APARTADA` con el `motivo`; no frenan a las demás. `--estricto` sale con 2 si hay alguna apartada
   (las tablas se escriben igualmente).
6. Informe por provincia sobre población estimada (interpolada + más cercana + no listada, ya ajustada); MARCA si > 1 % o si hay `sin_dato`.

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
`sección` (10 dígitos INE) · `población` (entero; vacío si `sin_dato`) · `origen` (`dato`/`interpolada`/`mas_cercana`/`no_listada`/`reasignada`/`sin_dato`) ·
`ajustada` (`sí`/`no`/`sin_ajuste_municipal`) · `años_fuente` (`dato`: año de la fuente; `interpolada`: `AAAA-AAAA`; `mas_cercana`: `AAAA`; `no_listada`: `AAAA-AAAA` o `AAAA` según el método; `reasignada`: año(s) de la fuente de las secciones reasignadas; `sin_dato`: vacío).
**Cambio de T-364b**: las tablas se escriben SIEMPRE (con o sin `--estricto`); `--estricto` solo da código 2 si alguna provincia-elección queda APARTADA
(sin filas en su tabla). Los avisos de municipio ya no bloquean: constan como `sin_ajuste_municipal` y en `informe_municipios.csv`/`municipios_aviso`.
El consumidor (`contrato_historico_epoca.leer_tabla`) lee `sección`, `población` y `origen`: cualquier `origen != dato` cuenta como no dato en el umbral del 1 %.
Además `informe_provincias.csv` (en esta carpeta) e `informe_municipios.csv` (fuera del repo). Salida determinista (dos ejecuciones idénticas byte a byte).

## Resultado (T-364b, ejecución del 2026-11-16, fuentes con sha256 verificado; 2 corridas idénticas byte a byte)
Seccionados 2015, 2016, 2019, 2020 (el del año) y 2012, 2021, 2022 (donantes de geometría) de `https://www.ine.es/prodyser/cartografia/seccionado_AAAA.zip`;
los de 2021 y 2022 se miden aquí (`SHA256SUMS.txt`). Las 52 secciones de 2019-11 sin pareja en el seccionado 2020 existen en el 2021 (el CSV 30832 usa
los códigos del seccionado 2021: 36 333 secciones).

| Elección | Secciones (informe) | Interp. | Más cerc. | No listadas | Reasignadas | Sin dato | Prov. apartadas | Población (prov. no apartadas) | Estimada | Prov. MARCA | Municipios aj./cuadran/aviso |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2011-11 | 35 917 | 0 | 0 | 0 | 0 | 0 | 0 | 46 575 200 | 0 | 0 | sin ajuste (censo) |
| 2015-12 | 36 229 | 0 | 1 314 | 0 | 29 | 43 | 13 | 34 212 416 | 146 524 (0,43 %) | 12 | 1 236 / 55 / 35 |
| 2016-06 | 36 216 | 317 | 1 290 | 47 | 35 | 7 | 2 | 43 881 195 | 615 357 (1,40 %) | 17 | 1 306 / 62 / 4 |
| 2019-04 | 36 317 | 167 | 1 261 | 38 | 30 | 0 | 0 | 46 821 039 | 224 698 (0,48 %) | 17 | 1 337 / 99 / 3 |
| 2019-11 | 36 309 | 0 | 0 | 28 | 47 | 0 | 0 | 46 886 644 | 187 888 (0,40 %) | 6 | 22 / 0 / 3 |

Filas escritas en las tablas: 35 917 · 27 196 · 34 544 · 36 317 · 36 309. 2019-11 y 2019-04 quedan sin provincias apartadas y con exactamente las secciones de
su seccionado (36 309 y 36 317). La tabla de 2019-11 trae 36 234 `dato`, 47 `reasignada` (52 secciones del Atlas → 47 sucesoras) y 28 `no_listada`;
`ajustada`: 25 `sí`, 3 `sin_ajuste_municipal`.
**Apartadas (15)**: 2015-12 en 13 provincias (02, 04, 18, 20, 23, 24, 25, 27, 29, 33, 36, 46, 48) y 2016-06 en 2 (36, 48) por secciones `sin_dato` (43 en 2015, 7 en
2016: existen en el seccionado y el Atlas no trae NINGÚN valor en ningún año) y, en 2016-06 provincia 36, la sección 3690201004 sin geometría en ningún seccionado
(2012-2022). Motivo exacto en `informe_provincias.csv` (`estado`, `motivo`).
La columna «Prov. MARCA» cuenta solo provincias no apartadas; la población reasignada cuenta como estimada (por eso 2016-06 y 2019-04 suben a 17).

Tablas completas (fuera del repo, reproducibles con el comando de arriba; el propietario decide R2): sha256
2011-11 `45aa3552592a8819beab26b2a885551fbe1e8ccba0ec68ac3ccbb7621f0496a3` · 2015-12 `7d8a67dccaca7dd87fbde6bec8b4a13abed808dd8c028a6a429e00324c7909b3` ·
2016-06 `6941ae4af6b8b58ef31dfd7e1aca56d10632b864d59b8b92c55e3838100cd9a5` · 2019-04 `55048fe207e6ddc97653aa237f700bfa42800846848682aa59d17119f60677e7` ·
2019-11 `aef26748a31f9500efa8d9c30f9cf7b2e3a7312c41d214906a96141454acf56d` · informe_provincias `bba3fdd357233f526354cf5585cd6d224d86b706352fcb137662dbf2e579f0e0` ·
informe_municipios `61b32855d37b9771caa32a66ae74a5985d706ad9e5a6cdea4c552f697f3ea6b8`.

Nota: `docs/ESTUDIOS/T358_POBLACION_SECCION_RELLENO/causa_relleno.py` es histórico: solo corre con la herramienta 1.0.0 (en `legacy/`); con la 1.2.0 aborta con un aviso.
