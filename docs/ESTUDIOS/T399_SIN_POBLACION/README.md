# T-399 · 2011-11: secciones del seccionado 2012 sin fila en la tabla del Censo (D-158, opción B')

Herramienta `herramientas/contrato_historico_epoca.py` 1.3.0, contratos 1.3.0. **B' = D-158 según el Coordinador/Planificador (17-11); pendiente de confirmar literal por el propietario** (PR con `no-automerge`). Sobre el análisis de `docs/ESTUDIOS/T399_2011_SIN_POBLACION/`. La opción A (seccionado del Censo y excepciones M07) queda retirada.

El seccionado de 2011-11 sigue siendo el de 2012. De las 105 secciones del seccionado sin fila en la tabla del Censo 2011:

1. **63 hijas** (la sección nueva parte una del Censo: cae ≥ 50 % de su área en una sección con población del mismo municipio, la **madre**; mayor solape): la población 2011 de la madre se reparte entre madre e hijas según el valor de cada una en el año más cercano del Atlas 30832 con dato (para 2011, el 2015; empate: el anterior; restos mayores). **Se conservan los totales del Censo** (por madre, municipio y provincia). Origen `repartida_madre`/`repartida_hija`. 58 madres con 61 hijas: pasan de las madres a las hijas 87.090 hab. de 177.790. Las 2 hijas restantes (0804703001 y 3605901003) no tienen dato en ningún año: sin dato, no se inventa.
2. **42 sin madre** (existen en la cartografía del Censo con su código pero sin fila en la tabla): D-126 (valor de la misma sección en el año más cercano del Atlas, `rellenada_año_cercano`: 47.083 hab.). **Ajuste municipal al total oficial del Censo 2011: sin ajuste, declarado**, porque no he localizado una tabla del INE con ese total y su sha256 (`Municipios_Censo_2011.xls` es la lista de códigos); el contrato declara `poblacion.total_municipal_oficial.fuente = null` y el código ajusta (restos mayores; residuo ≤ 0 → sin ajuste) en cuanto se le dé el total.
3. **Sin dato en ningún año → BLOQUEADA_SIN_DATO** (08 y 36).
4. **Votos:** con el seccionado 2012 solo 5 provincias pierden votos del Observatorio por encima del 0,1 % (03, 24, 27, 32, 33: 5.752 votos, máx. 0,54 % en 27). Se **APARTAN** (estado `APARTADA_VOTOS`, declaradas en el contrato con su medición y la fuente `docs/ESTUDIOS/T399_2011_SIN_POBLACION/votos_fuera_del_seccionado.csv` con sha256). **D-70 (`historico_campana.D70`) no se toca y no hay excepciones nuevas en la puerta.**
5. La población que el contrato declara de cada madre se verifica al construirlo contra el Censo 2011 acreditado (`indicadores_seccion_censal_csv.zip`, sha256 de T-357; `poblacion.madres_verificadas_contra_censo`), no solo contra la tabla. El semáforo (`campana_estado.py`) aún no lee estados de contratos históricos: cuando T-378 lo haga, `APARTADA_VOTOS` (no LISTA, no declarable) debe ser causa roja; un test lo vigila.
6. `materializar` solo aplica lo declarado y falla cerrado si la madre no tiene la población declarada, si la suma no cuadra o si una hija ya tiene fila.

## Resultado en 2011-11
39 LISTA, 6 BLOQUEADA_RELLENO (15, 22, 29, 34, 47, 51), 5 APARTADA_VOTOS (03, 24, 27, 32, 33) y 2 BLOQUEADA_SIN_DATO (08, 36). `materializar`: 38 de 52 provincias OK (antes 2); no materializan las 13 no LISTA y la 35 (puente de La Graciosa: T-400). Las otras 4 elecciones solo cambian de versión y regla.

**Criterio del 1 % (a decidir):** se aplica el precedente de D-128 («criterio conservador»): madre e hijas cuentan ENTERAS como estimadas, lo que bloquea por relleno a 15, 22, 29, 34, 47 y 51 (1,37-3,04 %). Si solo contara la población movida a las hijas más la rellenada, solo 36 (2,64 %) y 51 (1,70 %) superarían el 1 %.

Motor real (`cadena`, M01-M08, con la normalización de geometría de T-402): nac10, 11, 21, 31, 37, 41, 43 y 45 dan `perdidos` = 0 y la puerta PASS. nac14 falla en M04 («invalid administrative component source binding») y nac07 (Baleares) en M04 («need=8 > unidades abiertas=0», islas): ajenos a D-158.

Informes (derivados del contrato, `informe_poblacion`): `informe_provincias.csv` y `cuadre_municipal.csv`.
